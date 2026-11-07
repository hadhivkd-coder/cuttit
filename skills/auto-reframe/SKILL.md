---
name: auto-reframe
description: Turn a landscape (16:9) video - podcast, YouTube video, screen recording, event footage - into a 9:16 reel that follows the speaker's face with smooth camera moves. Use when the user wants to "make this vertical", reframe, or cut YouTube videos into reels.
---

# Auto Reframe (16:9 -> 9:16)

## Ask first
1. The video. 2. Who to follow: the person speaking (default), one fixed person, or "keep both" (split screen when two people talk).

## Steps
1. Detect faces every 3rd frame with mediapipe face detection; track them across frames (IoU matching) so each person keeps one ID.
2. Who is speaking: if there is more than one face, transcribe with faster-whisper and use mouth-movement energy (lip landmarks) in each segment to pick the active speaker.
3. Crop path: a 9:16 window at full height. The target x = centre of the active face. Smooth it with a critically damped spring (no jitter) and only move when the face leaves the middle 40% of the window. On speaker change, cut (do not pan) if the jump is wider than 30% of the frame.
4. Two speakers in one shot for > 4 s with lots of back-and-forth: stack them top/bottom (split screen).
5. Render with ffmpeg using a `sendcmd` crop script, or crop per frame in Python and pipe to ffmpeg. Keep the original audio.
6. Offer word-by-word captions (word-captions skill) on top.

## Rules
- Never crop off a face that is talking.
- If no face is found (b-roll, screen), centre crop and tell the user which parts had no face.
