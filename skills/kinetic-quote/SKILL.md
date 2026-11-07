---
name: kinetic-quote
description: Turn a quote, a short script or a voice-over into a kinetic typography reel (words slam, slide and scale in to the beat). Use when the user wants a motivational/quote reel, text animation reel, or "typing" reel without After Effects.
---

# Kinetic Quote Reel

## Ask first
1. The text (or a voice-over file). 2. Music file (optional). 3. Mood: calm, hype, or luxury.

## Steps
1. If there is a voice-over, get word timings with faster-whisper. If there is only music, detect beats with `librosa.beat.beat_track` and put one word-group per beat.
2. Mark 1-2 "hero" words per line (the emotional words) - they get 2x size and the accent colour.
3. Render frames with Pillow at 1080x1920, 30 fps. Per word-group pick ONE entrance: slam (scale 1.6 -> 1 with 3-frame overshoot), slide-up with blur, or typewriter. Never mix more than 3 entrances in one reel.
4. Camera: slow 2% zoom over each line, quick 4-frame whip between lines.
5. Palettes: calm = cream/charcoal, hype = black/neon lime, luxury = black/gold. Fonts: Anton, Playfair Display, or Inter Tight (all OFL).
6. `ffmpeg -framerate 30 -i f/%05d.png -i audio.mp3 -shortest -c:v libx264 -pix_fmt yuv420p reel.mp4`

## Rules
- Text stays inside the 1080x1420 safe area (top 250 px and bottom 250 px are covered by the app UI).
- Every word on screen for at least 6 frames.
