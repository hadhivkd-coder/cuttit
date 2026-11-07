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


def run(cmd):
    subprocess.run(cmd, check=True)


def load_style(plan):
    st = json.load(open(os.path.join(HERE, "..", "style.json")))
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


def scrim(w, h, strength=0.42):
    yy, xx = np.mgrid[0:h, 0:w]
    d = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    a = np.clip(1 - d, 0, 1) ** 1.6 * 255 * strength
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


# ------------------------------------------------------------------ main
def main(plan_path):
    plan = json.load(open(plan_path))
    st = load_style(plan)
    wd = os.path.dirname(os.path.abspath(plan_path))
    src = os.path.join(wd, plan["source"])
    fonts = Fonts(st, os.path.join(wd, plan.get("font_dir", "fonts")))
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
    speed = plan.get("speed", 1.0)
    tm = TimeMap(plan.get("cuts", []), dur, speed); T = tm
    cs, cam, gr = st["captions"], st["camera"], st.get("grade", {})

    # 1) base: cut dead air, grade, 1080x1920@30
    vf, af = [], []
    for i, (a, b) in enumerate(tm.keep):
        vf.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]"); af.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}]")
    n = len(tm.keep)
    grade = gr.get("ffmpeg", "eq=contrast=1.10:brightness=-0.015:saturation=1.10,unsharp=5:5:0.5")
    fcv = ";".join(vf) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v];[v]setpts=PTS/{speed},scale={W}:{H}:flags=lanczos,minterpolate=fps={FPS}:mi_mode=blend[vs];[vs]{grade}[vo]"
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
            img, bo, adv = word_img(fonts, w, "serif" if pw else "sans", cs["serif_px"] if pw else cs["sans_px"])
            c["w"].append(dict(img=styled(img), glow=styled(img, shadow=False, glow=0.9, glow_px=22) if pw else None,
                               bo=bo, adv=adv, power=pw))
        tot = sum(x["adv"] for x in c["w"]) + gap * (len(c["w"]) - 1)
        x = W / 2 - tot / 2
        for x_ in c["w"]: x_["x"] = x; x += x_["adv"] + gap
        c["width"] = tot
        g, gbo, gadv = word_img(fonts, " ".join(c["words"]), "sans", cs["ghost_px"])
        g = styled(g); g.putalpha(g.split()[3].point(lambda v: int(v * 0.38))); c["ghost"], c["gbo"] = g, gbo
    for c in cards:
        spec = st["word_cards"][c["bg"]]
        img, bo, adv = word_img(fonts, c["text"], spec["font"], spec["px"], color=hex_rgb(spec["color"]))
        c["img"], c["bgc"] = img, hex_rgb(spec["bg"])
    for c in chips:
        col = st["colors"]["chip_" + c.get("color", "blue")]; gl = rgba_css(st["colors"]["chip_" + c.get("color", "blue") + "_glow"])
        for it in c["items"]: it["img"] = pill(fonts, it["text"], col, gl, st)
    blue = hex_rgb(st["colors"]["chip_blue"][0])
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
        for key in ("strike_t", "click_t"):
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

    def draw_graphic(img, g, t):
        if not (g["t0"] <= t < g["t1"]): return
        cy = g.get("y", 0.7) * H; age = t - g["t0"]
        if g["type"] == "counter":
            u = ease_out(age / g.get("count_s", 0.5))
            val = g.get("from", 0) + (g["to"] - g.get("from", 0)) * u
            txt = f"{int(val):,}"
            col = hex_rgb(g.get("color", "#FFFFFF"))
            num, nbo, nadv = word_img(fonts, txt, "sans", g.get("px", 110), color=col)
            lab, lbo, ladv = word_img(fonts, g.get("suffix", ""), "serif", int(g.get("px", 110) * 0.8), color=col)
            tot = nadv + 24 + ladv; x = W / 2 - tot / 2
            ni, ndy = land(num, age * FPS / 6, rise=24, blur=14, s_from=1.12)
            img.alpha_composite(ni, (int(x + nadv / 2 - ni.width / 2), int(cy - nbo + ndy)))
            img.alpha_composite(lab, (int(x + nadv + 24 - (lab.width - ladv) / 2), int(cy - lbo)))
            if "strike_t" in g:
                q = ease_out((t - g["strike_t"]) * FPS / 7)
                strike(img, x - 20, cy - g.get("px", 110) * 0.28, x + tot + 20, cy - g.get("px", 110) * 0.42, q)
        elif g["type"] == "grid":
            size = g.get("size", 330); x0 = W / 2 - size / 2; y0 = cy - size / 2
            panel = Image.new("RGBA", (int(size + 60), int(size + 60)), (0, 0, 0, 0))
            pm = Image.new("L", panel.size, 0); ImageDraw.Draw(pm).rounded_rectangle((0, 0, panel.width - 1, panel.height - 1), 34, fill=150)
            panel.putalpha(pm); img.alpha_composite(panel, (int(x0 - 30), int(y0 - 30)))
            for k_, (r_, c_, tim) in enumerate(g["tiles"]):
                tt = age - k_ * g.get("stagger", 0.05)
                if tt < 0: continue
                ti = scale_fade(tim, tt * FPS / 6, 0.2, 1.08)
                cx_ = x0 + c_ * (g["tile"] + g["gap"]) + g["tile"] / 2; cy_ = y0 + r_ * (g["tile"] + g["gap"]) + g["tile"] / 2
                img.alpha_composite(ti, (int(cx_ - ti.width / 2), int(cy_ - ti.height / 2)))
            if "strike_t" in g:
                q1 = ease_out((t - g["strike_t"]) * FPS / 6); q2 = ease_out((t - g["strike_t"]) * FPS / 6 - 0.6)
                strike(img, x0 - 10, y0 - 10, x0 + size + 10, y0 + size + 10, q1, 16)
                strike(img, x0 + size + 10, y0 - 10, x0 - 10, y0 + size + 10, q2, 16)
        elif g["type"] == "button":
            b = g["img"]; ct = g.get("click_t", g["t0"] + 0.6)
            sc = 1.0
            if 0 <= t - ct < 0.25: sc = 0.93 + 0.07 * ((t - ct) / 0.25)
            bi = scale_fade(b, age * FPS / 7)
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

    # 4) frames
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    dec_raw = subprocess.Popen(["ffmpeg", "-v", "error", "-i", ungraded, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE) if wm else None
    silent = os.path.join(wd, "_video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
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
             f"{crop}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setpts=PTS/{slow * speed},minterpolate=fps={FPS}:mi_mode=blend,{grade}",
             "-c:v", "libx264", "-crf", "14", path])
        cutaways.append(dict(t0=t0o, t1=t1o, path=path, dec=None, zoom=c.get("zoom", [1.0, 1.08])))

    trans_pts = plan.get("transitions_extra", [])
    trans_pts = [T(x) for x in trans_pts] + [c["t0"] for c in cutaways] + [c["t1"] for c in cutaways]
    trans_pts += [c["t0"] for c in cards] + [c["t1"] for c in cards] + [a for a, b in bw] + [b for a, b in bw]
    trans_pts = sorted(set(round(x, 3) for x in trans_pts))
    rb_frames, rb_peak = cam.get("radial_frames", 6), cam.get("radial_strength", 0.14)

    def radial_strength(t):
        return max([rb_peak * max(0, 1 - abs(t - p) * FPS / rb_frames) for p in trans_pts] + [0])

    def radial_blur(arr, s, cx=W / 2, cy=H * 0.45, n=9):
        acc = np.zeros_like(arr, np.float32)
        for j in range(n):
            z = 1 + s * j / (n - 1)
            M = np.float32([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]])
            acc += cv2.warpAffine(arr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return acc / n

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
            bump = sum(0.045 * (min(1, (t - b) * FPS / 3) if t - b < 3 / FPS else np.exp(-((t - b) * FPS - 3) / 6)) for b in bumps if 0 <= t - b < 1.0)
            s_eff = s_now * (1 + push * min(since, 3.0)) * (1 + bump) * (st["bw_punch"]["zoom"] if in_bw else 1.0)
            sh = [(rng.normal(0, 9) * np.exp(-(t - b) * FPS / 5), rng.normal(0, 9) * np.exp(-(t - b) * FPS / 5)) for b in shakes if 0 <= t - b < 0.35]
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
            else:
                out = zoom(fr, s_eff).astype(np.float32)
        else:
            k = int(round(since * FPS))
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

        card = next((c for c in cards if c["t0"] <= t < c["t1"]), None)
        if card:
            img = Image.new("RGBA", (W, H), card["bgc"] + (255,))
            p = (t - card["t0"]) * FPS / st["word_cards"]["enter"]["frames"]
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
                    top = y - (cs["serif_px"] if c.get("power") else cs["sans_px"]) * 0.78
                    gi = prev["ghost"]; img.alpha_composite(gi, (int(W / 2 - gi.width / 2), int(top - 12 - prev["gbo"])))
                for wd_, wt in zip(c["w"], c["wt"]):
                    if t < wt: continue
                    p = (t - wt) * FPS / 6
                    im, ddy = land(wd_["img"], p)
                    cx = wd_["x"] + wd_["adv"] / 2
                    sc = im.width / wd_["img"].width
                    if wd_["power"] and wd_["glow"] is not None:
                        pulse = max(0, 1 - (t - wt) * FPS / 14)
                        if p >= 1 and pulse > 0:
                            gl = wd_["glow"].copy(); gl.putalpha(gl.split()[3].point(lambda v: int(v * pulse)))
                            img.alpha_composite(gl, (int(cx - gl.width / 2), int(y - wd_["bo"])))
                    img.alpha_composite(im, (int(cx - im.width / 2), int(y - wd_["bo"] * sc + ddy)))
                    if wd_["power"]:  # underline sweep
                        q = ease_out(((t - wt) * FPS - 4) / 8)
                        if q > 0:
                            uw = int(wd_["adv"] * 0.92 * q); ux = int(wd_["x"] + wd_["adv"] * 0.04)
                            uy = int(y + cs["serif_px"] * 0.12)
                            ImageDraw.Draw(img).rounded_rectangle((ux, uy, ux + max(uw, 2), uy + 7), 3, fill=blue + (235,))
            if stat:
                p = (t - stat["t0"]) * FPS / 7
                si = scale_fade(stat["img"], p, 0.3, 1.1)
                sy = y + stat.get("dy", 40)
                img.alpha_composite(si, (int(W / 2 - si.width / 2), int(sy - si.height / 2)))
                if t - stat["t0"] > 0.2:
                    li, ldy = land(stat["label_img"], (t - stat["t0"] - 0.2) * FPS / 6)
                    img.alpha_composite(li, (int(W / 2 - li.width / 2), int(sy + stat.get("px", 360) * 0.42 - stat["label_img"].height * 0.35 + ldy)))
            if ch:
                shown = [it for it in ch["items"] if it["t"] <= t]
                hs = [it["img"].height - 140 for it in shown]
                yy = y - 40 - (sum(hs) + st["chips"]["stack_gap_px"] * (len(shown) - 1)) / 2
                for it, h0 in zip(shown, hs):
                    a = scale_fade(it["img"], (t - it["t"]) * FPS / st["chips"]["enter"]["frames"])
                    img.alpha_composite(a, (int(W / 2 - a.width / 2), int(yy + h0 / 2 - a.height / 2)))
                    yy += h0 + st["chips"]["stack_gap_px"]
            if cta and t >= cta["t0"]:
                p = (t - cta["t0"]) * FPS / 6
                big, bdy = land(cta["big"], p)
                img.alpha_composite(big, (int(W / 2 - big.width / 2), int(H * 0.52 - cta["kbo"] + bdy)))
                sm, sdy = land(cta["small"], p)
                img.alpha_composite(sm, (int(W / 2 - sm.width / 2), int(H * 0.52 - st["cta"]["big_px"] * 0.95 - cta["sbo"] + sdy)))
        for gfx in graphics:
            draw_graphic(img, gfx, t)
        rs = radial_strength(t)
        frame_out = np.asarray(img.convert("RGB"))
        if rs > 0.005:
            frame_out = np.clip(radial_blur(frame_out.astype(np.float32), rs), 0, 255).astype(np.uint8)
        enc.stdin.write(frame_out.tobytes())
    enc.stdin.close(); enc.wait(); dec.wait()
    if dec_raw: dec_raw.wait()

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
        events += [(c["t0"] - plan.get("riser_s", 0.5) + 2 / FPS, "riser") for c in cards if not any(abs(c["t0"] - d["t1"]) < 0.05 for d in cards)]
        if smooth:
            events = [e for e in events if e[1] != "whoosh"] + [(p_ - 0.12, "whoosh") for p_ in trans_pts if all(abs(p_ - c["t0"]) > 0.05 for c in cards)]
        if "highlight" in bank:
            events += [(c["wt"][i_] + 4 / FPS, "highlight") for c in caps for i_ in c.get("power", [])]
    for ts, nm in events:
        if nm not in bank: print("no sfx for", nm); continue
        s = bank[nm] * 10 ** ((levels.get(nm, -18) + 1) / 20)
        start = int(max(ts - 2 / FPS, 0) * SR); end = min(start + len(s), len(mix))
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
