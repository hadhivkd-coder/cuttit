# cuttit skill pack: setup guide

You get 12 folders, each with a `SKILL.md`. Each skill teaches Claude to make one kind of reel.

## Option A: Claude Code (recommended)
Claude Code can run Python and ffmpeg on your computer, so it can render the video for you.

1. Install Claude Code (the desktop app or the VS Code extension) and sign in.
2. Install the tools the skills use:
   - **ffmpeg:** macOS `brew install ffmpeg` · Windows `winget install ffmpeg` · Linux `sudo apt install ffmpeg`
   - **Python 3.10+:** from python.org (Claude installs the Python packages it needs when it runs a skill)
3. Copy the skill folders into your skills folder:
   - macOS / Linux: `~/.claude/skills/`
   - Windows: `C:\Users\<you>\.claude\skills\`
   You should end up with paths like `~/.claude/skills/city-map-reel/SKILL.md`.
4. Open Claude Code in an empty folder for your project and ask, for example:
   "Make a city map reel from Kochi railway station to Marine Drive."

## Option B: the Claude app
1. Settings > Capabilities (Skills) > Upload skill, then upload one skill folder as a .zip.
2. Ask for the reel in a chat. Skills that need ffmpeg or your local files work best in Claude Code.

## Tips
- Give notes one round at a time and be specific ("the caption covers my face", "the pin drops too late").
- The city map reel needs Google Earth Studio (free in Chrome at earth.google.com/studio) to render the 3D flight.
- Keep the credits the skills add (Google Earth, OpenStreetMap). They're required by those services.
