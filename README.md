# Altcoinist Hall of Fame

Public showcase of the top of Altcoinist's Inner Circle — proven callers ranked by
**reputation**, not referrals. A curated highlight reel that lives outside the mini app
and is built to be shared on X.

Two jobs:
1. **Flex.** Members share their card + rep on X. Status, exclusivity, social currency.
2. **Pull.** Viewers click a shared card, land on the Hall, get pulled into the network.

## Deployment

**Repo:** https://github.com/chichi-png/hall-of-fame — auto-deploys to **Vercel** on push to `master`.
Routing (clean URLs, rewrites, redirects) is in `vercel.json`.

**Live:** https://altcoinist-affiliate.vercel.app

**Routes:**
| URL | Page |
|---|---|
| `/` | Hall of Fame — hero + top-3 podium |
| `/rankings` | Full circle, ranked by rep (cards/table, all-time/weekly/monthly) + tier ladder |
| `/chains` | Filter by chain (SOL / ETH / BASE / SUI) |
| `/reach` | Sorted by X followers |
| `/calls` | Best winning calls, last 30 days |
| `/about` | What the Hall is vs the mini app |
| `/c/{handle}` | Individual member profile + Share-on-X |

## Structure

```
hall-of-fame/
├── index.html             # landing (/)
├── rankings.html chains.html reach.html calls.html about.html
├── profile.html           # dynamic /c/{handle} fallback (client-renders from hall-data.json)
├── c/{handle}.html        # pre-generated per-member pages (baked-in og: tags) — see below
├── styles/hall.css        # shared design system (one source of truth)
├── hall-data.json         # DATA SOURCE for every page (members + calls)
├── avatars/               # member profile pictures
├── assets/
│   ├── og-hall.png        # generic share card (og:image for non-profile pages)
│   ├── cards/{handle}.png # per-member share cards
│   └── tier-cards/{character}/{tier}.png  # reputation character art (5 chars × 5 tiers)
├── generate-og-card.py    # regenerates all share cards + c/ pages from hall-data.json
├── import-tier-cards.py   # imports + optimizes the 25 tier cards from Konsti's source folder
└── vercel.json
```

## Data

`hall-data.json` is the single source of truth — every page fetches it client-side.

```jsonc
{
  "meta": { "verifiedAplusCount": 3, "cohortSize": 42, "lastRefresh": "W22", ... },
  "athletes": [
    { "handle": "@rbthreek", "avatar": "avatars/rbthreek.jpg", "character": "samurai",
      "chain": "sol", "repTier": "A+", "repScore": 87, "repWeekly": 91, "repMonthly": 88,
      "repPeak": 94, "vol": "$12.4M", "followers": "128K" }
  ],
  "calls": [ { "chain": "sol", "ticker": "$BONK", "caller": "@rbthreek", "entry": "...", "pnl": 248, "time": "5d" } ]
}
```

> **Currently mock data.** Real rep scores come from Conor's reputation system (not live yet).
> When it ships, refresh `hall-data.json`, then regenerate share assets (below).

## Share cards (Open Graph)

When a link is shared on X / Telegram, the crawler reads the page's `og:image`. Two layers:

- **Non-profile pages** → generic `assets/og-hall.png`.
- **Profiles** → each `/c/{handle}` serves a pre-generated static page (`c/{handle}.html`) whose
  `og:` tags point at that member's card (`assets/cards/{handle}.png`). Static files are matched
  before the `/c/:handle` rewrite, so these win; the dynamic `profile.html` stays as the fallback
  for handles not pre-generated.

**Regenerate after any data change:**

```bash
python generate-og-card.py
```

Rebuilds `og-hall.png`, every `assets/cards/{handle}.png`, and every `c/{handle}.html` from
`hall-data.json`. Requires Pillow (`pip install Pillow`).

## Adding / refreshing a member

1. Add their picture to `avatars/{handle}.jpg`.
2. Add / edit their entry in `hall-data.json`.
3. Run `python generate-og-card.py`.
4. Commit + push (see below).

## Design

Black canvas, Inter for headings, JetBrains Mono for labels. A+ tier gets a verified ring +
badge (mirrors the X badge). Edit design tokens once in `styles/hall.css` and every page updates.

**Tier colors mirror the mini app** (locked — see `../../docs/reputation-tier-colors.md`):

| Tier | Color | Hex |
|---|---|---|
| A+ Legendary | mint (brand green, A+ only) | `#39F590` |
| A Elite | turquoise | `#2EE6D6` |
| B Respected | royal blue | `#1E88FF` |
| C Trusted | steel blue | `#6E9BFF` |
| D Newcomer | pearl white | `#F5F5F7` |

**Reputation character art.** The home spotlight (top-3 podium) renders each member's tier
character as the focal image. 5 classes (hunter / mage / paladin / samurai / shaman) × 5 tiers,
same character at every tier — only color + glow intensity change up the ladder. Each athlete's
`character` field in `hall-data.json` picks the class; `repTier` picks the tier variant. The art
is currently mock-assigned per member; the real class comes from the mini-app reputation system
when it ships.

**Importing tier cards** (when Konsti updates the source set):

```bash
python import-tier-cards.py "/path/to/Tier Cards characters"
```

Normalizes the inconsistent source filenames, resizes to web size, and writes
`assets/tier-cards/{character}/{tier}.png`. Requires Pillow.

## Push (dual-push)

This is a git submodule of `1-affiliates`. After any change:
1. Commit + push here (deploys to Vercel).
2. Bump the submodule pointer in the parent `1-affiliates` repo and push that too.
