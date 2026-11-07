"""Byline renderer: turns a source talking-head video + plan.json into the finished reel.

Usage: python render.py plan.json
All times in plan.json are in the SOURCE video's timeline (seconds); cuts are applied automatically.
See plan.example.json for the format. Style values come from ../style.json (overridable in plan["style"]).
"""
import json, math, os, subprocess, sys, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30


# ---------------------------------------------------------------- helpers
def run(cmd):
    subprocess.run(cmd, check=True)


def load_style(plan):
    st = json.load(open(os.path.join(HERE, "..", "style.json")))
    for k, v in plan.get("style", {}).items():  # user overrides (fonts, colours...)
        if isinstance(v, dict) and isinstance(st.get(k), dict):
            st[k].update(v)
        else:
            st[k] = v
    return st


def hex_rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class TimeMap:
    """Maps source time -> output time after removing cut ranges."""
    def __init__(self, cuts, dur):
        self.keep, t = [], 0.0
        for a, b in sorted(cuts):
            if a > t: self.keep.append((t, a))
            t = max(t, b)
        if t < dur: self.keep.append((t, dur))

    def __call__(self, ts):
        out = 0.0
        for a, b in self.keep:
            if ts <= b: return out + max(ts - a, 0)
            out += b - a
        return out

    @property
    def duration(self):
        return sum(b - a for a, b in self.keep)


# ---------------------------------------------------------------- text
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


def draw_line(fonts, parts, color=(255, 255, 255)):
    """parts: [(text, kind, size)] -> (RGBA image, baseline_y). Words joined by a space of 0.26 x sans size."""
    pad = 120
    big = max(p[2] for p in parts)
    canvas = Image.new("RGBA", (W * 2, big * 3 + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    base = pad + int(big * 1.6)
    x = pad
    for i, (text, kind, size) in enumerate(parts):
        f = fonts.get(kind, size); tr = fonts.tracking(kind) * size
        for ch in text:
            d.text((x, base), ch, font=f, fill=color + (255,), anchor="ls")
            x += f.getlength(ch) + tr
        if i < len(parts) - 1:
            x += parts[i][2] * 0.08 + parts[0][2] * 0.26 * (0.6 if kind == "serif" else 1)
    bbox = canvas.getbbox()
    if not bbox: return canvas.crop((0, 0, 2, 2)), 0
    img = canvas.crop((bbox[0] - 40, bbox[1] - 40, bbox[2] + 40, bbox[3] + 40))
    return img, base - (bbox[1] - 40)


def styled(img, shadow=True, glow=0.0):
    """Add the tight drop shadow and optional soft white glow under a text image."""
    a = img.split()[3]
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    if glow:
        g = a.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * glow))
        out = Image.alpha_composite(out, Image.merge("RGBA", (*[Image.new("L", img.size, 255)] * 3, g)))
    if shadow:
        s = a.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.6))
        sh = Image.merge("RGBA", (*[Image.new("L", img.size, 0)] * 3, s))
        out.alpha_composite(sh, (0, 2))
    return Image.alpha_composite(out, img)


def animate(img, p, scale_keys=(0.88, 1.04, 1.0), blur_from=14):
    """Blur-in with small overshoot. p in 0..1."""
    p = min(max(p, 0), 1)
    if p >= 1: return img
    s0, s1, s2 = scale_keys
    s = s0 + (s1 - s0) * (p / 0.7) if p < 0.7 else s1 + (s2 - s1) * ((p - 0.7) / 0.3)
    w, h = max(1, int(img.width * s)), max(1, int(img.height * s))
    out = img.resize((w, h), Image.LANCZOS)
    r = blur_from * (1 - p)
    if r > 0.3: out = out.filter(ImageFilter.GaussianBlur(r))
    a = out.split()[3].point(lambda v: int(v * p))
    out.putalpha(a)
    return out


