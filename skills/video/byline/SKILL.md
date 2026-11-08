---
name: byline
description: Edit a talking-head video in a premium "editorial captions" style - two-font word captions at chest level (clean sans + big italic serif power words), black/white full-screen word cards, glowing pill chips for lists, punch-in zoom-blur cuts, black-and-white punches, synced whoosh/pop SFX and a big "comment WORD" ending. Use when the user wants a high-end, fast-paced talking-head reel, "editorial" or "serif captions", or asks to edit a video "in this style". Also designs new on-screen elements that match the style.
---

# Byline (style template)

This skill is a **style**, not a fixed template. `style.json` (same folder) holds the exact numbers: fonts,
sizes, colours, timings, SFX levels. Read it first and use those values. The rules below say when to use each element,
and section 6 says how to invent new elements that still match.

## 1. Ask first

### Step 0: one question before anything else
Greet the user in one line and ask only this, then wait:

> "How would you like to work?
> **A) Customise:** I'll ask you a few quick questions (fonts, colours, music, ending...) before I edit.
> **B) Leave it to me:** I'll make every choice myself in this style, and you just send the video."

- **B (leave it to me):** ask only for the video (and for a CTA word only if the speaker says "comment" in it).
  Then use every default below, decide the power words, cards, chips and SFX yourself, and go straight to the
  edit plan in section 2. Mention once that they can change anything afterwards in the notes round.
- **A (customise):** send the questions below.

### Step 1: the questions (only for A)
Ask them **in one numbered message**. Show the default for each, so the user can answer only what they care
about, or reply "defaults" to accept everything.

1. **Video:** Please share your talking-head video (best 15-90 s).
2. **Fonts:** Do you have specific fonts (e.g. your brand fonts)?
   Default: the reference style, a heavy sans (Poppins Bold) + a high-contrast italic serif (Playfair Display Italic).
3. **Colours:** Do you want your brand colours for the chips and highlights?
   Default: blue for good/right, red for bad/wrong, with black and white cards.
4. **Music:** Do you want background music?
   a) Your own track (send it) b) no music c) I suggest a calm 85-95 BPM track you can download free
   (e.g. from the YouTube Audio Library) and you send it. Default: no music.
5. **Sound effects:** Default: whooshes, pops and hits that I generate for you (no licence needed).
   Or: send your own SFX pack, or "no SFX".
6. **Ending:** Should it end with "comment [WORD]"? Which word? Default: no CTA.
7. **Energy:** How intense should the edit be?
   a) Calm (fewer cards and punch-ins) b) Standard (the reference) c) Hype (more cards, faster cuts). Default: Standard.
8. **B-roll:** Any clips or screenshots of your own to include (proof of work, product, screen recordings)?
   Default: none, typography only.
9. **Language** of the captions, and any names or words I must spell exactly? Default: the spoken language.
10. **Handle/watermark** at the end (e.g. @yourname)? Default: none.

Then repeat back their choices as a short summary ("Fonts: yours - Poppins + Lora; Music: none; Energy: Hype...")
and wait for "ok". Everything they chose **overrides** the matching value in `style.json`; everything else uses
the style's defaults.

**Applying the answers**
- Their fonts: their sans replaces Inter Tight, their serif (or display font) replaces Instrument Serif.
  Keep the same sizes, tracking and glow. If they give only one font, use it for captions and keep the serif for power words.
- Their colours: the main brand colour replaces blue; keep red for "wrong" unless their brand colour is red
  (then use their second colour or black for "wrong").
- Energy: Calm = cards every 15-25 s, punch-ins every 2.5-3.5 s, no B&W punch.
  Hype = cards every 5-10 s, punch-ins every 0.8-1.5 s, chips on every list.

## 2. Prepare
1. Fonts: download Poppins Bold and Playfair Display Italic (Google Fonts, free licence) into `fonts/`.
2. Transcribe with faster-whisper, `word_timestamps=True` (model `small`; `medium` for non-English).
   Show the transcript, let the user fix names and spelling.
3. Remove dead air: cut every gap longer than 0.25 s at -35 dB, keeping 0.06 s padding (jump cuts are part of the look).
   Re-time the words to the new edit.
