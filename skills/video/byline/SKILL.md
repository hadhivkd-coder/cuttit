---
name: byline
description: Edit a talking-head video into a premium "Byline" reel - editorial pop-in captions (heavy sans + big serif-italic power words), kinetic black/white breaker cards, giant text behind the speaker, glowing orbit and swoosh lines, b-roll as floating 3D cards, motion graphics on frosted glass, white light-flash transitions, smooth intentional camera moves at 60 fps, and SFX synced to every moment. Designs a new edit for every script (no fixed template). Use when the user wants a high-end talking-head reel, "Byline style", "editorial captions", or asks to edit a video so people ask "how did he edit this?".
---

# Byline

Byline is a **style with a creative engine**, not a template. Every Byline video shares the same **DNA**
(section 3) so it is instantly recognisable, but **Claude designs a new edit for every script** (section 4):
different beats, different motion graphics, a different hero moment. Exact numbers live in `style.json`.
The tested renderer is in `scripts/` (section 6).

Goal for every edit: a viewer thinks *"how the hell did he edit this?"* - while the edit stays clean, calm and premium.

---

## 1. Start: one question

Greet the user in one line, then ask only this and wait:

> "How would you like to work?
> **A) Customise:** I'll ask a few quick questions (fonts, colours, music, ending...) first.
> **B) Leave it to me:** I'll make every creative choice in the Byline style - just send the video."

- **B:** ask only for the video (and the CTA word if the speaker says "comment ..."). Use all defaults, design the edit
  yourself, show the edit plan (section 5, step 4), then render. Mention once that anything can change in the notes round.
- **A:** send the questionnaire below in **one numbered message**, each with its default. "defaults" accepts all.

1. **Video** - your talking-head video (best 15-90 s, 1080p or better).
2. **Fonts** - your brand fonts? *Default: Poppins Bold + Playfair Display Italic.*
3. **Colours** - your brand colour for chips/highlights? *Default: blue = good/right, red = wrong, black & white cards.*
4. **Music** - your own track / none / a calm original bed I generate? *Default: generated bed, very low.*
5. **Sound effects** - your own SFX pack (folder) or mine? *Default: SFX I generate (no licence needed).*
6. **Ending** - "comment [WORD]" CTA? Which word? *Default: the speaker's own CTA, or none.*
7. **Energy** - Calm / Standard / Hype? *Default: Standard.*
8. **B-roll** - clips of your own? Or should I give you a shot list with free stock links? *Default: shot list.*
9. **Language** + names/words to spell exactly. *Default: spoken language.*
10. **Handle** at the end (e.g. @yourname)? *Default: none.*

Summarise their choices in one line ("Fonts: Poppins + Lora · Music: none · Energy: Hype ...") and wait for "ok".
Their answers override `style.json`; everything else keeps the defaults.
- Their fonts replace Poppins / Playfair at the same sizes. One font only = captions; keep Playfair for power words.
- Their brand colour replaces blue. Red stays "wrong" unless the brand colour is red (then use black for wrong).

---

## 2. Inputs Claude prepares
- **Transcript** with word timestamps (faster-whisper). Show it; let the user fix names.
- **B-roll shot list** if the user has none: one line per beat that needs proof or illustration, with a free stock
  search link (Pexels/Pixabay, `?orientation=portrait`) and an AI-video prompt alternative. The user downloads and sends
  the clips. B-roll is optional - the edit must work without it.
- **SFX:** the user's pack mapped to roles (section 3, Sound) or the generated set.

---

## 3. The Byline DNA (fixed in every video)

**Captions - "pop-in"**
- Poppins Bold, crisp white, tight high-opacity black drop shadow (blur 2, offset 2). No glows, outlines, underlines.
- Rapid **1-2 word chunks**, centred at chest/neck level, never over the face.
- Entry: the whole chunk pops 80% -> 100% in ~4 frames (at 30 fps timing) with a slight spring. Exit: **hard cut** on the
  exact frame the next chunk starts.

**Power words**
- The most important conceptual words (a result, a number, a feeling, a contrast) switch to **Playfair Display Italic**,
  25% larger. Paired with small text (e.g. "SESSION" over "with me") the serif word is massive and dominant.

