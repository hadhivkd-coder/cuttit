# Cuttit

AI video editing over WhatsApp. Clients send raw clips; Cuttit sends back an edited 9:16 reel with
Malayalam/English captions, first as a rough cut and then as the final.

## How it works

```
WhatsApp bot ──> clips saved to R2 ──> job added to the queue (Postgres)
                                             │
                     edit workers (run 1 or many) pick up jobs
                                             │
          Gemini transcript ──> Claude edit plan ──> ffmpeg cut + captions
                                             │
                     video uploaded to R2 ──> link sent back on WhatsApp
```

- **Speech-to-text:** Gemini (`cuttit/transcribe.py`), timed phrases per clip.
- **Edit decisions:** Claude Opus 5.5 (`cuttit/planner.py`) picks which phrases to keep and in what
  order, following the style's rules in `cuttit/styles.py`.
- **Render:** ffmpeg (`cuttit/render.py`) cuts each piece, removes long pauses
  (`cuttit/timeline.py`), fills a vertical frame, burns in captions and a hook title, and
  normalises loudness. Rough cuts are 720p with a "ROUGH CUT" mark; finals are 1080p.
- **Queue:** the `jobs` table (`cuttit/jobs.py`). Workers claim jobs with
  `FOR UPDATE SKIP LOCKED`, so you scale by starting more workers. Failed jobs retry 3 times,
  then the video is marked failed and the client's credit is refunded.

Styles automated so far: `talking_head`, `podcast`. `real_estate`, `product` and `event` are still
edited by hand.

## Try it on your own clips (no database needed)

Needs Python 3.11+, ffmpeg, and a Malayalam font (`sudo apt install fonts-noto-core`, or install
Noto Sans Malayalam on Mac/Windows).

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in ANTHROPIC_API_KEY and GEMINI_API_KEY
set -a; source .env; set +a

python -m cuttit.cli clip1.mp4 clip2.mp4 --style talking_head --out rough.mp4
# then, like a client asking for changes:
python -m cuttit.cli clip1.mp4 clip2.mp4 --final --feedback "start with the price offer" --out final.mp4
```

Transcripts and the last plan are cached in `.cuttit-work/`, so a revision only costs one Claude call.

## Run the service

1. Create a Supabase project and run `psql "$DATABASE_URL" -f db/schema.sql`.
2. Create an R2 bucket and an API token; fill in the `R2_*` values.
3. Start a worker on any server with ffmpeg: `python -m cuttit.worker`. Start more when the queue
   gets long.

The WhatsApp bot that creates videos and enqueues jobs is the next piece.

## Tests

```bash
pip install pytest && python -m pytest -q
```
