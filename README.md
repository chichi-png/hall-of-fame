# Altcoinist Affiliate Leaderboard

Public-facing leaderboard showcasing top-performing Altcoinist affiliates.

## 🚀 Deployment

**Repository:** https://github.com/chichi-png/hall-of-fame

Deployed automatically via **Vercel** from the `master` branch. Routing is defined in `vercel.json` (clean URLs, rewrites, redirects). Set / confirm the production domain in the Vercel dashboard.

**Routes:**
- `/` and `/hall-of-fame` — the Hall of Fame (ranked wall + rooms)
- `/cohort` — full ranked roster
- `/c/{handle}` — individual member profile (Share-on-X surface)
- `/leaderboard` — permanent redirect to `/hall-of-fame` (legacy)

## 📁 Structure

```
altcoinist-leaderboard/
├── index.html                    # ⚠️ IMPORTANT: Door entrance page (DO NOT DELETE!)
├── leaderboard.html              # Main single-page app (all views)
├── assets/
│   └── images/
│       └── affiliates/           # 35 affiliate profile pictures
├── functions/                    # Utility functions
├── .gitignore
└── README.md
```

**⚠️ CRITICAL FILES - DO NOT DELETE:**
- `index.html` - Landing page with door animation and "ACCESS GRANTED" screen
- `leaderboard.html` - Main leaderboard application

## 🎨 Features

- **🚪 Command Center Entrance** - Immersive door animation with security scanner (index.html)
- **Single-Page App** - All views (All-Time, Weekly, Monthly, Affiliates) in one page
- **Top 3 Podium** - Epic reveal animation for champions
- **Paginated Rankings** - 10 affiliates per page with navigation
- **Real Profile Pictures** - 35 actual Altcoinist affiliates
- **Responsive Design** - Works on desktop and mobile
- **Dark Cyber Theme** - Neon accents and smooth animations

## 📊 Data Structure

All rankings use the same data structure with correct field names:

```javascript
{
    rank: 1,
    name: 'rb3k',
    handle: '@rbthreek',
    avatar: 'RB',
    tweetScore: 60,           // Tweet performance score
    botActivityScore: 3770,   // Bot activity score
    total: 3830,              // Total score (sum of above)
    imgSrc: 'assets/images/affiliates/rbthreek.jpg',
    profileUrl: 'https://x.com/rbthreek',
    tgHandle: '@rbthreek'
}
```

**Data Location:**
- All-Time: `window.affiliatesData` (~line 1465)
- Weekly: `window.DEMO_WEEKLY_DATA` (~line 1857)
- Monthly: `window.DEMO_MONTHLY_DATA` (~line 2575)

**Sync Data:** Run `python sync-leaderboard-data.py` to automatically fetch scores from Notion and update the HTML file

```bash
cd tools/affiliate-leaderboard
python sync-leaderboard-data.py
```

This script:
- Fetches weekly & monthly scores from Notion (Tweet Scores + Bot Activity databases)
- Matches scores with affiliates by X handle
- Automatically updates `leaderboard.html` with real data
- Preserves all metadata (names, avatars, profile URLs)
- Re-ranks affiliates by total score

## 🔄 Navigation

- **All-Time Rankings:** Default view on load
- **Weekly Rankings:** Click "📊 Weekly Rankings" button
- **Monthly Rankings:** Click "📈 Monthly Rankings" button
- **Affiliates Directory:** Click "🎯 Affiliates" button

All navigation is handled via JavaScript - no page reloads.

## 🖼️ Adding New Affiliates

1. Add profile picture to `assets/images/affiliates/`
2. Update `weeklyData` and `monthlyData` arrays in `leaderboard.html`
3. Commit and push to trigger GitHub Pages deployment

## 📝 Notes

- **40 affiliates total** (as of 2026-04-01)
- **Pagination:** 10 per page = 4 pages (10, 10, 10, 10)
- **Data Source:** Real scores from Notion (Tweet Scores + Bot Activity Scores databases)
- **Modular:** Code split into external JS/CSS files for maintainability
