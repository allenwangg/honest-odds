# PYTHIA

**A Claude forecasting agent scored against the options market with a proper scoring rule.**

Pythia reads the market's probability that SPY or QQQ closes above a strike straight off the
option chain (Breeden–Litzenberger, `P(S > K) ≈ −∂C/∂K`), asks Claude for its own calibrated
probability of the same event, journals both *before* the event resolves, and trades only
when the gap survives eight hard-coded risk gates. Every forecast, including the ones it
didn't trade, is later graded with the Brier score against the market's own number.

Built solo in one week for the Alpaca AI Trading Agents Hackathon (Aug 31 – Sep 4, 2026).
Paper trading only: the client is hard-coded `paper=True`.

## Result, honestly stated

| 33 resolved forecasts, SPY + QQQ, Aug 31 – Sep 3 2026 | Brier ↓ |
|---|---|
| Market (option-chain mid) | 0.0317 |
| **Pythia (Claude)** | **0.0177** (44% lower) |

- **The published headline was 0.0159 vs 0.0566 (72% lower) on 37 forecasts.** Four of those
  were stale 0DTE quotes (~0.49 on strikes 1–2.5% in the money) that Pythia flagged as stale
  at the time. Counting a flagged data error as a forecasting win overstates the edge, so the
  number above excludes them. Both versions, and the script that produces them, are in
  [CALIBRATION.md](CALIBRATION.md#robustness-check-what-survives-removing-stale-quotes).
- **Where the edge comes from:** mostly far-from-the-money strikes, where chain mid-prices
  are noisy and Pythia correctly pushed them toward 0 or 1. On the 6 interior questions
  (market 15–85%) the gap is 29%.
- **The finding I'd act on:** when Pythia was more *bearish* than the chain it scored 11%
  *worse* (n = 16), and a put spread is a bearish bet, so the trade filter fired on the
  model's weak side. Two of its three worse-than-market forecasts were trades.
- **Limits:** one up-trending week; strikes sharing a close aren't independent, so the
  effective sample is about 6–8 symbol×day clusters; a cluster bootstrap interval for the
  Brier difference includes zero. This is evidence worth testing, not an established edge.
- Paper account: +6.8% on the week under a deliberately aggressive contest risk profile.
  One week of P&L says little; the Brier scores are the measurement that matters.

Reproduce offline, no keys: `python scripts/robustness.py`.

## How it works

Under the risk-neutral measure, `P(S > K at expiry) ≈ −dC/dK`. A tight call
spread around K is a binary contract on that event, and its price/width ratio
is the market's probability quote. Pythia computes that quote across strikes,
asks Claude for an independent, calibrated estimate of the same probabilities,
and trades the divergence with defined-risk debit spreads — every decision
gated, journaled, and narrated.

The math is 1970s-vintage on purpose — Breeden–Litzenberger, Girsanov,
proper scoring rules — with every identity mapped to the module that
implements it in **THEORY.md**. The novelty is the P̂ estimator and the
verification loop, not the calculus.

```
 chain ──► implied curve ──► Claude assessment ──► divergence ──► structure
 (Alpaca    (−dC/dK, put      (independent P,       (|edge| ≥      (call/put debit
  options    cross-check,      confidence,           threshold)     spread bracketing
  data API)  no-arb clean)     rationale, JSON)                     the strike)
                                                                        │
 dashboard ◄── state.json ◄── journal ◄── execution ◄── RISK GATES ◄────┘
 (ops console)               (JSONL +     (MLEG limit   (G1..G8 — all
                              fund        orders,        must pass)
                              letters)    idempotent)
```

## Quickstart

```bash
# 0. Python 3.10+
pip install -r requirements.txt
cp .env.example .env          # paste keys from your DEDICATED competition
                              # paper account + an Anthropic API key

# 1. Offline proof — no keys, no network: unit tests, then the FULL pipeline
python tests/test_implied.py && python tests/test_risk.py
python run.py --selftest

# 2. Account readiness (equity == $100k, options level 3 for spreads)
python scripts/setup_account_check.py

# 3. Watch it think without trading
python run.py --once --dry-run

# 4. Dashboard (from repo root; state.json is written by each cycle)
python -m http.server 8787    # open http://localhost:8787/dashboard/

# 5. Trade the day
python run.py --loop --config config.contest.yaml

# Controls
touch KILL                    # instant halt of new entries (gate G6)
python run.py --flatten       # close everything, cancel open orders
python run.py --letter        # Claude writes today's fund letter from the journal
```

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
| Options in every strategy | The only instruments Pythia trades are option spreads/longs |
| One-page write-up (AI logic, risk gates, infra) | `WRITEUP.md` — fill in results and submit |

## Risk gates (the part judges should poke)

G1 defined-risk only · G2 per-trade budget · G3 portfolio heat · G4 daily
circuit breaker · G5 liquidity · G6 kill switch · G7 concentration ·
G8 sanity (edge must survive the actual entry price). All eight in
`pythia/risk.py`, all exercised by `tests/test_risk.py`, all dumb on purpose —
the LLM can be wrong; the gates can't be argued with. `config.yaml` is the
sane profile; `config.contest.yaml` raises the caps for a 4-day leaderboard
and says so out loud.

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
  shows gold (Pythia) vs slate (market) per decision, gates light up
  red when they block, and the fund letter narrates the day.

## Repo map

```
run.py                  CLI: --once --loop --dry-run --flatten --letter
config.yaml             sane profile · config.contest.yaml  contest profile
pythia/
  market_data.py        chains, OCC parsing, expiry selection, spot/bars
  implied.py            the math: −dC/dK curves, blending, event strikes
  analyst.py            Claude-as-forecaster, strict JSON, fail-closed
  divergence.py         edge scoring and ranking
  structures.py         debit spreads bracketing the strike, Kelly-lite sizing
  risk.py               gates G1–G8, circuit breaker, kill switch
  execution.py          MLEG orders, idempotent ids, flatten
  journal.py            decisions.jsonl + Claude-written fund letters
  state.py              dashboard/state.json writer
  scheduler.py          the cycle and the RTH loop
dashboard/index.html    ops console (serve repo root, open /dashboard/)
tests/                  offline: curve math vs Black-Scholes, all 8 gates
notes/macro.md          human-maintained catalyst calendar → analyst prompt
mcp/README.md           Claude-over-MCP supervision setup
WRITEUP.md              the one-page submission
CALIBRATION.md          Brier scores vs the market, plus the robustness check
scripts/robustness.py   offline re-scoring (data/closes.json holds settlement prices)
THEORY.md               the stochastic-calculus grounding, module-mapped
```

*Pythia is a hackathon competition system for simulated funds. It is not
investment advice, and its contest risk profile is tuned for a paper
leaderboard, not for real capital.*
