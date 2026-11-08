"""Byline renderer v2: source talking-head video + plan.json -> finished reel.

Usage: python render.py plan.json
All times in plan.json are SOURCE-video seconds; cuts are applied automatically. Format: plan.example.json.
Style values come from ../style.json; plan["style"] overrides them (user's fonts, colours...).

v2 adds: per-word timed entrances with motion blur + land bounce, power-word glow pulse and underline sweep,
continuous push-in + impact bumps + shake, colour grade + vignette + grain, auto caption placement on the
calmest band (off hands/mic) with a soft scrim, auto SFX on every cut + risers before cards,
generated music bed with voice ducking, "stat" graphic element, watermark preservation.
"""
import json, os, re, subprocess, sys, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SFX

W, H, FPS, SR = 1080, 1920, 30, 48000
AF = 30  # animation timing base: durations written as 'frames at 30 fps', independent of output fps


def run(cmd):
    subprocess.run(cmd, check=True)


def load_style(plan):
    sp = plan.get("style_path")
    st = json.load(open(sp if sp and os.path.isabs(sp) else os.path.join(HERE, "..", "style.json") if not sp else os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), sp)))
    for k, v in plan.get("style", {}).items():
        if isinstance(v, dict) and isinstance(st.get(k), dict):
            st[k].update(v)
        else:
            st[k] = v
    return st


def hex_rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgba_css(s):
    v = [x.strip() for x in s[s.index("(") + 1:s.index(")")].split(",")]
    return tuple(int(x) for x in v[:3]) + (float(v[3]),)


def ease_out(p):
    p = min(max(p, 0), 1); return 1 - (1 - p) ** 3


class TimeMap:
    def __init__(self, cuts, dur, speed=1.0):
        self.speed = speed
        self.keep, t = [], 0.0
        for a, b in sorted(cuts):
            if a > t: self.keep.append((t, a))
            t = max(t, b)
        if t < dur: self.keep.append((t, dur))

    def __call__(self, ts):
        out = 0.0
        for a, b in self.keep:
            if ts <= b: return (out + max(ts - a, 0)) / self.speed
            out += b - a
        return out / self.speed

    @property
    def duration(self):
        return sum(b - a for a, b in self.keep) / self.speed


# ------------------------------------------------------------------ text
class Fonts:
    def __init__(self, st, font_dir):
        self.st, self.dir, self.cache = st, font_dir, {}

    def get(self, kind, size):
        key = (kind, size)
        if key not in self.cache:
            spec = self.st["fonts"][kind]
            f = ImageFont.truetype(os.path.join(self.dir, spec["file"]), size)
            if spec.get("weight"):
                try: f.set_variation_by_axes([spec["weight"]])
                except Exception: pass
            self.cache[key] = f
        return self.cache[key]

    def tracking(self, kind):
        return self.st["fonts"][kind].get("tracking", 0)


def word_img(fonts, text, kind, size, color=(255, 255, 255)):
    """Render one word -> (RGBA, baseline offset from top, advance width)."""
    f = fonts.get(kind, size); tr = fonts.tracking(kind) * size
    pad = int(size * 0.6)
    width = int(sum(f.getlength(c) + tr for c in text)) + 2 * pad
    canvas = Image.new("RGBA", (max(width, 4), int(size * 2.2) + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas); base = pad + int(size * 1.3); x = pad
    for ch in text:
        d.text((x, base), ch, font=f, fill=color + (255,), anchor="ls"); x += f.getlength(ch) + tr
    return canvas, base, x - pad


def styled(img, shadow=True, glow=0.0, glow_px=18):
    a = img.split()[3]
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    if glow:
        g = a.filter(ImageFilter.GaussianBlur(glow_px)).point(lambda v: int(min(255, v * glow)))
        out = Image.alpha_composite(out, Image.merge("RGBA", (*[Image.new("L", img.size, 255)] * 3, g)))
    if shadow:
        s = a.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.7))
        out.alpha_composite(Image.merge("RGBA", (*[Image.new("L", img.size, 0)] * 3, s)), (0, 3))
    return Image.alpha_composite(out, img)


