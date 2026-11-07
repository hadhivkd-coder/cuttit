---
name: website-scroll-reel
description: Build a one-page website for the user (portfolio, shop, menu, event) and record a smooth phone-frame scroll video of it as a reel. Use when the user wants "a website + a video of it", a portfolio showcase reel, or "Claude built my site in X minutes" content.
---

# Website + Scroll Reel

## Ask first
1. What the site is for, name, 3-5 sections, colours, photos/logo. 2. Should it be deployed (they need their own hosting account) or just shown.

## Steps
1. Build a single `index.html` (HTML + CSS, small vanilla JS) that is responsive and looks good at 390 px wide. Real copy, no lorem ipsum.
2. Serve locally (`python -m http.server`), open in Playwright with `viewport 390x844, deviceScaleFactor 3`, and use `record_video_dir` - or take a screenshot every frame while scrolling with an ease-in-out curve (smoother).
3. Scroll plan: hold the hero 1.5 s, glide through each section, pause 0.8 s on the best one, back to top.
4. Composite into a 1080x1920 reel: the recording inside a rounded phone frame (drawn, not a brand device image) over a gradient, a title at the top ("I built this in 20 minutes with Claude").
5. Give the user the HTML file too.

## Rules
- Only use photos/logos the user owns or free-licensed ones (credit them).