**Breaker cards**
- High-impact single words replace the video: solid black + white sans, or solid white + black serif italic;
  consecutive cards alternate. Letters rise in one by one with blur, tracking widens, slow eased zoom.
- Each card hits **exactly** on its first frame with a heavy bass whoosh.

**Colour & shape**
- White, black, blue (#2F7BFF), red (#FF3D55) only. Rounded shapes. Graphics sit on frosted-glass panels.

**Motion feel**
- Everything eases: expo/back-ease entrances (~0.5 s), gentle float while on screen, soft exits, a light shimmer sweep.
- Camera: smooth, **intentional** moves - dolly in on the hook, pull back to reveal, push in on the key line. Never snappy.
- **60 fps** with motion-interpolated footage; 0.9x speed for a calm premium pace (Calm/Standard).
- Transitions: a soft **white light flash/bloom** with a dreamy whoosh. No glitch effects.

**Grade**
- Crisp contrast, slight saturation, light sharpening, vignette, fine film grain.

**Sound (roles)**
| Role | Used for |
|---|---|
| `deep_whoosh` | breaker cards (exact first frame) |
| `flash` | white-flash transitions (dreamy whoosh) |
| `pop` / `click` | chips, graphics appearing, lock/checkbox/cursor clicks |
| `wrong` | strikes, red X, myths |
| `impact` + `shine` | hero numbers / big reveals |
| `count` | counters |
Music: a calm bed ~17 dB under the voice, ducked while speaking. Voice at -14 LUFS.

---

## 4. The creative engine (different in every video)

### Step 1 - find the beats
Read the transcript and tag every sentence with its beat:
**hook · claim · secret/reveal · myth/wrong · list · number · comparison · growth/result · emotion · time/booking ·
turn ("but here's the thing") · proof (b-roll) · CTA**.

### Step 2 - pick one effect per beat, by meaning
| Beat | Effects to choose from (vary across videos) |
|---|---|
| Hook | giant word **behind the speaker** (letters rise) + dolly-in · kinetic breaker card |
| Secret / exclusive | padlock that clicks shut · iris reveal · word that un-blurs |
| Myth / wrong | black-and-white section + text behind · red strike / red X on a graphic |
| List / apps | icon chips (play, pin, check, heart) · checklist that ticks itself |
| Number | giant serif number behind the speaker, peeking beside a shoulder · counter · ring + burst |
| Growth / result | bar chart (top bar blue) · rising line · counter |
| Comparison | red vs blue boxes · split-screen b-roll · two chips |
| Emotion / likes | heart with a number |
| Time / booking | calendar with a check · progress bar |
| Turn / connect ideas | swoosh line drawing across · orbit line looping behind the speaker's neck |
| Proof (b-roll) | 3D floating card (from right / left / bottom / scale) · iris reveal · full screen |
| CTA | massive serif trigger word with the instruction text cycling underneath |

### Step 3 - compose
- **One hero moment per video** - the biggest effect (usually text behind the speaker, a giant number, or the orbit).
  Put it on the hook or the strongest line.
- **Variety:** never the same effect twice in a row; rotate b-roll treatments; alternate card colours; vary entrance
  directions. Two Byline videos by the same creator should never share the same layout.
- **Rhythm:** something changes every 1.5-3 s, but at most **one** graphic on screen besides the caption.
  Leave 1-2 calm stretches (captions only) so the big moments land.
- **Energy:** Calm = fewer cards, no B&W, camera moves only. Standard = the defaults. Hype = more cards and graphics,
  faster camera moves, 1.0x speed.
- **Placement:** captions at chest level; graphics below them (~71% height); text-behind above the shoulders;
  nothing over the face; everything inside the 1080x1420 safe area.

### Step 4 - invent when the library doesn't fit
If a beat needs something new (dollar sign, map pin, clock, phone mockup, before/after label...), design it from the DNA:
the two fonts, the four colours, rounded shapes on frosted glass, eased-back entrance + float + shimmer + soft exit,
and the sound roles above. Describe every invented element in the plan (what, when, why) before rendering.

---

## 5. Workflow
1. Start question (section 1) -> inputs (section 2).
2. Transcribe; cut dead air (gaps > 0.25 s at -35 dB, keep 0.06 s padding); re-time words.
3. Beat map -> effects (section 4).
4. **Show the edit plan** as a readable list (time · line · effect · sound) and wait for "ok" (in B mode, show it and continue
   unless the user objects).
5. Write `plan.json` and render a **fast preview** (`"fps": 30, "interp": "fast"`, ~3 min) - check the frames yourself:
   nothing over the face, text-behind readable, graphics not crowding the caption.
6. Final render: `"fps": 60, "interp": "mci"` (about 2 min of render per second of video on a laptop CPU).
7. Notes round: one round at a time; change only what was asked.

---

## 6. Render (tested scripts included)
Setup once:
```
pip install faster-whisper numpy pillow "opencv-python-headless<5" onnxruntime
```
plus ffmpeg on PATH, and in the working folder:
- `fonts/Poppins-Bold.ttf`, `fonts/PlayfairDisplay-Italic.ttf` (Google Fonts, OFL)
- `models/modnet.onnx` - person cut-out model: `https://huggingface.co/Xenova/modnet/resolve/main/onnx/model.onnx` (Apache-2.0)

Transcribe (decode audio first to avoid a PyAV version clash; if the model download fails on a "xet" error set `HF_HUB_DISABLE_XET=1`):
```
ffmpeg -i input.mp4 -ac 1 -ar 16000 -f s16le a.raw
```
then pass the int16 array / 32768 to `WhisperModel("small").transcribe(audio, word_timestamps=True)` and save `words.json`.

Render: `python scripts/render.py plan.json` - format in `scripts/plan.example.json`. All times are **source-video seconds**.

### plan.json reference
| Key | What it does |
|---|---|
| `fps`, `interp`, `speed` | 60 / "mci" for finals, 30 / "fast" for previews; 0.9 speed (Calm/Standard) |
| `cuts` | dead-air ranges to remove |
| `scales` | camera keyframes `[time, zoom]`, smooth eased between them |
| `zoom_anchor` | zoom centre; set to a required watermark's position so it is never cropped |
| `captions` | `{t0, t1, words, power:[indexes]}` - 1-2 words each, contiguous |
| `cards` | `{t0, t1, text, bg: black/white}` |
| `bw` | `[t0, t1]` black-and-white sections |
| `chips` | `{t0, t1, items:[{t, text, icon}], shape: pill/box, color}` |
| `graphics` | `bars`, `lock`, `heart`, `ring`(+`burst`), `calendar`, `arrow`, `grid`(`style: clean`, `strike_t`), `counter`, `button` |
| `behind` | text behind the speaker `{t0, t1, lines, font, px, x, y, grow}` (needs `matte_model`) |
| `lines` | `orbit` `{dy, rx, ry, tilt}` around the speaker / `swoosh` `{pts: 4 bezier points}` |
| `cutaways` | b-roll `{t0, t1, file, from, slowmo, zoom, mode: card/full, enter, reveal: iris}` |
| `cta` | `{t0, t1, word, cycle:[[t, text]...]}` |
| `transition` | "flash" (default) or "radial" |
| `sfx`, `sfx_pack`, `sfx_map` | explicit SFX; the user's pack per role `{role: [file, max_s (neg = tail), level_db]}` |
| `music` | "generated", a file, or null |
| `matte_model` | path to `modnet.onnx` |

Rules for the depth effects:
- `behind` text: one short word (or a single giant glyph), above the shoulders; use `x` to let a big number peek out
  beside a shoulder. It scales with the camera.
- `orbit`: at neck/shoulder level (`dy` ~0.10), never at face height - it passes behind the neck and in front of the chest.

---

## 7. Never
- Emoji, neon, outlined text, heavy shadows, cartoon or glitch SFX, slow cross-dissolves, snappy zooms.
- Full sentences on screen; anything over the face.
- Real brand logos, other creators' footage, celebrities' likeness, copyrighted music.
- Removing an AI-video watermark that the generator requires.
- Committing the user's SFX pack, b-roll or videos to a public repository.
