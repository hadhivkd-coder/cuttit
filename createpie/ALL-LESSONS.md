# cuttit Skill Pack: everything to paste into CreatePie

Copy each block exactly. Sections are in order: course settings, then lessons 1 to 13.


---

## Course settings

### Course title

~~~~
cuttit Skill Pack: 12 Claude skills that edit your reels
~~~~

### Short description

~~~~
Turn clips, photos and ideas into finished reels with Claude. No After Effects, no timeline.
~~~~

### Long description

~~~~
Edit reels by asking Claude in plain words.

This pack gives you 12 ready-made Claude skills. Each skill is a set of instructions you give Claude once. Then you ask for the reel ("make a map reel of my city", "add captions to this video") and Claude builds it: it writes the code, runs the tools, and exports a 1080x1920 video ready to post.

What's inside:
1. City map reel: Make a 3D map flight along a real route in any city, with a maps-style overlay.
2. Word captions: Captions that pop word by word, in sync with your voice.
3. Kinetic quote: Animated words that hit on the beat.
4. Bar chart race: Animated rankings from real data.
5. Photos to ad: Turn product photos into a 15-second ad.
6. Carousel maker: Designed carousel slides with the copy written for you.
7. Before / after: A smooth before/after reveal.
8. Itinerary reel: A trip plan with an animated map.
9. Podcast clips: The best moments of a recording, turned into reels.
10. Website + scroll: A one-page website plus a phone scroll video of it.
11. Auto reframe: Landscape video turned vertical, following whoever is speaking.
12. Reel covers: Covers and thumbnails that stop the scroll.

What you need: a Claude account. Claude Code (desktop app or VS Code) works best, because it can run the video tools on your computer. Lesson 1 shows you how to set it up.

Includes all 12 skills and every skill released before 6 Dec 2026.
~~~~

### Tags

~~~~
Video editing, AI, Content creation, Instagram Reels, Claude
~~~~


---

## Lesson 1

### Lesson title

~~~~
Start here: setup
~~~~

### Lesson text

~~~~
Start here: how to use these skills

Every lesson has the full skill text. Copy it and add it to Claude in one of these ways:

Option 1 - Claude Code (best: it can render videos on your computer)
1. Install Claude Code (desktop app or VS Code extension) and sign in.
2. Install ffmpeg and Python 3.10+.
3. Create a folder for each skill: ~/.claude/skills/<skill-name>/ (Windows: C:\Users\<you>\.claude\skills\<skill-name>\)
4. In it, create a file named SKILL.md and paste the skill text.
5. Open Claude Code and ask for your reel, for example: "Make a city map reel from Kochi station to Marine Drive."

Option 2 - Claude app (phone or web)
1. Create a Project, paste the skill text into the project instructions, then chat inside that project.
   Or start a new chat with: "Follow these instructions:" and paste the skill text.
2. Note: skills that render video need tools on a computer, so they work best in Claude Code.

Tips
- Give notes one round at a time and be specific ("the caption covers my face").
- Keep the credits the skills add (Google Earth, OpenStreetMap). They are required by those services.

No computer? Send your video to cuttit on WhatsApp and we'll edit it for you.
~~~~


---

## Lesson 2

### Lesson title

~~~~
City map reel
~~~~

### Lesson text

~~~~
Make a 3D map flight along a real route in any city, with a maps-style overlay.

Try asking Claude: "Make a city map reel from [start] to [landmark]."

How to add it: copy the skill below and save it as ~/.claude/skills/city-map-reel/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as city-map-reel/SKILL.md)

~~~~
---
name: city-map-reel
description: Make a 9:16 "navigation app" style map reel of a real route through any city - a 3D Google Earth Studio flight plus an animated maps overlay (route line, turn card, landmark card, drop pin). Use when the user asks for a map reel, route reel, city flyover, or "map edit" of a place.
---

# City Map Reel

You produce a ~14 second vertical reel (1080x1920, 30 fps) that follows a real
route through a city and lands on one landmark. The user never keyframes by hand.

## Ask first (one message, then wait)
1. City, start point and the landmark to end on (e.g. "Kozhikode beach -> Mananchira Square").
2. Mode: driving or walking.
3. Their handle for the end card (optional).

## Step 1 - Real route
- Get directions from OSRM: `https://router.project-osrm.org/route/v1/{driving|foot}/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson&steps=true`
- Geocode names with Nominatim (`nominatim.openstreetmap.org/search?format=json&q=...`, 1 request/second, send a User-Agent).
- Keep the route between 0.8 and 2 km. Longer routes feel rushed in 14 s.
- Pull 3-5 "pop-in" places near the route from Overpass (`tourism`, `amenity=place_of_worship`, `shop=mall`, `historic`).
- SHOW THE USER the route as a list of street names + the pop-ins, and wait for "ok".

