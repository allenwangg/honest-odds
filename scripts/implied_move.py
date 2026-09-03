#!/usr/bin/env python3
"""What move is the market pricing by the close? ATM straddle / spot.
   python3 scripts/implied_move.py SPY QQQ"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia.config import Config
from pythia.market_data import MarketData

cfg = Config.load(); cfg.require_keys(need_anthropic=False)
md = MarketData(cfg)
for sym in [a.upper() for a in sys.argv[1:]] or ["SPY"]:
    try:
        spot = md.spot(sym)
        sl = md.pick_expiry(md.chain_slices(sym, spot))
        if not sl: print(f"{sym}: no usable expiry"); continue
        c = min(sl.calls, key=lambda r: abs(r.strike - spot))
        p = min(sl.puts,  key=lambda r: abs(r.strike - spot))
        straddle = c.mid + p.mid
        mv = straddle / spot
        print(f"{sym} {spot:.2f} exp {sl.expiry}: straddle ${straddle:.2f} "
              f"-> market prices ±{mv:.2%} (range {spot*(1-mv):.1f} – {spot*(1+mv):.1f})")
    except Exception as e:
        print(f"{sym}: {e}")
