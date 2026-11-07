// cuttit regional pricing.
// Prices are set per market, from what that market already pays (not currency conversions).
// Edit this table to change prices. The checkout must charge the same amounts:
// set the same per-currency prices in the payment provider.

window.CUTTIT_PRICING = (() => {
  // pack: price by sprint week [7-13 Nov, 14-20 Nov, 21 Nov-6 Dec]
  // skill: one skill. reel / ten / month: editing service packages.
  // Set from what each market already pays (freelance reel rates, creator template packs), Nov 2026.
  const PRICES = {
    USD: { pack: [29, 39, 49],     skill: 7,  reel: 39,  ten: 299,  month: 799 },
    CAD: { pack: [39, 49, 65],     skill: 9,  reel: 49,  ten: 399,  month: 1049 },
    GBP: { pack: [24, 29, 39],     skill: 6,  reel: 29,  ten: 229,  month: 629 },
    EUR: { pack: [27, 35, 45],     skill: 6,  reel: 35,  ten: 279,  month: 749 },
    AUD: { pack: [45, 59, 75],     skill: 10, reel: 59,  ten: 449,  month: 1199 },
    SAR: { pack: [99, 129, 179],   skill: 25, reel: 149, ten: 1099, month: 2799 },
    AED: { pack: [99, 129, 179],   skill: 25, reel: 149, ten: 1099, month: 2799 },
    INR: { pack: [299, 399, 499],  skill: 49, reel: 499, ten: 3999, month: 9999 }
  };

  // Sprint dates (UTC). Pack sales stop at the end of 6 Dec.
  const WEEK2 = Date.UTC(2026, 10, 14), WEEK3 = Date.UTC(2026, 10, 21), CLOSE = Date.UTC(2026, 11, 7);

  const EURO_ZONES = ["Berlin","Paris","Madrid","Rome","Amsterdam","Brussels","Vienna","Dublin","Lisbon","Helsinki",
    "Athens","Luxembourg","Bratislava","Ljubljana","Tallinn","Riga","Vilnius","Malta","Nicosia","Zagreb"];

  // Guess the visitor's currency from their time zone and browser language.
  // No network call and no tracking. Visitors can always change it with the switcher.
  function detect() {
    const saved = localStorage.getItem("cuttit_currency");
    if (saved && PRICES[saved]) return saved;
    const tz = (Intl.DateTimeFormat().resolvedOptions().timeZone || "");
    const region = ((navigator.language || "").split("-")[1] || "").toUpperCase();
    if (/^Asia\/(Kolkata|Calcutta)$/.test(tz) || region === "IN") return "INR";
    if (tz === "Asia/Riyadh" || region === "SA") return "SAR";
    if (/^Asia\/(Dubai|Muscat)$/.test(tz) || region === "AE") return "AED";
    if (/^America\/(Toronto|Vancouver|Edmonton|Winnipeg|Halifax|St_Johns|Regina|Moncton|Whitehorse|Yellowknife|Iqaluit|Glace_Bay|Goose_Bay)$/.test(tz) || region === "CA") return "CAD";
    if (tz === "Europe/London" || region === "GB") return "GBP";
    if (tz.startsWith("Europe/") && EURO_ZONES.includes(tz.split("/")[1])) return "EUR";
    if (tz.startsWith("Australia/") || region === "AU") return "AUD";
    return "USD";
  }

  function format(cur, amount) {
    return new Intl.NumberFormat(cur === "INR" ? "en-IN" : "en", {
      style: "currency", currency: cur, maximumFractionDigits: 0, currencyDisplay: cur === "USD" ? "narrowSymbol" : "symbol"
    }).format(amount);
  }

  function week(now = Date.now()) { return now < WEEK2 ? 0 : now < WEEK3 ? 1 : 2; }
  function packOpen(now = Date.now()) { return now < CLOSE; }

  function price(cur, item, now) {
    const p = PRICES[cur][item];
    return Array.isArray(p) ? p[week(now)] : p;
  }

  return { PRICES, detect, format, price, week, packOpen, currencies: Object.keys(PRICES) };
})();
