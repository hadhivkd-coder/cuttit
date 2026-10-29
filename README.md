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
4. Start the WhatsApp bot: `uvicorn cuttit.bot:app --host 0.0.0.0 --port 8000`, behind HTTPS.
   In the Meta developer console, set the webhook URL to `https://<your-domain>/webhook`, use your
   `WHATSAPP_VERIFY_TOKEN`, and subscribe to `messages`.
5. When a client pays, activate their pack:
   `python -m cuttit.admin add-pack +919876543210 20 4500 --name "Client name"`.
   `python -m cuttit.admin queue` shows what's waiting, failed, or needs a hand edit.

### What the client sees on WhatsApp

1. "Hi" → if they have no pack, the prices and payment link; otherwise a style menu.
2. They pick a style and send clips (as documents for best quality), then tap **Done**.
3. The rough cut arrives with **Looks good** / **Make changes** buttons. Any typed message
   (English or Malayalam) is taken as the change request; "ok", "ശരി", 👍 and so on approve it.
4. The final 1080p video arrives. Real estate, product and event videos go to you for a hand
   edit, and you get a WhatsApp alert.

Note: WhatsApp only allows free-form replies within 24 hours of the client's last message.
Deliveries usually land well inside that; for later ones you'll need an approved message template.

## Tests

```bash
pip install pytest && python -m pytest -q
# Also run the database test against an empty Postgres with db/schema.sql loaded:
CUTTIT_TEST_DATABASE_URL=postgresql://... python -m pytest -q
```