def land(img, p, rise=40, blur=22, s_from=1.28):
    """Word entrance: drops in from above with vertical motion blur, overshoots, lands. p 0..1 over 6 frames.
    Returns (image, dy)."""
    if p >= 1: return img, 0
    p = max(p, 0)
    s = s_from + (0.96 - s_from) * (p / 0.65) if p < 0.65 else 0.96 + 0.04 * ((p - 0.65) / 0.35)
    w, h = max(1, int(img.width * s)), max(1, int(img.height * s))
    im = img.resize((w, h), Image.BILINEAR)
    mb = int(blur * (1 - ease_out(p)))
    if mb > 1:  # vertical motion blur: average of shifted copies
        acc = Image.new("RGBA", (w, h + mb), (0, 0, 0, 0))
        n = 5
        for k in range(n):
            layer = Image.new("RGBA", acc.size, (0, 0, 0, 0)); layer.alpha_composite(im, (0, int(k * mb / (n - 1))))
            layer.putalpha(layer.split()[3].point(lambda v: v // n))
            acc = Image.alpha_composite(acc, layer)
        im = acc
    im.putalpha(im.split()[3].point(lambda v: int(v * min(1, p * 2.2))))
    return im, -rise * (1 - ease_out(p))


def scale_fade(img, p, s0=0.0, s1=1.12):
    """Pop entrance for chips/stats: scale 0 -> overshoot -> 1."""
    if p >= 1: return img
    p = max(p, 0)
    s = s0 + (s1 - s0) * (p / 0.6) if p < 0.6 else s1 + (1 - s1) * ((p - 0.6) / 0.4)
    w, h = max(1, int(img.width * s)), max(1, int(img.height * s))
    im = img.resize((w, h), Image.BILINEAR)
    im.putalpha(im.split()[3].point(lambda v: int(v * min(1, p * 2))))
    return im


def pill(fonts, text, colors, glow, st):
    c = st["chips"]
    t_img, base, adv = word_img(fonts, text, c["font"], c["px"])
    bb = t_img.getbbox(); t_img = t_img.crop(bb)
    ph, pw = c["padding_px"]
    w, h = t_img.width + 2 * pw, t_img.height + 2 * ph
    m = 70
    img = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    g = Image.new("L", img.size, 0); ImageDraw.Draw(g).rounded_rectangle((m, m, m + w, m + h), h // 2, fill=255)
    g = g.filter(ImageFilter.GaussianBlur(c["glow_px"])).point(lambda v: int(v * glow[3]))
    img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", img.size, v) for v in glow[:3]], g)))
    c0, c1 = np.array(hex_rgb(colors[0])), np.array(hex_rgb(colors[1]))
    body = np.repeat((np.linspace(0, 1, w)[None, :, None] * (c1 - c0) + c0), h, axis=0)
    hl = np.ones((h, w, 1)); hl[: int(h * 0.42)] = 1.18
    body = np.clip(body * hl, 0, 255).astype(np.uint8)
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=255)
    b = Image.fromarray(body, "RGB").convert("RGBA"); b.putalpha(mask)
    img.alpha_composite(b, (m, m)); img.alpha_composite(t_img, (m + pw, m + ph))
    return img


def ease_out_back(u, c1=1.45):
    u = min(max(u, 0), 1); c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def ease_out_expo(u):
    u = min(max(u, 0), 1); return 1 if u >= 1 else 1 - 2 ** (-10 * u)


def ease_in_cubic(u):
    u = min(max(u, 0), 1); return u ** 3


def shimmer(layer, u, strength=0.6):
    """A soft diagonal light band sweeping across an element (u: 0..1), clipped to its alpha."""
    if not (0 < u < 1): return layer
    w, h = layer.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    pos = (-0.4 + 1.8 * u) * (w + 0.5 * h)
    band = np.exp(-(((xx + 0.5 * yy) - pos) / (0.16 * w + 1)) ** 2)
    a = np.asarray(layer.split()[3], np.float32) / 255
    al = (band * a * strength * 255).astype(np.uint8)
    hl = Image.merge("RGBA", (*[Image.new("L", layer.size, 255)] * 3, Image.fromarray(al)))
    return Image.alpha_composite(layer, hl)


def spring(p, keys=(0.80, 0.98, 1.05, 1.0)):
    """Piecewise spring through keyframes over p in 0..1 (e.g. 4 frames: 80% -> overshoot -> 100%)."""
    p = min(max(p, 0), 1)
    if p >= 1: return keys[-1]
    x = p * (len(keys) - 1); i = int(x); f = x - i
    f = 0.5 - 0.5 * np.cos(np.pi * f)
    return keys[i] + (keys[i + 1] - keys[i]) * f


def tight_shadow(img, st):
    sh = st["captions"].get("shadow_tight", {"blur": 2, "opacity": 0.85, "dy": 2})
    a = img.split()[3]
    s = a.filter(ImageFilter.GaussianBlur(sh["blur"])).point(lambda v: int(v * sh["opacity"]))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(Image.merge("RGBA", (*[Image.new("L", img.size, 0)] * 3, s)), (0, sh["dy"]))
    return Image.alpha_composite(out, img)


def draw_icon(kind, size, color=(255, 255, 255)):
    """Small line icons drawn at 4x and downsampled (smooth edges)."""
    S = size * 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = color + (255,)
    if kind == "play":
        d.rounded_rectangle((S * .04, S * .14, S * .96, S * .86), int(S * .2), outline=c, width=int(S * .09))
        d.polygon([(S * .40, S * .33), (S * .40, S * .67), (S * .68, S * .5)], fill=c)
    elif kind == "pin":
        d.ellipse((S * .26, S * .04, S * .74, S * .52), fill=c)
        d.polygon([(S * .38, S * .45), (S * .62, S * .45), (S * .5, S * .96)], fill=c)
        d.ellipse((S * .40, S * .18, S * .60, S * .38), fill=(0, 0, 0, 0))
    elif kind == "check":
        d.line([(S * .12, S * .52), (S * .40, S * .80), (S * .88, S * .22)], fill=c, width=int(S * .14), joint="curve")
    elif kind == "heart":
        d.polygon(heart_pts(S * .5, S * .52, S * .42), fill=c)
    return im.resize((size, size), Image.LANCZOS)


def heart_pts(cx, cy, r, n=80):
    t = np.linspace(0, 2 * np.pi, n)
    x = 16 * np.sin(t) ** 3; y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    return [(cx + r * xi / 17, cy - r * yi / 17) for xi, yi in zip(x, y)]


def chip_flat(fonts, text, color, st, shape="pill", icon=None, text_color=(255, 255, 255)):
    c = st["chips"]
    t_img, base, adv = word_img(fonts, text, c.get("pop_font", "sans"), c.get("pop_px", 58), color=text_color)
    bb = t_img.getbbox(); t_img = t_img.crop(bb)
    if icon:
        ic = draw_icon(icon, int(t_img.height * 1.05), text_color)
        gap = int(t_img.height * 0.45)
        comb = Image.new("RGBA", (ic.width + gap + t_img.width, max(ic.height, t_img.height)), (0, 0, 0, 0))
        comb.alpha_composite(ic, (0, (comb.height - ic.height) // 2)); comb.alpha_composite(t_img, (ic.width + gap, (comb.height - t_img.height) // 2))
        t_img = comb
    ph, pw = c["padding_px"]
    w, h = t_img.width + 2 * pw, t_img.height + 2 * ph
    img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    r = h // 2 if shape == "pill" else c.get("box_radius", 22)
    sh = Image.new("L", img.size, 0); ImageDraw.Draw(sh).rounded_rectangle((10, 14, 10 + w, 14 + h), r, fill=90)
    img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", img.size, 0)] * 3, sh.filter(ImageFilter.GaussianBlur(4)))))
    ImageDraw.Draw(img).rounded_rectangle((10, 10, 10 + w, 10 + h), r, fill=hex_rgb(color) + (255,))
    img.alpha_composite(t_img, (10 + pw, 10 + ph))
    return img


def scrim(w, h, strength=0.42):
    yy, xx = np.mgrid[0:h, 0:w]
    d = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    a = np.clip(1 - d, 0, 1) ** 1.6 * 255 * strength
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


# ------------------------------------------------------------------ main
def main(plan_path):
    global FPS
    plan = json.load(open(plan_path))
    FPS = plan.get("fps", 30)
    st = load_style(plan)
    wd = os.path.dirname(os.path.abspath(plan_path))
    src = os.path.join(wd, plan["source"])
    fonts = Fonts(st, os.path.join(wd, plan.get("font_dir", "fonts")))
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
    speed = plan.get("speed", 1.0)
    interp_mode = plan.get("interp", "mci")
    tm = TimeMap(plan.get("cuts", []), dur, speed); T = tm
    cs, cam, gr = st["captions"], st["camera"], st.get("grade", {})

    # 1) base: cut dead air, grade, 1080x1920@30
    vf, af = [], []
    for i, (a, b) in enumerate(tm.keep):
        vf.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]"); af.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}]")
    n = len(tm.keep)
    grade = gr.get("ffmpeg", "eq=contrast=1.10:brightness=-0.015:saturation=1.10,unsharp=5:5:0.5")
    fcv = ";".join(vf) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v];[v]setpts=PTS/{speed}," + (f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" if interp_mode == "mci" else f"fps={FPS}") + f",scale={W}:{H}:flags=lanczos[vs];[vs]{grade}[vo]"
    fca = ";".join(af) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a];[a]atempo={speed},loudnorm=I=-14:TP=-1.5:LRA=11,aresample={SR}[ao]"
    base = os.path.join(wd, "_base.mp4"); ungraded = os.path.join(wd, "_raw.mp4"); voice = os.path.join(wd, "_voice.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fcv, "-map", "[vo]", "-an", "-c:v", "libx264", "-crf", "12", base])
    fcr = fcv.replace(f"[vs];[vs]{grade}[vo]", "[vo]")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fcr, "-map", "[vo]", "-an", "-c:v", "libx264", "-crf", "12", ungraded])
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fca, "-map", "[ao]", "-ac", "1", voice])
    nfr = int(tm.duration * FPS)

    # 2) face + calmest caption band
    cap = cv2.VideoCapture(base); faces, samples = [], []
    for k in range(0, nfr, 10):
        cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); samples.append(g)
        if hasattr(cv2, "CascadeClassifier"):
            det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml").detectMultiScale(g, 1.1, 5, minSize=(160, 160))
            if len(det): faces.append(max(det, key=lambda r: r[2] * r[3]))
    cap.release()
    fx, fy, fw, fh = np.median(np.array(faces), axis=0) if faces else (W * 0.35, H * 0.2, W * 0.3, W * 0.3)
    anchor = plan.get("zoom_anchor", [fx + fw / 2, fy + fh / 2])
    chin = fy + fh * 1.15
    if "caption_y" in plan:
        cap_base = plan["caption_y"] * H
    else:  # pick the band with the least motion + detail (hands, mic) among candidates
        cands = [chin + 0.07 * H, 0.52 * H, 0.64 * H]
        stack = np.array(samples, np.float32)
        motion = np.abs(np.diff(stack, axis=0)).mean(0) if len(stack) > 1 else np.zeros_like(stack[0])
        detail = np.mean([np.abs(cv2.Laplacian(s, cv2.CV_32F)) for s in samples], axis=0)
        score = lambda y: float(motion[int(y - 70):int(y + 50), 140:940].mean() * 3 + detail[int(y - 70):int(y + 50), 140:940].mean())
        cap_base = min(cands, key=score)
    cap_base = min(max(cap_base, 0.36 * H), 0.66 * H)

    # 3) timeline
    words = json.load(open(os.path.join(wd, plan["words_file"]))) if plan.get("words_file") else []
    wi = 0
    norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
    caps = []
    for c in plan.get("captions", []):
        times = c.get("times")
        if not times:
            times = []
            for w in c["words"]:
                j = next((k for k in range(wi, min(wi + 6, len(words))) if norm(words[k]["w"]) == norm(w)), None)
                if j is not None: times.append(words[j]["s"]); wi = j + 1
                else: times.append(None)
            k0 = c["t0"]
            times = [t if t is not None else k0 + (c["t1"] - k0) * i / len(c["words"]) for i, t in enumerate(times)]
        caps.append(dict(c, t0=T(c["t0"]), t1=T(c["t1"]), wt=[T(max(t, c["t0"])) for t in times]))
    cards = [dict(c, t0=T(c["t0"]), t1=T(c["t1"])) for c in plan.get("cards", [])]
    chips = [dict(c, t0=T(c["t0"]), t1=T(c["t1"]), items=[dict(i, t=T(i["t"])) for i in c["items"]]) for c in plan.get("chips", [])]
    stats = [dict(s, t0=T(s["t0"]), t1=T(s["t1"])) for s in plan.get("stats", [])]
    bw = [(T(a), T(b)) for a, b in plan.get("bw", [])]
    scales = sorted([(T(t), s) for t, s in plan.get("scales", [[0, 1.0]])])
    cta = plan.get("cta")
    if cta: cta = dict(cta, t0=T(cta["t0"]))

    # impacts: power-word landings (bump) and low hits (shake)
    bumps = [c["wt"][i] for c in caps for i in c.get("power", [])] + [s["t0"] for s in stats]
    shakes = [T(t) for t, nm in plan.get("sfx", []) if nm == "low_hit"]

    # pre-render
    gap = cs["sans_px"] * 0.26
    for c in caps:
        c["w"] = []
        for i, w in enumerate(c["words"]):
            pw = i in c.get("power", [])
            img, bo, adv = word_img(fonts, w, "serif" if pw else "sans", cs.get("serif_px", int(cs["sans_px"] * 1.2)) if pw else cs["sans_px"])
            c["w"].append(dict(img=styled(img), glow=styled(img, shadow=False, glow=0.9, glow_px=22) if pw else None,
                               bo=bo, adv=adv, power=pw))
        tot = sum(x["adv"] for x in c["w"]) + gap * (len(c["w"]) - 1)
        x = W / 2 - tot / 2
        for x_ in c["w"]: x_["x"] = x; x += x_["adv"] + gap
        c["width"] = tot
        g, gbo, gadv = word_img(fonts, " ".join(c["words"]), "sans", cs.get("ghost_px", 50))
        g = styled(g); g.putalpha(g.split()[3].point(lambda v: int(v * 0.38))); c["ghost"], c["gbo"] = g, gbo
    for c in cards:
        spec = st["word_cards"][c["bg"]]
        img, bo, adv = word_img(fonts, c["text"], spec["font"], spec["px"], color=hex_rgb(spec["color"]))
        c["img"], c["bgc"] = img, hex_rgb(spec["bg"])
    for c in chips:
        col = st["colors"]["chip_" + c.get("color", "blue")]; gl = rgba_css(st["colors"]["chip_" + c.get("color", "blue") + "_glow"])
        for it in c["items"]: it["img"] = pill(fonts, it["text"], col, gl, st)
    blue = hex_rgb(st["colors"]["chip_blue"][0])
    word_pop = cs.get("mode", "pop") == "word_pop"
    pop = cs.get("mode", "pop") in ("pop", "word_pop")
    if word_pop:
        pcol = hex_rgb(cs.get("power_color", "#FFD700"))
        for c in caps:
            c["pw"] = []
            for i_, w_ in enumerate(c["words"]):
                pw_ = i_ in c.get("power", [])
                size = int(cs["sans_px"] * cs.get("power_scale", 2.5)) if pw_ else cs["sans_px"]
                txt_ = w_.upper() if (pw_ and cs.get("power_upper", False)) else w_
                im_, bo_, adv_ = word_img(fonts, txt_, "sans", size, color=pcol if pw_ else (255, 255, 255))
                if pw_ and adv_ > cs.get("max_width", 960):  # fit very long power words
                    k_ = cs.get("max_width", 960) / adv_; size = int(size * k_)
                    im_, bo_, adv_ = word_img(fonts, txt_, "sans", size, color=pcol)
                if pw_:
                    a_ = im_.split()[3]
                    gb = cs.get("glow_blur_px")
                    if gb:
                        big = Image.new("L", (im_.width + 4 * gb, im_.height + 4 * gb), 0); big.paste(a_, (2 * gb, 2 * gb))
                        im2 = Image.new("RGBA", big.size, (0, 0, 0, 0)); im2.alpha_composite(im_, (2 * gb, 2 * gb)); im_ = im2; bo_ += 2 * gb
                        a_ = big
                        gl_ = a_.filter(ImageFilter.GaussianBlur(gb)).point(lambda v: int(min(255, v * cs.get("glow_strength", 1.6))))
                        glow = Image.merge("RGBA", (*[Image.new("L", im_.size, v) for v in pcol], gl_))
                    else:
                        g1 = a_.filter(ImageFilter.GaussianBlur(size * 0.10)).point(lambda v: int(min(255, v * 1.3)))
                        g2 = a_.filter(ImageFilter.GaussianBlur(size * 0.28)).point(lambda v: int(v * 0.7))
                        glow = Image.new("RGBA", im_.size, (0, 0, 0, 0))
                        for g_ in (g2, g1): glow = Image.alpha_composite(glow, Image.merge("RGBA", (*[Image.new("L", im_.size, v) for v in pcol], g_)))
                    im_ = Image.alpha_composite(glow, tight_shadow(im_, st))
                else:
                    im_ = tight_shadow(im_, st)
                c["pw"].append(dict(img=im_, bo=bo_, adv=adv_, power=pw_, size=size))
            gap_ = cs["sans_px"] * 0.30
            tot_ = sum(x["adv"] for x in c["pw"]) + gap_ * (len(c["pw"]) - 1)
            x_ = W / 2 - tot_ / 2
            for q_ in c["pw"]: q_["x"] = x_; x_ += q_["adv"] + gap_
    if pop and not word_pop:
        for c in caps:
            c["pw"] = []
            for i_, w_ in enumerate(c["words"]):
                pw_ = i_ in c.get("power", [])
                im_, bo_, adv_ = word_img(fonts, w_, "serif" if pw_ else "sans", int(cs["sans_px"] * cs.get("power_scale", 1.2)) if pw_ else cs["sans_px"])
                c["pw"].append(dict(img=tight_shadow(im_, st), bo=bo_, adv=adv_, power=pw_))
            gap_ = cs["sans_px"] * 0.28
            tot_ = sum(x["adv"] for x in c["pw"]) + gap_ * (len(c["pw"]) - 1)
            x_ = W / 2 - tot_ / 2
            for q_ in c["pw"]: q_["x"] = x_; x_ += q_["adv"] + gap_
    if pop:
        for c in chips:
            for it in c["items"]:
                ccol = it.get("color", c.get("color", "blue"))
                tcol = (17, 17, 20) if ccol == "white" else (255, 255, 255)
                it["img"] = chip_flat(fonts, it["text"], st["colors"]["chip_" + ccol][0], st, c.get("shape", "pill"), it.get("icon"), tcol)
    if pop and cta and cta.get("cycle"):
            bimg, bbo, _ = word_img(fonts, cta["word"].upper(), "serif", st["cta"]["big_px"])
            cta["bigp"], cta["bbo"] = tight_shadow(bimg, st), bbo
            cta["cyc"] = []
            for tt_, txt_ in cta["cycle"]:
                im_, bo_, _ = word_img(fonts, txt_, "sans", st["cta"]["small_px"])
                cta["cyc"].append((T(tt_), tight_shadow(im_, st), bo_))
            cta["t1"] = T(cta["t1"]) if "t1" in cta else 1e9
    for s in stats:
        big, bbo, badv = word_img(fonts, s["text"], "serif", s.get("px", 360))
        big = styled(big, glow=0.0)
        glow_layer = Image.new("RGBA", big.size, (0, 0, 0, 0))
        a = big.split()[3].filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.9))
        glow_layer = Image.merge("RGBA", (*[Image.new("L", big.size, v) for v in blue], a))
        s["img"] = Image.alpha_composite(glow_layer, big)
        lab, lbo, ladv = word_img(fonts, s.get("label", ""), "sans", cs["sans_px"] - 10)
        s["label_img"] = styled(lab)
    if cta:
        cimg, cbo, _ = word_img(fonts, st["cta"]["small"], "sans", st["cta"]["small_px"])
        kimg, kbo, _ = word_img(fonts, f"“{cta['word'].upper()}”", "serif", st["cta"]["big_px"])
        cta.update(small=styled(cimg), big=styled(kimg, glow=0.5), sbo=cbo, kbo=kbo)
    scr = scrim(980, 360)
    grain = [np.random.default_rng(k).normal(0, 1, (H // 2, W // 2)).astype(np.float32) for k in range(4)]
    vig = None

    # watermark patch (kept from the source frame, feathered)
    wm = plan.get("watermark")  # [x, y, r]
    if wm:
        r = int(wm[2]); yy, xx = np.mgrid[-r:r, -r:r]
        wm_mask = np.clip(1.3 - np.sqrt(xx ** 2 + yy ** 2) / r, 0, 1)[..., None].astype(np.float32)

    # motion graphics (counter, grid, button) - built from the style DNA
    red = hex_rgb(st["colors"]["chip_red"][0])
    graphics = []
    for g in plan.get("graphics", []):
        g = dict(g); g["t0"] = T(g["t0"]); g["t1"] = T(g["t1"])
        for key in ("strike_t", "click_t", "close_t", "check_t"):
            if key in g: g[key] = T(g[key])
        if g["type"] == "button":
            col = st["colors"]["chip_blue"]; gl = rgba_css(st["colors"]["chip_blue_glow"])
            g["img"] = pill(fonts, g["text"], col, gl, st)
        if g["type"] == "grid":
            n_, size = 3, g.get("size", 330); gap_ = size * 0.04; tile = (size - gap_ * 2) / 3
            tiles = []
            for r_ in range(3):
                for c_ in range(3):
                    tim = Image.new("RGBA", (int(tile), int(tile)), (0, 0, 0, 0))
                    shade = 150 + 25 * ((r_ + c_) % 3)
                    grad = np.linspace(shade + 30, shade - 30, int(tile))[:, None].repeat(int(tile), 1)
                    body = Image.fromarray(np.clip(grad, 0, 255).astype(np.uint8), "L").convert("RGBA")
                    m_ = Image.new("L", tim.size, 0); ImageDraw.Draw(m_).rounded_rectangle((0, 0, tim.width - 1, tim.height - 1), int(tile * 0.14), fill=235)
                    body.putalpha(m_); tiles.append((r_, c_, body))
            g.update(tiles=tiles, tile=tile, gap=gap_)
        graphics.append(g)

    def strike(img, x0, y0, x1, y1, q, width=12):
        if q <= 0: return
        xe, ye = x0 + (x1 - x0) * q, y0 + (y1 - y0) * q
        d = ImageDraw.Draw(img)
        d.line((x0, y0, xe, ye), fill=red + (240,), width=width)
        d.ellipse((x0 - width / 2, y0 - width / 2, x0 + width / 2, y0 + width / 2), fill=red + (240,))
        d.ellipse((xe - width / 2, ye - width / 2, xe + width / 2, ye + width / 2), fill=red + (240,))

    WHITE = (255, 255, 255)

    def drop_shadow(layer, blur=6, alpha=0.45, dy=6):
        a = layer.split()[3].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
        out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        out.alpha_composite(Image.merge("RGBA", (*[Image.new("L", layer.size, 0)] * 3, a)), (0, dy))
        return Image.alpha_composite(out, layer)

    def shape_layer(g, t, age):
        """Draw a shape graphic at 2x on its own layer (S = size). Returns RGBA at 1x or None."""
        S = g.get("size", 300); K = 2; L = S * K
        im = Image.new("RGBA", (int(L * (2.0 if g["type"] == "heart" else 1.4)), int(L * 1.4)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        o = L * 0.2  # margin
        typ = g["type"]
        if typ == "bars":
            hs = g.get("heights", [0.42, 0.68, 1.0]); n = len(hs); bw = L / (n * 1.45); gp = (L - n * bw) / max(n - 1, 1)
            for k, hf in enumerate(hs):
                gq = spring((age - k * 0.08) * AF / 7, (0.0, 0.8, 1.08, 0.98, 1.0))
                if gq <= 0: continue
                hh = L * hf * gq; x1 = o + k * (bw + gp)
                col = blue if k == g.get("highlight", n - 1) else WHITE
                d.rounded_rectangle((x1, o + L - hh, x1 + bw, o + L), int(bw * 0.22), fill=col + (255,))
        elif typ == "lock":
            ct = g.get("close_t", g["t0"] + 0.4)
            lift = L * 0.16 * (1 - spring((t - ct) * AF / 5, (0.0, 0.8, 1.08, 1.0))) if t >= ct else L * 0.16
            sw = int(L * 0.085)
            d.arc((o + L * .28, o + L * .06 - lift, o + L * .72, o + L * .58 - lift), 180, 360, fill=WHITE + (255,), width=sw)
            d.line((o + L * .28 + sw / 2, o + L * .32 - lift, o + L * .28 + sw / 2, o + L * .50), fill=WHITE + (255,), width=sw)
            d.line((o + L * .72 - sw / 2, o + L * .32 - lift, o + L * .72 - sw / 2, o + L * .50 - (lift if t < ct else 0)), fill=WHITE + (255,), width=sw)
            d.rounded_rectangle((o + L * .16, o + L * .44, o + L * .84, o + L * .98), int(L * .1), fill=WHITE + (255,))
            d.ellipse((o + L * .44, o + L * .60, o + L * .56, o + L * .72), fill=(15, 15, 18, 255))
            d.rounded_rectangle((o + L * .475, o + L * .68, o + L * .525, o + L * .84), int(L * .02), fill=(15, 15, 18, 255))
        elif typ == "heart":
            # heart outline on the left, number on the right; the pair is centred in the layer
            num, nbo, nadv = word_img(fonts, g.get("text", "0"), "sans", int(S * 0.62 * K))
            num = num.crop(num.getbbox())
            hw = L * .62; gap = L * .14; tot = hw + gap + num.width
            x0 = im.width / 2 - tot / 2; cy0 = im.height / 2
            d.polygon(heart_pts(x0 + hw / 2, cy0, hw * .48), outline=WHITE + (255,), width=int(L * .05))
            im.alpha_composite(num, (int(x0 + hw + gap), int(cy0 - num.height / 2)))
        elif typ == "calendar":
            d.rounded_rectangle((o, o, o + L, o + L * .9), int(L * .1), fill=WHITE + (245,))
            d.rounded_rectangle((o, o, o + L, o + L * .22), int(L * .1), fill=blue + (255,))
            d.rectangle((o, o + L * .12, o + L, o + L * .22), fill=blue + (255,))
            for ring_x in (.3, .7):
                d.rounded_rectangle((o + L * ring_x - L * .03, o - L * .06, o + L * ring_x + L * .03, o + L * .08), int(L * .03), fill=(200, 205, 215, 255))
            mark = g.get("mark", (1, 2)); ckt = g.get("check_t", g["t0"] + 0.4)
            for r_ in range(3):
                for c_ in range(4):
                    cx_ = o + L * (.17 + c_ * .22); cy_ = o + L * (.38 + r_ * .17); rr = L * .045
                    if (r_, c_) == tuple(mark) and t >= ckt:
                        q = spring((t - ckt) * AF / 6, (0.0, 0.8, 1.15, 1.0)); R = L * .085 * q
                        d.ellipse((cx_ - R, cy_ - R, cx_ + R, cy_ + R), fill=blue + (255,))
                        if q > 0.6:
                            ic = draw_icon("check", int(L * .11)); im.alpha_composite(ic, (int(cx_ - ic.width / 2), int(cy_ - ic.height / 2)))
                    else:
                        d.ellipse((cx_ - rr, cy_ - rr, cx_ + rr, cy_ + rr), fill=(190, 195, 205, 255))
        elif typ == "arrow":
            q = ease_out(age * AF / g.get("draw_frames", 10))
            pts = [(o + L * (0.05 + 0.9 * u), o + L * (0.8 - 0.75 * np.sin(np.pi * u * 0.6) * u)) for u in np.linspace(0, q, 30)]
            if len(pts) > 1:
                d.line(pts, fill=WHITE + (255,), width=int(L * .045), joint="curve")
                (x2, y2), (x1, y1) = pts[-1], pts[-2]; ang = np.arctan2(y2 - y1, x2 - x1); ah = L * .12
                d.polygon([(x2 + np.cos(ang) * ah * .3, y2 + np.sin(ang) * ah * .3),
                           (x2 + np.cos(ang + 2.5) * ah, y2 + np.sin(ang + 2.5) * ah),
                           (x2 + np.cos(ang - 2.5) * ah, y2 + np.sin(ang - 2.5) * ah)], fill=WHITE + (255,))
        else:
            return None
        im = im.resize((im.width // K, im.height // K), Image.LANCZOS)
        return drop_shadow(im)

    def draw_overlay_fx(img, g, t, age):
        """Ring that draws around a point (e.g. a power word) + burst lines. Drawn in place at 2x."""
        cx = W / 2; cyy = g.get("y", None)
        cyy = cyy * H if cyy is not None else cap_base - cs["sans_px"] * 0.38
        R = g.get("r", 120); K = 2
        lay = Image.new("RGBA", (int(R * 4 * K), int(R * 4 * K)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        C = lay.width / 2
        if g["type"] == "ring":
            q = ease_out(age * AF / g.get("draw_frames", 9))
            if q > 0:
                d.arc((C - R * K, C - R * K * 0.78, C + R * K, C + R * K * 0.78), -100, -100 + 360 * q,
                      fill=hex_rgb(g.get("color", "#2F7BFF")) + (255,), width=int(11 * K))
        if g["type"] in ("ring", "burst") and g.get("burst", g["type"] == "burst"):
            bq = age * AF / 9
            if 0 <= bq <= 1:
                for k in range(8):
                    a = 2 * np.pi * k / 8 + 0.3
                    r1 = R * K * (1.05 + 0.35 * ease_out(bq)); r2 = r1 + R * K * 0.28 * (1 - bq)
                    d.line((C + np.cos(a) * r1, C + np.sin(a) * r1 * 0.8, C + np.cos(a) * r2, C + np.sin(a) * r2 * 0.8),
                           fill=(255, 255, 255, int(255 * (1 - bq))), width=int(6 * K))
        lay = lay.resize((lay.width // K, lay.height // K), Image.LANCZOS)
        fo = 1 - ease_in_cubic((age - (g["t1"] - g["t0"] - 0.22)) / 0.22)
        if fo < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * max(fo, 0))))
        img.alpha_composite(lay, (int(cx - lay.width / 2), int(cyy - lay.height / 2)))

    def bounce_in(age, frames=9):
        return spring(age * AF / frames, (0.0, 0.7, 1.16, 0.95, 1.0))

    emoji_cache = {}

    def emoji_img(ch, size):
        if (ch, size) in emoji_cache: return emoji_cache[(ch, size)]
        res = None
        for path in ("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", os.path.join(wd, "fonts", "NotoColorEmoji.ttf")):
            if os.path.exists(path):
                try:
                    f_ = ImageFont.truetype(path, 109); im = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
                    ImageDraw.Draw(im).text((10, 10), ch, font=f_, embedded_color=True)
                    im = im.crop(im.getbbox()); res = im.resize((size, int(size * im.height / im.width)), Image.LANCZOS); break
                except Exception: pass
        emoji_cache[(ch, size)] = res
        return res

    def flame(size):
        K = 4; S_ = size * K; im = Image.new("RGBA", (S_, S_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        pts = [(S_ * .5, S_ * .02), (S_ * .78, S_ * .38), (S_ * .86, S_ * .66), (S_ * .7, S_ * .9), (S_ * .5, S_ * .98),
               (S_ * .3, S_ * .9), (S_ * .14, S_ * .66), (S_ * .24, S_ * .42), (S_ * .36, S_ * .52)]
        d.polygon(pts, fill=(255, 120, 20, 255))
        inner = [(S_ * .5, S_ * .36), (S_ * .68, S_ * .62), (S_ * .62, S_ * .86), (S_ * .5, S_ * .92), (S_ * .38, S_ * .86), (S_ * .32, S_ * .66)]
        d.polygon(inner, fill=(255, 215, 0, 255))
        return im.resize((size, size), Image.LANCZOS)

    def ember_graphic(img, g, t, age):
        """Ember UI widgets: progress bar, weekday calendar, polaroid PiP."""
        dur = g["t1"] - g["t0"]
        if cs.get("hard_exit"):
            out_k = 1.0; sc = spring(age * AF / cs.get("pop_frames", 4), tuple(cs.get("pop_keys", (0.0, 0.7, 1.16, 0.95, 1.0))))
        else:
            out_k = 1 - ease_in_cubic((age - (dur - 0.2)) / 0.2)
            sc = bounce_in(age) * (1 - 0.1 * ease_in_cubic((age - (dur - 0.2)) / 0.2))
        if sc <= 0.02 or out_k <= 0.01: return
        yel = hex_rgb(st["colors"].get("power", "#FFD700"))
        K = 2
        if g["type"] == "progress":
            Wd, Hd = 840, 210
            L = Image.new("RGBA", (Wd * K, Hd * K), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
            d.rounded_rectangle((0, 0, Wd * K - 1, Hd * K - 1), 44 * K, fill=(16, 16, 18, 225), outline=(255, 255, 255, 40), width=2 * K)
            lf = fonts.get("sans", 36 * K)
            d.text((44 * K, 58 * K), g.get("label", "PROGRESS"), font=lf, fill=(255, 255, 255, 235), anchor="lm")
            if "fill_t0" in g:
                q = min(1, max(0, (t - T(g["fill_t0"])) / max(T(g["fill_t1"]) - T(g["fill_t0"]), 0.1)))
            else:
                q = ease_out(min(1, max(0, (age - 0.25) / g.get("fill_s", 1.0))))
            pct = g.get("value", 0.9) * q
            d.text((Wd * K - 44 * K, 58 * K), f"{int(round(pct * 100))}%", font=lf, fill=yel + (255,), anchor="rm")
            x0, y0, x1, y1 = 44 * K, 116 * K, Wd * K - 44 * K, 160 * K
            d.rounded_rectangle((x0, y0, x1, y1), 22 * K, fill=(255, 255, 255, 30))
            xf = x0 + (x1 - x0) * pct
            if xf > x0 + 10:
                bar = Image.new("RGBA", L.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
                if g.get("fill") == "orange":
                    gr_ = np.linspace(0, 1, max(2, int(xf - x0)))[None, :, None] * (np.array(yel) - np.array([255, 110, 0])) + np.array([255, 110, 0])
                    gim = Image.fromarray(np.repeat(gr_, int(y1 - y0), 0).astype(np.uint8)).convert("RGBA")
                    mk = Image.new("L", gim.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, gim.width - 1, gim.height - 1), 22 * K, fill=255); gim.putalpha(mk)
                    bar.alpha_composite(gim, (int(x0), int(y0)))
                else:
                    bd.rounded_rectangle((x0, y0, xf, y1), 22 * K, fill=yel + (255,))
                gl = bar.split()[3].filter(ImageFilter.GaussianBlur(14 * K)).point(lambda v: int(v * 0.8))
                L.alpha_composite(Image.merge("RGBA", (*[Image.new("L", L.size, v) for v in yel], gl))); L.alpha_composite(bar)
            fl = emoji_img("🔥", 74 * K) if g.get("emoji", True) else None
            fl = fl or flame(70 * K)
            L.alpha_composite(fl, (int(xf - fl.width / 2), int((y0 + y1) / 2 - fl.height * 0.62)))
            L = L.resize((Wd, Hd), Image.LANCZOS)
        elif g["type"] == "week":
            days = g.get("days", ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"])
            Wd, Hd = 880, 250
            L = Image.new("RGBA", (Wd * K, Hd * K), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
            d.rounded_rectangle((0, 0, Wd * K - 1, Hd * K - 1), 40 * K, fill=(250, 250, 252, 245))
            tf = fonts.get("sans", 30 * K); nf = fonts.get("sans", 44 * K)
            if g.get("title"): d.text((44 * K, 48 * K), g["title"], font=fonts.get("sans", 32 * K), fill=(20, 20, 24, 255), anchor="lm")
            step = g.get("step_s", 0.18); cur = min(len(days) - 1, int(max(0, age - 0.3) / step))
            cw_ = (Wd * K - 88 * K) / len(days)
            for i_, dname in enumerate(days):
                cx_ = 44 * K + cw_ * (i_ + 0.5)
                d.text((cx_, 112 * K), dname, font=tf, fill=(140, 140, 150, 255), anchor="mm")
                num = str(g.get("start", 12) + i_)
                if i_ == cur:
                    R = 46 * K; d.ellipse((cx_ - R, 178 * K - R, cx_ + R, 178 * K + R), fill=(255, 61, 85, 255))
                    d.text((cx_, 178 * K), num, font=nf, fill=(255, 255, 255, 255), anchor="mm")
                else:
                    d.text((cx_, 178 * K), num, font=nf, fill=(20, 20, 24, 255) if i_ > cur else (190, 190, 198, 255), anchor="mm")
                    if i_ < cur: d.line((cx_ - 30 * K, 178 * K + 26 * K, cx_ + 30 * K, 178 * K - 26 * K), fill=(255, 61, 85, 200), width=5 * K)
            L = L.resize((Wd, Hd), Image.LANCZOS)
        elif g["type"] == "polaroid":
            ph = Image.open(os.path.join(wd, g["file"])).convert("RGB")
            s_ = min(ph.size); ph = ph.crop(((ph.width - s_) // 2, (ph.height - s_) // 2, (ph.width + s_) // 2, (ph.height + s_) // 2)).resize((330, 330))
            L = Image.new("RGBA", (330 + 40, 330 + 100), (250, 250, 248, 255)); L.paste(ph, (20, 20))
            L = L.rotate(g.get("angle", -6), resample=Image.BICUBIC, expand=True)
        else:
            return
        L = drop_shadow(L, blur=14, alpha=0.5, dy=10)
        if sc != 1.0: L = L.resize((max(1, int(L.width * sc)), max(1, int(L.height * sc))), Image.BILINEAR)
        if out_k < 1: L.putalpha(L.split()[3].point(lambda v: int(v * out_k)))
        cy_ = g.get("y", 0.72) * H + 5 * np.sin(2 * np.pi * 0.45 * age)
        img.alpha_composite(L, (int(g.get("x", 0.5) * W - L.width / 2), int(cy_ - L.height / 2)))

    fullscreens = [dict(f, t0=T(f["t0"]), t1=T(f["t1"])) for f in plan.get("fullscreens", [])]

    def draw_fullscreen(fs, t):
        """Full-screen graphic background (captions keep popping on top)."""
        age = t - fs["t0"]
        yy_, xx_ = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
        d_ = np.exp(-(((xx_ - W / 2) / (W * 0.7)) ** 2 + ((yy_ - H * 0.7) / (H * 0.5)) ** 2))
        bgarr = (np.zeros(d_.shape + (3,), np.float32) + 10) + np.array([255, 170, 0], np.float32) * 0.22 * d_[..., None]
        bgi = Image.fromarray(bgarr.clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).convert("RGBA")
        if fs.get("type") == "black":
            return Image.new("RGBA", (W, H), (0, 0, 0, 255))
        if fs.get("type", "tallbar") == "tallbar":
            yel = hex_rgb(st["colors"].get("power", "#FFD700"))
            q = ease_out(min(1, age / fs.get("fill_s", 0.9)))
            bw = fs.get("bar_w", 440); top = H - 120 - (H * fs.get("fill", 0.72)) * q
            bar = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
            bd.rounded_rectangle((W / 2 - bw / 2, top, W / 2 + bw / 2, H - 120), 36, fill=yel + (255,))
            gl = bar.split()[3].filter(ImageFilter.GaussianBlur(60)).point(lambda v: int(v * 0.7))
            bgi.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), v) for v in yel], gl))); bgi.alpha_composite(bar)
        return bgi

    def draw_graphic(img, g, t):
        if not (g["t0"] <= t < g["t1"]): return
        cy = g.get("y", 0.7) * H; age = t - g["t0"]
        if g["type"] in ("progress", "week", "polaroid"):
            ember_graphic(img, g, t, age); return
        if g["type"] in ("ring", "burst"):
            draw_overlay_fx(img, g, t, age); return
        if g["type"] in ("bars", "lock", "heart", "calendar", "arrow"):
            lay = shape_layer(g, t, age)
            if lay is None: return
            dur = g["t1"] - g["t0"]
            u_in = age / g.get("in_s", 0.5); u_out = (age - (dur - 0.25)) / 0.25
            sc = ease_out_back(u_in) * (1 - 0.12 * ease_in_cubic(u_out)) if g["type"] != "arrow" else 1.0
            alpha_k = min(1, ease_out(u_in * 2.2)) * (1 - ease_in_cubic(u_out))
            if sc <= 0.01 or alpha_k <= 0.01: return
            lay = shimmer(lay, (age - 0.35) / 0.55, 0.55)
            float_y = 6 * np.sin(2 * np.pi * 0.45 * age)
            gx = g.get("x", 0.5) * W; gy = cy + float_y
            if g.get("panel", True):  # frosted glass panel behind the graphic
                bb = lay.getbbox() or (0, 0, lay.width, lay.height)
                pw_ = (bb[2] - bb[0]) * sc + 90; ph_ = (bb[3] - bb[1]) * sc + 90
                pcx = gx + ((bb[0] + bb[2]) / 2 - lay.width / 2) * sc; pcy = gy + ((bb[1] + bb[3]) / 2 - lay.height / 2) * sc
                box = (int(pcx - pw_ / 2), int(pcy - ph_ / 2), int(pcx + pw_ / 2), int(pcy + ph_ / 2))
                if box[2] > box[0] + 4 and box[3] > box[1] + 4:
                    reg = img.crop(box).convert("RGB").filter(ImageFilter.GaussianBlur(22))
                    reg = Image.blend(reg, Image.new("RGB", reg.size, (255, 255, 255)), 0.12).convert("RGBA")
                    m = Image.new("L", reg.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, reg.width - 1, reg.height - 1), int(min(reg.size) * 0.18), fill=int(255 * alpha_k))
                    reg.putalpha(m)
                    shd = Image.new("RGBA", (reg.width + 80, reg.height + 80), (0, 0, 0, 0))
                    sm_ = Image.new("L", shd.size, 0); ImageDraw.Draw(sm_).rounded_rectangle((40, 50, 40 + reg.width, 50 + reg.height), int(min(reg.size) * 0.18), fill=int(110 * alpha_k))
                    shd.putalpha(sm_.filter(ImageFilter.GaussianBlur(18)))
                    img.alpha_composite(shd, (box[0] - 40, box[1] - 40))
                    img.alpha_composite(reg, (box[0], box[1]))
                    rim = Image.new("RGBA", reg.size, (0, 0, 0, 0))
                    ImageDraw.Draw(rim).rounded_rectangle((0, 0, reg.width - 1, reg.height - 1), int(min(reg.size) * 0.18), outline=(255, 255, 255, int(90 * alpha_k)), width=2)
                    img.alpha_composite(rim, (box[0], box[1]))
            if sc != 1.0: lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BILINEAR)
            if alpha_k < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha_k)))
            img.alpha_composite(lay, (int(gx - lay.width / 2), int(gy - lay.height / 2)))
            return
        if g["type"] == "counter":
            u = ease_out(age / g.get("count_s", 0.5))
            val = g.get("from", 0) + (g["to"] - g.get("from", 0)) * u
            txt = f"{int(val):,}"
            col = hex_rgb(g.get("color", "#FFFFFF"))
            num, nbo, nadv = word_img(fonts, txt, "sans", g.get("px", 110), color=col)
            lab, lbo, ladv = word_img(fonts, g.get("suffix", ""), "serif", int(g.get("px", 110) * 0.8), color=col)
            tot = nadv + 24 + ladv; x = W / 2 - tot / 2
            ni, ndy = land(num, age * AF / 6, rise=24, blur=14, s_from=1.12)
            img.alpha_composite(ni, (int(x + nadv / 2 - ni.width / 2), int(cy - nbo + ndy)))
            img.alpha_composite(lab, (int(x + nadv + 24 - (lab.width - ladv) / 2), int(cy - lbo)))
            if "strike_t" in g:
                q = ease_out((t - g["strike_t"]) * AF / 7)
                strike(img, x - 20, cy - g.get("px", 110) * 0.28, x + tot + 20, cy - g.get("px", 110) * 0.42, q)
        elif g["type"] == "grid" and g.get("style", "clean") == "clean":
            # clean white 3x3 grid, whole graphic springs in from the centre; red diagonal line over the squares
            size = g.get("size", 330); gap_ = size * 0.05; tile = (size - 2 * gap_) / 3
            dur = g["t1"] - g["t0"]; u_out = (age - (dur - 0.25)) / 0.25
            sc = ease_out_back(age / 0.5) * (1 - 0.12 * ease_in_cubic(u_out))
            if sc <= 0.01: return
            cy = cy + 6 * np.sin(2 * np.pi * 0.45 * age)
            layer = Image.new("RGBA", (int(size + 40), int(size + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
            for r_ in range(3):
                for c_ in range(3):
                    x1 = 20 + c_ * (tile + gap_); y1 = 20 + r_ * (tile + gap_)
                    d.rounded_rectangle((x1, y1 + 3, x1 + tile, y1 + tile + 3), int(tile * 0.12), fill=(0, 0, 0, 70))
                    d.rounded_rectangle((x1, y1, x1 + tile, y1 + tile), int(tile * 0.12), fill=(255, 255, 255, 240))
            if "strike_t" in g:
                q = ease_out((t - g["strike_t"]) * AF / 7)
                if q > 0:
                    ax, ay = 20 + tile * 0.25, 20 + tile * 0.25; bx_, by_ = 20 + size - tile * 0.25, 20 + size - tile * 0.25
                    strike(layer, ax, ay, ax + (bx_ - ax), ay + (by_ - ay), q, g.get("line_px", 16))
            layer = shimmer(layer, (age - 0.3) / 0.55, 0.5)
            if sc != 1.0:
                layer = layer.resize((max(1, int(layer.width * sc)), max(1, int(layer.height * sc))), Image.BILINEAR)
            if u_out > 0: layer.putalpha(layer.split()[3].point(lambda v: int(v * (1 - ease_in_cubic(u_out)))))
            img.alpha_composite(layer, (int(W / 2 - layer.width / 2), int(cy - layer.height / 2)))
        elif g["type"] == "grid":
            size = g.get("size", 330); x0 = W / 2 - size / 2; y0 = cy - size / 2
            panel = Image.new("RGBA", (int(size + 60), int(size + 60)), (0, 0, 0, 0))
            pm = Image.new("L", panel.size, 0); ImageDraw.Draw(pm).rounded_rectangle((0, 0, panel.width - 1, panel.height - 1), 34, fill=150)
            panel.putalpha(pm); img.alpha_composite(panel, (int(x0 - 30), int(y0 - 30)))
            for k_, (r_, c_, tim) in enumerate(g["tiles"]):
                tt = age - k_ * g.get("stagger", 0.05)
                if tt < 0: continue
                ti = scale_fade(tim, tt * AF / 6, 0.2, 1.08)
                cx_ = x0 + c_ * (g["tile"] + g["gap"]) + g["tile"] / 2; cy_ = y0 + r_ * (g["tile"] + g["gap"]) + g["tile"] / 2
                img.alpha_composite(ti, (int(cx_ - ti.width / 2), int(cy_ - ti.height / 2)))
            if "strike_t" in g:
                q1 = ease_out((t - g["strike_t"]) * AF / 6); q2 = ease_out((t - g["strike_t"]) * AF / 6 - 0.6)
                strike(img, x0 - 10, y0 - 10, x0 + size + 10, y0 + size + 10, q1, 16)
                strike(img, x0 + size + 10, y0 - 10, x0 - 10, y0 + size + 10, q2, 16)
        elif g["type"] == "button":
            b = g["img"]; ct = g.get("click_t", g["t0"] + 0.6)
            sc = 1.0
            if 0 <= t - ct < 0.25: sc = 0.93 + 0.07 * ((t - ct) / 0.25)
            bi = scale_fade(b, age * AF / 7)
            if sc != 1.0: bi = bi.resize((int(bi.width * sc), int(bi.height * sc)), Image.BILINEAR)
            img.alpha_composite(bi, (int(W / 2 - bi.width / 2), int(cy - bi.height / 2)))
            # cursor glides in (eased) and clicks
            u = ease_out(min(1, max(0, (t - g["t0"] - 0.1) / max(ct - g["t0"] - 0.1, 0.1))))
            sx, sy = W * 0.88, H * 0.86; ex, ey = W / 2 + b.width * 0.18, cy + 10
            px_, py_ = sx + (ex - sx) * u, sy + (ey - sy) * u
            if t - ct >= 0:
                rr = (t - ct) * 420; al = int(max(0, 160 * (1 - (t - ct) / 0.45)))
                if al > 0: ImageDraw.Draw(img).ellipse((ex - rr, ey - rr, ex + rr, ey + rr), outline=(255, 255, 255, al), width=5)
            arrow = [(0, 0), (0, 58), (15, 45), (26, 70), (37, 65), (26, 41), (46, 41)]
            d = ImageDraw.Draw(img)
            d.polygon([(px_ + x * 1.15 + 3, py_ + y * 1.15 + 4) for x, y in arrow], fill=(0, 0, 0, 110))
            d.polygon([(px_ + x * 1.15, py_ + y * 1.15) for x, y in arrow], fill=(255, 255, 255, 255), outline=(10, 10, 10, 255))

    # ---------- v9: person matte, text behind the speaker, animated lines, kinetic letters ----------
    matte_sess = None
    if plan.get("matte_model") and (plan.get("behind") or plan.get("lines")):
        import onnxruntime as ort
        matte_sess = ort.InferenceSession(os.path.join(wd, plan["matte_model"]), providers=["CPUExecutionProvider"])
    matte_prev = [None]

    def person_matte(frame_u8):
        x = cv2.resize(frame_u8, (288, 512), interpolation=cv2.INTER_AREA).astype(np.float32)
        x = ((x / 255 - 0.5) / 0.5).transpose(2, 0, 1)[None]
        m = matte_sess.run(None, {"input": x})[0][0, 0]
        if matte_prev[0] is not None: m = 0.55 * m + 0.45 * matte_prev[0]  # temporal smoothing (no flicker)
        matte_prev[0] = m
        return cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)

    char_cache = {}

    def char_img(ch, kind, px, color):
        k = (ch, kind, px, color)
        if k not in char_cache:
            im_, bo_, adv_ = word_img(fonts, ch, kind, px, color=color)
            char_cache[k] = (im_, bo_, adv_)
        return char_cache[k]

    def kinetic_text(text, kind, px, color, age, stagger=0.035, dur_in=0.32, track=0.0, rise=None):
        """Letters rise in one by one (eased, with blur), tracking widens by `track` em. Returns (RGBA, baseline_y)."""
        rise = px * 0.45 if rise is None else rise
        chars = [char_img(c, kind, px, color) for c in text]
        tr = fonts.tracking(kind) * px + track * px
        tot = sum(c[2] for c in chars) + tr * (len(chars) - 1)
        pad = int(px * 0.9)
        lay = Image.new("RGBA", (int(tot + 2 * pad), int(px * 2.6)), (0, 0, 0, 0)); base = int(px * 1.75)
        x = pad
        for k, (im_, bo_, adv_) in enumerate(chars):
            u = (age - k * stagger) / dur_in
            if u > 0:
                e = ease_out_expo(u)
                li = im_
                bl = 10 * (1 - e)
                if bl > 0.5: li = li.filter(ImageFilter.GaussianBlur(bl))
                if e < 1: li = li.copy(); li.putalpha(li.split()[3].point(lambda v: int(v * min(1, e * 1.4))))
                lay.alpha_composite(li, (int(x - (im_.width - adv_) / 2), int(base - bo_ + rise * (1 - e))))
            x += adv_ + tr
        return lay, base

    behind = []
    for b_ in plan.get("behind", []):
        b_ = dict(b_); b_["t0"] = T(b_["t0"]); b_["t1"] = T(b_["t1"]); behind.append(b_)
    lines = []
    for l_ in plan.get("lines", []):
        l_ = dict(l_); l_["t0"] = T(l_["t0"]); l_["t1"] = T(l_["t1"]); lines.append(l_)
    face_c = (fx + fw / 2, fy + fh * 0.45)

    def map_pt(x, y, s):
        return anchor[0] + s * (x - anchor[0]), anchor[1] + s * (y - anchor[1])

    def draw_behind_layer(t, s):
        """Giant text placed behind the speaker (composited under the person matte)."""
        lay = None
        for b_ in behind:
            if not (b_["t0"] <= t < b_["t1"]): continue
            age = t - b_["t0"]; dur = b_["t1"] - b_["t0"]
            lay = lay or Image.new("RGBA", (W, H), (0, 0, 0, 0))
            out_k = 1 - ease_in_cubic((age - (dur - 0.25)) / 0.25)
            grow = (1 + b_.get("grow", 0.06) * (age / max(dur, 0.1))) * s
            col = hex_rgb(b_.get("color", "#FFFFFF"))
            y = b_.get("y", 0.25) * H
            for j, txt in enumerate(b_["lines"]):
                kl, kb = kinetic_text(txt, b_.get("font", "sans"), b_.get("px", 240), col, age - j * 0.12,
                                      stagger=b_.get("stagger", 0.045), dur_in=0.42, track=0.02 * age)
                kl = kl.resize((max(1, int(kl.width * grow)), max(1, int(kl.height * grow))), Image.BILINEAR)
                op = b_.get("opacity", 0.95) * out_k
                if op < 1: kl.putalpha(kl.split()[3].point(lambda v: int(v * op)))
                ly = y + j * b_.get("px", 240) * b_.get("leading", 0.9) * grow
                lay.alpha_composite(kl, (int(b_.get("x", 0.5) * W - kl.width / 2), int(ly - kb * grow)))
        return lay

    def stroke_path(pts, width, color, glow=True):
        """Smooth glowing stroke along a list of points, returned as an RGBA layer (2x supersampled)."""
        if len(pts) < 2: return None
        xs = [p_[0] for p_ in pts]; ys = [p_[1] for p_ in pts]
        x0_, y0_ = int(min(xs) - 60), int(min(ys) - 60); x1_, y1_ = int(max(xs) + 60), int(max(ys) + 60)
        K = 2; lw, lh = (x1_ - x0_) * K, (y1_ - y0_) * K
        if lw <= 0 or lh <= 0: return None
        lay = Image.new("RGBA", (lw, lh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        P = [((x - x0_) * K, (y - y0_) * K) for x, y in pts]
        d.line(P, fill=color + (255,), width=int(width * K), joint="curve")
        r = width * K / 2
        for cx_, cy_ in (P[0], P[-1]): d.ellipse((cx_ - r, cy_ - r, cx_ + r, cy_ + r), fill=color + (255,))
        lay = lay.resize((lw // K, lh // K), Image.LANCZOS)
        if glow:
            g_ = lay.split()[3].filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.8))
            gl = Image.merge("RGBA", (*[Image.new("L", lay.size, c) for c in color], g_))
            lay = Image.alpha_composite(gl, lay)
        return lay, (x0_, y0_)

    def trim(age, dur, draw_s=0.55, lag=0.32):
        """Trim-path animation: head draws on, tail chases it off near the end."""
        head = ease_out_expo(age / draw_s)
        tail = ease_in_cubic((age - max(dur - draw_s, lag)) / draw_s) if dur > 0 else 0
        return max(0.0, min(tail, 1.0)), head

    def line_layers(t, s):
        back, front = [], []
        for l_ in lines:
            if not (l_["t0"] <= t < l_["t1"]): continue
            age = t - l_["t0"]; dur = l_["t1"] - l_["t0"]
            a0, a1 = trim(age, dur, l_.get("draw_s", 0.55))
            if a1 - a0 < 0.005: continue
            col = hex_rgb(l_.get("color", "#FFFFFF")); wdt = l_.get("width", 7)
            if l_["type"] == "orbit":
                cxo, cyo = map_pt(*face_c, s)
                cyo += l_.get("dy", 0.0) * H
                rx, ry = l_.get("rx", 0.40) * W * s, l_.get("ry", 0.055) * H * s
                tilt = np.radians(l_.get("tilt", -10)); spin = l_.get("start", 0.6)
                th = spin + 2 * np.pi * l_.get("turns", 1.0) * np.linspace(a0, a1, 160)
                ex, ey = rx * np.cos(th), ry * np.sin(th)
                X = cxo + ex * np.cos(tilt) - ey * np.sin(tilt); Y = cyo + ex * np.sin(tilt) + ey * np.cos(tilt)
                isback = np.sin(th) < 0  # upper half of the ellipse passes behind the head
                seg, cur = [], None
                for k in range(len(th)):
                    if cur is None or isback[k] != cur:
                        if seg: (back if cur else front).append(stroke_path(seg, wdt, col)); seg = seg[-1:]
                        cur = isback[k]
                    seg.append((X[k], Y[k]))
                if seg: (back if cur else front).append(stroke_path(seg, wdt, col))
            elif l_["type"] == "swoosh":
                C = np.array(l_["pts"], np.float32) * np.array([W, H], np.float32)
                u = np.linspace(a0, a1, 120)[:, None]
                B = ((1 - u) ** 3) * C[0] + 3 * ((1 - u) ** 2) * u * C[1] + 3 * (1 - u) * u ** 2 * C[2] + u ** 3 * C[3]
                front.append(stroke_path([tuple(p_) for p_ in B], wdt, col))
        return [x for x in back if x], [x for x in front if x]

    # 4) frames
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    dec_raw = subprocess.Popen(["ffmpeg", "-v", "error", "-i", ungraded, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE) if wm else None
    silent = os.path.join(wd, "_video.mp4")
    reuse = plan.get("reuse_frames") and os.path.exists(silent)
    if reuse: nfr = 0
    enc = None if reuse else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    tf = cam["transition"]["frames"]; flash = cam["after_cut_flash"]; push = cam.get("push_per_s", 0.012)
    smooth = plan.get("camera_mode", cam.get("mode", "smooth")) == "smooth"
    rng = np.random.default_rng(1)

    def smooth_scale(t):
        """Slow eased zoom between keyframes [(t, scale)] - no jumps."""
        if t <= scales[0][0]: return scales[0][1]
        for (t0, s0), (t1, s1) in zip(scales, scales[1:]):
            if t0 <= t < t1:
                u = (t - t0) / max(t1 - t0, 1e-6); u = 0.5 - 0.5 * np.cos(np.pi * u)
                return s0 + (s1 - s0) * u
        return scales[-1][1]

    # cutaways (slow-motion b-roll from the source or from a b-roll file), pre-rendered
    cutaways = []
    for k_, c in enumerate(plan.get("cutaways", [])):
        t0o = T(c["t0"]); t1o = T(c["t1"]); dur_o = t1o - t0o
        clip_src = os.path.join(wd, c["file"]) if c.get("file") else src
        start = c.get("from", c["t0"]); slow = c.get("slowmo", 0.6)
        span = dur_o * slow * speed + 0.2
        x, y, w, h = c.get("crop", [0, 0, 0, 0])
        crop = f"crop={w}:{h}:{x}:{y}," if w else ""
        path = os.path.join(wd, f"_cut{k_}.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(span), "-i", clip_src, "-an", "-vf",
             f"{crop}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},scale=608:1080,setpts=PTS/{slow * speed}," + (f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" if interp_mode == "mci" else f"fps={FPS}") + f",scale={W}:{H}:flags=lanczos,{grade}",
             "-c:v", "libx264", "-crf", "14", path])
        cutaways.append(dict(t0=t0o, t1=t1o, path=path, dec=None, zoom=c.get("zoom", [1.0, 1.08]),
                             mode=c.get("mode", "full"), enter=c.get("enter", "right"), card_w=c.get("card_w", 0.66),
                             card_y=c.get("card_y", 0.44), reveal=c.get("reveal")))

    trans_pts = plan.get("transitions_extra", [])
    trans_pts = [T(x) for x in trans_pts] + [c["t0"] for c in cutaways] + [c["t1"] for c in cutaways]
    trans_pts += [c["t0"] for c in cards] + [c["t1"] for c in cards] + [a for a, b in bw] + [b for a, b in bw]
    trans_pts += [T(f["t0"]) for f in plan.get("fullscreens", [])] + [T(f["t1"]) for f in plan.get("fullscreens", [])]
    trans_pts = sorted(set(round(x, 3) for x in trans_pts))
    rb_frames, rb_peak = cam.get("radial_frames", 6), cam.get("radial_strength", 0.14)

    ttype = plan.get("transition", cam.get("transition_type", "flash"))
    yy_, xx_ = np.mgrid[0:H, 0:W].astype(np.float32)
    flash_mask = (1 - 0.5 * (((xx_ - W / 2) / (W / 2)) ** 2 + ((yy_ - H * 0.45) / (H / 2)) ** 2)).clip(0.35, 1)[..., None]
    del yy_, xx_

    def flash_amount(t):
        a = 0.0
        for p_ in trans_pts:
            if p_ - 0.14 <= t < p_: a = max(a, ((t - (p_ - 0.14)) / 0.14) ** 2)
            elif p_ <= t < p_ + 0.6: a = max(a, np.exp(-(t - p_) / 0.15))
        return a * cam.get("flash_peak", 0.85)

    def apply_flash(arr, a):
        small = cv2.resize(arr, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
        bloom = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6), (W, H), interpolation=cv2.INTER_LINEAR)
        out = arr * (1 - 0.4 * a) + bloom * 0.4 * a * 1.3
        return out + a * flash_mask * (255 - out) * 0.92

    def radial_strength(t):
        return max([rb_peak * max(0, 1 - abs(t - p) * AF / rb_frames) for p in trans_pts] + [0])

    def radial_blur(arr, s, cx=W / 2, cy=H * 0.45, n=9):
        acc = np.zeros_like(arr, np.float32)
        for j in range(n):
            z = 1 + s * j / (n - 1)
            M = np.float32([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]])
            acc += cv2.warpAffine(arr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return acc / n

    card_cache = {}

    def card_composite(bg, clip, cw, t):
        """B-roll as a floating 3D card over a blurred, darkened speaker."""
        cwid = int(W * cw["card_w"]); chei = int(cwid * 16 / 9)
        key = (cwid, chei)
        if key not in card_cache:
            m = Image.new("L", (cwid, chei), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, cwid - 1, chei - 1), int(cwid * 0.07), fill=255)
            rim = Image.new("L", (cwid, chei), 0); ImageDraw.Draw(rim).rounded_rectangle((1, 1, cwid - 2, chei - 2), int(cwid * 0.07), outline=255, width=4)
            card_cache[key] = (np.asarray(m, np.float32) / 255, np.asarray(rim, np.float32)[..., None] / 255)
        mask, rim = card_cache[key]
        # background: blurred + darkened speaker
        sm = cv2.resize(bg, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
        bgb = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 3), (W, H), interpolation=cv2.INTER_LINEAR) * 0.42
        # card texture (centre crop of the clip)
        tex = cv2.resize(clip, (cwid, chei), interpolation=cv2.INTER_AREA)
        tex = tex * (1 - rim * 0.25) + 255 * rim * 0.25
        # motion: expo ease in, gentle float, eased exit
        dur = cw["t1"] - cw["t0"]; age = t - cw["t0"]
        e = ease_out_expo(age / 0.6); x_out = ease_in_cubic((age - (dur - 0.3)) / 0.3)
        ry = (1 - e) * 38 + 7 * np.sin(2 * np.pi * 0.33 * t); rx = 4 * np.sin(2 * np.pi * 0.27 * t + 1.0)
        sc = (0.72 + 0.28 * e) * (1 - 0.08 * x_out)
        dx = (1 - e) * W * 0.85 if cw["enter"] == "right" else ((1 - e) * -W * 0.85 if cw["enter"] == "left" else 0)
        dy = (1 - e) * H * 0.7 if cw["enter"] == "bottom" else 0
        if cw["enter"] == "bottom": rx += (1 - e) * 30; ry *= 0.3
        dy += 10 * np.sin(2 * np.pi * 0.4 * t)
        cx, cy = W / 2 + dx, H * cw["card_y"] + dy
        a_y, a_x = np.radians(ry), np.radians(rx)
        Ry = np.array([[np.cos(a_y), 0, np.sin(a_y)], [0, 1, 0], [-np.sin(a_y), 0, np.cos(a_y)]])
        Rx = np.array([[1, 0, 0], [0, np.cos(a_x), -np.sin(a_x)], [0, np.sin(a_x), np.cos(a_x)]])
        f = 2200.0
        corners = np.array([[-cwid / 2, -chei / 2, 0], [cwid / 2, -chei / 2, 0], [cwid / 2, chei / 2, 0], [-cwid / 2, chei / 2, 0]]) * sc
        P = corners @ (Rx @ Ry).T
        dst = np.float32([[cx + f * X / (f + Z), cy + f * Y / (f + Z)] for X, Y, Z in P])
        src_ = np.float32([[0, 0], [cwid, 0], [cwid, chei], [0, chei]])
        Mp = cv2.getPerspectiveTransform(src_, dst)
        warped = cv2.warpPerspective(tex, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        alpha = cv2.warpPerspective(mask, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
        alpha *= (1 - x_out)
        sh = cv2.resize(cv2.GaussianBlur(cv2.resize(alpha, (W // 8, H // 8)), (0, 0), 4), (W, H))[..., None]
        sh = np.roll(sh, 40, axis=0) * 0.6
        bgb *= (1 - sh)
        return bgb * (1 - alpha) + warped * alpha

    for i in range(nfr):
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        rawsrc = dec_raw.stdout.read(W * H * 3) if dec_raw else None
        t = i / FPS
        fr = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        in_bw = any(a <= t < b for a, b in bw)
        dx = dy = 0
        if smooth:
            s_eff = smooth_scale(t) * (st["bw_punch"]["zoom"] if in_bw else 1.0)
            cur, since = [], 99
        else:
            cur = [s_ for s_ in scales if s_[0] <= t + 1e-6]; s_now = cur[-1][1] if cur else 1.0
            since = t - (cur[-1][0] if cur else 0)
            bump = sum(0.045 * (min(1, (t - b) * AF / 3) if t - b < 3 / AF else np.exp(-((t - b) * AF - 3) / 6)) for b in bumps if 0 <= t - b < 1.0)
            s_eff = s_now * (1 + push * min(since, 3.0)) * (1 + bump) * (st["bw_punch"]["zoom"] if in_bw else 1.0)
            sh = [(rng.normal(0, 9) * np.exp(-(t - b) * AF / 5), rng.normal(0, 9) * np.exp(-(t - b) * AF / 5)) for b in shakes if 0 <= t - b < 0.35]
            dx, dy = (sum(s_[0] for s_ in sh), sum(s_[1] for s_ in sh)) if sh else (0, 0)

        def zoom(img, s):
            M = np.float32([[s, 0, anchor[0] * (1 - s) + dx], [0, s, anchor[1] * (1 - s) + dy]])
            return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

        cw = next((c for c in cutaways if c["t0"] <= t < c["t1"]), None)
        if cw:
            if cw["dec"] is None:
                cw["dec"] = subprocess.Popen(["ffmpeg", "-v", "error", "-i", cw["path"], "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            craw = cw["dec"].stdout.read(W * H * 3)
            if len(craw) == W * H * 3:
                cf = np.frombuffer(craw, np.uint8).reshape(H, W, 3)
                u = (t - cw["t0"]) / (cw["t1"] - cw["t0"]); z0, z1 = cw["zoom"]
                zz = z0 + (z1 - z0) * (0.5 - 0.5 * np.cos(np.pi * u))
                M = np.float32([[zz, 0, W / 2 * (1 - zz)], [0, zz, H / 2 * (1 - zz)]])
                out = cv2.warpAffine(cf, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
                if cw["mode"] == "card":
                    out = card_composite(zoom(fr, s_eff).astype(np.float32), out, cw, t)
                elif cw.get("reveal") == "iris":
                    ia = t - cw["t0"]
                    if ia < 0.5:
                        e = ease_out_expo(ia / 0.5); R = e * np.hypot(W, H) * 0.55
                        if not hasattr(card_composite, "grid"):
                            yy2, xx2 = np.mgrid[0:H, 0:W].astype(np.float32); card_composite.grid = np.hypot(xx2 - W / 2, yy2 - H * 0.42)
                        dist = card_composite.grid
                        mk = np.clip((R - dist) / 6, 0, 1)[..., None]
                        ring = np.clip(1 - np.abs(dist - R) / 5, 0, 1)[..., None] * (1 - e)
                        out = out * mk + zoom(fr, s_eff).astype(np.float32) * (1 - mk)
                        out = out + ring * (255 - out)
            else:
                out = zoom(fr, s_eff).astype(np.float32)
        else:
            k = int(round(since * AF))
            if not smooth and len(cur) > 1 and k < tf:
                strength = 1 - k / tf
                out = np.mean([zoom(fr, s_eff * (1 + 0.07 * strength * j / 4)) for j in range(5)], axis=0, dtype=np.float32)
            else:
                out = zoom(fr, s_eff).astype(np.float32)
            if not smooth and len(cur) > 1 and k < flash["decay_frames"]:
                out *= 1 + flash["brightness"] * (1 - k / flash["decay_frames"])
        if in_bw:
            g = out @ np.array([0.299, 0.587, 0.114], np.float32)
            out = np.repeat(g[..., None], 3, axis=2)
            out = (out - 128) * 1.15 + 128
        front_lines = []
        back_l = []
        if lines:
            back_l, front_lines = line_layers(t, s_eff)
            if cw: front_lines, back_l = back_l + front_lines, []
        if matte_sess is not None and not cw:
            bl_ = draw_behind_layer(t, s_eff)
            if bl_ is not None or back_l:
                m_ = person_matte(fr)
                m_ = cv2.warpAffine(m_, np.float32([[s_eff, 0, anchor[0] * (1 - s_eff)], [0, s_eff, anchor[1] * (1 - s_eff)]]), (W, H))[..., None]
                bgp = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")
                if bl_ is not None: bgp.alpha_composite(bl_)
                for lay_, (lx, ly) in back_l: bgp.alpha_composite(lay_, (int(lx), int(ly)))
                bga = np.asarray(bgp.convert("RGB"), np.float32)
                out = out * m_ + bga * (1 - m_)
            else:
                matte_prev[0] = None
        if vig is None:
            yy, xx = np.mgrid[0:H, 0:W]
            vig = (1 - 0.28 * (((xx - W / 2) / (W / 2)) ** 2 * 0.6 + ((yy - H / 2) / (H / 2)) ** 2 * 0.8)).clip(0.6, 1)[..., None].astype(np.float32)
        out *= vig
        gn = cv2.resize(grain[i % 4], (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 3.5
        out += gn
        if wm and rawsrc is not None and not cw:
            src_fr = np.frombuffer(rawsrc, np.uint8).reshape(H, W, 3).astype(np.float32)
            x0, y0, r = int(wm[0]) - int(wm[2]), int(wm[1]) - int(wm[2]), int(wm[2])
            region = out[y0:y0 + 2 * r, x0:x0 + 2 * r]
            out[y0:y0 + 2 * r, x0:x0 + 2 * r] = region * (1 - wm_mask) + src_fr[y0:y0 + 2 * r, x0:x0 + 2 * r] * wm_mask
        img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")

        if pop:
            card = next((c for c in cards if c["t0"] <= t < c["t1"]), None)
            in_cta = cta and cta.get("cycle") and cta["t0"] <= t < cta.get("t1", 1e9)
            if card:
                img = Image.new("RGBA", (W, H), card["bgc"] + (255,))
                u = (t - card["t0"]) / max(card["t1"] - card["t0"], 1e-3)
                k0, k1 = st["word_cards"].get("scale_from_to", [0.86, 1.22])
                sc = k0 + (k1 - k0) * (0.5 - 0.5 * np.cos(np.pi * u))  # slow, continuous eased zoom
                spec = st["word_cards"][card["bg"]]
                ki, kb = kinetic_text(card["text"], spec["font"], spec["px"], hex_rgb(spec["color"]), t - card["t0"],
                                      stagger=0.04, dur_in=0.3, track=0.06 * u)
                ci = ki.resize((max(1, int(ki.width * sc)), max(1, int(ki.height * sc))), Image.BILINEAR)
                img.alpha_composite(ci, (int(W / 2 - ci.width / 2), int(H / 2 - (kb - spec["px"] * 0.35) * sc)))
            elif in_cta:
                p = (t - cta["t0"]) * AF / 4
                bs = spring(p)
                bi = cta["bigp"].resize((int(cta["bigp"].width * bs), int(cta["bigp"].height * bs)), Image.BILINEAR)
                cyb = H * 0.50
                img.alpha_composite(bi, (int(W / 2 - bi.width / 2), int(cyb - cta["bbo"] * bs)))
                cur_ = [x for x in cta["cyc"] if x[0] <= t]
                if cur_:
                    ct_, ci_, cbo_ = cur_[-1]
                    ss = spring((t - ct_) * AF / 4)
                    si = ci_.resize((int(ci_.width * ss), int(ci_.height * ss)), Image.BILINEAR)
                    img.alpha_composite(si, (int(W / 2 - si.width / 2), int(cyb + st["cta"]["small_px"] * 1.5 - cbo_ * ss)))
            else:
                fs_ = next((f for f in fullscreens if f["t0"] <= t < f["t1"]), None)
                if fs_: img = draw_fullscreen(fs_, t)
                y = fs_.get("caption_y", 0.30) * H if fs_ else cap_base
                c = next((c for c in caps if c["t0"] <= t < c["t1"]), None)
                ch = next((c for c in chips if c["t0"] <= t < c["t1"]), None)
                if c and word_pop:
                    for q_, wt_ in zip(c["pw"], c["wt"]):
                        if t < wt_: continue
                        sc_ = spring((t - wt_) * AF / cs.get("pop_frames", 6), tuple(cs.get("pop_keys", (0.0, 0.7, 1.18, 0.94, 1.0))))
                        if q_["power"]:
                            if "power_grow_total" in cs: sc_ *= 1 + cs["power_grow_total"] * min(1, (t - wt_) / max(c["t1"] - wt_, 0.1))
                            else: sc_ *= 1 + cs.get("power_grow_per_s", 0.12) * (t - wt_)
                        if sc_ <= 0.02: continue
                        im_ = q_["img"].resize((max(1, int(q_["img"].width * sc_)), max(1, int(q_["img"].height * sc_))), Image.BILINEAR)
                        cxw = q_["x"] + q_["adv"] / 2
                        cyw = y - q_["size"] * 0.36  # visual centre of the word
                        img.alpha_composite(im_, (int(cxw - im_.width / 2), int(cyw - (q_["bo"] - q_["size"] * 0.36) * sc_)))
                elif c and not ch:
                    hgt = int(cs["sans_px"] * 4); base_ = int(cs["sans_px"] * 2.6)
                    line = Image.new("RGBA", (W, hgt), (0, 0, 0, 0))
                    for q_ in c["pw"]:
                        im_ = q_["img"]
                        if q_["power"]:  # slow continuous scale-up while on screen
                            g_ = 1 + cs.get("power_grow_per_s", 0.10) * (t - c["t0"])
                            im_ = im_.resize((int(im_.width * g_), int(im_.height * g_)), Image.BILINEAR)
                            cxw = q_["x"] + q_["adv"] / 2; pad_ = (q_["img"].width - q_["adv"]) / 2
                            line.alpha_composite(im_, (int(cxw - im_.width / 2), int(base_ - q_["bo"] * g_ + (g_ - 1) * cs["sans_px"] * 0.3)))
                        else:
                            line.alpha_composite(im_, (int(q_["x"] - (im_.width - q_["adv"]) / 2), int(base_ - q_["bo"])))
                    ps = spring((t - c["t0"]) * AF / cs.get("pop_frames", 4))
                    if ps != 1.0:
                        line = line.resize((int(W * ps), int(hgt * ps)), Image.BILINEAR)
                    img.alpha_composite(line, (int(W / 2 - line.width / 2), int(y - base_ * ps)))
                if ch:
                    shown = [it for it in ch["items"] if it["t"] <= t]
                    hs = [it["img"].height for it in shown]
                    yy = (ch.get("y", 0.76) * H if word_pop else y - 30) - (sum(hs) + st["chips"]["stack_gap_px"] * (len(shown) - 1)) / 2
                    fade_c = 1.0 if cs.get("hard_exit") else 1 - ease_in_cubic((t - (ch["t1"] - 0.22)) / 0.22)
                    for it, h0 in zip(shown, hs):
                        sc = spring((t - it["t"]) * AF / st["chips"].get("pop_frames", 10), tuple(st["chips"].get("pop_keys", (0.0, 0.7, 1.18, 0.95, 1.0))))
                        base_img = shimmer(it["img"], (t - it["t"] - 0.25) / 0.5, 0.6)
                        a_ = base_img.resize((max(1, int(it["img"].width * sc)), max(1, int(it["img"].height * sc))), Image.BILINEAR)
                        if fade_c < 1: a_.putalpha(a_.split()[3].point(lambda v: int(v * max(fade_c, 0))))
                        img.alpha_composite(a_, (int(W / 2 - a_.width / 2), int(yy + h0 / 2 - a_.height / 2)))
                        yy += h0 + st["chips"]["stack_gap_px"]
        else:
            card = next((c for c in cards if c["t0"] <= t < c["t1"]), None)
            if card:
                img = Image.new("RGBA", (W, H), card["bgc"] + (255,))
                p = (t - card["t0"]) * AF / st["word_cards"].get("enter", {}).get("frames", 5)
                ci, cdy = land(card["img"], p, rise=30, blur=26, s_from=1.18)
                cz = 1 + 0.03 * (t - card["t0"])  # slow push on the card
                ci = ci.resize((int(ci.width * cz), int(ci.height * cz)), Image.BILINEAR)
                img.alpha_composite(ci, (int(W / 2 - ci.width / 2), int(H / 2 - ci.height / 2 + cdy)))
            else:
                y = cap_base
                c = next((c for c in caps if c["t0"] <= t < c["t1"]), None)
                stat = next((s for s in stats if s["t0"] <= t < s["t1"]), None)
                ch = next((c for c in chips if c["t0"] <= t < c["t1"]), None)
                if (c or ch) and not stat:
                    img.alpha_composite(scr, (int(W / 2 - scr.width / 2), int(y - scr.height * 0.62)))
                if c and not stat:
                    prev = next((q for q in reversed(caps) if q["t1"] <= c["t0"] + 1e-6 and c["t0"] - q["t1"] < 0.4), None)
                    if prev and not any(cd["t0"] >= prev["t1"] - 1e-6 and cd["t1"] <= c["t0"] + 1e-6 for cd in cards):
                        top = y - (cs.get("serif_px", int(cs["sans_px"] * 1.2)) if c.get("power") else cs["sans_px"]) * 0.78
                        gi = prev["ghost"]; img.alpha_composite(gi, (int(W / 2 - gi.width / 2), int(top - 12 - prev["gbo"])))
                    for wd_, wt in zip(c["w"], c["wt"]):
                        if t < wt: continue
                        p = (t - wt) * AF / 6
                        im, ddy = land(wd_["img"], p)
                        cx = wd_["x"] + wd_["adv"] / 2
                        sc = im.width / wd_["img"].width
                        if wd_["power"] and wd_["glow"] is not None:
                            pulse = max(0, 1 - (t - wt) * AF / 14)
                            if p >= 1 and pulse > 0:
                                gl = wd_["glow"].copy(); gl.putalpha(gl.split()[3].point(lambda v: int(v * pulse)))
                                img.alpha_composite(gl, (int(cx - gl.width / 2), int(y - wd_["bo"])))
                        img.alpha_composite(im, (int(cx - im.width / 2), int(y - wd_["bo"] * sc + ddy)))
                        if wd_["power"]:  # underline sweep
                            q = ease_out(((t - wt) * FPS - 4) / 8)
                            if q > 0:
                                uw = int(wd_["adv"] * 0.92 * q); ux = int(wd_["x"] + wd_["adv"] * 0.04)
                                uy = int(y + cs.get("serif_px", int(cs["sans_px"] * 1.2)) * 0.12)
                                ImageDraw.Draw(img).rounded_rectangle((ux, uy, ux + max(uw, 2), uy + 7), 3, fill=blue + (235,))
                if stat:
                    p = (t - stat["t0"]) * AF / 7
                    si = scale_fade(stat["img"], p, 0.3, 1.1)
                    sy = y + stat.get("dy", 40)
                    img.alpha_composite(si, (int(W / 2 - si.width / 2), int(sy - si.height / 2)))
                    if t - stat["t0"] > 0.2:
                        li, ldy = land(stat["label_img"], (t - stat["t0"] - 0.2) * AF / 6)
                        img.alpha_composite(li, (int(W / 2 - li.width / 2), int(sy + stat.get("px", 360) * 0.42 - stat["label_img"].height * 0.35 + ldy)))
                if ch:
                    shown = [it for it in ch["items"] if it["t"] <= t]
                    hs = [it["img"].height - 140 for it in shown]
                    yy = y - 40 - (sum(hs) + st["chips"]["stack_gap_px"] * (len(shown) - 1)) / 2
                    for it, h0 in zip(shown, hs):
                        a = scale_fade(it["img"], (t - it["t"]) * AF / st["chips"]["enter"]["frames"])
                        img.alpha_composite(a, (int(W / 2 - a.width / 2), int(yy + h0 / 2 - a.height / 2)))
                        yy += h0 + st["chips"]["stack_gap_px"]
                if cta and t >= cta["t0"]:
                    p = (t - cta["t0"]) * AF / 6
                    big, bdy = land(cta["big"], p)
                    img.alpha_composite(big, (int(W / 2 - big.width / 2), int(H * 0.52 - cta["kbo"] + bdy)))
                    sm, sdy = land(cta["small"], p)
                    img.alpha_composite(sm, (int(W / 2 - sm.width / 2), int(H * 0.52 - st["cta"]["big_px"] * 0.95 - cta["sbo"] + sdy)))
        for lay_, (lx, ly) in front_lines:
            img.alpha_composite(lay_, (int(lx), int(ly)))
        for gfx in graphics:
            draw_graphic(img, gfx, t)
        frame_out = np.asarray(img.convert("RGB"))
        if ttype == "radial":
            rs = radial_strength(t)
            if rs > 0.005:
                frame_out = np.clip(radial_blur(frame_out.astype(np.float32), rs), 0, 255).astype(np.uint8)
        else:
            fa = flash_amount(t)
            if fa > 0.01:
                frame_out = np.clip(apply_flash(frame_out.astype(np.float32), fa), 0, 255).astype(np.uint8)
        enc.stdin.write(frame_out.tobytes())
    if enc: enc.stdin.close(); enc.wait()
    dec.stdout.close(); dec.kill(); dec.wait()  # never block on unread frames
    for c in cutaways:
        if c["dec"]: c["dec"].stdout.close(); c["dec"].kill(); c["dec"].wait()
    if dec_raw: dec_raw.stdout.close(); dec_raw.kill(); dec_raw.wait()

    # 5) audio: voice + SFX (plan + automatic) + ducked music bed
    with wave.open(voice) as w: v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    mix = v.copy(); levels = st["audio"]["sfx_levels_db"]
    bank = {k: f() for k, f in SFX.PALETTE.items()}
    pack = plan.get("sfx_pack"); smap = plan.get("sfx_map", {})
    if pack:
        pack = os.path.join(wd, pack)
        for role, (fname, max_s, lvl) in smap.items():
            fp = os.path.join(pack, fname)
            if not os.path.exists(fp): print("missing sfx:", fname); continue
            raw_ = subprocess.check_output(["ffmpeg", "-v", "error", "-i", fp, "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"])
            x = np.frombuffer(raw_, np.int16).astype(np.float32) / 32768
            nz = np.where(np.abs(x) > 10 ** (-45 / 20))[0]
            if len(nz): x = x[max(nz[0] - int(0.005 * SR), 0):]
            if max_s < 0:  # take the tail (risers build up to their end)
                x = x[-int(-max_s * SR):]; fl = min(int(0.05 * SR), len(x)); x[:fl] *= np.linspace(0, 1, fl)
            else:
                x = x[: int(max_s * SR)]; fl = min(int(0.04 * SR), len(x)); x[-fl:] *= np.linspace(1, 0, fl)
            x = x / (np.max(np.abs(x)) + 1e-9)
            bank[role] = x; levels[role] = lvl
    events = [(T(ts), nm) for ts, nm in plan.get("sfx", [])]
    if plan.get("auto_sfx", True):
        card_t = [c["t0"] for c in cards] + [c["t1"] for c in cards]
        events += [(t, "whoosh") for t, _ in scales[1:] if all(abs(t - ct) > 0.15 for ct in card_t)]
        if st["audio"].get("risers", False): events += [(c["t0"] - plan.get("riser_s", 0.5) + 2 / FPS, "riser") for c in cards if not any(abs(c["t0"] - d["t1"]) < 0.05 for d in cards)]
        if smooth:
            tsound = "flash" if (ttype == "flash" and "flash" in bank) else "whoosh"
            events = [e for e in events if e[1] != "whoosh"] + [(p_ - 0.14, tsound) for p_ in trans_pts if all(abs(p_ - c["t0"]) > 0.05 for c in cards)]
        if "highlight" in bank and not pop:
            events += [(c["wt"][i_] + 4 / FPS, "highlight") for c in caps for i_ in c.get("power", [])]
    for ts, nm in events:
        if nm not in bank: print("no sfx for", nm); continue
        s = bank[nm] * 10 ** ((levels.get(nm, -18) + 1) / 20)
        start = int(max(ts - st["audio"].get("sfx_lead_frames", 0) / FPS, 0) * SR); end = min(start + len(s), len(mix))
        if end > start: mix[start:end] += s[: end - start]
    mus = st["audio"]["music"]
    if plan.get("music", "generated") == "generated":
        bed = SFX.music_bed(len(v) / SR + 0.1, bpm=plan.get("bpm", 90))[: len(v)]
    elif plan.get("music"):
        mp = os.path.join(wd, "_music.wav")
        run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(wd, plan["music"]), "-ac", "1", "-ar", str(SR), mp])
        with wave.open(mp) as w: bed = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        bed = np.pad(bed, (0, max(0, len(v) - len(bed))))[: len(v)]
    else:
        bed = None
    if bed is not None:
        env = np.convolve(np.abs(v), np.ones(int(0.08 * SR)) / int(0.08 * SR), "same")
        env = env / (env.max() + 1e-9)
        duck = 1 - 0.65 * np.clip(env / 0.15, 0, 1)
        duck = np.convolve(duck, np.ones(int(0.05 * SR)) / int(0.05 * SR), "same")
        vr = np.sqrt(np.mean(v ** 2)) + 1e-9; br = np.sqrt(np.mean(bed ** 2)) + 1e-9
        bed = bed / br * vr * 10 ** (mus["level_db_under_voice"] / 20) * duck
        mix += bed
    peak = np.max(np.abs(mix))
    if peak > 0.98: mix *= 0.98 / peak
    mixed = os.path.join(wd, "_mix.wav")
    with wave.open(mixed, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    out = os.path.join(wd, plan.get("out", "byline.mp4"))
    run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", mixed, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-shortest", out])
    print("done:", out, "| caption y =", round(cap_base / H, 3))


if __name__ == "__main__":
    main(sys.argv[1])