def paste_center(frame, img, cx, baseline_y=None, cy=None, base_off=None):
    x = int(cx - img.width / 2)
    y = int(baseline_y - base_off) if baseline_y is not None else int(cy - img.height / 2)
    frame.alpha_composite(img, (max(x, -img.width + 1), y)) if 0 <= y < H else None


def pill(fonts, text, colors, glow_rgba, st):
    c = st["chips"]; size = c["px"]
    t_img, _ = draw_line(fonts, [(text, c["font"], size)])
    pw, ph = c["padding_px"][1], c["padding_px"][0]
    w, h = t_img.width - 80 + 2 * pw, t_img.height - 80 + 2 * ph
    m = 60
    img = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    # glow
    g = Image.new("L", img.size, 0); ImageDraw.Draw(g).rounded_rectangle((m, m, m + w, m + h), h // 2, fill=255)
    g = g.filter(ImageFilter.GaussianBlur(c["glow_px"]))
    gr = glow_rgba
    img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", img.size, v) for v in gr[:3]], g.point(lambda v: int(v * gr[3])))))
    # gradient body
    c0, c1 = np.array(hex_rgb(colors[0])), np.array(hex_rgb(colors[1]))
    grad = np.linspace(0, 1, w)[None, :, None] * (c1 - c0) + c0
    body = np.repeat(grad, h, axis=0).astype(np.uint8)
    hl = np.ones((h, w, 1)); hl[: int(h * 0.42)] = 1.18
    body = np.clip(body * hl, 0, 255).astype(np.uint8)
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=255)
    b = Image.fromarray(body, "RGB").convert("RGBA"); b.putalpha(mask)
    img.alpha_composite(b, (m, m))
    img.alpha_composite(t_img, (m + pw - 40, m + ph - 40))
    return img


