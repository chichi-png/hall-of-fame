#!/usr/bin/env python3
"""
Import + optimize the reputation tier character cards into the Hall of Fame.

Source = the "Tier Cards characters" folder (5 character subfolders, 25 PNGs total),
maintained by Konsti. Filenames are inconsistent across folders, so this normalizes
them to assets/tier-cards/{character}/{tier}.png (tier in aplus|a|b|c|d).

Usage:
    python import-tier-cards.py "/path/to/Tier Cards characters"

No source path is hardcoded (portable-paths rule). Requires Pillow.
"""
import sys, os, re, glob
from PIL import Image

CHARACTERS = ["hunter", "mage", "paladin", "samurai", "shaman"]
TARGET_PX = 760          # spotlight art — display ~340px, 760 covers retina
THUMB_PX = 320           # rankings compact card — display ~116px, 320 covers retina
OUT_ROOT = os.path.join(os.path.dirname(__file__), "assets", "tier-cards")


def detect_tier(stem: str, character: str) -> str | None:
    """Strip the character name out of the filename; what's left is the tier token."""
    rest = stem.lower().replace(character, "")
    rest = rest.replace("_", " ").replace(" ", "")
    if rest in ("a+", "aplus"):
        return "aplus"
    if rest in ("a", "b", "c", "d"):
        return rest
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit('usage: python import-tier-cards.py "<Tier Cards characters dir>"')
    src = sys.argv[1]
    if not os.path.isdir(src):
        sys.exit(f"source dir not found: {src}")

    total = 0
    for character in CHARACTERS:
        # match folder case-insensitively
        folder = next((d for d in os.listdir(src)
                       if d.lower() == character and os.path.isdir(os.path.join(src, d))), None)
        if not folder:
            print(f"!! no folder for {character}")
            continue
        out_dir = os.path.join(OUT_ROOT, character)
        os.makedirs(out_dir, exist_ok=True)
        found = {}
        for path in glob.glob(os.path.join(src, folder, "*.png")):
            stem = os.path.splitext(os.path.basename(path))[0]
            tier = detect_tier(stem, character)
            if not tier:
                print(f"   ? could not classify {os.path.basename(path)}")
                continue
            found[tier] = path
        for tier in ("aplus", "a", "b", "c", "d"):
            if tier not in found:
                print(f"   !! {character} missing tier {tier}")
                continue
            base = Image.open(found[tier]).convert("RGB")
            # full-size spotlight art
            out = os.path.join(out_dir, f"{tier}.png")
            base.resize((TARGET_PX, TARGET_PX), Image.LANCZOS).save(out, "PNG", optimize=True)
            # lightweight thumbnail for the rankings compact cards
            thumb = os.path.join(out_dir, f"{tier}-thumb.png")
            base.resize((THUMB_PX, THUMB_PX), Image.LANCZOS).save(thumb, "PNG", optimize=True)
            kb = round(os.path.getsize(out) / 1024)
            tkb = round(os.path.getsize(thumb) / 1024)
            print(f"   {character}/{tier}.png  {kb}KB  (+thumb {tkb}KB)")
            total += 1
    print(f"\ndone — {total}/25 cards imported to {OUT_ROOT}")


if __name__ == "__main__":
    main()
