# cuttit: 30-day sprint strategy
**International. Priced in local currency. Runs 7 Nov to 6 Dec 2026. Goal: as much revenue as possible in 30 days, then close and start the next program.**

## 1. Why a sprint
After about a month, "Claude makes your reels" stops being new and anyone can write these skills themselves.
So everything is planned to **sell fast now** and turn buyers into **editing-service clients**, because the service keeps
earning after the skills stop selling.

Two products:
1. **Skill pack:** all the editing skills, sold until 6 Dec.
2. **Editing service:** send a video on WhatsApp, get an edited reel back. Starts **14 Nov**.

## 2. The offer (international, priced in local currency)
Visitors see prices in their own currency, picked from their location (they can switch it in the top bar).
Prices are **set per currency as round local numbers**, not live conversions, so a Saudi visitor sees SAR 69, not SAR 71.25.
The table lives in `site/pricing.js`; change prices there.

### Skill pack (sold until 6 Dec; price rises each week, and that's real)
| Currency | 7-13 Nov | 14-20 Nov | 21 Nov-6 Dec | Single skill |
|----------|---------|-----------|--------------|--------------|
| USD (US + everywhere else) | $19 | $25 | $29 | $5 |
| CAD (Canada) | C$25 | C$35 | C$39 | C$7 |
| GBP (UK) | £15 | £19 | £23 | £4 |
| EUR (Eurozone) | €17 | €23 | €27 | €5 |
| AUD (Australia) | A$29 | A$39 | A$45 | A$8 |
| SAR (Saudi Arabia) | SAR 69 | SAR 89 | SAR 109 | SAR 19 |
| AED (UAE) | AED 69 | AED 89 | AED 109 | AED 19 |
| INR (India) | ₹299 | ₹399 | ₹499 | ₹49 |

- Don't promise "lifetime updates". Promise "every skill released before 6 Dec".

### Editing service (from 14 Nov)
| Currency | Single reel | 10 reels | Monthly (30 reels) |
|----------|-------------|----------|--------------------|
| USD | $29 | $199 | $499 |
| CAD | C$39 | C$269 | C$679 |
| GBP | £23 | £159 | £399 |
| EUR | €27 | €179 | €459 |
| AUD | A$45 | A$299 | A$759 |
| SAR | SAR 109 | SAR 749 | SAR 1,879 |
| AED | AED 109 | AED 729 | AED 1,829 |
| INR | ₹299 | ₹1,999 | ₹4,999 |

Skill-pack buyers get their first edited reel free.

### Payments for international customers
Selling digital products abroad means collecting **sales tax / VAT in each country** (EU and UK VAT, Saudi 15% VAT, Canadian GST, etc.).
Doing that yourself is a lot of paperwork, so use a **Merchant of Record (MoR)**: they sell on your behalf, charge local currency
and local payment methods, file the taxes, and pay you out to your Indian bank account.

| Option | Good | Watch out |
|--------|------|-----------|
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
| Skill packs | 300 sales at ~$20 average | ~$6,000 |
| Single skills | 300 sales at $5 | ~$1,500 |
| Service: single reels | 60 at $29 | ~$1,740 |
| Service: 10-reel packs | 20 at $199 | ~$3,980 |
| Service: monthly clients | 10 at $499 | ~$4,990 |
| **Total** | | **~$18,000** |

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
