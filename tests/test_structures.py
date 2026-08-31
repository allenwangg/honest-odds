#!/usr/bin/env python3
"""Structure selection: spreads by default, convex longs on high conviction."""
import datetime as dt, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia.config import Config
from pythia.divergence import Opportunity
from pythia.market_data import ExpirySlice, OptionQuoteRow
from pythia import structures

def row(k, bid, ask, kind):
    occ = f"SPY261204{kind}{int(k*1000):08d}"
    return OptionQuoteRow(symbol=occ, strike=k, kind=kind, bid=bid, ask=ask)

sl = ExpirySlice(expiry=dt.date.today() + dt.timedelta(days=3))
for i, k in enumerate([498.0, 499.0, 500.0, 501.0, 502.0]):
    c = 2.5 - i * 0.45
    sl.calls.append(row(k, c - 0.03, c + 0.03, "C"))
    p = 0.7 + i * 0.45
    sl.puts.append(row(k, p - 0.03, p + 0.03, "P"))

def opp(edge, conf):
    return Opportunity(symbol="SPY", expiry=sl.expiry, strike=500.0,
                       direction="above", implied_p=0.45, inferred_p=0.45 + edge,
                       confidence=conf, rationale="t")

cfg = Config()  # convexity off by default
plan = structures.build(opp(0.12, 0.8), sl, 100_000, cfg)
assert plan and len(plan.legs) == 2 and "spread" in plan.structure, plan.structure
print("default: spread", plan.structure, f"x{plan.contracts}")

cfg.convexity_mode = True
plan = structures.build(opp(0.12, 0.8), sl, 100_000, cfg)
assert plan and len(plan.legs) == 1 and plan.structure.startswith("convex long call"), plan.structure
assert plan.contracts >= 1 and plan.width == 0.0
print("high conviction: convex long", plan.structure, f"x{plan.contracts}")

plan = structures.build(opp(0.08, 0.65), sl, 100_000, cfg)   # below convexity bars
assert plan and len(plan.legs) == 2 and "spread" in plan.structure
print("modest edge stays a spread even with convexity on")
print("ALL STRUCTURE TESTS PASSED")
