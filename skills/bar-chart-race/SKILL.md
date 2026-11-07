---
name: bar-chart-race
description: Build an animated bar chart race reel (e.g. "most populated cities 1950-2025", "richest people", "most followed accounts") from a CSV or from data Claude collects. Use when the user wants a data/ranking/race video.
---

# Bar Chart Race Reel

## Ask first
1. Topic, and whether they have a CSV. 2. Years/time range. 3. Top N (default 10).

## Steps
1. Get data: the user's CSV, or a public source (World Bank API, Wikipedia tables). Always show the source and 3 sample rows before animating. Never invent numbers.
2. Reshape to wide format (rows = dates, columns = items). Interpolate 15 steps between periods so bars glide.
3. Render with matplotlib at 1080x1920 (figsize 10.8x19.2, dpi 100): horizontal bars, rank-based y with smooth position tweening, value labels with thousands separators, the big period label bottom-right, a title + source line at the top.
4. One fixed colour per item (stable across frames). Add flags/logos only if the user supplies them.
5. Hold the final frame 2 s, then encode with ffmpeg at 30 fps.

## Rules
- Source credit on screen the whole time.
- Hook in the first second: show the title as a question ("Which city wins?").
