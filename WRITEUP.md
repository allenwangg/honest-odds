# Honest Odds — the options chain is a prediction market

*Alpaca AI Trading Agents Hackathon · Options Alpha Agents · one-page write-up*

**Thesis.** By Breeden–Litzenberger, option prices encode a probability
distribution: −∂C/∂K is the risk-neutral probability Q(S_T > K), and a tight
debit spread around K is that digital contract, tradable. So the options chain
is a prediction market quoting probabilities all day. For 0–7 DTE the Girsanov
drift correction is negligible (≈0.06% vs a 2% diffusion scale), so Q differs
from the physical measure mainly through the variance risk premium — exactly
the correction channel Honest Odds's analyst is fed. The strategy is probability
arbitrage: trade the spread between the market's measure and the model's, in
defined-risk size, and grade every call in public. (Full math → THEORY.md.)

## AI logic

Every cycle (5–20 min, RTH only), per underlying: (1) pull the near-dated chain
via Alpaca's options data API and compute the market-implied probability curve
from finite differences of call mids, cross-checked against the put-derived
curve, with no-arbitrage monotonicity enforced (isotonic cleanup) and stale or
one-sided quotes rejected; (2) hand the implied probabilities, recent bars,
realized-vol context, Alpaca news headlines, and a human-maintained macro
calendar to Claude (`claude-sonnet-5`), prompted as a calibrated
superforecaster: the market's number is its prior, and it must articulate why
before deviating; (3) trade only strikes where |inferred − implied| clears the
edge threshold and the model's stated confidence clears a floor, sized
Kelly-lite (∝ edge × confidence, hard-capped). Model output is strict,
schema-validated JSON; anything malformed means the cycle trades nothing.

Positions are managed by rule, not by the model. A take-profit rule closes any
leg or spread once it has captured a set fraction of its maximum payoff — on
Sep 1 it banked SPY puts at +193% at 8:41am, minutes after the open, and TSLA
puts at +101% at 11:28am, with no human involved — and unfilled orders are
cancelled after a fixed window. Every decision (traded, skipped, blocked, banked) is
journaled with its thesis; Claude writes a nightly fund letter from the
journal; the day's biggest disagreement with the market is posted publicly
before it resolves and graded the next day.

## Risk gates

Eight dumb, non-negotiable checks between any plan and the exchange: **G1**
defined-risk only (net-debit structures, bounded max loss, no naked shorts);
**G2** per-trade max loss cap; **G3** portfolio heat cap on total open cost
basis; **G4** daily circuit breaker halting new entries past a daily loss
limit; **G5** liquidity — real bids, spread and friction tolerance on every
leg; **G6** a kill-switch file that halts entries instantly; **G7**
per-underlying concentration cap; **G8** sanity — the edge must survive the
actual entry price (debit/width < inferred probability). The gates contain no
ML and no LLM: the intelligence upstream can be wrong; these cannot be argued
with. Limits are parameters — a contest profile (10% per trade, −15% halt) and
a protect profile (3% per trade, 10% heat, −3% halt) used to defend a lead —
but the gates themselves are not.

Live lesson, logged in the journal: on Sep 1 and Sep 2 the circuit breaker
halted new entries on a phantom drawdown — the offline self-test shares the
live day-state file and stamped a synthetic $100k baseline against a $109k
account. The halt cost nothing (G4 fails closed, as designed); the fix —
isolate self-test state, take the baseline from the account's official
previous close — is specified in the journal and is the first post-hackathon
change.

## Alpaca infrastructure

Execution: Trading API via `alpaca-py` — atomic multi-leg (MLEG) limit orders
at the net debit for vertical spreads, deterministic `pythia-` client-order ids
for idempotent restarts, `close_all_positions` behind a `--flatten` command.
Data: options-chain snapshots (indicative feed) with quotes, IV and greeks;
stock bars, latest trades and the News API for context. Supervision: Alpaca's
official MCP server connects Claude to the same account, so the human can
interrogate positions, cancel orders, or override the agent in plain language —
autonomous loop on the Trading API, human judgment over MCP. Account: a
dedicated $100,000 paper account (PA3C8Y75G64Y) opened Aug 30 for this
hackathon.

## Results

Dedicated $100,000 paper account **PA3C8Y75G64Y**, opened Aug 30 for this hackathon.
Daily closes as marked by Alpaca: Mon $98,474 (−1.5%) · Tue $109,584 (+11.3%) ·
Wed $107,814 (−1.6%) · **Thu $106,824 — +6.8% on the week**, flat into Friday payrolls.
9 orders placed by the agent, 7 vetoed by gates (6 on portfolio heat, 1 on liquidity),
zero manual entries.

- **Two exits auto-banked by the take-profit rule**: SPY puts +193% at 8:41am and TSLA
  puts +101% at 11:28am on Sep 1, with no human involved.
- **Forecast quality, scored properly.** 37 resolved forecasts graded against official
  closes with the Brier rule, benchmarked against the same option chain they were read
  from: **market 0.0566, Honest Odds 0.0159 — 72% lower.** *(Nov 2026 correction: four of these
  were stale 0DTE quotes Honest Odds flagged at the time; without them it is market 0.0317,
  Honest Odds 0.0177, 44% lower over 33, and the coin-flip claim below does not hold. See
  CALIBRATION.md § Robustness.)* On the seven near-coin-flip
  questions (market 40–60%) the market went 3-for-7 and Honest Odds went 7-for-7:
  0.2319 vs 0.0395, 83% lower. Optimal shrinkage toward the market prior grid-searched
  to **λ = 0.00**. Full table, method and caveats in **CALIBRATION.md**.
- **The finding I did not want.** Splitting those forecasts by direction of disagreement:
  where Honest Odds was more bullish than the chain it scored 96% better; where it was more
  *bearish* it scored 11% **worse**. Buying a put spread is a bearish disagreement, so
  the trade filter fires precisely where the model has no measured edge — and it did.
  Honest Odds scored worse than the market on three forecasts all week and **two of them were
  trades** (an earlier version said four and three; the journal shows three and two). n=16 on the bearish side over four sessions is not yet a fact, which is why
  it is logged rather than patched into the config; `scripts/calibrate.py` is built to
  settle it with more data.
- **The graded call, in full.** On Sep 2 the chain implied 60% that QQQ finishes above
  708 on Sep 3; Honest Odds said 52% and bought the 708/704 put debit spread, 22 contracts,
  filled at 1.27 for a maximum loss of $2,794 known before the order left. QQQ closed
  Sep 3 at **717.67** — the market was right and Honest Odds was wrong. Realised loss $2,750,
  inside the cap the gate printed, and it is in the journal with the reasoning that
  produced it. A forecaster who only publishes the calls that land is not a forecaster.
- **Operator interventions, disclosed**: none on entries; risk-reducing closes of orphaned
  legs on Sep 1 during a config change, and a `--flatten` at 11:14am Thu to avoid holding
  a 0-DTE put spread into assignment risk overnight. Agent orders carry `pythia-` client
  ids, so the two are separable in the account history.

*Built solo by Allen Wang, with Claude as a coding assistant · github.com/allenwangg/pythia · demo video: [YouTube link]*
