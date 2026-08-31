#!/usr/bin/env python3
"""Verify the competition paper account is ready. Run this FIRST."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia.config import Config
from pythia.market_data import MarketData

cfg = Config.load()
cfg.require_keys(need_anthropic=False)
md = MarketData(cfg)
acct = md.trading.get_account()
equity = float(acct.equity)
level = int(acct.options_trading_level or 0)
clock = md.trading.get_clock()

print(f"account            {acct.account_number}")
print(f"equity             ${equity:,.2f}")
print(f"options level      {level}  (need 3 for spreads; set in paper dashboard)")
print(f"options BP         ${float(acct.options_buying_power or 0):,.2f}")
print(f"market open now    {clock.is_open}  (next open {clock.next_open})")

ok = True
if abs(equity - 100_000) > 0.01:
    ok = False
    print("!! equity is not exactly $100,000 — the contest requires a fresh "
          "dedicated paper account reset to $100k. Fix before trading.")
if level < 3:
    print("!! options level < 3: spreads will be rejected. Either raise the "
          "level in the Alpaca paper dashboard or set allow_spreads: false.")
print("READY" if ok else "NOT READY")
