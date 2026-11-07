# cuttit: 30-day sprint strategy
**International. Priced per market. Runs 7 Nov to 6 Dec 2026. Goal: as much revenue as possible in 30 days, then close and start the next program.**

## 1. Why a sprint
After about a month, "Claude makes your reels" stops being new and anyone can write these skills themselves.
So everything is planned to **sell fast now** and turn buyers into **editing-service clients**, because the service keeps
earning after the skills stop selling.

Two products:
1. **Skill pack:** all the editing skills, sold until 6 Dec.
2. **Editing service:** send a video on WhatsApp, get an edited reel back. Starts **14 Nov**.

## 2. The offer (priced per market)
Each market pays its own **market price**: what people there already pay for reel editing and creator packs.
It is not one price converted into other currencies. The site picks the visitor's market from their location
(they can switch it in the top bar). The table lives in `site/pricing.js`.

**How the service prices were set:** a little below a mid-level freelance editor in each market. We're faster
(AI-assisted, 24 h), but not budget-marketplace cheap.
Market rates found (Nov 2026, from published rate guides and freelancer listings, so rough):
- US: about $30-100 per simple reel, $100-300 branded; monthly plans about $300-3,000.
- India: about ₹100-500 budget, ₹800-2,500 mid-level per reel.
- Gulf: little public data; quotes seen at about $100-500 per reel (in USD) and SAR 3,000-8,000 for shoot-day packages.
  **Test Gulf prices in week 1 and raise them if they sell easily.**

### Skill pack (sold until 6 Dec; price rises each week, and that's real)
| Market | 7-13 Nov | 14-20 Nov | 21 Nov-6 Dec | Single skill |
|--------|---------|-----------|--------------|--------------|
| US + rest of world (USD) | $29 | $39 | $49 | $7 |
| Canada (CAD) | C$39 | C$49 | C$65 | C$9 |
| UK (GBP) | £24 | £29 | £39 | £6 |
| Eurozone (EUR) | €27 | €35 | €45 | €6 |
| Australia (AUD) | A$45 | A$59 | A$75 | A$10 |
| Saudi Arabia (SAR) | SAR 99 | SAR 129 | SAR 179 | SAR 25 |
| UAE (AED) | AED 99 | AED 129 | AED 179 | AED 25 |
| India (INR) | ₹299 | ₹399 | ₹499 | ₹49 |

- Don't promise "lifetime updates". Promise "every skill released before 6 Dec".

### Editing service (from 14 Nov)
| Market | Single reel | 10 reels | Monthly (30 reels) |
|--------|-------------|----------|--------------------|
| US + rest of world | $39 | $299 | $799 |
| Canada | C$49 | C$399 | C$1,049 |
| UK | £29 | £229 | £629 |
| Eurozone | €35 | €279 | €749 |
| Australia | A$59 | A$449 | A$1,199 |
| Saudi Arabia | SAR 149 | SAR 1,099 | SAR 2,799 |
| UAE | AED 149 | AED 1,099 | AED 2,799 |
| India | ₹499 | ₹3,999 | ₹9,999 |

Skill-pack buyers get their first edited reel free.

### Payments for international customers
Selling digital products abroad means collecting **sales tax / VAT in each country** (EU and UK VAT, Saudi 15% VAT, Canadian GST, etc.).
Doing that yourself is a lot of paperwork, so use a **Merchant of Record (MoR)**: they sell on your behalf, charge local currency
and local payment methods, file the taxes, and pay you out to your Indian bank account.

| Option | Good | Watch out |
|--------|------|-----------|
In plain words: it's the shop's checkout and cashier. The customer pays them, they handle the tax, and they send you the money.

| **Paddle** (recommended) | MoR; you can set a fixed price per currency/country, which matches our table | Reviews your site and product before approval; apply on day 1 |
| **Lemon Squeezy** | MoR; very easy for digital downloads | Check whether it supports fixed per-currency prices; if it converts from USD, checkout amounts may differ slightly from the site |
| Razorpay International / Stripe | Lower fees | **Not** MoR: you handle foreign taxes yourself |

Whichever you pick, the checkout must charge the same numbers as `site/pricing.js`.
For the service (paid over WhatsApp), send a payment link from the same provider in the client's currency.

### Target markets
1. **Gulf (Saudi, UAE):** high spending, big creator and small-business market, and WhatsApp is everywhere.
2. **US / Canada / UK / Australia:** biggest buyers of creator tools.
3. **Europe:** smaller, same content works.
4. **India:** lower price, high volume; good for social proof and reviews.

Content is in English. For the Gulf, add Arabic captions to demos (the word-captions skill supports Arabic) to stand out.

### Service across time zones
- The 24 h turnaround means a US client's evening order is edited during your morning. That's fine.
- Monthly clients get 12 h priority; take them only up to your daily cap (max 15 reels/day at first).

## 3. How the service works in week 1 (no waiting for approvals)
The fully automated WhatsApp bot needs Meta Business verification and the WhatsApp Cloud API, which can take days to weeks.
So **don't wait**:

1. **Now:** get a separate number on the **WhatsApp Business app** (free, works today). Add a catalog with the 3 packages,
   a greeting message, and quick replies.
