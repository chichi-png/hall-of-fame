"""
Refresh the Hall of Fame from a fresh v19.8 caller-reputation board.

One command: read a board -> map internal caller names to Hall X-handles via
caller-map.json -> update the score fields in hall-data.json -> regenerate all
share cards + profile pages.

Score fields it updates per scored member: repScore (= display_score),
calls4x (= n_4x), calls (= all-time deduped call count). Everything else
(chain, character, avatar, followers) is left untouched — the board doesn't
carry those.

Board sources (pick one):
  --csv  path/to/v198_board.csv      canonical output of score_v198.py
                                     (columns: caller, n_wide, n_4x, display_score, ...)
  --html path/to/v19.8-leaderboard.html   the handover leaderboard table

Safety: prints a full change summary (up/down/new/dropped + any board callers
that aren't mapped to a Hall handle) and does NOT touch a member's scored state
unless --apply is passed. Without --apply it's a dry run.

Run:
  python refresh-hall.py --html "<path-to>/v19.8-leaderboard.html"          # preview
  python refresh-hall.py --csv  "<path-to>/v198_board.csv" --apply          # write + regenerate

Needs Pillow only for the regeneration step (same as generate-og-card.py).
"""
import argparse
import csv
import html as ihtml
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "hall-data.json")
MAP = os.path.join(HERE, "caller-map.json")


def load_board_csv(path):
    """score_v198.py output. Returns {caller: {display, n4x, calls}}."""
    board = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            caller = (row.get("caller") or "").strip()
            if not caller:
                continue
            board[caller] = {
                "display": _num(row.get("display_score")),
                "n4x": _int(row.get("n_4x")),
                # all-time deduped call count drives the Hall "calls" stat
                "calls": _int(row.get("n_wide") or row.get("n")),
            }
    return board


def load_board_html(path):
    """Parse the handover leaderboard table. Each summary row is prefixed by a
    <span class='toggle'> marker; cells after it are rank, caller, call/100,
    scan/5, score/100 (display), raw, ... , n calls/scans, n 4x+."""
    raw = open(path, encoding="utf-8").read()
    board = {}
    for chunk in raw.split("<span class='toggle'>")[1:]:
        head = re.split(r"<table", chunk, maxsplit=1)[0]
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", head, re.S | re.I)
        clean = [ihtml.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in cells]
        if len(clean) < 12:
            continue
        try:
            ri = next(i for i, v in enumerate(clean) if v.isdigit())  # rank cell
        except StopIteration:
            continue
        if ri + 10 >= len(clean):
            continue
        caller = clean[ri + 1]
        display = _num(clean[ri + 4])
        if not caller or display is None:
            continue
        ncalls_cell = clean[ri + 9]
        m = re.search(r"\((\d+)\s*all-time\)", ncalls_cell) or re.match(r"(\d+)", ncalls_cell)
        board[caller] = {
            "display": display,
            "n4x": _int(clean[ri + 10]),
            "calls": int(m.group(1)) if m else None,
        }
    return board


def _num(v):
    try:
        return round(float(str(v).strip()), 1)
    except (TypeError, ValueError):
        return None


def _int(v):
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description="Refresh the Hall from a v19.8 board.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--csv", help="v198_board.csv from score_v198.py")
    g.add_argument("--html", help="v19.8-leaderboard.html handover file")
    ap.add_argument("--apply", action="store_true",
                    help="write hall-data.json + regenerate. Without it, dry run.")
    ap.add_argument("--label", default=None,
                    help="lastRefreshLabel for meta (e.g. 'jun 18'). Defaults to keeping current.")
    args = ap.parse_args()

    board = load_board_csv(args.csv) if args.csv else load_board_html(args.html)
    print(f"board: {len(board)} scored callers loaded from {args.csv or args.html}")

    cmap = json.load(open(MAP, encoding="utf-8"))
    data = json.load(open(DATA, encoding="utf-8"))
    handle_to_internal = {c["handle"]: c["internalName"] for c in cmap["callers"] if c.get("internalName")}
    unverified = [c["handle"] for c in cmap["callers"] if c.get("internalName") and not c.get("verified")]

    athletes = {a["handle"]: a for a in data["athletes"]}
    ups, downs, newly, dropped, missing_map = [], [], [], [], []

    for handle, internal in handle_to_internal.items():
        a = athletes.get(handle)
        if not a:
            continue
        row = board.get(internal)
        if row is None:
            if a.get("scored"):
                dropped.append((handle, internal, a.get("repScore")))
            continue
        old = a.get("repScore")
        was_scored = bool(a.get("scored"))
        new = {"scored": True, "repScore": row["display"], "calls4x": row["n4x"], "calls": row["calls"]}
        if args.apply:
            a.update(new)
        if not was_scored:
            newly.append((handle, row["display"]))
        elif old is not None and row["display"] is not None:
            if row["display"] > old:
                ups.append((handle, old, row["display"]))
            elif row["display"] < old:
                downs.append((handle, old, row["display"]))

    # board callers not mapped to any Hall handle (may be affiliates worth adding)
    mapped_internal = set(handle_to_internal.values())
    for caller in board:
        if caller not in mapped_internal:
            missing_map.append(caller)

    print(f"\n  ↑ up:      {len(ups)}")
    for h, o, n in ups: print(f"      {h:<18} {o} -> {n}")
    print(f"  ↓ down:    {len(downs)}")
    for h, o, n in downs: print(f"      {h:<18} {o} -> {n}")
    print(f"  + newly scored: {len(newly)}")
    for h, n in newly: print(f"      {h:<18} -> {n}")
    print(f"  - dropped off board (still on Hall, NOT auto-unscored): {len(dropped)}")
    for h, i, s in dropped: print(f"      {h:<18} ({i}) was {s}")
    if unverified:
        print(f"\n  ! {len(unverified)} mapped callers still verified=false in caller-map.json "
              f"(used anyway): {', '.join(unverified[:6])}{'...' if len(unverified) > 6 else ''}")
    print(f"\n  ? board callers not in the map ({len(missing_map)}) — assign in caller-map.json "
          f"if any are Hall affiliates:")
    print("     " + ", ".join(missing_map))

    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to update + regenerate.")
        return

    scored_count = sum(1 for a in data["athletes"] if a.get("scored"))
    data["meta"]["scoredCount"] = scored_count
    if args.label:
        data["meta"]["lastRefreshLabel"] = args.label
    json.dump(data, open(DATA, "w", encoding="utf-8"), indent=2)
    print(f"\nwrote hall-data.json ({scored_count} scored). regenerating share assets...")
    subprocess.run([sys.executable, os.path.join(HERE, "generate-og-card.py")], cwd=HERE, check=True)
    print("done.")


if __name__ == "__main__":
    main()
