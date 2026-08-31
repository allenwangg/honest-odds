#!/usr/bin/env python3
"""Print the numbers the write-up needs: equity, P&L, decision and gate stats."""
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia.config import ROOT, Config
from pythia.market_data import MarketData

cfg = Config.load(); cfg.require_keys(need_anthropic=False)
acct = MarketData(cfg).trading.get_account()
equity = float(acct.equity)
print(f"equity        ${equity:,.2f}")
print(f"total P&L     ${equity-100_000:+,.2f}  ({(equity/100_000-1)*100:+.2f}%)")

trades = ROOT / "journal" / "decisions.jsonl"
if trades.exists():
    rows = [json.loads(l) for l in trades.read_text().splitlines() if l.strip()]
    actions = Counter(r.get("action", "?") for r in rows)
    print(f"decisions     {dict(actions)}")
    submitted = [r for r in rows if r.get("action") == "submitted"]
    if submitted:
        edges = [abs(r.get("edge", 0)) for r in submitted]
        print(f"trades sent   {len(submitted)}, avg |edge| {sum(edges)/len(edges)*100:.1f}pts")
    blocked_by = Counter(g["gate"] for r in rows for g in r.get("gates", [])
                         if not g.get("passed"))
    if blocked_by:
        print(f"gate blocks   {dict(blocked_by)}")
else:
    print("no journal yet")
