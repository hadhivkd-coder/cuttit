"""One video, start to finish: transcripts -> Claude's plan -> tightened cuts -> render."""

from dataclasses import dataclass
from pathlib import Path

from .media import detect_silences
from .models import ClipTranscript, EditPlan
from .planner import plan_edit
from .render import render
from .timeline import build_captions, remove_silences, total_length
from .transcribe import transcribe_all


@dataclass
class EditResult:
    video: Path
    plan: EditPlan
    transcripts: list[ClipTranscript]
    seconds: float


def edit_video(clips: list[Path], style: str, out: Path, work: Path, kind: str = "rough",
               transcripts: list[ClipTranscript] | None = None,
               previous: EditPlan | None = None, feedback: str | None = None) -> EditResult:
    work.mkdir(parents=True, exist_ok=True)
    transcripts = transcripts or transcribe_all(clips, work)

    # A final with no new feedback reuses the approved rough-cut plan.
    if previous and not feedback:
        plan = previous
    else:
        plan = plan_edit(style, transcripts, previous=previous, feedback=feedback)

    silences = {i: detect_silences(c) for i, c in enumerate(clips)}
    ranges = remove_silences(plan.keep, silences)
    if not ranges:
        raise RuntimeError("nothing left after removing pauses")
    captions = build_captions(ranges, transcripts)
    render(clips, ranges, captions, out, work / "render", kind=kind, hook_text=plan.hook_text)
    return EditResult(video=out, plan=plan, transcripts=transcripts, seconds=total_length(ranges))
