# Pythia — the options chain is a prediction market

*Alpaca AI Trading Agents Hackathon · Options Alpha Agents · one-page write-up*

**Thesis.** By Breeden–Litzenberger, option prices encode a probability
distribution: −∂C/∂K is the risk-neutral probability Q(S_T > K), and a tight
debit spread around K is that digital contract, tradable. So the options chain
is a prediction market quoting probabilities all day. For 0–7 DTE the Girsanov
drift correction is negligible (≈0.06% vs a 2% diffusion scale), so Q differs
from the physical measure mainly through the variance risk premium — exactly
the correction channel Pythia's analyst is fed. The strategy is probability
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

- Equity ≈$109,333 on $100,000 (**+9.3%**) after 3 of 5 sessions: Day 1 −1.5%,
  Day 2 +11.3%, Day 3 −0.2% while holding a QQQ 708/704 put spread (max loss
  $3,058) overnight by design. [Thu night: final equity, %, round-trips, hit
  rate, max drawdown, orders blocked by gates — from `scripts/snapshot.py`;
  Brier scores from `scripts/calibrate.py`]
- Two exits auto-banked by the take-profit rule (+193%, +101%).
- Operator interventions, disclosed: none on entries; risk-reducing closes of
  orphaned legs on Sep 1 during a config change. Agent orders carry `pythia-`
  client ids, so the two are separable in the account history.
- Daily letters, full decision journal, dashboard and the public grading
  thread: see repo.

*Built solo by Allen Wang · github.com/allenwangg/pythia · demo video: [YouTube link]*
