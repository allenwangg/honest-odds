#!/usr/bin/env python3
"""Standalone-long detection: spread legs must never be closed one-sided."""
import sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia.scheduler import standalone_long_positions

def pos(sym, qty):
    p = types.SimpleNamespace(); p.symbol, p.qty = sym, qty; return p

positions = [
    pos("SPY260904C00500000",  2),   # long leg of a spread ...
    pos("SPY260904C00501000", -2),   # ... with its short: NOT standalone
    pos("SPY260904P00495000",  3),   # lone long put, same expiry, no short put pair?
    pos("QQQ260904C00480000",  1),   # lone long call: standalone
    pos("NVDA260911C00200000", 1),   # different name/expiry: standalone
]
# SPY 260904 has a short (the call leg) -> ALL SPY 260904 longs are treated as
# paired (conservative: never risk breaking a spread)
got = {p.symbol for p in standalone_long_positions(positions)}
assert got == {"QQQ260904C00480000", "NVDA260911C00200000"}, got
print("spread legs protected; convex longs identified")
print("ALL MANAGER TESTS PASSED")
