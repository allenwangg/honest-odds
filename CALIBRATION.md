# Calibration — what the forecasts were actually worth

> **Read this first (robustness check, Nov 2026).** The headline below counts four Aug 31
> 0DTE "market probabilities" of ~0.49 on strikes 1–2.5% in the money. Pythia's own log
> called them stale quotes at the time. Without them the result is **Pythia 0.0177 vs
> market 0.0317 over 33 forecasts (44% lower Brier), not 0.0159 vs 0.0566 (72%)**, and the
> "7-for-7 on near coin-flips" claim falls to 3 forecasts on which both sides called the
> direction correctly. Effective sample size is about 6–8 independent draws. Details in
> [Robustness](#robustness-check-what-survives-removing-stale-quotes); the original
> analysis is kept unchanged below it for the record, with two factual corrections marked.

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
*(Correction: all four of the market's misses here are the stale Aug 31 quotes. Without them
the subset is n = 3 and the market is 3-for-3 too. See Robustness.)*

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

Pythia scored worse than the market on three forecasts all week. **Two of them are trades**
(QQQ 706 and QQQ 708); the third (QQQ 701) was a bearish call the gates blocked. *(Correction:
an earlier version said "four losing forecasts, three of them the three it traded"; the
journal shows three and two, and the SPY 751 trade in the table above was a winning
forecast.)* The brain scored 0.0159; the hands were pointed at its blind spot.

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
  forecaster looks excellent in that week and would look terrible in the mirror image. *(The
  near-coin-flip −83% does not survive removing stale quotes; see Robustness.)*
- **Closes are official daily closes**, not option settlement prices; for a strike within pennies
  of the close the two can disagree. No strike here was that close.
- Deep-ITM and deep-OTM strikes flatter both sides. That is why the table is split by difficulty.

The point of publishing a proper scoring rule is that it can embarrass you later. This is the
number; Friday's run of `scripts/calibrate.py` will either confirm it or move it.

## Robustness check: what survives removing stale quotes

*Added Nov 2026. Reproduce offline, no keys: `python scripts/robustness.py`. Settlement
prices and their sources are in `data/closes.json`.*

**The problem.** At 10:26 ET on Aug 31 the chain gave four same-day strikes a "probability"
of 0.477–0.492: SPY 746 and 757 with spot at 764.96, QQQ 696 and 706 with spot at 713.37.
A strike 1–2.5% in the money with hours to expiry is not a coin flip; those numbers are
what −∂C/∂K returns from a stale or one-sided quote. Pythia said so in the logged rationale
("the 0.492 quote looks like a stale/default fill, not a real price") before the close.
Marking them near 1 was correct, but it is a data-quality catch, not a forecast that beat a
real market price. Each one contributes about 0.25 to the market's squared error and almost
nothing to Pythia's, so four rows out of 37 drive most of the gap.

**Same scoring, with and without those four rows** (last forecast per symbol/expiry/strike,
as in the headline):

| Subset | n | Market | Pythia | Δ |
|---|---|---|---|---|
| All, as published | 37 | 0.0566 | 0.0159 | −72% |
| **All, stale quotes removed** | **33** | **0.0317** | **0.0177** | **−44%** |
| Market 25–75%, as published | 8 | 0.2228 | 0.0634 | −72% |
| Market 25–75%, stale removed | 4 | 0.1836 | 0.1260 | −31% |
| Market 40–60%, as published | 7 | 0.2319 | 0.0395 | −83% |
| Market 40–60%, stale removed | 3 | 0.1917 | 0.0911 | −52% |
| Wings (market <15% or >85%), stale removed | 27 | 0.0097 | 0.0009 | −91% |
| Interior (market 15–85%), stale removed | 6 | 0.1306 | 0.0932 | −29% |
| More bullish than chain, stale removed | 17 | 0.0339 | 0.0035 | −90% |
| More bearish than chain, stale removed | 16 | 0.0293 | 0.0327 | +11% |

Directional hit rate after removal: 100% for both. The market's four directional misses in
the headline were all stale quotes.

**What is left, read plainly.**

1. **Most of the remaining gap is in the wings.** 27 of the 33 remaining forecasts are
   strikes the market priced below 15% or above 85%, and the logged rationales flag most of
   those quotes as wide or stale too. Pythia pushed them toward 0 or 1 and was right every
   time. That is real information about how unreliable mid-price wing probabilities are on
   a 1-day horizon, but it is a weak benchmark. It does not show Pythia could beat a price
   you could actually trade at.
2. **On the six interior questions the edge is −29%, n = 6.** Two of them are the QQQ put
   spreads it traded and lost.
3. **The bullish/bearish asymmetry is unchanged** by the correction (all four stale rows were
   bullish disagreements). It is still the most useful finding here, and still small-sample.

**Sample size.** Strikes on one symbol and expiry resolve on one close, so they are not
independent. There are 8 symbol×expiry clusters in the published set and 6 after removal.
Pythia has the lower Brier score in 4 of the 6. A cluster bootstrap of
Brier(Pythia) − Brier(market) gives a 95% interval of [−0.041, +0.007] after removal (11%
of resamples at or above zero), versus [−0.112, −0.007] as published. With six clusters
this interval is itself rough; the honest reading is "consistent with a modest edge, not
established."

**Settlement data.** QQQ closes for all four days and the SPY close for Sep 1 are recorded
in `data/closes.json`. For SPY on Aug 31, Sep 2 and Sep 3 only a bound on the close is
recorded (e.g. the S&P 500 closed at 7,666.60 on Sep 2, putting SPY near 765 against scored
strikes of 744–748 and 777–780). Every scored SPY strike on those days sits outside its
bound, and the script refuses to score a strike inside one. The bounds are inferences from
index and QQQ moves, not exchange prints. `scripts/calibrate.py`
with Alpaca keys pulls the exact bars and reproduces the published 0.0566 / 0.0159.

**What would make this a real result.** A pre-registered filter that drops quotes failing
basic no-arbitrage or width checks *before* scoring, scoring against the bid/ask (not the
mid) for wing strikes, and enough weeks to get dozens of independent clusters rather than
six. Until then the claim this repo supports is: *on one up-trending week, Pythia's
probabilities scored 44% better than chain mid-prices, almost entirely by correcting
obviously mispriced wing quotes, with a possible bearish-side weakness that needs more data.*
