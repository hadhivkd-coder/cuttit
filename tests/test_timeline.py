from cuttit.models import ClipTranscript, KeepRange, Segment
from cuttit.planner import _Pick, picks_to_ranges
from cuttit.timeline import build_captions, remove_silences, total_length


def test_remove_silences_splits_long_pause():
    ranges = [KeepRange(clip=0, start=0.0, end=10.0)]
    out = remove_silences(ranges, {0: [(4.0, 6.0)]})
    assert [(r.start, r.end) for r in out] == [(0.0, 4.15), (5.85, 10.0)]


def test_remove_silences_ignores_other_clips_and_drops_slivers():
    ranges = [KeepRange(clip=0, start=0.0, end=3.0), KeepRange(clip=1, start=0.0, end=1.0)]
    out = remove_silences(ranges, {1: [(0.2, 1.0)]})
    assert [(r.clip, r.start, r.end) for r in out] == [(0, 0.0, 3.0), (1, 0.0, 0.35)]
    assert round(total_length(out), 2) == 3.35


def test_picks_to_ranges_pads_and_clamps():
    t = ClipTranscript(clip=0, duration=5.0, segments=[
        Segment(start=0.05, end=1.0, text="a"), Segment(start=1.2, end=2.0, text="b"),
        Segment(start=3.0, end=4.95, text="c")])
    out = picks_to_ranges([_Pick(clip=0, from_seg=2, to_seg=9), _Pick(clip=0, from_seg=0, to_seg=1),
                           _Pick(clip=7, from_seg=0, to_seg=0)], [t])
    assert [(r.start, round(r.end, 2)) for r in out] == [(2.88, 5.0), (0.0, 2.12)]


def test_captions_follow_output_timeline():
    t = ClipTranscript(clip=0, duration=20.0, segments=[
        Segment(start=10.0, end=12.0, text="one two three four five six seven eight")])
    ranges = [KeepRange(clip=0, start=10.0, end=12.0)]
    caps = build_captions(ranges, [t], max_words=4)
    assert [c.text for c in caps] == ["one two three four", "five six seven eight"]
    assert caps[0].start == 0.0 and caps[1].end == 2.0
