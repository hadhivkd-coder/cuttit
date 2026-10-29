"""Pure timing logic: tightening cuts around pauses and placing captions on the output timeline."""

from .models import CaptionLine, ClipTranscript, KeepRange

MIN_PIECE = 0.35          # drop slivers shorter than this (seconds)
SILENCE_KEEP = 0.15       # pause left on each side of a removed silence


def remove_silences(ranges: list[KeepRange],
                    silences: dict[int, list[tuple[float, float]]]) -> list[KeepRange]:
    """Split each kept range wherever there is a long pause inside it (jump cuts)."""
    out: list[KeepRange] = []
    for r in ranges:
        pieces = [(r.start, r.end)]
        for s_start, s_end in sorted(silences.get(r.clip, [])):
            cut_from, cut_to = s_start + SILENCE_KEEP, s_end - SILENCE_KEEP
            if cut_to <= cut_from:
                continue
            next_pieces = []
            for a, b in pieces:
                if cut_to <= a or cut_from >= b:
                    next_pieces.append((a, b))
                    continue
                if cut_from > a:
                    next_pieces.append((a, cut_from))
                if cut_to < b:
                    next_pieces.append((cut_to, b))
            pieces = next_pieces
        out.extend(KeepRange(clip=r.clip, start=a, end=b) for a, b in pieces if b - a >= MIN_PIECE)
    return out


def total_length(ranges: list[KeepRange]) -> float:
    return sum(r.end - r.start for r in ranges)


def _chunk(text: str, max_words: int) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)] or [text]


def build_captions(ranges: list[KeepRange], transcripts: list[ClipTranscript],
                   max_words: int = 4) -> list[CaptionLine]:
    """Map transcript phrases that fall inside kept ranges onto the output timeline,
    split into short chunks that read well on a phone."""
    by_clip = {t.clip: t for t in transcripts}
    captions: list[CaptionLine] = []
    offset = 0.0
    for r in ranges:
        t = by_clip.get(r.clip)
        for seg in (t.segments if t else []):
            a, b = max(seg.start, r.start), min(seg.end, r.end)
            if b - a < 0.2:
                continue
            # Only show the part of the phrase that is actually kept, by time share.
            words = seg.text.split()
            span = seg.end - seg.start
            first = int(len(words) * (a - seg.start) / span)
            last = max(first + 1, round(len(words) * (b - seg.start) / span))
            visible = " ".join(words[first:last])
            if not visible:
                continue
            chunks = _chunk(visible, max_words)
            step = (b - a) / len(chunks)
            for i, c in enumerate(chunks):
                start = offset + (a - r.start) + i * step
                captions.append(CaptionLine(start=start, end=start + step, text=c))
        offset += r.end - r.start
    return captions
