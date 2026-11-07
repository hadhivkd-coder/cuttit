"""Generate the Byline SFX palette as WAV files (original sounds, no licence needed).

Usage: python sfx.py OUT_DIR
"""
import sys, os, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def _write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def _pink(n):
    # Voss-style pink noise approximation via 1/f filtering in the frequency domain
    f = np.fft.rfft(rng.standard_normal(n))
    k = np.arange(len(f)); k[0] = 1
    return np.fft.irfft(f / np.sqrt(k), n)


def _sweep_bandpass(x, f_lo, f_hi, up_frac=0.6):
    """Time-varying band-pass by STFT masking: centre sweeps f_lo -> f_hi -> f_lo."""
    n_fft, hop = 1024, 256
    win = np.hanning(n_fft)
    frames = 1 + (len(x) - n_fft) // hop
    out = np.zeros(len(x)); norm = np.zeros(len(x))
    freqs = np.fft.rfftfreq(n_fft, 1 / SR)
    for i in range(frames):
        t = i / max(frames - 1, 1)
        c = f_lo * (f_hi / f_lo) ** (t / up_frac) if t < up_frac else f_hi * (f_lo / f_hi) ** ((t - up_frac) / (1 - up_frac))
        bw = c * 0.9
        mask = np.exp(-0.5 * ((freqs - c) / bw) ** 2)
        seg = x[i * hop:i * hop + n_fft] * win
        y = np.fft.irfft(np.fft.rfft(seg) * mask, n_fft) * win
        out[i * hop:i * hop + n_fft] += y; norm[i * hop:i * hop + n_fft] += win ** 2
    return out / np.maximum(norm, 1e-6)


def _env(n, attack, release_pow=1.5):
    t = np.linspace(0, 1, n)
    a = np.clip(t / attack, 0, 1)
    r = (1 - t) ** release_pow
    return a * r


def _norm(x, peak_db):
    return x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)


def whoosh(dur=0.4, sub=False):
    n = int(SR * dur)
    x = _sweep_bandpass(_pink(n), 300, 3000) * _env(n, 0.55, 2.0)
    if sub:
        t = np.arange(n) / SR
        x = _norm(x, -3) + 0.6 * np.sin(2 * np.pi * 60 * t) * _env(n, 0.5, 2.0)
    return _norm(x, -1)


def pop(dur=0.06):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 1200 * (500 / 1200) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return _norm(np.sin(ph) * np.exp(-t / 0.015), -1)


def click(dur=0.008):
    n = int(SR * dur)
    x = rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4))
    return _norm(np.convolve(x, [0.5, 0.5], "same"), -1)


def glitch(dur=0.3):
    n = int(SR * dur); x = np.zeros(n)
    for s in rng.choice(np.arange(0, n - 2000, 500), 4, replace=False):
        L = int(rng.integers(900, 2400))
        b = np.round(rng.standard_normal(L) * 4) / 4  # bit-crush
        b = np.repeat(b[::6], 6)[:L]
        x[s:s + L] += b * np.hanning(L)
    return _norm(x, -1)


def low_hit(dur=0.6):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 55 + 40 * np.exp(-t / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)
    x[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return _norm(x, -1)


def riser(dur=0.5):
    n = int(SR * dur); t = np.arange(n) / SR
    noise = _sweep_bandpass(_pink(n), 400, 6000, up_frac=0.98)
    tone = np.sin(2 * np.pi * np.cumsum(200 * (4 ** (t / dur))) / SR) * 0.25
    env = (t / dur) ** 2.2
    return _norm((_norm(noise, -2) + tone) * env, -1)


def music_bed(seconds, bpm=90, seed=3):
    """Soft original lo-fi bed: warm chord pad + soft kick + quiet hats + vinyl hiss."""
    r = np.random.default_rng(seed)
    n = int(SR * seconds); t = np.arange(n) / SR
    beat = 60 / bpm; bar = beat * 4
    chords = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 65]]  # Am7 Fmaj7 Cmaj7 G7
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    pad = np.zeros(n)
    for b in range(int(seconds / bar) + 1):
        s0 = int(b * bar * SR); s1 = min(int((b + 1) * bar * SR), n)
        if s0 >= n: break
        tt = np.arange(s1 - s0) / SR
        env = np.minimum(tt / 0.4, 1) * np.minimum((bar - tt) / 0.3, 1)
        for m in chords[b % 4]:
            f = hz(m)
            pad[s0:s1] += env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt + 0.5)) * 0.12
    # gentle low-pass (one-pole)
    lp = np.zeros(n); a = 0.06
    for i in range(1, n): lp[i] = lp[i - 1] + a * (pad[i] - lp[i - 1])
    drums = np.zeros(n)
    k = low_hit(0.35) * 0.55
    for i in range(int(seconds / beat) + 1):
        s0 = int(i * beat * SR)
        if s0 >= n: break
        if i % 4 in (0, 2):
            e = min(len(k), n - s0); drums[s0:s0 + e] += k[:e]
        for h in (0, 0.5):
            hs = int((i + h) * beat * SR)
            if hs < n:
                L = min(int(0.03 * SR), n - hs)
                drums[hs:hs + L] += r.standard_normal(L) * np.exp(-np.arange(L) / (0.006 * SR)) * 0.05
    hiss = r.standard_normal(n) * 0.004
    x = lp * 1.0 + drums + hiss
    fade = np.minimum(np.minimum(t / 0.8, 1), np.minimum((seconds - t) / 1.0, 1))
    return _norm(x * fade, -1)


PALETTE = {
    "riser": riser,
    "deep_whoosh": lambda: whoosh(0.5, sub=True),
    "whoosh": lambda: whoosh(0.4),
    "pop": pop, "click": click, "glitch": glitch, "low_hit": low_hit,
}

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "sfx"
    os.makedirs(out, exist_ok=True)
    for name, fn in PALETTE.items():
        _write(os.path.join(out, name + ".wav"), fn())
    print("wrote", ", ".join(PALETTE))
