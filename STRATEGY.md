# cuttit strategy

## 1. The idea in one line
A store of 40-60 Claude skills, one per editing style. Each skill comes with a short demo video showing exactly what it makes.
Buyers see the demo, buy the skill, and make the same edit on their own footage.

## 2. The three things every product has
Every skill in the store is one product, and every product has exactly these three parts:

| Part | What it is | Who sees it |
|------|------------|-------------|
| `SKILL.md` | The instructions Claude follows to make the edit | Buyers only (after payment) |
| Demo video | 10-15 s, 9:16, the skill applied to an AI talking-head clip | Everyone (website + Instagram) |
| Listing | Name, one-line promise, category, price, cover image | Everyone (website) |

If a skill doesn't have all three, it doesn't go live.

## 3. Catalog structure
Two categories, so the store stays simple:

- **Video styles (20-30):** edits applied to talking-head footage: captions, zooms, b-roll, reframing, podcast clips, etc.
- **Motion graphics (20-30):** animated elements: titles, maps, charts, lower thirds, transitions, kinetic text, etc.

The 12 skills we have already get sorted into these two.

## 4. Repo structure (the system)
```
cuttit/
  catalog.json                 # the single list of every product -> the website reads this
  skills/
    video/<slug>/
      SKILL.md                 # the product
      meta.json                # name, promise, category, price, status
      demo/source.mp4          # the raw AI talking-head clip (not shipped)
      demo/demo.mp4            # the finished demo, watermarked
      demo/cover.jpg           # first frame / cover
    motion/<slug>/ ...         # same shape
  templates/                   # blank SKILL.md and meta.json to copy for new skills
  site/                        # the store
```
One folder per skill, always the same shape. Adding a product means copying the template, filling it in, and setting `status` to `live`.

## 5. Production pipeline (per skill)
Same 6 steps every time, so 40-60 is a routine job, not 40-60 projects:

1. **Spec:** you send the style (a screenshot, screen recording, or description). I write `SKILL.md` + `meta.json`.
2. **Source clip:** you generate a 10-15 s AI talking-head clip (Gemini / Veo or similar).
   - Use 2-3 recurring AI "presenters" so the whole store looks like one brand.
   - Keep a script library (section 6) so each clip says something useful, not filler.
   - Export 1080x1920 if possible; if not, the auto-reframe skill fixes it.
3. **Edit:** run the skill in Claude Code on the source clip. Give notes until it looks right.
   If the skill needed a fix to get there, **update `SKILL.md`**: buyers must get the version that worked.
4. **QA checklist:** text inside the safe area; nothing covers the face; captions match the audio;
   audio loudness normal; exported 1080x1920 30 fps; runs on a fresh machine from the instructions alone.
5. **Demo export:** small "cuttit" watermark; compress for the web (under 2 MB, `crf 28`, no audio track
   for the autoplay preview + a version with audio for Instagram); cover image.
6. **List it:** add to `catalog.json`, set `status: live`. The site updates itself.

Batching: script 10 clips -> generate 10 -> edit 10 -> QA 10. A batch of 10 is about 2 days of work.

## 6. Source clips: script library
Every demo clip is also content, so it should say something people want to hear. Rotate these themes:
- AI/Claude tips ("3 things Claude can do that you didn't know")
- Creator tips ("Why your reels die in the first second")
- Small-business tips ("Your shop needs this one video")

Rules for AI talking heads:
- Check the generator's terms allow commercial use, and keep any watermark it requires (Google adds SynthID to Veo output).
- Don't make an AI presenter that looks or sounds like a real person or celebrity.
- Label it as AI where Instagram asks (the "AI info" label).

## 7. Pricing
Simple ladder. Prices are a starting point; change them after the first 2 weeks of sales data.

| Product | Price | Why |
|---------|-------|-----|
| Single skill | ₹49 | Impulse buy, easy first purchase |
| Video styles pack (all) | ₹299 | Main product |
| Motion graphics pack (all) | ₹299 | Main product |
| All access (every skill + all future ones) | ₹499 | Best value; this is what you push |
| Free skill | ₹0 | 1-2 skills, given out on Instagram for follows and email signups |

Anyone who already bought the 12-skill pack gets upgraded to all access free. Early buyers become your best promoters.

## 8. Website (store)
- **Home:** headline + one hero demo + "All access ₹499" button.
- **Catalog:** grid of demo videos (muted, autoplaying, looping) with a filter: All / Video styles / Motion graphics.
  Tap a card -> the product page.
