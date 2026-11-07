---
name: audiogram-clip
description: Cut the best 30-60 s moments from a podcast/interview/voice note and turn them into reels with a waveform, speaker card and captions. Use for podcast clips, audiograms, or "find the viral parts of this recording".
---

# Audiogram / Podcast Clip

## Ask first
1. The audio or video file. 2. Speaker names + photo (optional). 3. How many clips (default 3).

## Steps
1. Transcribe with faster-whisper (word timestamps).
2. Find candidate moments: a strong opening line, a complete thought, 25-60 s, ends on a punchline or a clear point. List 5 candidates with timestamps and a one-line reason; let the user pick.
3. Cut on word boundaries with 0.15 s padding. Normalise loudness: `ffmpeg -af loudnorm=I=-14:TP=-1.5`.
4. Visual: blurred/darkened background (their photo or brand colour), speaker card at the top, live waveform via `showwaves=s=900x220:mode=cline:colors=white`, word-by-word captions (see word-captions skill) in the middle.
5. Title the hook in the first 2 seconds as on-screen text.

## Rules
- Never cut words to change the meaning of what someone said.
