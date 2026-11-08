"""Append an outro: the last frame darkens and blurs, the brand logo pops in at the centre with a bounce,
then the handle appears cleanly beneath it.

Usage: python outro.py input.mp4 output.mp4 --logo logo.png --handle @cuttit [--secs 1.8] [--font Poppins-Bold.ttf]
"""
import argparse, os, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def spring(p, keys=(0.0, 0.7, 1.16, 0.95, 1.0)):
    p = min(max(p, 0), 1)
    if p >= 1: return keys[-1]
    x = p * (len(keys) - 1); i = int(x); f = x - i; f = 0.5 - 0.5 * np.cos(np.pi * f)
    return keys[i] + (keys[i + 1] - keys[i]) * f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--logo", required=True); ap.add_argument("--handle", required=True)
    ap.add_argument("--secs", type=float, default=1.8); ap.add_argument("--font", required=True)
    a = ap.parse_args()
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                               "stream=width,height,r_frame_rate:format=duration", "-of", "json", a.inp]))
    W, H = info["streams"][0]["width"], info["streams"][0]["height"]
    num, den = map(int, info["streams"][0]["r_frame_rate"].split("/")); fps = num / den
    dur = float(info["format"]["duration"])
    last = subprocess.check_output(["ffmpeg", "-v", "error", "-sseof", "-0.1", "-i", a.inp, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    base = Image.frombytes("RGB", (W, H), last[:W * H * 3])
    logo = Image.open(a.logo).convert("RGBA"); L = int(W * 0.30); logo = logo.resize((L, L), Image.LANCZOS)
    m = Image.new("L", (L, L), 0); ImageDraw.Draw(m).ellipse((0, 0, L - 1, L - 1), fill=255); logo.putalpha(m)
    font = ImageFont.truetype(a.font, int(W * 0.055))
    tmp = os.path.join(os.path.dirname(os.path.abspath(a.out)), "_outro.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                            "-f", "lavfi", "-t", str(a.secs), "-i", "anullsrc=r=48000:cl=stereo",
                            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", tmp], stdin=subprocess.PIPE)
    n = int(a.secs * fps)
    for i in range(n):
        t = i / fps
        k = min(1, t / 0.35)
        bl = base.filter(ImageFilter.GaussianBlur(14 * k))
        fr = Image.blend(base, bl, k).convert("RGBA")
        fr.alpha_composite(Image.new("RGBA", (W, H), (8, 8, 10, int(185 * k))))
        s = spring((t - 0.12) / 0.4)
        if s > 0.02:
            li = logo.resize((max(1, int(L * s)), max(1, int(L * s))), Image.BILINEAR)
            fr.alpha_composite(li, (int(W / 2 - li.width / 2), int(H * 0.45 - li.height / 2)))
        ha = min(1, max(0, (t - 0.55) / 0.3))
        if ha > 0:
            tl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(tl)
            d.text((W / 2, H * 0.45 + L * 0.5 + W * 0.09 - 12 * (1 - ha)), a.handle, font=font, fill=(255, 255, 255, int(255 * ha)), anchor="mm")
            fr.alpha_composite(tl)
        enc.stdin.write(np.asarray(fr.convert("RGB")).tobytes())
    enc.stdin.close(); enc.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.inp, "-i", tmp, "-filter_complex",
                    "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][au]", "-map", "[v]", "-map", "[au]",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", a.out], check=True)
    os.remove(tmp)
    print("outro added:", a.out)


if __name__ == "__main__":
    main()
