"""End-to-end render with fake AI steps: checks ffmpeg cutting, silence removal and captions."""

import subprocess
from pathlib import Path

import pytest

from cuttit import pipeline
from cuttit.media import duration
from cuttit.models import ClipTranscript, EditPlan, KeepRange, Segment


def _make_clip(path: Path, size: str) -> Path:
    # 6 s: tone 0-2 s, silence 2-4 s, tone 4-6 s.
    audio = ("sine=frequency=440:duration=6,volume=enable='between(t,2,4)':volume=0")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=30:duration=6",
                    "-f", "lavfi", "-i", audio, "-shortest", "-c:v", "libx264", "-c:a", "aac", str(path)],
                   check=True)
    return path


@pytest.mark.parametrize("kind,expected_size", [("rough", "720x1280"), ("final", "1080x1920")])
def test_edit_video_renders_vertical_reel(tmp_path, monkeypatch, kind, expected_size):
    clips = [_make_clip(tmp_path / "a.mp4", "1280x720"), _make_clip(tmp_path / "b.mp4", "720x1280")]
    transcripts = [ClipTranscript(clip=i, duration=6.0, segments=[
        Segment(start=0.0, end=2.0, text="ഹലോ എല്ലാവർക്കും welcome"),
        Segment(start=4.0, end=6.0, text="ഇന്ന് നമുക്ക് നോക്കാം")]) for i in range(2)]
    plan = EditPlan(keep=[KeepRange(clip=1, start=4.0, end=6.0), KeepRange(clip=0, start=0.0, end=6.0)],
                    hook_text="ഇത് കാണൂ", notes="test")
    monkeypatch.setattr(pipeline, "plan_edit", lambda *a, **k: plan)

    out = tmp_path / "out.mp4"
    result = pipeline.edit_video(clips, "talking_head", out, tmp_path / "work", kind=kind,
                                 transcripts=transcripts)

    # The 2 s pause in clip 0 is cut down to 0.3 s: 2 + (2.15 + 2.15) ≈ 6.3 s.
    assert 5.8 < duration(out) < 6.8
    assert abs(result.seconds - duration(out)) < 0.5
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0:s=x", str(out)],
                           capture_output=True, text=True, check=True).stdout.strip()
    assert probe == expected_size
