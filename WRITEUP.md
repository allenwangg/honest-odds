# Pythia — the options chain is a prediction market

*Alpaca AI Trading Agents Hackathon · Options Alpha Agents · one-page write-up*

**Thesis.** By Breeden–Litzenberger, option prices encode a probability
distribution: −∂C/∂K is the risk-neutral probability Q(S_T > K), and a tight
debit spread around K is that digital contract, tradable. So the options
chain is a prediction market quoting probabilities all day. For 0–7 DTE the
Girsanov drift correction is negligible (≈0.06% vs a 2% diffusion scale), so
Q differs from the physical measure mainly through the variance risk premium
— which is exactly the correction channel Pythia's analyst is fed. The
strategy is probability arbitrage: trade the spread between the market's
measure and the model's, in defined-risk size. (Full math → THEORY.md.)

## AI logic

Every cycle (15–20 min, RTH only), per underlying: (1) pull the near-dated
chain via Alpaca's options data API and compute the market-implied probability
curve from finite differences of call mids, cross-checked against the same
curve derived from puts, with no-arbitrage monotonicity enforced; (2) hand the
implied probabilities, recent price action, and a human-maintained macro
calendar to Claude (`claude-sonnet-5`), which is prompted as a calibrated
superforecaster: the market's number is its prior, and it must articulate why
before deviating; (3) trade only strikes where |inferred − implied| ≥ the edge
threshold and the model's stated confidence clears a floor, sized Kelly-lite
(fraction ∝ edge × confidence, hard-capped). The model's output is strict,
schema-validated JSON; anything malformed means the cycle trades nothing.
Every decision — traded, skipped, or blocked — is journaled with its thesis,
and Claude writes a nightly fund letter from the journal.

## Risk gates

Eight dumb, non-negotiable checks between any plan and the exchange:
**G1** defined-risk only (net-debit structures, bounded max loss, no naked
shorts); **G2** per-trade max loss ≤ 10% of equity (contest profile);
**G3** portfolio heat cap on total open cost basis; **G4** daily circuit
breaker halting new entries on a −15% day; **G5** liquidity — real bids and
spread tolerance on every leg; **G6** a kill-switch file that halts entries
instantly; **G7** per-underlying concentration cap; **G8** sanity — the edge
must survive the actual entry price (debit/width < inferred probability).
The gates contain no ML and no LLM: the intelligence upstream can be wrong;
these cannot be argued with. Conservative and contest risk profiles ship as
separate config files — limits are parameters, gates are not.

## Alpaca infrastructure

Execution: Trading API via `alpaca-py` — atomic multi-leg (MLEG) limit orders
at the net debit for vertical spreads, deterministic client-order ids for
idempotent restarts, `close_all_positions` behind a `--flatten` command.
Data: options chain snapshots (indicative feed) with quotes, IV, and greeks;
stock bars and latest trades for context. Supervision: Alpaca's official MCP
server connects Claude to the same dedicated $100k paper account, so the human
can interrogate positions, cancel orders, or override the agent in plain
language — autonomous loop on the Trading API, human judgment over MCP.

## Results

- Final equity: $[____] on $100,000 ([__]%), [N] round-trips, hit rate [__]%
- Largest win / loss: $[____] / $[____]; max drawdown [__]%; gates blocked [N] orders
- Daily letters, full decision journal, and dashboard: see repo

*Built solo by Allen Wang · github.com/[repo] · demo video: [link]*
