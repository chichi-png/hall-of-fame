"""
Generate Open Graph share assets for the Hall of Fame.

Outputs:
  assets/og-hall.png            generic branded card (og:image for non-profile pages)
  assets/cards/{handle}.png     per-member flex card (avatar + tier + rep + rank)
  c/{handle}.html               per-member profile page with baked-in og: tags

Why c/{handle}.html: crawlers (X, Telegram) read og:image from static HTML and
don't run JS, so per-member share cards need per-URL meta. Vercel serves these
static files for /c/{handle} (filesystem wins over the rewrite); the dynamic
profile.html stays as the fallback for handles not pre-generated.

Brand: black canvas, single green accent (#38FF93). Run: `python generate-og-card.py`
Re-run whenever hall-data.json changes (e.g. real rep scores land).
"""
import json
import os
import re
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (56, 255, 147)        # #38FF93
PAD = 80
SITE = "https://altcoinist-affiliate.vercel.app"

F_BOLD = "C:/Windows/Fonts/arialbd.ttf"
F_REG = "C:/Windows/Fonts/arial.ttf"
F_MONO = "C:/Windows/Fonts/consola.ttf"

CHAIN = {"sol": "SOL", "eth": "ETH", "base": "BASE", "sui": "SUI"}
TIER_COLOR = {
    "A+": GREEN,
    "A": (255, 255, 255),
    "B": (255, 255, 255, 178),
    "C": (255, 255, 255, 140),
    "D": (255, 255, 255, 77),
}


def font(path, size):
    return ImageFont.truetype(path, size)


def draw_tracked(draw, xy, text, fnt, fill, tracking=6):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x


def tracked_width(draw, text, fnt, tracking=6):
    return sum(draw.textlength(c, font=fnt) + tracking for c in text)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def base_canvas():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([18, 18, W - 18, H - 18], outline=(56, 255, 147, 40), width=1)
    for r, a in [(420, 10), (320, 12), (220, 16), (130, 20)]:
        d.ellipse([W - r + 240, -r + 120, W + r + 120, r + 120], fill=(56, 255, 147, a))
    return img, d


def eyebrow(d, label):
    d.line([PAD, 92, PAD + 26, 92], fill=GREEN, width=2)
    draw_tracked(d, (PAD + 40, 80), label, font(F_MONO, 22), GREEN, tracking=5)


def footer_brand(d):
    fb = font(F_BOLD, 30)
    bx = PAD
    d.text((bx, H - 92), "altcoinist", font=fb, fill=WHITE)
    bx += d.textlength("altcoinist", font=fb)
    d.text((bx, H - 92), ".", font=fb, fill=GREEN)


def circle_avatar(path, size, ring=False):
    """Return an RGBA avatar cropped to a circle, with optional green ring."""
    try:
        av = Image.open(path).convert("RGB")
    except Exception:
        av = Image.new("RGB", (size, size), (26, 58, 42))
    # center-crop to square
    w, h = av.size
    s = min(w, h)
    av = av.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(av, (0, 0), mask)
    if ring:
        ImageDraw.Draw(out).ellipse([1, 1, size - 2, size - 2], outline=GREEN, width=5)
    return out


def verified_badge(d, cx, cy, r=20):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN, outline=(0, 0, 0), width=3)
    d.line([(cx - 8, cy + 1), (cx - 2, cy + 8)], fill=(0, 0, 0), width=3)
    d.line([(cx - 2, cy + 8), (cx + 9, cy - 7)], fill=(0, 0, 0), width=3)


# ---------- generic card ----------
def generic_card():
    img, d = base_canvas()
    eyebrow(d, "THE HALL OF FAME")
    head_font = font(F_BOLD, 88)
    y = 200
    for ln in wrap(d, "Reputation is the only flex.", head_font, W - 2 * PAD):
        d.text((PAD, y), ln, font=head_font, fill=WHITE)
        y += 96
    d.text((PAD, y + 14), "Ranked by rep. Proven on-chain.", font=font(F_BOLD, 40), fill=GREEN)
    footer_brand(d)
    d.text((PAD + 200, H - 90), " the inner circle", font=font(F_REG, 26), fill=(255, 255, 255, 130))
    pill, pf = "EXCLUSIVE", font(F_MONO, 20)
    pw = tracked_width(d, pill, pf, 5)
    px1 = W - PAD - pw - 36
    d.rounded_rectangle([px1, H - 100, W - PAD, H - 60], radius=20, outline=(255, 255, 255, 90), width=1)
    draw_tracked(d, (px1 + 18, H - 92), pill, pf, (255, 255, 255, 150), tracking=5)
    img.save("assets/og-hall.png", "PNG")
    print("wrote assets/og-hall.png")


