#!/usr/bin/env python3
"""State-dependent Friday plan. Run Thursday after the close.

Podium and 1st want different Fridays. If the account is already up big,
the podium play is to protect it; if it's flat or down, only the right
tail matters and max variance is correct. This prints which config to run
and why — the meta-risk decision, made explicit.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia.config import Config
from pythia.market_data import MarketData

cfg = Config.load(); cfg.require_keys(need_anthropic=False)
acct = MarketData(cfg).trading.get_account()
equity = float(acct.equity)
ret = (equity / 100_000 - 1) * 100
print(f"equity ${equity:,.2f}  ({ret:+.2f}%)\n")

if ret >= 8:
    print("PROTECT MODE — you likely already have a top-quartile number.")
    print("Friday: run config.event.yaml but FIRST edit it:")
    print("  portfolio_heat_frac: 0.15   per_trade_max_frac: 0.05")
    print(f"  (risking ~1/3 of the ${equity-100_000:,.0f} gain, no more)")
    print("Rationale: a locked +8-15% beats a coin flip for podium; a modest")
    print("NFP add can still contend for 1st in a thin field.")
elif ret >= -3:
    print("STANDARD EVENT MODE — run config.event.yaml as shipped.")
    print("Rationale: nothing decisive to protect; NFP convexity is the edge.")
else:
    print("FULL SEND — run config.event.yaml, and consider raising")
    print("  portfolio_heat_frac to 0.75 for the morning.")
    print("Rationale: below water, median outcomes are worthless; only the")
    print("right tail changes your rank. Losses past here cost nothing extra.")
print("\nEither way: flatten 10:45 ET, snapshot 10:50, deadline 11:00 ET.")
