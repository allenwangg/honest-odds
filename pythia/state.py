"""Writes dashboard/state.json — everything the console renders, nothing more."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .config import ROOT

STATE_PATH = ROOT / "dashboard" / "state.json"
EQUITY_LOG = ROOT / "journal" / "equity.jsonl"


def _append_equity(equity: float) -> list[dict]:
    EQUITY_LOG.parent.mkdir(exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    with EQUITY_LOG.open("a") as f:
        f.write(json.dumps({"ts": ts, "equity": equity}) + "\n")
    rows = []
    for line in EQUITY_LOG.read_text().splitlines()[-500:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def write_state(*, account, clock, positions, decisions: list[dict],
                gates: list[dict], halted: bool, day_start_equity: float,
                letter_excerpt: str = "") -> None:
    equity = float(account.equity)
    history = _append_equity(equity)
    day_pnl = equity - day_start_equity
    option_positions = [p for p in positions if getattr(p.asset_class, "value", "") == "us_option"]
    state = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "market": {
            "is_open": bool(clock.is_open),
            "next_open": clock.next_open.isoformat(),
            "next_close": clock.next_close.isoformat(),
        },
        "account": {
            "equity": equity,
            "cash": float(account.cash),
            "options_buying_power": float(account.options_buying_power or 0),
            "day_start_equity": day_start_equity,
            "day_pnl": round(day_pnl, 2),
            "day_pnl_pct": round(day_pnl / day_start_equity * 100, 3) if day_start_equity else 0,
            "total_pnl": round(equity - 100_000, 2),
            "total_pnl_pct": round((equity / 100_000 - 1) * 100, 3),
        },
        "halted": halted,
        "gates": gates,
        "equity_history": history,
        "positions": [{
            "symbol": p.symbol,
            "qty": float(p.qty),
            "cost_basis": float(p.cost_basis or 0),
            "market_value": float(p.market_value or 0),
            "unrealized_pl": float(p.unrealized_pl or 0),
            "unrealized_plpc": round(float(p.unrealized_plpc or 0) * 100, 2),
        } for p in option_positions],
        "decisions": decisions[:50],
        "letter_excerpt": letter_excerpt,
    }
    STATE_PATH.parent.mkdir(exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=1, default=str))
