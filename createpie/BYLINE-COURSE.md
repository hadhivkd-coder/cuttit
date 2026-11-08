# CreatePie course: Byline

Copy each field exactly.

## Course settings
- **Title:** Byline: premium reel edits with Claude
- **Short description:** A Claude skill that edits your talking-head video into a premium editorial reel. A new edit for every video.
- **Price:** ₹99 (one-time)
- **Cover image:** `site/byline/poster.jpg` (or a screenshot of the demo)
- **Tags:** Video editing, Claude, AI, Instagram Reels, Motion graphics

## Long description
Turn any talking-head video into a premium editorial reel, made by Claude.

Byline gives Claude a complete editing style and a creative engine:
- Text behind you: giant words rise letter by letter behind your head and shoulders
- Orbit & swoosh lines that draw themselves around you and across the frame
- B-roll as floating 3D cards, or opened with an iris reveal
- Pop-in captions with big serif-italic power words
- Motion graphics on frosted glass: bar charts, padlocks, counters, calendars, icon chips
- Soft white light-flash transitions, smooth camera moves, 60 fps, and sound effects synced to every moment

It is not a template. Claude reads your script, finds the beats (hook, secret, myth, number, list, proof, call to action)
and designs a different edit for every video.

What you need: a computer with Claude Code (desktop app or VS Code). Python and ffmpeg are free; Claude installs the rest.
Rendering takes about 2 minutes per second of video at 60 fps.

## Lessons

### Lesson 1: Welcome (title: "What Byline does")
Text:
Byline turns a talking-head video into a premium reel with text behind you, orbit lines, 3D b-roll cards,
motion graphics and smooth 60 fps motion. Watch the demo, then go to Lesson 2 to set it up (10 minutes, once).
Attach / embed: `site/byline/demo.mp4`

### Lesson 2: Setup (title: "Set up Byline (once)")
Text:
1. Install Claude Code (desktop app or VS Code extension) and sign in.
2. Install ffmpeg and Python 3.10+:
   - Mac: `brew install ffmpeg python`
   - Windows: `winget install Gyan.FFmpeg` and `winget install Python.Python.3.12`
3. Download the Byline skill (attached: `byline-skill.zip`) and unzip it into your Claude skills folder:
   - Mac / Linux: `~/.claude/skills/byline/`
   - Windows: `C:\Users\<you>\.claude\skills\byline\`
   You should end up with `.../skills/byline/SKILL.md`.
4. Make a project folder for your video, open it in Claude Code, and say:
   "Set up Byline: install the Python packages, download the two fonts and the MODNet model as the Byline skill says."
Attach: `createpie/downloads/byline-skill.zip`

### Lesson 3: Make your first reel (title: "Your first Byline edit")
Text:
1. Put your talking-head video in the project folder (1080p, 15-90 seconds works best).
2. In Claude Code say: "Edit this video with Byline."
3. Choose **A) Customise** (fonts, colours, music, ending...) or **B) Leave it to me**.
4. Claude shows you the edit plan: every effect, where and why. Say "ok" or ask for changes.
5. Claude renders a quick preview, then the final 60 fps reel.
6. Give notes one round at a time ("the 1 is too big", "less music").

### Lesson 4: B-roll, sound and music (title: "Make it even better")
Text:
- B-roll: ask Claude for a shot list. It gives you free stock links (Pexels) per moment. Download, put the clips in a
  `broll` folder, and Claude turns them into floating 3D cards.
- Sound effects: Byline makes its own. If you have an SFX pack, put it in a `sfx_pack` folder and tell Claude.
- Music: Byline makes a calm original bed, or send your own track.
- Use your own videos and clips only, and never post copyrighted music.

## Refund / support (if CreatePie asks)
Support: your Instagram or WhatsApp. Please don't share or resell the skill files.
