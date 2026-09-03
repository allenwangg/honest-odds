# Calibration — what the forecasts were actually worth

Every probability Pythia produced this week is in `journal/decisions.jsonl`, written **before**
the event resolved, including the ones the gates refused to trade. This file scores all of them
against official daily closes. Reproduce with `python scripts/calibrate.py`.

Scoring rule: **Brier** — mean squared error of a probability against a 0/1 outcome. It is a
*proper* scoring rule, so the only way to minimise it is to report what you actually believe.
Hedging toward 0.5 is penalised, and so is bluster. Lower is better; 0.25 is a coin flip.

The benchmark is not a naive baseline. It is **the market itself** — the risk-neutral probability
read off the same option chain at the same instant via Breeden–Litzenberger (−∂C/∂K). Beating it
means beating the consensus of everyone quoting that chain.

## Headline

37 resolved forecasts · Aug 31 – Sep 3 2026 · SPY and QQQ · one forecast per (symbol, expiry,
strike), the last one of the session.

| | Brier ↓ | Directional hit rate |
|---|---|---|
| Market (option chain) | 0.0566 | 89% |
| **Pythia** | **0.0159** | **100%** |

**72% lower Brier than the market.**

Broken out by how hard the question was — the only split that matters, because a 0.09 strike is
free to both sides:

| Subset | n | Market | Pythia | Δ |
|---|---|---|---|---|
| All resolved | 37 | 0.0566 | 0.0159 | **−72%** |
| Genuinely uncertain (market 25–75%) | 8 | 0.2228 | 0.0634 | **−72%** |
| Near coin-flip (market 40–60%) | 7 | 0.2319 | 0.0395 | **−83%** |
| SPY only | 22 | 0.0331 | 0.0012 | −96% |
| QQQ only | 15 | 0.0910 | 0.0373 | −59% |

On the seven near-coin-flip questions the market went 3-for-7. Pythia went 7-for-7.

**Optimal shrinkage toward the market prior: λ = 0.00.** The pipeline grid-searches the λ in
`p_final = (1−λ)·p_model + λ·p_market` that minimises Brier, and feeds it back into config as
`edge_shrinkage`. This week no amount of shrinkage improved the score, so the config stays at
zero. That is an empirical result, not a preference.

## The finding that matters more than the headline

Splitting the forecasts by *which way* Pythia disagreed with the chain:

| Disagreement direction | n | Market | Pythia | Δ |
|---|---|---|---|---|
| More **bullish** than the chain | 21 | 0.0773 | 0.0030 | −96% |
| More **bearish** than the chain | 16 | 0.0293 | 0.0327 | **+11% — worse** |

Buying a put spread *is* a bearish disagreement. So the trade filter fires on exactly the subset
where the model has no measurable edge — and it did:

| Traded | Market | Pythia | Close | Outcome |
|---|---|---|---|---|
| Sep 1 · SPY 751 | 89% | 98% | 761.78 | above — Pythia right |
| Sep 2 · QQQ 706 | 57% | 51% | 709.24 | above — **market right** |
| Sep 3 · QQQ 708 | 60% | 52% | 717.67 | above — **market right** |

Pythia produced four losing forecasts all week. **Three of them are the three it traded.** The
brain scored 0.0159; the hands were pointed at its blind spot.

The mechanical explanation is visible in the data: mean signed shift versus the chain is
**+0.071** — Pythia was systematically more confident *and* more bullish, on a week where 65% of
the scored strikes closed above their level. Its bullish sharpening was rewarded by the tape. Its
bearish sharpening was not, and the bearish side is the only side the put-spread filter can act on.

The config change this implies, and the reason it is not in this week's config: a directional
asymmetry measured over four days and 16 bearish observations is not yet a fact. The honest move
is to log it, keep grading, and let `scripts/calibrate.py` decide it with more data — which is
what the loop was built to do.

## What these numbers are not

- **n = 37 over four sessions.** Small.
- **The observations are not independent.** Ten strikes on SPY for one expiry resolve on one
  draw of one underlying. The effective sample is closer to 8 (symbol × day) than 37.
- **The tape trended up.** 65% of scored strikes closed above. A systematically bullish, confident
  forecaster looks excellent in that week and would look terrible in the mirror image. The
  near-coin-flip subset is the least contaminated by this and it is still −83%, but n = 7.
- **Closes are official daily closes**, not option settlement prices; for a strike within pennies
  of the close the two can disagree. No strike here was that close.
- Deep-ITM and deep-OTM strikes flatter both sides. That is why the table is split by difficulty.

The point of publishing a proper scoring rule is that it can embarrass you later. This is the
number; Friday's run of `scripts/calibrate.py` will either confirm it or move it.
