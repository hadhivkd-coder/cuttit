"""Turn an edit plan into a vertical MP4 with burned-in captions."""

from pathlib import Path

from .config import settings
from .media import has_audio, run
from .models import CaptionLine, KeepRange

FPS = 30
SIZES = {"rough": (720, 1280), "final": (1080, 1920)}


def _ass_time(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


def write_ass(path: Path, captions: list[CaptionLine], size: tuple[int, int],
              hook_text: str = "", watermark: str = "") -> Path:
    w, h = size
    font = settings.caption_font
    cap_size, hook_size, mark_size = round(h * 0.045), round(h * 0.055), round(h * 0.03)
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # White text, black outline, lower third.
        f"Style: Caption,{font},{cap_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,"
        f"1,0,0,0,100,100,0,0,1,{max(2, cap_size // 12)},1,2,60,60,{round(h * 0.22)},1",
        # Yellow box title near the top.
        f"Style: Hook,{font},{hook_size},&H00000000,&H00000000,&H0000D7FF,&H0000D7FF,"
        f"1,0,0,0,100,100,0,0,3,{max(6, hook_size // 5)},0,8,60,60,{round(h * 0.12)},1",
        f"Style: Mark,{font},{mark_size},&H80FFFFFF,&H80FFFFFF,&H80000000,&H00000000,"
        f"1,0,0,0,100,100,0,0,1,2,0,9,30,30,30,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for c in captions:
        lines.append(f"Dialogue: 0,{_ass_time(c.start)},{_ass_time(c.end)},Caption,,0,0,0,,"
                     f"{_ass_escape(c.text)}")
    if hook_text:
        lines.append(f"Dialogue: 1,{_ass_time(0)},{_ass_time(3)},Hook,,0,0,0,,{_ass_escape(hook_text)}")
    if watermark:
        lines.append(f"Dialogue: 2,{_ass_time(0)},{_ass_time(36000)},Mark,,0,0,0,,{_ass_escape(watermark)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _render_piece(src: Path, r: KeepRange, size: tuple[int, int], dst: Path) -> Path:
    """Cut one piece, fill a vertical frame, and normalise audio/video so pieces concat cleanly."""
    w, h = size
    vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"setsar=1,fps={FPS},format=yuv420p")
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{r.start:.3f}", "-to", f"{r.end:.3f}", "-i", str(src)]
    if not has_audio(src):
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    cmd += ["-map", "0:v:0", "-map", "0:a:0" if has_audio(src) else "1:a:0", "-shortest",
            "-vf", vf, "-af", "aresample=48000,aformat=channel_layouts=stereo",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", str(dst)]
    run(cmd)
    return dst


def render(clips: list[Path], ranges: list[KeepRange], captions: list[CaptionLine],
           out: Path, work: Path, kind: str = "final", hook_text: str = "") -> Path:
    size = SIZES[kind]
    work.mkdir(parents=True, exist_ok=True)
    pieces = [_render_piece(clips[r.clip], r, size, work / f"piece_{i:03d}.mp4")
              for i, r in enumerate(ranges)]

    concat_list = work / "pieces.txt"
    concat_list.write_text("".join(f"file '{p.resolve()}'\n" for p in pieces))
    joined = work / "joined.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c", "copy", str(joined)])

    ass = write_ass(work / "captions.ass", captions, size, hook_text=hook_text,
                    watermark="ROUGH CUT" if kind == "rough" else "")
    sub_filter = f"subtitles=filename='{ass.resolve()}'"
    if settings.fonts_dir:
        sub_filter += f":fontsdir='{settings.fonts_dir}'"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), "-vf", sub_filter,
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         "-c:v", "libx264", "-preset", "medium" if kind == "final" else "veryfast",
         "-crf", "20" if kind == "final" else "26",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)])
    return out
