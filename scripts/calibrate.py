#!/usr/bin/env python3
"""Forecast verification: Brier-score Pythia vs the market on RESOLVED events.

Every journaled decision is a probability forecast that settles when its
expiry passes (close above strike or not) — including blocked and dry-run
decisions, so the brain gets graded even when the hands were tied. Prints
both Brier scores and the shrinkage λ that would have scored best; put that
number in config as edge_shrinkage. Run nightly from Tuesday on.
"""
import datetime as dt, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from pythia.config import ROOT, Config
from pythia.market_data import MarketData

cfg = Config.load(); cfg.require_keys(need_anthropic=False)
md = MarketData(cfg)
trades = ROOT / "journal" / "decisions.jsonl"
if not trades.exists():
    sys.exit("no journal yet")

rows = [json.loads(l) for l in trades.read_text().splitlines() if l.strip()]
today = dt.date.today()
# unique forecasts on resolved expiries
seen, forecasts = set(), []
for r in rows:
    if not all(k in r for k in ("symbol", "expiry", "strike", "inferred_p", "implied_p")):
        continue
    expiry = dt.date.fromisoformat(r["expiry"])
    key = (r["symbol"], r["expiry"], r["strike"])
    if expiry >= today or key in seen:
        continue
    seen.add(key); forecasts.append((r, expiry))
if not forecasts:
    sys.exit("no resolved events yet — check back after an expiry passes")

closes: dict[tuple, float] = {}
for r, expiry in forecasts:
    ck = (r["symbol"], expiry)
    if ck in closes:
        continue
    bars = md.stocks.get_stock_bars(StockBarsRequest(
        symbol_or_symbols=r["symbol"], timeframe=TimeFrame.Day,
        start=dt.datetime.combine(expiry, dt.time()) - dt.timedelta(days=1),
        end=dt.datetime.combine(expiry, dt.time()) + dt.timedelta(days=1)))
    day = [b for b in bars.data.get(r["symbol"], []) if b.timestamp.date() == expiry]
    if day:
        closes[ck] = float(day[-1].close)

scored = []
for r, expiry in forecasts:
    close = closes.get((r["symbol"], expiry))
    if close is None:
        continue
    outcome = 1.0 if close > float(r["strike"]) else 0.0
    scored.append((float(r["inferred_p"]), float(r["implied_p"]), outcome, r, close))

n = len(scored)
if not n:
    sys.exit("expiries passed but no settlement bars found")
brier_p = sum((p - o) ** 2 for p, _, o, _, _ in scored) / n
brier_m = sum((m - o) ** 2 for _, m, o, _, _ in scored) / n
print(f"resolved events: {n}")
print(f"Brier — Pythia:  {brier_p:.4f}")
print(f"Brier — market:  {brier_m:.4f}   ({'PYTHIA BEATS MARKET' if brier_p < brier_m else 'market ahead'})")

best_lam, best_score = 1.0, 1e9
for lam in [0.0, 0.25, 0.5, 0.75, 1.0, 1.25]:
    s = sum(((m + lam * (p - m)) - o) ** 2 for p, m, o, _, _ in scored) / n
    if s < best_score:
        best_lam, best_score = lam, s
print(f"best shrinkage λ: {best_lam}  (Brier {best_score:.4f}) -> set edge_shrinkage: {best_lam}")
print("\nworst 3 calls:")
for p, m, o, r, close in sorted(scored, key=lambda x: -(x[0] - x[2]) ** 2)[:3]:
    print(f"  {r['symbol']} >{r['strike']} {r['expiry']}: said {p:.2f}, mkt {m:.2f}, "
          f"closed {close:.2f} -> {'above' if o else 'below'}")
