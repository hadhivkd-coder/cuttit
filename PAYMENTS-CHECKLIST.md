# Connecting payments (Paddle): checklist

Paddle = the checkout and cashier. The customer pays Paddle, Paddle handles each country's tax, and Paddle pays you.
Lemon Squeezy is moving its sellers onto Stripe, which is reported to be invite-only in India, so **use Paddle**.

## A. What YOU need to get (only you can do these)

### 1. Documents (identity check)
- [ ] Passport or Aadhaar (photo ID), plus a selfie / live check during signup
- [ ] PAN card
- [ ] Your address
- Sign up as an **individual / sole trader**. Paddle doesn't require business verification for individuals.

### 2. A bank account that can receive money from abroad
- [ ] An Indian bank account that accepts international transfers (SWIFT). Ask your bank for the SWIFT code.
- Payouts come in USD (not rupees), so the bank converts them and may charge a fee. **Payoneer** is the other option Paddle offers, and it's often cheaper.
- You can start selling before this is set up, but you won't get paid until it is.

### 3. A domain name
- [ ] Buy a domain, e.g. `cuttit.co` or `getcuttit.com` (about $10-15/year at Namecheap, Cloudflare or GoDaddy).
- Paddle reviews your **domain and website** before approving you. A free `vercel.app` address may be rejected.

### 4. An email address on that domain
- [ ] e.g. `hello@cuttit.co`. Zoho Mail has a free plan. This is the support address shown on the site.

### 5. Accounts to create
| Account | Why | Cost |
|---------|-----|------|
| Paddle | Checkout, tax, payouts | About 5% + 50¢ per sale, no monthly fee |
| Vercel (or Netlify) | Hosts the website | Free |
| Resend | Sends the "here are your files" email | Free up to a few thousand emails/month |
| WhatsApp Business app | Service orders | Free |

### 6. Tax at home (ask a CA once)
- Money from Paddle counts as income from exporting a digital service. Ask a chartered accountant about income tax,
  whether you need GST registration (the usual threshold is ₹20 lakh/year turnover), and keeping the bank's
  foreign-remittance records (FIRC / e-FIRA). One short consultation is enough.

## B. What the WEBSITE needs before Paddle approves it (I build these)
- [ ] Live on your domain, publicly reachable
- [ ] Clear product descriptions and prices (done)
- [ ] **Terms of Service** that name Paddle as the merchant of record ("Our order process is conducted by our online reseller Paddle.com...")
- [ ] **Privacy Policy**
- [ ] **Refund Policy** (e.g. 14 days for skill packs; unused service credits refundable)
- [ ] Contact email in the footer

## C. The connections (I build these once you have Paddle)
```
Visitor -> site shows local price (pricing.js)
        -> "Buy" opens the Paddle checkout in their currency (Paddle.js, on the page)
        -> Paddle charges them, adds local tax
        -> Paddle sends a "payment completed" message (webhook) to our site
        -> our site emails a private download link for the skill files (Resend)
Service buyers -> after payment, a "Send your video on WhatsApp" button with their order number
```
What I'll need from your Paddle dashboard:
- [ ] Client-side token (safe to put on the website)
- [ ] Webhook secret (kept private, stored in Vercel settings, never on the page or GitHub)
- [ ] Products and prices created in Paddle. **I'll give you the exact list**: skill pack, single skills,
      3 service packages, each with a price per currency from `site/pricing.js`.

Why the webhook is needed: Paddle handles payments, but delivering the skill files is up to us.
The files sit in private storage and each buyer gets a link that works only for them.

## D. Order of work
1. **Today:** buy the domain; sign up to Paddle (sandbox/test account first); start the bank or Payoneer setup.
2. **I build:** legal pages, Paddle checkout, webhook + file delivery, all tested with Paddle's sandbox (test cards, no real money).
3. **You:** put the site live on the domain, then submit the Paddle live account for review (usually a few days).
4. **Approved:** switch from sandbox to live keys. Done.

## Backup if Paddle says no
Gumroad also handles tax for you and supports creators in many countries; check India payouts when signing up.