- **Product page:** the demo with sound, what it does, what you need (Claude Code, ffmpeg...), price, buy button,
  "included in all access" note.
- **Checkout + delivery:** start with Razorpay Payment Pages or Gumroad (UPI, automatic download email).
  Move to our own checkout only once sales justify it.
- **Video hosting:** small MP4s in the site are fine up to ~60 videos. Move to Cloudflare Stream or Bunny if bandwidth grows.
- Everything is generated from `catalog.json`, so adding a skill never means editing HTML.

## 9. Marketing
Every demo video is also a reel. 40-60 products = 40-60 posts with no extra work.
- Post 2-3 a day. Caption: "Made this edit with one Claude skill. Comment <WORD> to get it."
- ManyChat sends the product page link (not the file) for paid skills, and the file for the 1-2 free ones.
- Collect emails on free downloads. Email list = launch list for the WhatsApp service.
- Track which comment words win. Make more skills in those styles.

## 10. Community
The community is what makes people stay after they buy, and it's why all access is worth ₹499.

### Two levels
| Level | Where | Who | What they get |
|-------|-------|-----|---------------|
| Free | Instagram broadcast channel + WhatsApp Channel | Followers | New skill drops, free skill of the month, tips, launch news |
| Members | WhatsApp Community (private) | Paying buyers | Help, weekly challenge, live sessions, early access, vote on new skills |

Why WhatsApp: your audience already lives there, and the product itself (cuttit on WhatsApp) will too.
If it grows past ~1,000 members or needs more structure, move members to Discord or Skool.

### Member community layout (WhatsApp Community groups)
- **Announcements** (admins only): new skills, updates, live session times
- **Start here:** the setup guide, rules, "post your first edit" prompt
- **Help:** "my render fails" questions. Answer within 24 h; turn repeat questions into FAQ / skill fixes
- **Showcase:** members post edits they made with the skills
- **Requests:** members suggest and vote on the next skills

### Weekly rhythm
| Day | What |
|-----|------|
| Monday | New skill drop (from the batches in section 5) |
| Wednesday | Weekly challenge: one skill + one theme ("map reel of your hometown") |
| Friday | Live session (30 min, Instagram Live or Google Meet): build one edit live, answer questions |
| Sunday | Best 3 challenge edits reposted on cuttit's Instagram, with credit |

### Why it grows the business
- Members' edits = free content for cuttit's Instagram (always ask permission and credit them).
- Requests tell you which skills to build next.
- Help questions show where a skill is unclear; fix the `SKILL.md`, and everyone gets the update.
- The most active members become the WhatsApp service's first beta testers, and later affiliates
  (a referral link with 20-30% commission through Razorpay / Gumroad affiliates).

### Rules (pinned in Start here)
1. Be kind; no spam or self-promotion outside Showcase.
2. Don't share the skill files outside the community.
3. Credit other members if you reuse their idea.
4. Only post content you have the rights to; no one else's videos.
Admins: you + 1 helper once the community passes ~200 members.

### What to measure
- % of buyers who join the community (target: 60%+)
- Weekly challenge entries
- Help questions answered within 24 h
- Members who buy again or upgrade to all access

## 11. Protecting the product
- Make the GitHub repo **private** (it's public now).
- Skills are delivered only after payment, through the checkout's download link.
- A short licence in every download: use it for your own and your clients' videos; don't resell or share the files.
- Accept that some sharing will happen. Updates and new skills for all-access buyers are what keep people paying.

## 12. How this connects to the WhatsApp service
The skill library is the service's editing engine. Each skill becomes an edit style a WhatsApp user can pick:
"send a video + reply 7 for map reel". Building 60 skills now is building the service's menu.

## 13. Timeline
| When | Goal |
|------|------|
| Day 1-2 | Restructure the repo (section 4), templates, `catalog.json`, sort the 12 existing skills |
| Day 2-3 | Store site with catalog + product pages; payment links; set up WhatsApp Channel + member Community |
| Week 1-2 | Batches 1-2 (20 skills + demos). Start posting |
| Week 2-3 | Batches 3-4 (40 skills). Launch all access |
| Week 3-4 | Batches 5-6 (60 skills). Start the WhatsApp service beta (see ROADMAP.md) |

## 14. Decisions needed from you
1. Prices: OK with the ladder in section 7?
2. Checkout: Razorpay (best for UPI and India) or Gumroad (easiest, worldwide)?
3. The 20 video styles + 20 motion graphics list, in batches of 10.
4. The WhatsApp number to run the community from (best: a separate business number)
5. Which AI talking-head tool you'll use, so I can check its commercial-use terms.
