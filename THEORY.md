# THEORY — the mathematics under Pythia, mapped to the code that uses it

*One page for judges who want to know whether the math is decoration or
load-bearing. Every claim below names the module that implements it.*

## 1. Options prices are probabilities (Breeden–Litzenberger)

Under no-arbitrage there is a risk-neutral measure **Q** under which
discounted prices are martingales. A European call is
C(K) = e^{-rT} E_Q[(S_T − K)^+], and differentiating under the integral:

    ∂C/∂K = −e^{-rT} Q(S_T > K)        ∂²C/∂K² = e^{-rT} q_Q(K)

The first derivative is the price of a digital option — the market's
probability quote. The second (Breeden–Litzenberger 1978) is the full
risk-neutral density. **`implied.py`** computes the discrete first
derivative, −ΔC/ΔK between adjacent listed strikes, with r ≈ 0 for 0–7 DTE.
Under geometric Brownian motion this recovers N(d₂) exactly — which is what
`tests/test_implied.py` verifies against Black–Scholes to three decimals.

## 2. The cleanup steps are no-arbitrage projections

Static no-arbitrage constrains the call curve: **decreasing** in K (else a
vertical spread is free money) and **convex** in K (else a butterfly is).
`implied.py` enforces the first by monotone rearrangement of the mids, and
the second by forcing the digital curve non-increasing — since the digital
curve is −C′(K), "digitals non-increasing" ⇔ "C convex" ⇔ butterfly-
arbitrage-free. The put-side curve (1 − ∂P/∂K) is a second estimator of the
same object; **put–call parity**, C − P = S − Ke^{-rT}, pins the two, and
`parity_residual()` uses its violation as a stale-quote detector: a chain
that breaks parity by dollars is not a market, it is a cache.

## 3. What the trade actually is: measure arbitrage

The chain quotes **Q**. Decisions need the physical measure **P**. Girsanov's
theorem says the change of measure shifts *drift only*: W_t^Q = W_t^P + λt,
λ = (μ−r)/σ. Over T = 3/252 the drift term (μ−r)T ≈ 0.06% is an order of
magnitude smaller than the diffusion term σ√T ≈ 2%, so for short-dated
contracts **Q ≈ P up to the variance risk premium** — implied vol's
systematic overstatement of realized vol, which fattens Q's tails. Pythia's
edge is therefore a spread between two probability measures:

    edge(K) = P̂_claude(S_T > K) − Q_chain(S_T > K)

**`analyst.py`** estimates P̂ (with the market's Q as its stated prior);
**`divergence.py`** trades the spread; the realized-vs-implied vol context
fed to the analyst is precisely the variance-risk-premium correction
channel; and the calibration shrinkage λ (see §5) is the empirical estimate
of how much of the analyst's deviation from Q is signal.

## 4. The instrument is a discrete digital

A K₁/K₂ debit spread's payoff, divided by its width, converges to the
digital's as K₂→K₁ — so `structures.py` buys the tightest listed bracket
around the event strike, and gate **G8** checks that debit/width (the
market's probability, paid at the actual fill) is still below P̂. Sizing is
fractional Kelly: full Kelly for a binary is f* = edge/odds; Pythia uses
f ∝ edge × confidence, hard-capped — fractional Kelly under model
uncertainty, which maximizes long-run log-growth subject to not being wrong
about being right (**`structures.py`**, caps in **`risk.py`**).

## 5. Forecasts are scored, not admired

The Brier score is a strictly proper scoring rule: it is uniquely minimized
by reporting true beliefs, so it cannot be gamed by hedging the forecast.
**`scripts/calibrate.py`** scores every resolved journal forecast — Pythia's
P̂ and the market's Q against realized outcomes — and grid-searches the
shrinkage λ* minimizing Brier for the blended forecast Q + λ(P̂ − Q). That λ*
goes back into config as `edge_shrinkage`: the loop that keeps the agent's
confidence an empirical quantity rather than a mood.

## 6. What the gates are, formally

G1–G8 (**`risk.py`**) are ruin constraints: they bound the support of the
one-day P&L distribution (defined-risk only, per-trade and portfolio caps,
correlated SPY/QQQ treated as one factor bucket) and truncate the adverse
path (circuit breaker, kill file). Kelly theory assumes you survive to play
the next round; the gates are that assumption, made executable.

*— Built solo. The math above is 1970s-vintage and deliberately so: the
novelty is the P̂ estimator and the verification loop, not the calculus.*