2. Clients send the video + choose a style (the style numbers = the skills).
3. **You run the edit in Claude Code with the skills**, then send it back. Payment before the edit, by a payment link in the client's currency (same provider as the store).
4. Cap it: **max 15 reels a day** at first, so the 24 h promise is always kept.
5. **At the same time:** start Meta Business verification on day 1. When it's approved, automate the most-ordered style first
   (see ROADMAP.md), then the next.

Customers see the same thing either way ("send a video, get a reel"), so there's no reason to wait for the bot.

Costs per reel to track: your time + Claude plan + ElevenLabs / Higgsfield credits if the style uses them.
Only offer AI voice / generated b-roll on packages where the price covers the credits.

## 4. Who buys what
| Who | Buys | Where to find them |
|-----|------|--------------------|
| Creators who want to learn | Skill pack | Instagram reels + comment-to-DM |
| Creators who don't have time | Service | The same reels: "or just send it to us" |
| Local businesses (restaurants, gyms, salons, real estate, shops) | Service, monthly | Direct DMs + WhatsApp, with a free sample reel made from their own Instagram video |

Local businesses pay the most and pay monthly. Spend 1 hour every day on direct outreach to them from week 2.

## 5. Revenue targets (in USD)
These are **targets to aim for**, not forecasts: the real numbers depend on how many people your reels reach.
Check them every Sunday and adjust.

| Source | Target | Revenue |
|--------|--------|---------|
| Skill packs | 300 sales at ~$25 average (mix of markets) | ~$7,500 |
| Single skills | 300 sales at ~$6 | ~$1,800 |
| Service: single reels | 60 at ~$39 | ~$2,340 |
| Service: 10-reel packs | 20 at ~$299 | ~$5,980 |
| Service: monthly clients | 10 at ~$799 | ~$7,990 |
| **Total** | | **~$25,600** |

Minus the payment provider's fee (roughly 5% + a small fixed fee per sale for MoR providers) and AI tool costs.

## 6. The 30 days, week by week

### Week 1 (7-13 Nov): launch the skill pack, prepare the service
- Apply to Paddle (or Lemon Squeezy) on day 1; set the per-currency prices from section 2. Site online; repo private.
- 8 new skills, so 20 at launch. You send the styles; I write the skills.
- Make AI talking-head demo clips (10-15 s) for each skill. **Post 3 reels a day**, each with a comment keyword.
- ManyChat comment-to-DM sends the product link.
- Service setup: WhatsApp Business number, catalog, payment link, style menu. Start Meta verification.
- Collect a waitlist: "Service opens 14 Nov. First 20 get 20% off."

### Week 2 (14-20 Nov): service live
- Open the service to the waitlist first, then everyone.
- Skills to 30. Price to ₹399 on 14 Nov.
- Start local-business outreach: 20 DMs a day with a free sample reel.
- Post every finished client reel (with permission) as proof.

### Week 3 (21-27 Nov): scale what works
- Look at the numbers: which skills sell, which service package sells. Do more of the top one, drop the rest.
- Skills to 40. Price to ₹499.
- Automate the most-ordered service style if Meta approval is through; otherwise add a helper editor.

### Week 4 (28 Nov-6 Dec): final push and close
- "Closes 6 Dec" countdown in reels and stories (it really closes).
- Offer: skill pack + 3 edited reels bundle.
- Move every happy client to a monthly plan.
- 6 Dec: stop selling skills. Keep the service running. Plan the next program.

## 7. Community (kept small for 30 days)
- **One WhatsApp Community for buyers**, with groups: Announcements, Help, Showcase.
- Weekly: new skill drop (Mon), challenge (Wed), 30-min live build (Fri), best edits reposted (Sun, with credit).
- Its real job in this sprint: answer questions fast (fewer refunds), collect member edits to post as proof,
  and **turn members into service clients and referrers** (20% referral commission).
- After 6 Dec it becomes the launch list for the next program.

## 8. The system (repo structure)
```
cuttit/
  catalog.json           # every skill: name, category, price, status -> the website reads this
  skills/video/<slug>/   # SKILL.md, meta.json, demo/ (source clip, demo video, cover)
  skills/motion/<slug>/
  templates/             # blank SKILL.md + meta.json
  service/               # style menu, price list, quick replies, client tracker
  site/                  # the store
```
Per skill, every time: write the skill -> AI clip -> edit with the skill -> QA -> watermarked demo -> live.

## 9. Daily routine (you)
| Time | Task |
|------|------|
| Morning | Post reel 1; reply to comments and DMs; check new orders |
| Midday | Edit service orders (max 15/day) |
| Afternoon | Make 3-5 new demo clips; post reel 2 |
| Evening | 1 h local-business outreach; post reel 3; Help group |

## 10. Rules that protect the business
- Make the GitHub repo private, so the skills can't be downloaded free.
- Only promise what exists before 6 Dec. No "lifetime".
- AI talking heads: check the tool allows commercial use; label as AI on Instagram; no look-alikes of real people.
- Client videos: use them only for their edit, and post them only with permission. Delete after 30 days.
- A refund policy on the site (e.g. 7 days if a skill doesn't work for you). It builds trust and costs little.

## 11. Decisions needed from you (to start today)
1. Payment provider: **Paddle** (recommended) or **Lemon Squeezy**?
2. The WhatsApp Business number for the service and the community.
3. Your Instagram handle and current follower count (to set realistic targets).
4. The first 8 styles for the new skills.
5. OK with the regional prices in section 2? Any other countries to add (Qatar, Kuwait, Singapore...)?
