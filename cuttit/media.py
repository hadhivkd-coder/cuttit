"""ffmpeg helpers: probing, audio extraction and silence detection."""

import json
import re
import subprocess
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise FFmpegError(f"{cmd[0]} failed ({proc.returncode}): {proc.stderr[-2000:]}")
    return proc


def duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "json", str(path)]).stdout
    return float(json.loads(out)["format"]["duration"])


def has_audio(path: Path) -> bool:
    out = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
               "stream=index", "-of", "json", str(path)]).stdout
    return bool(json.loads(out).get("streams"))


def extract_audio(src: Path, dst: Path) -> Path:
    """Small mono MP3 for speech-to-text (about 0.25 MB per minute)."""
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
         "-b:a", "32k", str(dst)])
    return dst


_SILENCE_START = re.compile(r"silence_start: (-?[\d.]+)")
_SILENCE_END = re.compile(r"silence_end: (-?[\d.]+)")


def detect_silences(path: Path, noise_db: int = -35, min_len: float = 0.6) -> list[tuple[float, float]]:
    """Return (start, end) pairs of pauses longer than min_len seconds."""
    if not has_audio(path):
        return []
    proc = run(["ffmpeg", "-hide_banner", "-i", str(path), "-af",
                f"silencedetect=n={noise_db}dB:d={min_len}", "-f", "null", "-"])
    starts = [max(0.0, float(m)) for m in _SILENCE_START.findall(proc.stderr)]
    ends = [float(m) for m in _SILENCE_END.findall(proc.stderr)]
    if len(starts) > len(ends):          # file ended while silent
        ends.append(duration(path))
    return list(zip(starts, ends))
