# Hackathon archive

Contest-week material from the Alpaca AI Trading Agents Hackathon (Aug 31 to
Sep 4, 2026), kept as it was written. Nothing here is needed to run Honest
Odds or to reproduce its forecast scores; for those, start at the
[main README](../../README.md).

| File | What it was |
|---|---|
| `RUNBOOK.md`, `TONIGHT.md`, `TOMORROW.md`, `FRIDAY.md` | Day-by-day operating cards for contest week |
| `COMPLIANCE.md` | Pre-submission checklist against the hackathon rules |
| `PLAYBOOK.md`, `POSTS.md` | Pre-written video, Discord and social posts |
| `video/` | Video scripts, title cards, explainer page and slide deck |
| `Pythia_Cover_Title (2).jpg` | Submission cover image |

The sections below were moved here from the main README. Paths in them are
relative to the repo root.

## Judges: the 60-second path

`pip install -r requirements.txt && python run.py --selftest` — the entire
pipeline runs offline, no keys, and prints a fully gated trade. Then:
`WRITEUP.md` for the numbers, `journal/letters/` for the nightly fund
letters, `scripts/calibrate.py` output for the Brier scores and
`scripts/robustness.py` for how much of them survives removing stale quotes. Everything else
below is for reproducing the week.

## Hackathon compliance

| Requirement | Where |
|---|---|
| Dedicated competition paper account, $100k start | `scripts/setup_account_check.py` verifies both |
| Alpaca Trading API | `pythia/execution.py` — MLEG limit orders via `alpaca-py` |
| MCP server or CLI | `mcp/README.md` — Claude supervises the same account via Alpaca's MCP server |
| Options in every strategy | The only instruments Honest Odds trades are option spreads/longs |
| One-page write-up (AI logic, risk gates, infra) | `WRITEUP.md` — fill in results and submit |

## Operating notes for contest week

- Feed the analyst: keep `notes/macro.md` current — it's injected into every
  assessment verbatim. The Friday NFP print lands 90 minutes before the
  submission deadline; positions held into it settle the contest.
- The indicative options feed is free on paper accounts and is the default.
- MLEG limit orders post at net debit (mid + slippage buffer). Watch the first
  fill; widen `slippage_buffer` if resting unfilled.
- If your paper account's options level is < 3, set `allow_spreads: false`
  (plain long calls/puts) or raise the level in the Alpaca dashboard.
- Thursday ~3:00-3:45 pm ET: `python run.py --loop --config config.overnight.yaml`
  builds the Friday-expiry NFP book, then stop it. After the close, run
  `python scripts/friday_planner.py` — it reads the account and tells you
  whether Friday is protect-the-gain or full variance, and why.
- Winners get banked: standalone convex longs up past `take_profit_close_plpc`
  are closed automatically (spread legs are never touched one-sided).
- `python scripts/show_curve.py SPY` prints/saves the live implied-probability
  curve — the money shot for the demo video.
- `config.event.yaml` is the Friday-NFP-morning profile (fast cycles,
  convexity mode, wide caps). Run it only 9:30-10:45 ET on Sep 4, then
  `python run.py --flatten` and `python scripts/snapshot.py` for final numbers.
- Everything the video needs is on screen: the dashboard's divergence ledger
  shows gold (Honest Odds) vs slate (market) per decision, gates light up
  red when they block, and the fund letter narrates the day.