## Step 2 - Camera (.esp for Google Earth Studio)
Write `make_camera.py` that outputs `camera.esp` (Earth Studio project JSON):
- Sample the route polyline into one keyframe every 0.5 s.
- 0-60% of time: chase cam, altitude 250-400 m, tilt 60-65 deg, heading = bearing of the road ahead, smoothed over 1 s so turns don't snap.
- At the final turn: tilt down to 35-45 deg over 1.5 s.
- Arrival: hold 0.5 s, then orbit the landmark 120 deg at 500 m, radius 300 m.
- Ease every segment (no linear jumps). Export frames at 1080x1920.
- Also write `track.json`: for every frame, the screen x/y of the blue dot and of each pop-in. The overlay uses this so it stays glued to the flight.

Tell the user: open earth.google.com/studio in Chrome, File > Import > camera.esp, Render, drop `flight.mp4` back here.

## Step 3 - Overlay (maps UI layer)
Build with Python (Pillow) frames + ffmpeg, or an HTML page captured with Playwright:
- Top: turn card (arrow + street name + distance counting down).
- Bottom: ETA bar, speed sign.
- Pop-in pins: scale 0 -> 1.1 -> 1 over 8 frames when their point enters the frame.
- Landmark card slides up from the bottom at arrival; red pin drops with 2 expanding rings.
- "Arrived" banner, then end card with the handle.
- Use your own design: rounded white cards, one accent colour, Inter/Roboto. Do NOT copy any real app's logo or icon.

Composite: `ffmpeg -i flight.mp4 -framerate 30 -i overlay/%05d.png -filter_complex overlay -c:v libx264 -pix_fmt yuv420p -crf 18 reel.mp4`

## Step 4 - Notes
Take notes one round at a time ("the card covers the route", "the pin is late") and re-render only the overlay when possible.

## Rules
- Google Earth requires visible attribution: keep the small "Google Earth" credit in the frame.
- OSM data: add "Map data (c) OpenStreetMap contributors" in the caption or end card.
- Never guess a route - always use real OSRM output.
~~~~


---

## Lesson 3

### Lesson title

~~~~
Word captions
~~~~

### Lesson text

~~~~
Captions that pop word by word, in sync with your voice.

Try asking Claude: "Add word-by-word captions to this video."

How to add it: copy the skill below and save it as ~/.claude/skills/word-captions/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as word-captions/SKILL.md)

~~~~
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
~~~~


---

## Lesson 4

### Lesson title

~~~~
Kinetic quote
~~~~

### Lesson text

~~~~
Animated words that hit on the beat.

Try asking Claude: "Make a kinetic quote reel from this text and song."

How to add it: copy the skill below and save it as ~/.claude/skills/kinetic-quote/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as kinetic-quote/SKILL.md)

~~~~
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
~~~~


---

## Lesson 5

### Lesson title

~~~~
Bar chart race
~~~~

### Lesson text

~~~~
Animated rankings from real data.

Try asking Claude: "Make a bar chart race of the biggest cities, 1950 to 2025."

How to add it: copy the skill below and save it as ~/.claude/skills/bar-chart-race/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as bar-chart-race/SKILL.md)

~~~~
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
~~~~


---

## Lesson 6

### Lesson title

~~~~
Photos to ad
~~~~

### Lesson text

~~~~
Turn product photos into a 15-second ad.

Try asking Claude: "Make an ad reel from these 5 photos. Price 499, DM to order."

How to add it: copy the skill below and save it as ~/.claude/skills/photo-to-ad/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as photo-to-ad/SKILL.md)

~~~~
---
name: photo-to-ad
description: Turn 3-8 product photos into a polished 15 s product ad reel with motion, price tag, features and a call to action. Use for small businesses, shops, restaurants, real estate listings, or "make an ad from these photos".
---

# Photos to Ad Reel

## Ask first
1. The photos. 2. Product name, price, 3 key features, CTA ("DM to order", phone, website). 3. Brand colour.

## Steps
1. Check each photo: resolution, orientation. Remove backgrounds with `rembg` for cutout shots if the photo is a plain product shot.
2. Structure (15 s): hook 0-2 s (best photo + bold claim), 3 feature beats 2-11 s (one photo + one feature each), price + CTA 11-15 s.
3. Motion per shot: Ken Burns (slow 6% zoom + drift) or parallax (cutout over blurred copy of the background). Transitions: 6-frame zoom-through or wipe in the brand colour.
4. Text: feature as a short chip (max 4 words), price in a big sticker with a 4-frame bounce.
5. Add music the user provides, or leave silent and say so. Duck nothing - there is no voice.
6. Export 1080x1920 and also 1080x1080 for the feed.

## Rules
- Never change what the product looks like (no AI-generated product details).
- Price and phone number are read back to the user for confirmation before final render.
~~~~


---

## Lesson 7

### Lesson title

~~~~
Carousel maker
~~~~

### Lesson text

~~~~
Designed carousel slides with the copy written for you.