4. Face track (mediapipe) every 3rd frame. Store the chin y per frame for caption placement.
5. **Edit plan first.** Write `plan.json`: every caption chunk, which word is the power word, where word cards,
   chips, B&W punches, b-roll and punch-ins go, and each SFX. Show the plan to the user as a readable list and wait for "ok".

## 3. Style rules (how to plan)
**Captions (typography + "pop-in")**
- Fonts: heavy sans (Poppins Bold) for standard text; high-contrast serif italic (Playfair Display Italic) **only** for the power word.
- Crisp white text with a tight, high-opacity, low-distance black drop shadow. No heavy shadows, glows, outlines, underlines or ghost lines.
- Centred horizontally at chest/neck level, never over the face.
- Rapid 1-2 word chunks. Never a full sentence.
- Entry: the whole chunk pops from 80% to 100% in 4 frames with a slight spring overshoot.
- Exit: hard cut on the exact frame the next chunk starts. No fades, slides or blur.
- **Power words:** the most important conceptual words of the script (e.g. "secret", "one", "SESSION") switch to the serif italic,
  25% larger than the sans. Paired with standard text (e.g. "SESSION" over "with me"), the serif word is massive and dominant.

**Full-screen breaker cards**
- For high-impact single words: replace the video with solid black (white sans) or solid white (black serif italic),
  one word dead centre. Consecutive cards alternate black/white. Voice keeps playing.
- The word sits dead centre with a subtle, continuous slow zoom (100% to 108%).
- Every card hits **exactly** on its first frame with a heavy, bass-driven whoosh.

**Concept graphics**
- Minimalist graphics explain concepts: one graphic per idea, below the caption (about 71% height), never over the face.
  Pick from the library in section 5 (bars, lock, heart, ring, calendar, arrow, grid, icon chips) by meaning, e.g. "grid":
  a clean white 3x3 grid, then a red diagonal line over the squares. White, black, blue and red only.
- Each graphic gets a sound: appear = pop, lock/check/click moments = click, ring = shine, wrong/strike = wrong.

**UI elements**
- App/feature chips ("Reels") and lists: when the speaker names apps/features or lists items, no normal caption - a flat blue rounded pill with white text per item, stacked near
  the speaker, scaling 0% to 100% with a heavy spring overshoot, each synced to a sharp click/pop.
- Quote/comparison boxes (e.g. "$20 vs $2,000"): clean rounded rectangles (`"shape": "box"`), red for the weak side and blue for the
  strong side, scaling up from the centre with an overshoot, synced to a paper swoosh or pop.

**Camera**
- Default: slow, smooth, eased zooms (100% to ~107%) that change direction every 2-3 s. Never snap.
- Transitions between scenes (cards, B&W, b-roll) use a soft white light flash/bloom with a dreamy whoosh. No glitches.
- B-roll is motion design, not a hard swap: mostly floating 3D cards over the blurred speaker, sometimes full-screen for variety.
- Nothing stays unchanged longer than 3 s (a punch-in, card, chip or b-roll counts as a change).

**Black-and-white punch**
- When the speaker names a mistake, something bad or "what not to do", go black-and-white with a 4% zoom
  for that phrase only. Add a short **glitch** SFX. At most once every 20 s.

**B-roll**
- Only the user's own footage: proof of work, the product, a screen recording of the thing being described.
- Enter with a 6-frame zoom-blur and a **whoosh**. Max 2.5 s each. Two related clips can stack as a top/bottom split.
- A name card (blue pill + small sans subtitle) only for people in the user's own footage, with their permission.

**Ending (CTA)**
- At the final call to action, clear the captions: the primary trigger word (e.g. COMMENT) huge and centred, and the
  secondary instruction text cycling underneath it in time with the speech (`cta.cycle`).

## 4. Sound
- Voice: normalise to -14 LUFS (`loudnorm=I=-14:TP=-1.5`).
- **SFX are generated, not downloaded** (so the user owns them). Write `sfx.py` with numpy and export WAVs:
  - `deep_whoosh`: 0.5 s pink noise, band-pass sweeping 300 Hz to 3 kHz and back, plus a 60 Hz sine swell, fade in/out.
  - `whoosh`: 0.4 s, same sweep, no sub.
  - `pop`: 60 ms sine dropping 1200 to 500 Hz with a fast decay.
  - `click`: 8 ms filtered noise burst.
  - `glitch`: 0.3 s of 3-4 chopped, bit-crushed noise bursts.
  - `low_hit`: 0.6 s 55 Hz sine with fast attack and exponential decay.
