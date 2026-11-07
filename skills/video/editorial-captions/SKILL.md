---
name: editorial-captions
description: Edit a talking-head video in a premium "editorial captions" style - two-font word captions at chest level (clean sans + big italic serif power words), black/white full-screen word cards, glowing pill chips for lists, punch-in zoom-blur cuts, black-and-white punches, synced whoosh/pop SFX and a big "comment WORD" ending. Use when the user wants a high-end, fast-paced talking-head reel, "editorial" or "serif captions", or asks to edit a video "in this style". Also designs new on-screen elements that match the style.
---

# Editorial Captions (style template)

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
   Default: the reference style, a clean sans (Inter Tight) + an elegant italic serif (Instrument Serif).
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
1. Fonts: download Inter Tight and Instrument Serif (Google Fonts, free licence) into `fonts/`.
2. Transcribe with faster-whisper, `word_timestamps=True` (model `small`; `medium` for non-English).
   Show the transcript, let the user fix names and spelling.
3. Remove dead air: cut every gap longer than 0.25 s at -35 dB, keeping 0.06 s padding (jump cuts are part of the look).
   Re-time the words to the new edit.
4. Face track (mediapipe) every 3rd frame. Store the chin y per frame for caption placement.
5. **Edit plan first.** Write `plan.json`: every caption chunk, which word is the power word, where word cards,
   chips, B&W punches, b-roll and punch-ins go, and each SFX. Show the plan to the user as a readable list and wait for "ok".

## 3. Style rules (how to plan)
**Captions**
- 1-3 words per caption. Break at natural phrase ends, never mid-name or mid-number.
- One **power word** per sentence (the word that carries the meaning: a result, a number, a feeling, a contrast).
  It is set in the serif italic at the large size; the rest of the caption is in the sans.
- The previous caption line stays above the new one as a faded ghost (style.json `ghost`) for one caption, then disappears.
- Position: from style.json `y_rule`. Never cover the mouth or eyes.
- Enter: 5-frame blur-in with a tiny overshoot. Exit: cut.

**Full-screen word cards**
- Every 8-15 s, take the strongest phrase (the hook, the key idea, the twist) and replace the video with 1-5 cards,
  one word each, alternating black (sans, white) and white (serif italic, black). Voice keeps playing.
- Each card gets a **deep whoosh**. Card length = that word's spoken length (0.35-1.2 s).

**Chips (lists and labels)**
- When the speaker lists 2-5 things, pop one blue pill chip per item exactly when it is said, stacked at chest level. Each gets a **pop**.
- Contrast/quote pairs ("a cheap editor asks... / a great editor asks..."): red pill for the weak side, blue pill for the strong side.

**Camera**
- Change the shot every 1.2-2.5 s: alternate scale 100% / 112% on new clauses, never mid-word.
- Every cut between scales is a 4-frame zoom-blur, followed by a small brightness flash that settles over 12 frames.
- Nothing stays unchanged longer than 3 s (a punch-in, card, chip or b-roll counts as a change).

**Black-and-white punch**
- When the speaker names a mistake, something bad or "what not to do", go black-and-white with a 4% zoom
  for that phrase only. Add a short **glitch** SFX. At most once every 20 s.

**B-roll**
- Only the user's own footage: proof of work, the product, a screen recording of the thing being described.
- Enter with a 6-frame zoom-blur and a **whoosh**. Max 2.5 s each. Two related clips can stack as a top/bottom split.
- A name card (blue pill + small sans subtitle) only for people in the user's own footage, with their permission.

**Ending (CTA)**
- Last 3-4 s: clear everything else. Small sans "comment" above the keyword in huge serif italic, uppercase, in quotes,
  with a soft glow. **Whoosh** + **low hit** on entry. Hold to the end.

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

## 5. Render
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
