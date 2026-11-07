# cuttit: notes for Claude

## Current focus (Nov 2026)
**Only one job right now: create Claude skills that make reels, and sell them on CreatePie.**
Do not work on the website, payments, the WhatsApp service, or strategy docs unless asked.
cuttit (the WhatsApp video-editing platform) is a separate, later project.

## How we make a skill
1. The user shares a reference video (and sometimes a PDF/notes) and says what the skill should do.
2. Watch the reference: extract frames (`ffmpeg -i ref.mp4 -vf fps=4 frames/%04d.png`), note the text style,
   motion, timing, captions, zooms, transitions, music sync. Describe it back to the user before writing.
3. Write `skills/<category>/<slug>/SKILL.md`:
   - YAML front matter: `name` (the slug) and `description` (what it makes + when to use it).
   - Sections: Ask first, Steps, Rules. Concrete numbers (sizes, frames, fonts, colours), real commands.
   - Original wording and design. Recreate a style or technique, never copy one creator's exact video,
     branding, or assets. No real brand logos.
4. Test it: run the skill on a sample clip, show the user the result, fix the SKILL.md until the output is right.
5. Add it to `createpie/` (lesson text) so it can be sold.

Categories: `skills/video/` (edits on talking-head footage) and `skills/motion/` (motion graphics).
The first 12 skills are in `skills/<slug>/` and will be sorted into those folders later.

## Format
- Output: 1080x1920, 30 fps, H.264 + AAC, `-pix_fmt yuv420p`.
- Keep text inside the 1080x1420 safe area (top/bottom 250 px are covered by app UI).
- Tools available to skills: Python 3.10+, ffmpeg, Pillow, OpenCV, faster-whisper, mediapipe, Playwright.

## Selling
- Sold on CreatePie as a course: one lesson per skill, with the skill text pasted in the lesson
  (copy-paste) and optionally the zip in `createpie/downloads/`.
- `createpie/tools/build_kit.py` rebuilds `createpie/copy-kit.html`; `createpie/ALL-LESSONS.md` has all lesson text.