- Levels from style.json `sfx_levels_db`. SFX start 2 frames **before** the visual so they feel synced.
- Literal SFX (cash register for "sell", typing for "write") are allowed only if the user supplies them; max one per 15 s.
- Music (optional, user-supplied, 85-95 BPM, calm): 26 dB under the voice, ducked with
  `sidechaincompress=threshold=0.02:ratio=8:attack=5:release=250`.

## 5. Render (tested scripts included)
Use the scripts in `scripts/` instead of writing a renderer from scratch:
- Setup once: `pip install faster-whisper numpy pillow "opencv-python-headless<5"` and ffmpeg on PATH.
  Put the two fonts in `fonts/` next to the plan (`Poppins-Bold.ttf`, `PlayfairDisplay-Italic.ttf`).
- Transcribe: decode audio first (`ffmpeg -i input.mp4 -ac 1 -ar 16000 -f s16le a.raw`) and pass the numpy array to
  faster-whisper; this avoids a PyAV version clash. If the model download fails on a "xet" error, set `HF_HUB_DISABLE_XET=1`.
- Write `plan.json` in the format of `scripts/plan.example.json` (all times in the source video's seconds).
- Render: `python scripts/render.py plan.json` - cuts dead air, punch-ins with zoom-blur + flash, B&W segments,
  captions with ghost lines, word cards, chips, CTA, generated SFX (`scripts/sfx.py`), loudness-normalised voice.
- If the source has a required watermark (e.g. AI video generators), set `zoom_anchor` to the watermark's position
  so punch-ins never crop it.
If the user wants something the scripts don't do (b-roll, music, new elements from section 6), extend `render.py`.


### v3 options in plan.json (see scripts/plan.example.json)
- `speed`: e.g. 0.9 slows the whole video and voice slightly for a calmer, premium pace.
- `camera_mode: "smooth"` (default): only slow, eased zooms between `scales` keyframes. No snap punch-ins.
  `"punch"` brings back fast punch-ins with bumps and shake for high-energy edits.
- Radial-blur transitions are added automatically at every card, B&W and cutaway boundary (`camera.radial_strength`).
- `fps: 60` (recommended): footage is motion-interpolated (ffmpeg `minterpolate` mci) to real in-between frames, so slow motion,
  zooms and every animation are silky. Animation durations are defined in time, so they look the same at any fps.
- `transition: "flash"` (default): a soft white light bloom that rises over ~0.14 s and fades over ~0.4 s at every scene change
  (b-roll, cards, B&W), with a dreamy whoosh (`flash` SFX role). `"radial"` gives the radial-blur zoom instead.
- Cutaway `mode: "card"`: the b-roll becomes a rounded 3D card (`card_w`, `card_y`) that flies in (`enter`: right / left / bottom /
  scale) with an expo ease and perspective tilt, floats gently, and eases out, over a blurred, darkened copy of the speaker with a
  soft shadow. Graphics placed at ~0.71 height overlap the card's lower edge for depth. `mode: "full"` keeps full-screen b-roll.
- Graphics: eased-back entrance (~0.5 s), gentle float, soft exit, a light shimmer sweep, and a frosted glass panel behind
  (`panel: false` to turn it off). Chips get the shimmer and fade out at the end of the list.
- **Depth effects (need the person matte):** set `matte_model` to MODNet (`huggingface.co/Xenova/modnet`, file
  `onnx/model.onnx`, Apache-2.0; `pip install onnxruntime`). The speaker is cut out on every frame (~0.1 s/frame, temporally smoothed).
  - `behind`: giant text placed **behind the speaker** (`lines`, `font`, `px`, `x`, `y`, `grow`). Letters rise in one by one;
    it scales with the camera. Keep it above the shoulders and short (one word) so the head doesn't hide it; use `x` to let
    a big glyph peek out beside a shoulder (e.g. a giant serif "1").
  - `lines` `orbit`: a glowing line that draws itself around the speaker at neck/shoulder level (`dy`), passing **behind** the
    neck and in front of the chest, then retracts. Never at face height.
- `lines` `swoosh`: a cubic-bezier light stroke (`pts`, 4 points as width/height fractions) that draws on and chases off
  (trim-path animation). Use it to lead a b-roll card in, or to connect two elements.
- Breaker cards are kinetic: letters rise one by one with blur, tracking widens, slow eased zoom.
- Cutaway `reveal: "iris"`: full-screen b-roll opens as an expanding circle with a white rim.
- Camera: plan `scales` as intentional moves - dolly in on the hook, pull back to reveal the text behind, push in on the key line.
- `interp: "fast"` renders a quick 30 fps preview for checking placement; final renders use `fps: 60` with `interp: "mci"`.
- `cutaways`: slow-motion b-roll, from the user's b-roll file (`file`) or a crop of the source (`crop`), with `slowmo` and a slow zoom.
- `graphics` (motion graphics in the style DNA; every shape springs in from the centre with a bounce, drawn at 2x for smooth edges):
  - `bars`: bar chart growing bar by bar, `highlight` bar in blue ("top tier", "growth", "results").
  - `lock`: padlock that clicks shut at `close_t` ("secret", "private", "exclusive").
  - `heart`: outline heart with a number, e.g. "0" ("nobody cares", "likes", "engagement").
  - `ring` (+ `burst: true`): blue ring that draws around the caption word, with burst lines ("one", "only", key numbers).
  - `calendar`: calendar card whose date gets a blue check at `check_t` ("book", "session", "schedule", "deadline").
  - `arrow`: curved arrow that draws itself ("this", "look", pointing at a chip or b-roll detail).
  - chip `icon`: "play", "pin", "check" or "heart" inside a chip (e.g. Reels = play, Pinned posts = pin).
  - `grid` (`style: clean`): white 3x3 grid with a red diagonal line at `strike_t`.
  - `counter`: a number counting up with a serif label, optional red strike-through (`strike_t`).
  - `grid`: tiles popping in one by one, optional red X (`strike_t`).
  - `button`: a blue pill button with a cursor that glides in and clicks (`click_t`).
- `sfx_pack` + `sfx_map`: use the user's own SFX files per role: `{role: [file, max_seconds (negative = take the tail, for risers), level_db]}`.
  Roles: deep_whoosh, whoosh, riser, pop, click, glitch, impact, shine, count, wrong, highlight. Without a pack, `sfx.py` generates them.
  Whooshes on transitions, risers before word cards and a highlighter sound on power-word underlines are added automatically.
  Never commit a user's SFX pack to a public repo.
- `music`: "generated" (original bed from sfx.py), a file path, or null.

### Manual details (for extending the scripts)
- Draw overlays (captions, cards, chips, CTA) as transparent PNG frames with Pillow, or as HTML/CSS captured with Playwright.
- Composite with ffmpeg in one pass: scaled/cut base video, zoom-blur transitions, B&W segments
  (`hue=s=0`), overlays, mixed audio.
- Export 1080x1920, 30 fps, H.264 `-crf 18 -pix_fmt yuv420p`, AAC 192k.
- Then check: watch 3 random 3-second spots; no caption over the mouth; no gap longer than 3 s without a change;
  SFX not louder than the voice.

## 6. Creating NEW elements in this style
When the video needs something this style doesn't list (a price tag, a stat counter, a checklist, a progress bar,
a map pin, a before/after label...), design it from the same DNA so it looks native:
- **Type:** only the two fonts. Labels/numbers in sans; the one word that matters in serif italic.
- **Shape:** either flat (no box) text, or the pill shape with the inner highlight and soft glow. No sharp rectangles, outlines or strokes.
- **Colour:** white, black, paper, blue, red. Blue = good/right/feature, red = bad/wrong/cheap. Nothing else.
- **Motion:** blur-in with small overshoot (5-6 frames), exit by cut. Counters count up over 12-18 frames with ease-out.
- **Placement:** chest level or full-screen centre; inside the safe area; never over the face.
- **Sound:** small UI element = pop or click; anything full-screen = deep whoosh; impact moment = low hit.
- Describe any new element to the user (what, when, why) in the plan before rendering it.

## 7. Never
- Emoji, neon or outlined text, heavy drop shadows, cartoon SFX, slow cross-dissolves.
- Full sentences on screen; captions over the face.
- Real brand logos, other creators' footage, or famous people's footage/likeness unless the user owns the rights.

## 8. Notes round
Ask for notes one round at a time ("card too long", "pop too loud", "power word wrong") and re-render only what changed.
