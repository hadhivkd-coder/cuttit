"""Build one themed product page per skill.

Usage: python pages/build.py            (all products in pages/products/*.json)
       python pages/build.py byline     (one product)

For each product: site/<slug>/index.html (from templates/product.html) and site/<slug>/og.jpg (1200x630 share image).
The product folder must already contain its demo video and poster (site/<slug>/demo.mp4, poster.jpg).
Site settings (domain, Meta Pixel ID) live in pages/site.json.
"""
import json, os, sys
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def hex_rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def og_image(p, out_path):
    """1200x630 share card: product name, one-line promise, price, and the demo poster in a phone frame."""
    th = p["theme"]; W, H = 1200, 630
    bg = hex_rgb(th["bg"]); ink = hex_rgb(th["ink"]); muted = hex_rgb(th["muted"]); acc = hex_rgb(th["accent"])
    im = Image.new("RGB", (W, H), bg)
    glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).ellipse((700, -40, 1260, 680), fill=70)
    im.paste(Image.new("RGB", (W, H), acc), (0, 0), glow.filter(ImageFilter.GaussianBlur(120)))
    d = ImageDraw.Draw(im)
    disp = ImageFont.truetype(os.path.join(HERE, "fonts", th["og_display_font"]), 150)
    sans = ImageFont.truetype(os.path.join(HERE, "fonts", th["og_sans_font"]), 30)
    small = ImageFont.truetype(os.path.join(HERE, "fonts", th["og_sans_font"]), 22)
    d.text((70, 120), p["eyebrow"].upper(), font=small, fill=acc)
    d.text((62, 300), p["name"], font=disp, fill=ink, anchor="ls")
    y = 360
    words, line = p["og_description"].split(), ""
    for w in words:
        test = (line + " " + w).strip()
        if d.textlength(test, font=sans) > 560:
            d.text((70, y), line, font=sans, fill=muted); y += 44; line = w
        else:
            line = test
    if line: d.text((70, y), line, font=sans, fill=muted); y += 44
    d.rounded_rectangle((70, y + 26, 70 + d.textlength(p["price_label"], font=sans) + 48, y + 86), 16, fill=ink)
    d.text((94, y + 56), p["price_label"], font=sans, fill=bg, anchor="lm")
    poster = Image.open(os.path.join(ROOT, "site", p["slug"], p["poster"])).convert("RGB")
    ph, pw = 540, int(540 * 9 / 16)
    poster = poster.resize((pw, ph))
    frame = Image.new("RGB", (pw + 20, ph + 20), (30, 30, 36))
    m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pw - 1, ph - 1), 26, fill=255)
    fm = Image.new("L", frame.size, 0); ImageDraw.Draw(fm).rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), 34, fill=255)
    frame.paste(poster, (10, 10), m)
    x0, y0 = 840, (H - frame.height) // 2
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle((x0 + 10, y0 + 24, x0 + frame.width + 10, y0 + frame.height + 24), 34, fill=160)
    im.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(24)))
    im.paste(frame, (x0, y0), fm)
    im.save(out_path, quality=88)


def build(slug=None):
    site = json.load(open(os.path.join(HERE, "site.json")))
    env = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")), autoescape=True)
    tpl = env.get_template("product.html")
    files = sorted(f for f in os.listdir(os.path.join(HERE, "products")) if f.endswith(".json"))
    for f in files:
        p = json.load(open(os.path.join(HERE, "products", f)))
        if slug and p["slug"] != slug: continue
        outdir = os.path.join(ROOT, "site", p["slug"]); os.makedirs(outdir, exist_ok=True)
        url = (site.get("base_url") or "") + "/" + p["slug"]
        jsonld = {
            "@context": "https://schema.org", "@type": "Product", "name": p["name"], "description": p["seo_description"],
            "image": (site.get("base_url") or "") + f"/{p['slug']}/{p['og_image']}", "brand": {"@type": "Brand", "name": site["brand"]},
            "offers": {"@type": "Offer", "price": str(p["price"]), "priceCurrency": p["currency"],
                       "availability": "https://schema.org/InStock", "url": url},
        }
        html = tpl.render(p=p, site=site, jsonld=json.dumps(jsonld, ensure_ascii=False))
        open(os.path.join(outdir, "index.html"), "w").write(html)
        og_image(p, os.path.join(outdir, p["og_image"]))
        print("built", p["slug"], "->", os.path.relpath(outdir, ROOT))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