# ---------------------------------------------------------------- main
def main(plan_path):
    plan = json.load(open(plan_path))
    st = load_style(plan)
    wd = os.path.dirname(os.path.abspath(plan_path))
    src = os.path.join(wd, plan["source"])
    fonts = Fonts(st, os.path.join(wd, plan.get("font_dir", "fonts")))
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
    tm = TimeMap(plan.get("cuts", []), dur)
    T = lambda x: tm(x)

    # 1) base video/audio with dead air removed, 1080x1920 @ 30 fps
    vf, af = [], []
    for i, (a, b) in enumerate(tm.keep):
        vf.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]"); af.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}]")
    n = len(tm.keep)
    fcv = ";".join(vf) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v];[v]scale={W}:{H}:flags=lanczos,fps={FPS}[vo]"
    fca = ";".join(af) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a];[a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[ao]"
    base = os.path.join(wd, "_base.mp4"); voice = os.path.join(wd, "_voice.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fcv, "-map", "[vo]", "-an", "-c:v", "libx264", "-crf", "12", base])
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fca, "-map", "[ao]", "-ac", "1", voice])

    # 2) caption height from the face (OpenCV), anchor for zooms
    cap = cv2.VideoCapture(base); faces = []
    for k in range(0, int(tm.duration * FPS), 15):
        cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        if not hasattr(cv2, "CascadeClassifier"):  # OpenCV 5 removed it: pip install "opencv-python-headless<5"
            break
        det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml").detectMultiScale(g, 1.1, 5, minSize=(160, 160))
        if len(det): faces.append(max(det, key=lambda r: r[2] * r[3]))
    cap.release()
    fx, fy, fw, fh = np.median(np.array(faces), axis=0) if faces else (W * 0.35, H * 0.2, W * 0.3, W * 0.3)
    chin = fy + fh * 1.12
    anchor = plan.get("zoom_anchor", [fx + fw / 2, fy + fh / 2])

    def cap_y(scale):
        y = anchor[1] + scale * (chin - anchor[1]) + 0.17 * H
        return min(max(y, 0.44 * H), 0.62 * H)

    # 3) timeline (output seconds)
    scales = sorted([(T(t), s) for t, s in plan.get("scales", [[0, 1.0]])])
    bw = [(T(a), T(b)) for a, b in plan.get("bw", [])]
    cards = [dict(c, t0=T(c["t0"]), t1=T(c["t1"])) for c in plan.get("cards", [])]
    caps = [dict(c, t0=T(c["t0"]), t1=T(c["t1"])) for c in plan.get("captions", [])]
    chips = [dict(c, t0=T(c["t0"]), t1=T(c["t1"]), items=[dict(i, t=T(i["t"])) for i in c["items"]]) for c in plan.get("chips", [])]
    cta = plan.get("cta")
    if cta: cta = dict(cta, t0=T(cta["t0"]))
    cs = st["captions"]; cam = st["camera"]

    # pre-render static text images
    def cap_img(c):
        parts = [(w, "serif" if i in c.get("power", []) else "sans", cs["serif_px"] if i in c.get("power", []) else cs["sans_px"]) for i, w in enumerate(c["words"])]
        img, bo = draw_line(fonts, parts)
        return styled(img, glow=0.35 if c.get("power") else 0), bo
    for c in caps:
        c["img"], c["bo"] = cap_img(c)
        g, gbo = draw_line(fonts, [(" ".join(c["words"]), "sans", cs["ghost_px"])])
        g.putalpha(g.split()[3].point(lambda v: int(v * 0.35))); c["ghost"], c["gbo"] = g, gbo
    for c in cards:
        spec = st["word_cards"][c["bg"]]
        img, _ = draw_line(fonts, [(c["text"], spec["font"], spec["px"])], color=hex_rgb(spec["color"]))
        c["img"], c["bgc"] = img, hex_rgb(spec["bg"])
    for c in chips:
        col = st["colors"]["chip_" + c.get("color", "blue")]
        gl = st["colors"]["chip_" + c.get("color", "blue") + "_glow"]
        rgba = [int(x) for x in gl[gl.index("(") + 1:gl.index(")")].split(",")[:3]] + [float(gl.split(",")[-1].rstrip(")"))]
        for it in c["items"]: it["img"] = pill(fonts, it["text"], col, rgba, st)
    if cta:
        cimg, cbo = draw_line(fonts, [(st["cta"]["small"], "sans", st["cta"]["small_px"])])
        kimg, kbo = draw_line(fonts, [(f"“{cta['word'].upper()}”", "serif", st["cta"]["big_px"])])
        cta.update(small=styled(cimg), big=styled(kimg, glow=0.4), sbo=cbo, kbo=kbo)

    # 4) frames
    nfr = int(round(tm.duration * FPS))
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    silent = os.path.join(wd, "_video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    tf = cam["transition"]["frames"]; flash = cam["after_cut_flash"]
    for i in range(nfr):
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        t = i / FPS
        fr = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        # current scale + transition
        cur = [s for s in scales if s[0] <= t + 1e-6]; s_now = cur[-1][1] if cur else 1.0
        since = t - cur[-1][0] if cur else 99
        in_bw = any(a <= t < b for a, b in bw)
        s_eff = s_now * (st["bw_punch"]["zoom"] if in_bw else 1.0)

        def zoom(img, s):
            M = np.float32([[s, 0, anchor[0] * (1 - s)], [0, s, anchor[1] * (1 - s)]])
            return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

        k = int(round(since * FPS))
        if len(cur) > 1 and k < tf:
            strength = 1 - k / tf
            acc = np.zeros_like(fr, np.float32)
            for j in range(5):
                acc += zoom(fr, s_eff * (1 + cam["transition"]["scale"][1] - 1) ** 0 * (1 + 0.06 * strength * j / 4))
            img = acc / 5
        else:
            img = zoom(fr, s_eff).astype(np.float32)
        if len(cur) > 1 and k < flash["decay_frames"]:
            img *= 1 + flash["brightness"] * (1 - k / flash["decay_frames"])
        if in_bw:
            g = img @ np.array([0.299, 0.587, 0.114], np.float32)
            img = np.repeat(g[..., None], 3, axis=2) * 1.05
        img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")

        card = next((c for c in cards if c["t0"] <= t < c["t1"]), None)
        if card:
            img = Image.new("RGBA", (W, H), card["bgc"] + (255,))
            p = (t - card["t0"]) * FPS / st["word_cards"]["enter"]["frames"]
            a = animate(card["img"], p, (0.92, 0.99, 1.0), st["word_cards"]["enter"]["blur_px"][0])
            paste_center(img, a, W / 2, cy=H / 2)
        else:
            y = cap_y(s_now)
            c = next((c for c in caps if c["t0"] <= t < c["t1"]), None)
            if c:
                p = (t - c["t0"]) * FPS / cs["enter"]["frames"]
                a = animate(c["img"], p)
                prev = next((q for q in reversed(caps) if q["t1"] <= c["t0"] + 1e-6 and c["t0"] - q["t1"] < 0.4), None)
                if prev and not any(cd["t0"] >= prev["t1"] - 1e-6 and cd["t1"] <= c["t0"] + 1e-6 for cd in cards):
                    k_s = a.height / c["img"].height
                    big_px = cs["serif_px"] if c.get("power") else cs["sans_px"]
                    top = y - big_px * 0.72 * k_s  # top of the current line's letters
                    paste_center(img, prev["ghost"], W / 2, baseline_y=top - 14, base_off=prev["gbo"])
                paste_center(img, a, W / 2, baseline_y=y, base_off=c["bo"] * (a.height / c["img"].height))
            ch = next((c for c in chips if c["t0"] <= t < c["t1"]), None)
            if ch:
                shown = [it for it in ch["items"] if it["t"] <= t]
                hgt = sum(it["img"].height - 120 for it in shown) + st["chips"]["stack_gap_px"] * (len(shown) - 1)
                yy = y - 60 - hgt / 2
                for it in shown:
                    p = (t - it["t"]) * FPS / st["chips"]["enter"]["frames"]
                    a = animate(it["img"], p, (0.0, 1.12, 1.0), 0)
                    h0 = it["img"].height - 120
                    paste_center(img, a, W / 2, cy=yy + h0 / 2)
                    yy += h0 + st["chips"]["stack_gap_px"]
            if cta and t >= cta["t0"]:
                p = (t - cta["t0"]) * FPS / 6
                big = animate(cta["big"], p)
                paste_center(img, big, W / 2, baseline_y=H * 0.52, base_off=cta["kbo"] * (big.height / cta["big"].height))
                paste_center(img, animate(cta["small"], p), W / 2, baseline_y=H * 0.52 - st["cta"]["big_px"] * 0.95, base_off=cta["sbo"])
        enc.stdin.write(np.asarray(img.convert("RGB")).tobytes())
    enc.stdin.close(); enc.wait(); dec.wait()

    # 5) audio: voice + generated SFX
    sfx_dir = os.path.join(wd, "_sfx"); run([sys.executable, os.path.join(HERE, "sfx.py"), sfx_dir])
    with wave.open(voice) as w: v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    mix = v.copy(); levels = st["audio"]["sfx_levels_db"]
    for ts, name in plan.get("sfx", []):
        with wave.open(os.path.join(sfx_dir, name + ".wav")) as w:
            s = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        s *= 10 ** ((levels.get(name, -18) + 1) / 20)
        start = int(max(T(ts) - 2 / FPS, 0) * 48000); end = min(start + len(s), len(mix))
        mix[start:end] += s[: end - start]
    mix = np.clip(mix, -1, 1)
    mixed = os.path.join(wd, "_mix.wav")
    with wave.open(mixed, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    out = os.path.join(wd, plan.get("out", "byline.mp4"))
    run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", mixed, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-shortest", out])
    print("done:", out)


if __name__ == "__main__":
    main(sys.argv[1])
