# Hall of Fame — auto-refresh pipeline (scope)

**Status:** scoped, not built. Blocked on Conor's reputation system going live (today the data is a manual v19.8 handover from 2026-05-29; `repTier` is still null).

## Problem

`hall-data.json` is hand-updated. Every time scores move, someone has to edit the JSON, run `generate-og-card.py`, and dual-push. That makes the Hall a snapshot, not a living asset. The whole "ranked by rep, refreshed weekly" promise on the site depends on a manual chore that won't happen weekly.

## Goal

When the reputation system is live, the Hall refreshes itself on a schedule with zero manual steps.

## Pipeline (4 steps)

1. **Pull** the current caller scores + roster from source (Conor's reputation system / PostHog leaderboard insight, TBD which is canonical when it ships).
2. **Build** `hall-data.json` — map source rows → the schema (`handle`, `avatar`, `scored`, `repScore`, `repTier`, `calls4x`, `calls`, `followers`, chain) + `meta` (rosterSize, scoredCount, lastRefresh, lastRefreshLabel). Reuse existing avatars in `avatars/`; flag any new handle with no avatar.
3. **Regenerate** share assets — run `generate-og-card.py` (rebuilds `og-hall.png`, 48+ `assets/cards/*.png`, 48+ `c/*.html`).
4. **Publish** — commit + push the submodule (Vercel auto-deploys), then bump the pointer in `1-affiliates`, then `marketing-brain`.

## Open questions (resolve before building)

- **Source of truth:** Conor's rep system API, or a PostHog insight? Need the endpoint + field names.
- **Cadence:** weekly (matches the "refreshed weekly" copy) vs daily. Weekly is enough.
- **Tier bands:** wire `repTier` (A+/A/B/C/D) once the team locks score→grade bands. Until then keep the green-ring "scored" treatment.
- **New avatars:** auto-fetch from X, or flag for manual add? (See the Hall of Fame pfp workflow.)
- **Run location:** the affiliate report cron is currently blocked (no PostHog reach from remote agent, no GitHub App on the repo) — same blockers likely apply here. May need to run from ChiChi's machine until eng unblocks.

## Shape

A single `refresh.py` orchestrating steps 1–3, plus the dual-push. Trigger: scheduled job (cron / remote agent) once the source + run-location questions are answered. Until then, the manual path (edit JSON → `generate-og-card.py` → dual-push) stays.
