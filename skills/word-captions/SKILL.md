---
name: word-captions
description: Add viral-style word-by-word animated captions to a talking-head video (the highlighted-word look), fully local with Whisper and ffmpeg. Use when the user wants captions, subtitles, or "those TikTok captions" on a reel.
---

# Word-by-Word Captions

## Ask first
1. The video file. 2. Language. 3. Style: bold white + yellow highlight (default), or their brand colour.

## Steps
1. `pip install faster-whisper` and transcribe with `word_timestamps=True` (model `small`; `medium` for Malayalam/Hindi/Arabic).
2. Show the transcript, let the user fix spelling of names, then re-align words to the fixed text.
3. Group words into lines of 2-4 words, max 18 characters, break on pauses > 0.35 s.
4. Write an ASS subtitle file: font Montserrat ExtraBold 78 px, white, 6 px black outline, centred at 62% height.
   The current word is coloured (`{\c&H00D7FF&}`) and pops (`{\t(0,80,\fscx112\fscy112)\t(80,160,\fscx100\fscy100)}`).
5. Burn in: `ffmpeg -i in.mp4 -vf "ass=captions.ass" -c:a copy -crf 18 out.mp4`
6. Also export `captions.srt` for platforms that take a separate file.

## Rules
- Never cover the face: if a face is detected in the lower third (use mediapipe), move captions to 25% height.
- Keep emoji out unless the user asks.
