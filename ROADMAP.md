# cuttit roadmap

**Goal:** people send a raw video on WhatsApp and get it back edited, fully automated.
**Funnel:** free skills -> followers -> paid skill pack -> WhatsApp editing service.

## Phase 1: Week 1, sell the skills
- [x] 10 skills in `skills/`
- [x] 2-day posting plan in `PLAN.md`
- [x] Landing page in `site/index.html`
- [ ] Make the 10 reels with the skills, and post them over 2 days
- [ ] ManyChat comment-to-DM for each keyword (free skill link)
- [ ] Paid pack product on Gumroad or Razorpay Payment Pages (Rs 499). Put the link in `site/index.html` (`LINKS.pack`)
- [ ] WhatsApp number for the waitlist (`LINKS.waitlist`) and the Instagram handle (`LINKS.instagram`)
- [ ] Deploy `site/` (Vercel, Netlify or GitHub Pages; free)
- [ ] Record the 10 walkthrough videos promised on the pricing card

## Phase 2: Weeks 2-4, the WhatsApp editing service (MVP)

```
User on WhatsApp
   |  sends video + "add captions and music"
   v
WhatsApp Business Cloud API webhook  ->  API server (Node or Python)
   |                                         |
   |                          job queue (Redis / BullMQ, or a DB table)
   |                                         v
   |                                    Worker
   |      1. Download the media from the WhatsApp media URL -> storage (S3 / R2)
   |      2. Claude Haiku: read the request -> an edit plan as JSON
   |         (captions? music? cut silences? voice-over? style?)
   |      3. Run the plan:
   |           - Transcribe (Whisper) -> captions (ffmpeg + ASS, as in skills/word-captions)
   |           - ElevenLabs: voice-over / dubbing when asked
   |           - Higgsfield: generated b-roll / effects when asked
   |           - ffmpeg: cut, resize to 9:16, music, loudness, encode
   |      4. Upload the result -> send it back on WhatsApp
   v
User gets the edited video (plus "reply with changes")
```

### MVP scope (only build this first)
1. One edit type: auto captions + silence cut + 9:16 (no AI generation yet).
2. Then add: music, ElevenLabs voice-over, Higgsfield b-roll.
3. Payments: credits bought through a Razorpay link; the bot checks credits before each job.

### Things to check before building
- **WhatsApp limits:** the Business Cloud API caps media at 16 MB per video. Longer videos need a
  "send a link / upload here" fallback page. You need a Meta Business account and a verified number,
  and verification can take days, so **start it in Week 1**.
- **Higgsfield:** confirm they offer an API for your use and what it costs per generation.
- **Cost per video:** Haiku is cheap; ElevenLabs and Higgsfield cost the most. Price credits at
  2-3x your cost per video.
- **Privacy:** people send personal videos. Delete media after N days and say so in the terms.

## Timeline
| Week | Goal |
|------|------|
| 1 | Skills live, 10 reels posted, start Meta Business verification |
| 2 | WhatsApp webhook + captions-only pipeline working end to end |
| 3 | Music + ElevenLabs + Higgsfield, credits and payments |
| 4 | Beta for the waitlist (first 50 people), then launch |
