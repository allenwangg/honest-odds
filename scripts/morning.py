#!/usr/bin/env python3
"""THE MORNING COMMAND. Run this, read it, decide. Nothing else required.

    python3 scripts/morning.py

It checks the account, runs ONE cycle with no real orders, then explains in
plain English what the market believes, what Pythia believes, and what it
would have traded — and hands you the day's post with the numbers filled in.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pythia.config import ROOT, Config
from pythia.market_data import MarketData

BAR = "─" * 62


def money(x: float) -> str:
    return f"${x:,.2f}"


def main() -> int:
    cfg = Config.load()
    cfg.require_keys(need_anthropic=(cfg.llm_backend == "api"))
    md = MarketData(cfg)
    acct = md.trading.get_account()
    clock = md.trading.get_clock()
    equity = float(acct.equity)
    pnl = equity - 100_000

    print(BAR)
    print("  PYTHIA — morning check")
    print(BAR)
    print(f"  balance      {money(equity)}   ({pnl:+,.2f} since the start)")
    print(f"  market       {'OPEN' if clock.is_open else 'CLOSED'}")
    if not clock.is_open:
        print(f"  next open    {clock.next_open.astimezone()}")
        print(BAR)
        print("\n  Market is closed, so there is nothing to decide yet.")
        print("  Come back after 8:30am CT and run this again.\n")
        return 0

    positions = [p for p in md.trading.get_all_positions()
                 if getattr(p.asset_class, "value", "") == "us_option"]
    print(f"  positions    {len(positions)} open option position(s)")
    for p in positions:
        pl = float(p.unrealized_pl or 0)
        print(f"               {p.symbol}  {float(p.qty):+g}  {pl:+,.2f}")
    print(BAR)
    print("\n  Thinking... (this takes a minute — it is reading the whole\n"
          "  options chain and asking Claude for its own view)\n")

    before = _todays_decisions()
    from pythia.scheduler import Pythia
    Pythia(cfg, dry_run=True).cycle()
    new = [d for d in _todays_decisions() if d not in before]

    print(BAR)
    print("  WHAT PYTHIA THINKS")
    print(BAR)
    if not new:
        print("\n  No disagreements big enough to trade right now.")
        print("  That is normal and it is the agent being disciplined.")
        print("  It will keep checking every cycle while the loop runs.\n")
        _print_footer(equity, None)
        return 0

    tradeable = [d for d in new if d.get("action") in ("dry_run", "submitted")]
    best = max(tradeable, key=lambda d: abs(d.get("edge", 0))) if tradeable else None
    for d in new:
        mkt = d["implied_p"] * 100
        pyt = d["inferred_p"] * 100
        edge = d["edge"] * 100
        star = " <-- biggest" if (best is not None and d is best) else ""
        print(f"\n  {d['symbol']} closing above {d['strike']} on {d['expiry']}:")
        print(f"     the market says   {mkt:.0f}%")
        print(f"     Pythia says       {pyt:.0f}%   ({edge:+.0f} points){star}")
        print(f"     confidence        {d['confidence'] * 100:.0f}%")
        if d.get("rationale"):
            print(f"     why               {d['rationale'][:110]}")
        action = d.get("action", "")
        if action == "dry_run":
            print(f"     WOULD TRADE       {d.get('structure')} x{d.get('contracts')}"
                  f"  (most it can lose: {money(d.get('max_loss', 0))})")
        elif action == "blocked":
            print(f"     BLOCKED by its own safety gates: {d.get('reason')}")
        elif action == "skipped":
            print(f"     skipped: {d.get('reason')}")
    _print_footer(equity, best)
    return 0


def _print_footer(equity: float, best: dict | None) -> None:
    print("\n" + BAR)
    print("  WHAT TO DO NOW")
    print(BAR)
    print("""
  Nothing was actually traded — that was a rehearsal.

  If the numbers above look sane, start the real run:

      python3 run.py --loop

  Leave that Terminal window open and go about your day. To stop it,
  click that window and press Control-C. To halt it instantly at any
  time, run this in a NEW window:   touch ~/Downloads/pythia/KILL
""")
    if best:
        mkt, pyt = best["implied_p"] * 100, best["inferred_p"] * 100
        card = (f"python3 scripts/make_card.py --day 1 --symbol {best['symbol']} "
                f"--strike {best['strike']} --implied {mkt:.0f} "
                f"--inferred {pyt:.0f} --equity {equity:.0f}")
        print(BAR)
        print("  YOUR POST FOR TODAY (make the image, then paste the text)")
        print(BAR)
        print(f"\n  {card}\n")
        print(f"""  Day 1. Pythia's biggest disagreement with the market today:

  The market says {mkt:.0f}% that {best['symbol']} closes above {best['strike']}
  on {best['expiry']}. Pythia says {pyt:.0f}%.

  {best.get('structure', 'Position')} — max loss known to the dollar before entry.
  Grading this call publicly tomorrow.
""")


def _todays_decisions() -> list[dict]:
    path = ROOT / "journal" / "decisions.jsonl"
    if not path.exists():
        return []
    today = dt.date.today().isoformat()
    rows = []
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("ts", "").startswith(today):
            rows.append(row)
    return rows


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nstopped.")
