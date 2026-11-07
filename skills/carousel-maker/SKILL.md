---
name: carousel-maker
description: Write and design a 7-10 slide Instagram/LinkedIn carousel (1080x1350 PNGs) on any topic, rendered from HTML with Playwright. Use when the user wants a carousel, slides post, swipe post, or "post about X".
---

# Carousel Maker

## Ask first
1. Topic and audience. 2. Handle + brand colour + (optional) headshot. 3. Language.

## Steps
1. Write the copy first and show it: slide 1 hook (max 8 words), slides 2-8 one idea each (title max 6 words + body max 30 words), last slide CTA ("Save this", "Comment X").
2. Wait for approval, then build one HTML file per slide (or one page with 1080x1350 sections): big type, generous margins (96 px), slide counter, handle in the footer, a swipe arrow on all but the last.
3. Render each with Playwright: `page.set_viewport_size({'width':1080,'height':1350})`, `page.screenshot(path=f'slide_{i:02}.png')`.
4. Also export a PDF of all slides (LinkedIn document posts).

## Rules
- Max 2 fonts, max 3 colours. Contrast at least 4.5:1.
- Facts get a source line on the slide.