# ---------- per-member card ----------
def member_card(m, rank):
    img, d = base_canvas()
    verified = m["repTier"] == "A+"
    eyebrow(d, "ALTCOINIST · INNER CIRCLE")

    av_size = 200
    av_x, av_y = PAD, 150
    av = circle_avatar(m["avatar"], av_size, ring=verified)
    img.paste(av, (av_x, av_y), av)
    if verified:
        verified_badge(d, av_x + av_size - 24, av_y + av_size - 24)

    tx = av_x + av_size + 44
    handle = m["handle"]
    hf = font(F_BOLD, 60)
    d.text((tx, av_y + 18), handle, font=hf, fill=WHITE)
    if verified:
        hx = tx + d.textlength(handle, font=hf) + 26
        verified_badge(d, int(hx + 18), int(av_y + 18 + 34), r=18)
    label = "VERIFIED CALLER" if verified else "INNER CIRCLE MEMBER"
    draw_tracked(d, (tx + 2, av_y + 100), label, font(F_MONO, 22), GREEN, tracking=4)
    draw_tracked(d, (tx + 2, av_y + 138), "REPUTATION IS THE ONLY FLEX",
                 font(F_MONO, 18), (255, 255, 255, 120), tracking=3)

    # stat strip: TIER | REP | CHAIN | RANK
    cells = [
        ("REP TIER", m["repTier"], TIER_COLOR.get(m["repTier"], WHITE)),
        ("REP", str(m["repScore"]), WHITE),
        ("CHAIN", CHAIN.get(m["chain"], m["chain"].upper()), WHITE),
        ("RANK", f"#{rank}", GREEN if rank <= 3 else WHITE),
    ]
    strip_y = 430
    cw = (W - 2 * PAD) / 4
    d.line([PAD, strip_y - 24, W - PAD, strip_y - 24], fill=(255, 255, 255, 30), width=1)
    for i, (lab, val, col) in enumerate(cells):
        cx = PAD + cw * i
        if i:
            d.line([cx, strip_y - 6, cx, strip_y + 96], fill=(255, 255, 255, 25), width=1)
        draw_tracked(d, (cx + 24, strip_y), lab, font(F_MONO, 18), (255, 255, 255, 90), tracking=3)
        d.text((cx + 24, strip_y + 34), val, font=font(F_BOLD, 54), fill=col)

    footer_brand(d)
    rtxt = f"ranked #{rank} in the circle"
    rf = font(F_REG, 24)
    d.text((W - PAD - d.textlength(rtxt, font=rf), H - 90), rtxt, font=rf, fill=(255, 255, 255, 130))

    os.makedirs("assets/cards", exist_ok=True)
    slug = handle.replace("@", "")
    img.save(f"assets/cards/{slug}.png", "PNG")
    return slug


# ---------- per-member HTML ----------
def member_html(template, m, rank, slug):
    verified = m["repTier"] == "A+"
    title = f"{m['handle']} · {m['repTier']} · Altcoinist Inner Circle"
    if verified:
        desc = f"Verified {m['repTier']}. Rep {m['repScore']}, ranked #{rank} in the circle. Reputation is the only flex."
    else:
        desc = f"Tier {m['repTier']}, rep {m['repScore']}, ranked #{rank} in the circle."
    card = f"{SITE}/assets/cards/{slug}.png"

    html = template.replace(f"{SITE}/assets/og-hall.png", card)
    html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1)
    html = re.sub(r'(property="og:title" content=").*?(")', rf"\g<1>{title}\g<2>", html, count=1)
    html = re.sub(r'(property="og:description" content=").*?(")', rf"\g<1>{desc}\g<2>", html, count=1)

    os.makedirs("c", exist_ok=True)
    with open(f"c/{slug}.html", "w", encoding="utf-8") as f:
        f.write(html)


def main():
    generic_card()
    data = json.load(open("hall-data.json", encoding="utf-8"))
    members = sorted(data["athletes"], key=lambda a: a["repScore"], reverse=True)
    template = open("profile.html", encoding="utf-8").read()
    for rank, m in enumerate(members, 1):
        slug = member_card(m, rank)
        member_html(template, m, rank, slug)
    print(f"wrote {len(members)} member cards + pages")


if __name__ == "__main__":
    main()
