import html, json, re, pathlib
root = pathlib.Path('/home/user/cuttit')
order = [('city-map-reel','City map reel','Make a 3D map flight along a real route in any city, with a maps-style overlay.','Make a city map reel from [start] to [landmark].'),
('word-captions','Word captions','Captions that pop word by word, in sync with your voice.','Add word-by-word captions to this video.'),
('kinetic-quote','Kinetic quote','Animated words that hit on the beat.','Make a kinetic quote reel from this text and song.'),
('bar-chart-race','Bar chart race','Animated rankings from real data.','Make a bar chart race of the biggest cities, 1950 to 2025.'),
('photo-to-ad','Photos to ad','Turn product photos into a 15-second ad.','Make an ad reel from these 5 photos. Price 499, DM to order.'),
('carousel-maker','Carousel maker','Designed carousel slides with the copy written for you.','Make a 7-slide carousel about [topic].'),
('before-after-reel','Before / after','A smooth before/after reveal.','Make a before/after slider reel from these two photos.'),
('itinerary-reel','Itinerary reel','A trip plan with an animated map.','Make a 3 days in [city] reel.'),
('audiogram-clip','Podcast clips','The best moments of a recording, turned into reels.','Find the 3 best clips in this podcast.'),
('website-scroll-reel','Website + scroll','A one-page website plus a phone scroll video of it.','Build a one-page site for my cafe and make a scroll reel.'),
('auto-reframe','Auto reframe','Landscape video turned vertical, following whoever is speaking.','Make this YouTube video vertical.'),
('reel-cover','Reel covers','Covers and thumbnails that stop the scroll.','Make a cover for this reel.')]
course = [
 ('Course title','cuttit Skill Pack: 12 Claude skills that edit your reels'),
 ('Short description','Turn clips, photos and ideas into finished reels with Claude. No After Effects, no timeline.'),
 ('Long description', """Edit reels by asking Claude in plain words.

This pack gives you 12 ready-made Claude skills. Each skill is a set of instructions you give Claude once. Then you ask for the reel ("make a map reel of my city", "add captions to this video") and Claude builds it: it writes the code, runs the tools, and exports a 1080x1920 video ready to post.

What's inside:
""" + "\n".join(f"{i}. {t}: {d}" for i,(s,t,d,_) in enumerate(order,1)) + """

What you need: a Claude account. Claude Code (desktop app or VS Code) works best, because it can run the video tools on your computer. Lesson 1 shows you how to set it up.

Includes all 12 skills and every skill released before 6 Dec 2026."""),
 ('Tags','Video editing, AI, Content creation, Instagram Reels, Claude'),
]
setup = """Start here: how to use these skills

Every lesson has the full skill text. Copy it and add it to Claude in one of these ways:

Option 1 - Claude Code (best: it can render videos on your computer)
1. Install Claude Code (desktop app or VS Code extension) and sign in.
2. Install ffmpeg and Python 3.10+.
3. Create a folder for each skill: ~/.claude/skills/<skill-name>/ (Windows: C:\\Users\\<you>\\.claude\\skills\\<skill-name>\\)
4. In it, create a file named SKILL.md and paste the skill text.
5. Open Claude Code and ask for your reel, for example: "Make a city map reel from Kochi station to Marine Drive."

Option 2 - Claude app (phone or web)
1. Create a Project, paste the skill text into the project instructions, then chat inside that project.
   Or start a new chat with: "Follow these instructions:" and paste the skill text.
2. Note: skills that render video need tools on a computer, so they work best in Claude Code.

Tips
- Give notes one round at a time and be specific ("the caption covers my face").
- Keep the credits the skills add (Google Earth, OpenStreetMap). They are required by those services.

No computer? Send your video to cuttit on WhatsApp and we'll edit it for you."""
items = []  # (group, label, text)
for l,t in course: items.append(('Course settings', l, t))
items.append(('Lesson 1', 'Lesson title', 'Start here: setup'))
items.append(('Lesson 1', 'Lesson text', setup))
for i,(slug,title,desc,tryit) in enumerate(order, 2):
    skill = (root/'skills'/slug/'SKILL.md').read_text()
    g = f'Lesson {i}'
    items.append((g, 'Lesson title', title))
    items.append((g, 'Lesson text', f"{desc}\n\nTry asking Claude: \"{tryit}\"\n\nHow to add it: copy the skill below and save it as ~/.claude/skills/{slug}/SKILL.md (Claude Code), or paste it into a Claude Project's instructions. Full steps in Lesson 1."))
    items.append((g, f'Skill text (save as {slug}/SKILL.md)', skill))
data = json.dumps(items)
page = open('/home/user/cuttit/createpie/tools/kit_template.html').read().replace('/*DATA*/[]', data)
(root/'createpie'/'copy-kit.html').write_text(page)
print(len(items), 'blocks')
