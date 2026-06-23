"""
Generate Open Graph share assets for the Hall of Fame.

Outputs:
  assets/og-hall.png            generic branded card (og:image for non-profile pages)
  assets/cards/{handle}.png     per-member flex card (avatar + rep + rank + stats)
  c/{handle}.html               per-member profile page with baked-in og: tags

Why c/{handle}.html: crawlers (X, Telegram) read og:image from static HTML and
don't run JS, so per-member share cards need per-URL meta. Vercel serves these
static files for /c/{handle} (filesystem wins over the rewrite); the dynamic
profile.html stays as the fallback for handles not pre-generated.

Schema: v19.8 reputation snapshot. repScore (0-100, floor 40) is the ranking
number; repTier is null until the team locks score->grade bands, so this script
does NOT render letter tiers. Scored callers get the green-ring treatment;
unscored members get a calmer "inner circle member" card. Mirrors profile.html.

Brand: black canvas, single green accent (#38FF93). Run: `python generate-og-card.py`
Re-run whenever hall-data.json changes (e.g. real rep scores land). Needs Pillow.
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


def font(path, size):
    return ImageFont.truetype(path, size)


def fmt_score(v):
    """94.5 -> '94.5', 60.0 -> '60' (match how the JSON number renders on the site)."""
    if v is None:
        return "—"
    return str(int(v)) if float(v).is_integer() else str(v)


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


def circle_avatar(path, size, initials="", ring=False):
    """Circle-cropped avatar with optional green ring. Falls back to initials on a
    dark disc when the file is missing or unreadable (mirrors the site's onerror)."""
    av = None
    if path:
        try:
            av = Image.open(path).convert("RGB")
        except Exception:
            av = None
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    if av is not None:
        w, h = av.size
        s = min(w, h)
        av = av.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((size, size), Image.LANCZOS)
        out.paste(av, (0, 0), mask)
    else:
        disc = Image.new("RGB", (size, size), (20, 28, 24))
        out.paste(disc, (0, 0), mask)
        dd = ImageDraw.Draw(out)
        f = font(F_BOLD, int(size * 0.34))
        tw = dd.textlength(initials, font=f)
        dd.text(((size - tw) / 2, size * 0.3), initials, font=f, fill=(56, 255, 147, 200))
    if ring:
        ImageDraw.Draw(out).ellipse([1, 1, size - 2, size - 2], outline=GREEN, width=5)
    return out


def stat_strip(d, cells):
    """Render an evenly-spaced label/value strip across the card width."""
    strip_y = 430
    cw = (W - 2 * PAD) / len(cells)
    d.line([PAD, strip_y - 24, W - PAD, strip_y - 24], fill=(255, 255, 255, 30), width=1)
    for i, (lab, val, col) in enumerate(cells):
        cx = PAD + cw * i
        if i:
            d.line([cx, strip_y - 6, cx, strip_y + 96], fill=(255, 255, 255, 25), width=1)
        draw_tracked(d, (cx + 24, strip_y), lab, font(F_MONO, 18), (255, 255, 255, 90), tracking=3)
        d.text((cx + 24, strip_y + 34), val, font=font(F_BOLD, 54), fill=col)


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
    scored = bool(m.get("scored"))
    slug = m["handle"].replace("@", "")
    initials = slug[:2].upper()
    eyebrow(d, "ALTCOINIST · INNER CIRCLE")

    av_size = 200
    av_x, av_y = PAD, 150
    av = circle_avatar(m.get("avatar"), av_size, initials=initials, ring=scored)
    img.paste(av, (av_x, av_y), av)

    tx = av_x + av_size + 44
    handle = m["handle"]
    d.text((tx, av_y + 18), handle, font=font(F_BOLD, 60), fill=WHITE)
    label = "RANKED CALLER" if scored else "INNER CIRCLE MEMBER"
    draw_tracked(d, (tx + 2, av_y + 100), label, font(F_MONO, 22), GREEN, tracking=4)
    draw_tracked(d, (tx + 2, av_y + 138), "REPUTATION IS THE ONLY FLEX",
                 font(F_MONO, 18), (255, 255, 255, 120), tracking=3)

    chain_val = CHAIN.get(m.get("chain"), (m.get("chain") or "").upper()) or "—"
    if scored:
        cells = [
            ("REP", fmt_score(m.get("repScore")), GREEN),
            ("RANK", f"#{rank}", GREEN if rank and rank <= 3 else WHITE),
            ("4X+ CALLS", str(m.get("calls4x")) if m.get("calls4x") is not None else "—", WHITE),
            ("CHAIN", chain_val, WHITE),
        ]
    else:
        cells = [
            ("CHAIN", chain_val, WHITE),
            ("FOLLOWERS", m.get("followers") or "—", WHITE),
        ]
    stat_strip(d, cells)

    footer_brand(d)
    rtxt = f"ranked #{rank} in the circle" if scored else "inner circle member"
    rf = font(F_REG, 24)
    d.text((W - PAD - d.textlength(rtxt, font=rf), H - 90), rtxt, font=rf, fill=(255, 255, 255, 130))

    os.makedirs("assets/cards", exist_ok=True)
    img.save(f"assets/cards/{slug}.png", "PNG")
    return slug


# ---------- per-member HTML ----------
def member_html(template, m, rank, slug):
    scored = bool(m.get("scored"))
    if scored:
        title = f"{m['handle']} · rep {fmt_score(m.get('repScore'))} · Altcoinist Inner Circle"
        desc = (f"Ranked #{rank} in the Altcoinist Inner Circle. Rep {fmt_score(m.get('repScore'))}, "
                f"proven on-chain. Reputation is the only flex.")
    else:
        title = f"{m['handle']} · Altcoinist Inner Circle"
        desc = "In the Altcoinist Inner Circle. Reputation, not referrals."
    card = f"{SITE}/assets/cards/{slug}.png"

    html = template.replace(f"{SITE}/assets/og-hall.png", card)
    html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1)
    html = re.sub(r'(property="og:title" content=").*?(")', rf"\g<1>{title}\g<2>", html, count=1)
    html = re.sub(r'(property="og:description" content=").*?(")', rf"\g<1>{desc}\g<2>", html, count=1)
    html = re.sub(r'(name="description" content=").*?(")', rf"\g<1>{desc}\g<2>", html, count=1)

    os.makedirs("c", exist_ok=True)
    with open(f"c/{slug}.html", "w", encoding="utf-8") as f:
        f.write(html)


def main():
    generic_card()
    data = json.load(open("hall-data.json", encoding="utf-8"))
    athletes = data["athletes"]

    # Rank counts among scored callers only, by repScore desc. Unscored have no rank.
    scored = sorted([a for a in athletes if a.get("scored")],
                    key=lambda a: a.get("repScore") or 0, reverse=True)
    rank_of = {a["handle"]: i + 1 for i, a in enumerate(scored)}

    template = open("profile.html", encoding="utf-8").read()
    for m in athletes:
        rank = rank_of.get(m["handle"])
        slug = member_card(m, rank)
        member_html(template, m, rank, slug)
    print(f"wrote {len(athletes)} member cards + pages ({len(scored)} scored, {len(athletes) - len(scored)} unscored)")


if __name__ == "__main__":
    main()
