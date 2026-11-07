// cuttit regional pricing.
// Prices are set per currency as round local numbers (not live conversions).
// Edit this table to change prices. The checkout must charge the same amounts:
// set the same per-currency prices in the payment provider.

window.CUTTIT_PRICING = (() => {
  // pack: price by sprint week [7-13 Nov, 14-20 Nov, 21 Nov-6 Dec]
  // skill: one skill. reel / ten / month: editing service packages.
  const PRICES = {
    USD: { pack: [19, 25, 29],    skill: 5,  reel: 29,  ten: 199,  month: 499 },
    CAD: { pack: [25, 35, 39],    skill: 7,  reel: 39,  ten: 269,  month: 679 },
    GBP: { pack: [15, 19, 23],    skill: 4,  reel: 23,  ten: 159,  month: 399 },
    EUR: { pack: [17, 23, 27],    skill: 5,  reel: 27,  ten: 179,  month: 459 },
    AUD: { pack: [29, 39, 45],    skill: 8,  reel: 45,  ten: 299,  month: 759 },
    SAR: { pack: [69, 89, 109],   skill: 19, reel: 109, ten: 749,  month: 1879 },
    AED: { pack: [69, 89, 109],   skill: 19, reel: 109, ten: 729,  month: 1829 },
    INR: { pack: [299, 399, 499], skill: 49, reel: 299, ten: 1999, month: 4999 }
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
