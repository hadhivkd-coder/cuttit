"""Claude reads the transcripts and decides which parts to keep, in what order."""

import json

import anthropic
from pydantic import BaseModel

from .config import settings
from .models import ClipTranscript, EditPlan, KeepRange
from .styles import instructions

SYSTEM = """You are the editor at Cuttit, a reel-editing service for businesses and creators in Kerala.
Clients send raw phone clips over WhatsApp; you decide the cut. Speech is Malayalam, English or a mix.
You only see transcripts. Each line is one phrase, labelled [c<clip> s<segment>].
Pick the phrases to keep as ranges of consecutive segments from one clip, listed in the order
they should play. You may reorder ranges (for example, to move a hook to the front) and use
ranges from several clips. Never invent content and never split a segment."""


class _Pick(BaseModel):
    clip: int
    from_seg: int
    to_seg: int


class _PlanOut(BaseModel):
    keep: list[_Pick]
    hook_text: str
    notes: str


_SCHEMA = {
    "type": "object",
    "properties": {
        "keep": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "clip": {"type": "integer"},
                    "from_seg": {"type": "integer"},
                    "to_seg": {"type": "integer"},
                },
                "required": ["clip", "from_seg", "to_seg"],
                "additionalProperties": False,
            },
        },
        "hook_text": {"type": "string", "description": "On-screen title for the first 3 seconds, max 6 words, in the speaker's language. Empty string for none."},
        "notes": {"type": "string", "description": "One sentence for the human reviewer: what you cut and why."},
    },
    "required": ["keep", "hook_text", "notes"],
    "additionalProperties": False,
}


def _format_transcripts(transcripts: list[ClipTranscript]) -> str:
    lines = []
    for t in transcripts:
        lines.append(f"## Clip {t.clip} ({t.duration:.1f}s, language: {t.language})")
        if not t.segments:
            lines.append("(no speech)")
        for i, s in enumerate(t.segments):
            lines.append(f"[c{t.clip} s{i}] {s.start:.1f}-{s.end:.1f}: {s.text}")
    return "\n".join(lines)


def plan_edit(style: str, transcripts: list[ClipTranscript],
              previous: EditPlan | None = None, feedback: str | None = None,
              client: anthropic.Anthropic | None = None) -> EditPlan:
    client = client or anthropic.Anthropic()
    user = f"{instructions(style)}\n\n# Transcripts\n{_format_transcripts(transcripts)}"
    if previous and feedback:
        user += (f"\n\n# Previous cut (sent to the client as the rough cut)\n"
                 f"{previous.model_dump_json(indent=1)}\n\n"
                 f"# Client's change request\n{feedback}\n\n"
                 "Make a new cut that applies the client's request. Change nothing else.")

    resp = client.beta.messages.create(
        model=settings.anthropic_model,
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": _SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined to plan this edit: {resp.stop_details}")
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("edit plan was cut off (max_tokens)")
    text = next(b.text for b in resp.content if b.type == "text")
    out = _PlanOut.model_validate(json.loads(text))
    return EditPlan(keep=picks_to_ranges(out.keep, transcripts),
                    hook_text=out.hook_text.strip(), notes=out.notes.strip())


def picks_to_ranges(picks: list[_Pick], transcripts: list[ClipTranscript],
                    pad: float = 0.12) -> list[KeepRange]:
    """Turn segment picks into time ranges, with a little padding so words aren't clipped."""
    by_clip = {t.clip: t for t in transcripts}
    ranges: list[KeepRange] = []
    for p in picks:
        t = by_clip.get(p.clip)
        if t is None or not t.segments:
            continue
        lo = max(0, min(p.from_seg, p.to_seg))
        hi = min(len(t.segments) - 1, max(p.from_seg, p.to_seg))
        if lo > hi:
            continue
        start = max(0.0, t.segments[lo].start - pad)
        end = min(t.duration, t.segments[hi].end + pad)
        ranges.append(KeepRange(clip=p.clip, start=start, end=end))
    if not ranges:
        raise RuntimeError("edit plan kept nothing")
    return ranges