Try asking Claude: "Make a 7-slide carousel about [topic]."

How to add it: copy the skill below and save it as ~/.claude/skills/carousel-maker/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as carousel-maker/SKILL.md)

~~~~
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
~~~~


---

## Lesson 8

### Lesson title

~~~~
Before / after
~~~~

### Lesson text

~~~~
A smooth before/after reveal.

Try asking Claude: "Make a before/after slider reel from these two photos."

How to add it: copy the skill below and save it as ~/.claude/skills/before-after-reel/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as before-after-reel/SKILL.md)

~~~~
---
name: before-after-reel
description: Make a before/after transformation reel (slider wipe, split screen, or flash cut) from two photos or two clips - renovations, fitness, design, haircuts, photo edits, cleaning. Use when the user has a "before" and "after".
---

# Before / After Reel

## Ask first
1. Before and after files. 2. Style: slider wipe (default), split screen, or beat-synced flash cut. 3. Labels/caption text.

## Steps
1. Align the two images: match size, then align with OpenCV ECC (`cv2.findTransformECC`, MOTION_AFFINE) so the wipe doesn't jump. Crop both to 9:16 on the same box.
2. Slider wipe: 1 s hold on "BEFORE", 2.5 s eased wipe with a white 6 px divider and a round handle, 1.5 s hold on "AFTER", then 1 s wipe back halfway (makes people rewatch).
3. Split screen: stack top/bottom with labels; for clips, sync them by length.
4. Flash cut: with music, alternate before/after on each beat for the last 3 s (librosa beat detection).
5. Encode 1080x1920, 30 fps.

## Rules
- Same crop and colour grade on both sides unless the edit itself is the point - say so on screen if the "after" is retouched.
~~~~


---

## Lesson 9

### Lesson title

~~~~
Itinerary reel
~~~~

### Lesson text

~~~~
A trip plan with an animated map.

Try asking Claude: "Make a 3 days in [city] reel."

How to add it: copy the skill below and save it as ~/.claude/skills/itinerary-reel/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as itinerary-reel/SKILL.md)

~~~~
---
name: itinerary-reel
description: Turn a trip plan into a "3 days in <city>" reel - day cards, a map with pins hopping stop to stop, travel times, and the user's own clips. Use for travel itinerary reels, "things to do in X", or food trails.
---

# Itinerary Reel

## Ask first
1. City and number of days. 2. Their own clips/photos per stop (optional). 3. Budget level / interests.

## Steps
1. Draft the itinerary: 3-4 stops per day, geographically sensible order. Geocode each stop with Nominatim, compute walking/driving time between stops with OSRM. Show the plan as a table and wait for approval.
2. Map: draw a stylised base map from OpenStreetMap data (Overpass roads + water + parks) with Pillow or matplotlib - do NOT download map tiles in bulk. Animate a dashed line drawing between pins, pin pops on arrival.
3. Per stop: 1.5 s of the user's clip (or a styled title card if none) with name + "12 min walk" chip.
4. Day cards between days ("DAY 2"), 0.8 s each. End card: "Save this for your trip".
5. Export 1080x1920. Put the full written itinerary in the caption text file `caption.txt`.

## Rules
- Credit "(c) OpenStreetMap contributors".
- Opening hours and prices: tell the user to verify; don't state them as fact.
~~~~


---

## Lesson 10

### Lesson title

~~~~
Podcast clips
~~~~

### Lesson text

~~~~
The best moments of a recording, turned into reels.

Try asking Claude: "Find the 3 best clips in this podcast."

How to add it: copy the skill below and save it as ~/.claude/skills/audiogram-clip/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as audiogram-clip/SKILL.md)

~~~~
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
~~~~


---

## Lesson 11

### Lesson title

~~~~
Website + scroll
~~~~

### Lesson text

~~~~
A one-page website plus a phone scroll video of it.

Try asking Claude: "Build a one-page site for my cafe and make a scroll reel."

How to add it: copy the skill below and save it as ~/.claude/skills/website-scroll-reel/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as website-scroll-reel/SKILL.md)

~~~~
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
~~~~


---

## Lesson 12

### Lesson title

~~~~
Auto reframe
~~~~

### Lesson text

~~~~
Landscape video turned vertical, following whoever is speaking.

Try asking Claude: "Make this YouTube video vertical."

How to add it: copy the skill below and save it as ~/.claude/skills/auto-reframe/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as auto-reframe/SKILL.md)

~~~~
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
~~~~


---

## Lesson 13

### Lesson title

~~~~
Reel covers
~~~~

### Lesson text

~~~~
Covers and thumbnails that stop the scroll.

Try asking Claude: "Make a cover for this reel."

How to add it: copy the skill below and save it as ~/.claude/skills/reel-cover/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1.
~~~~

### Skill text (save as reel-cover/SKILL.md)

~~~~
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
~~~~
