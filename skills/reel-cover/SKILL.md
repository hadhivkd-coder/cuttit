---
name: reel-cover
description: Design scroll-stopping reel covers and YouTube thumbnails (1080x1920 cover + 1080x1440 grid crop + 1280x720 thumbnail) from a frame of the user's video or a photo. Use when the user wants a cover, thumbnail, or a consistent Instagram grid.
---

# Reel Cover & Thumbnail

## Ask first
1. The video or photo. 2. The reel's topic in a few words. 3. Brand colour + font (or "pick for me").

## Steps
1. If it's a video, pull 30 candidate frames (`ffmpeg -vf "select='gt(scene,0.25)'" -vsync vfr`), score them for sharpness (Laplacian variance), open eyes and a visible face, and show the best 4. The user picks one.
2. Write 5 cover titles (max 5 words, a curiosity gap or a number: "I edited this with 0 apps"). The user picks one.
3. Cut out the person with `rembg`, place them over a clean background (blurred original, or the brand colour), and add a 6 px white outline for depth.
4. Title: 2 lines max, heavy font, one word in the accent colour. Keep text inside the middle 1080x1440 so the Instagram grid crop doesn't cut it.
5. Export: `cover_1080x1920.png`, `grid_1080x1440.png`, `thumb_1280x720.png` (re-laid out for landscape, not just cropped).

## Rules
- Text must be readable at 200 px wide. Check by downscaling the image and looking at it.
- Don't add things that aren't in the video (no fake reactions or objects).
