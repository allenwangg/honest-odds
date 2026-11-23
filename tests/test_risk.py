#!/usr/bin/env python3
"""Risk gates must block what they exist to block. No network, no keys."""
import sys, tempfile, types, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia.config import Config
import pythia.risk as _risk

# Sandbox the files the gates read and write. Without this the test wrote,
# then deleted, the live journal/day_state.json, and touched the live KILL
# file, which halts a running loop.
_TMP = Path(tempfile.mkdtemp(prefix="pythia-test-risk-"))
_risk.DAY_STATE = _TMP / "journal" / "day_state.json"
_risk.KILL_FILE = _TMP / "KILL"
from pythia.risk import RiskGates, KILL_FILE
from pythia.structures import TradePlan, Leg
from pythia.divergence import Opportunity
from pythia.market_data import OptionQuoteRow

cfg = Config()
gates = RiskGates(cfg)

def row(sym, strike, bid, ask, kind="C"):
    return OptionQuoteRow(symbol=sym, strike=strike, kind=kind, bid=bid, ask=ask)

def opp(direction="above", inferred=0.55, implied=0.42):
    return Opportunity(symbol="SPY", expiry=dt.date.today(), strike=500.0,
                       direction=direction, implied_p=implied, inferred_p=inferred,
                       confidence=0.7, rationale="test")

def plan(contracts=5, debit=0.45, width=1.0, direction="above", inferred=0.55):
    p = TradePlan(opp=opp(direction, inferred))
    long_row = row("SPY..C00500000", 500.0, 0.60, 0.70)
    short_row = row("SPY..C00501000", 501.0, 0.22, 0.26)
    p.legs = [Leg(long_row.symbol, "buy", long_row), Leg(short_row.symbol, "sell", short_row)]
    p.contracts, p.limit_debit, p.width = contracts, debit, width
    p.net_mid, p.net_conservative = debit - 0.05, debit
    return p

def fake_pos(symbol, cost):
    p = types.SimpleNamespace()
    p.symbol, p.cost_basis = symbol, cost
    return p

EQUITY = 100_000.0

# 1) clean plan passes every gate
res = gates.evaluate(plan(), EQUITY, [])
assert RiskGates.approved(res), [f"{g.gate}: {g.detail}" for g in res if not g.passed]
print("clean plan approved")

# 2) per-trade budget: 5% of 100k = $5,000; 120 contracts * .45 * 100 = $5,400 -> block
res = gates.evaluate(plan(contracts=120), EQUITY, [])
assert not RiskGates.approved(res)
assert any(g.gate.startswith("G2") and not g.passed for g in res)
print("G2 per-trade budget blocks oversize")

# 3) portfolio heat: $24k open + $2.25k new > $25k cap -> block
res = gates.evaluate(plan(contracts=50), EQUITY, [fake_pos("QQQ..", 24_000)])
assert any(g.gate.startswith("G3") and not g.passed for g in res)
print("G3 heat blocks a hot book")

# 4) concentration: $14k already in SPY + new > 15% cap -> block
res = gates.evaluate(plan(contracts=50), EQUITY, [fake_pos("SPY260904C00500000", 21_000)])
assert any(g.gate.startswith("G7") and not g.passed for g in res)
print("G7 concentration blocks stacking one name")

# 5) wide markets -> G5 blocks
p = plan()
p.legs[0].row.bid, p.legs[0].row.ask = 0.10, 0.60   # 133% spread
res = gates.evaluate(p, EQUITY, [])
assert any(g.gate.startswith("G5") and not g.passed for g in res)
print("G5 liquidity blocks wide markets")

# 6) paying >= breakeven sense: debit .45/width 1.0 needs inferred > .45 -> .40 blocks
res = gates.evaluate(plan(inferred=0.40), EQUITY, [])
assert any(g.gate.startswith("G8") and not g.passed for g in res)
print("G8 sanity blocks negative edge at fill")

# 7) kill switch
KILL_FILE.write_text("halt")
try:
    res = gates.evaluate(plan(), EQUITY, [])
    assert any(g.gate.startswith("G6") and not g.passed for g in res)
finally:
    KILL_FILE.unlink()
print("G6 kill switch halts")

# 8) circuit breaker via day_state
import json
from pythia.risk import DAY_STATE
DAY_STATE.parent.mkdir(exist_ok=True)
DAY_STATE.write_text(json.dumps({"date": dt.date.today().isoformat(),
                                 "day_start_equity": 100_000, "halted": False}))
halted, _ = gates.check_circuit_breaker(91_000.0)   # -9% > 8% limit
assert halted
res = gates.evaluate(plan(), 91_000.0, [])
assert any(g.gate.startswith("G4") and not g.passed for g in res)
DAY_STATE.unlink()
print("G4 circuit breaker halts on -9% day")
print("ALL RISK TESTS PASSED")

# G7 correlation bucket: heavy QQQ book blocks a new SPY trade (shared bucket)
res = gates.evaluate(plan(contracts=20), EQUITY, [fake_pos("QQQ260904C00480000", 22_000)])
assert any(g.gate.startswith("G7") and not g.passed for g in res)
res = gates.evaluate(plan(contracts=20), EQUITY, [fake_pos("NVDA260904C00200000", 22_000)])
assert not any(g.gate.startswith("G7") and not g.passed for g in res)
print("G7 treats SPY/QQQ as one correlated bucket")
