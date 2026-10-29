"""Edit clips on your own machine, no database or storage needed. Good for testing styles.

    python -m cuttit.cli clip1.mp4 clip2.mp4 --style talking_head --out reel.mp4
    python -m cuttit.cli clip1.mp4 --out final.mp4 --final --feedback "remove the part about prices"
"""

import argparse
import json
from pathlib import Path

from .models import ClipTranscript, EditPlan
from .pipeline import edit_video


def main() -> None:
    ap = argparse.ArgumentParser(description="Cuttit: edit raw clips into a reel")
    ap.add_argument("clips", nargs="+", type=Path)
    ap.add_argument("--style", default="talking_head")
    ap.add_argument("--out", type=Path, default=Path("reel.mp4"))
    ap.add_argument("--final", action="store_true", help="1080p final instead of a 720p rough cut")
    ap.add_argument("--feedback", help="client's change request (re-plans from the saved plan)")
    ap.add_argument("--work", type=Path, default=Path(".cuttit-work"))
    args = ap.parse_args()

    # Reuse transcripts and the last plan between runs, so a revision costs one Claude call.
    state_file = args.work / "state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    same_clips = state.get("clips") == [str(c.resolve()) for c in args.clips]
    transcripts = ([ClipTranscript.model_validate(t) for t in state["transcripts"]]
                   if same_clips else None)
    previous = EditPlan.model_validate(state["plan"]) if same_clips and args.final else None

    result = edit_video(args.clips, args.style, args.out, args.work,
                        kind="final" if args.final else "rough",
                        transcripts=transcripts, previous=previous, feedback=args.feedback)

    args.work.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({
        "clips": [str(c.resolve()) for c in args.clips],
        "transcripts": [t.model_dump() for t in result.transcripts],
        "plan": result.plan.model_dump(),
    }, ensure_ascii=False, indent=1))
    print(f"Saved {result.video} ({result.seconds:.0f}s)")
    print(f"Editor notes: {result.plan.notes}")


if __name__ == "__main__":
    main()
