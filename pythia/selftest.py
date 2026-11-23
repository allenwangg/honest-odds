"""Offline end-to-end rehearsal. Runs the ENTIRE cycle — curve, analyst,
divergence, structures, all eight gates, journal, dashboard state — against a
synthetic Black-Scholes chain and a canned analyst, with zero API keys.

Unit tests prove the parts; this proves the glue. If selftest passes, the only
things left to fail on Monday are live-data quirks and fills.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import shutil
import tempfile
import types
from pathlib import Path

from . import journal as _journal, risk as _risk, state as _state
from .config import ROOT, Config  # noqa: F401  (ROOT kept for callers that import it)
from .execution import Executor  # noqa: F401  (imported to prove it loads)
from .journal import Journal
from .market_data import ExpirySlice, OptionQuoteRow
from .risk import RiskGates
from .scheduler import Pythia

SPOT = 500.0


def _ncdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _bs_call(s: float, k: float, t: float, vol: float) -> float:
    d1 = (math.log(s / k) + vol * vol / 2 * t) / (vol * math.sqrt(t))
    return s * _ncdf(d1) - k * _ncdf(d1 - vol * math.sqrt(t))


def _slice() -> ExpirySlice:
    sl = ExpirySlice(expiry=dt.date.today() + dt.timedelta(days=3))
    t, vol = 3 / 252, 0.18
    for k in range(int(SPOT) - 12, int(SPOT) + 13):
        c = _bs_call(SPOT, float(k), t, vol)
        p = c - SPOT + k
        occ_tail = f"260904{{}}{int(k * 1000):08d}"
        sl.calls.append(OptionQuoteRow("SELF" + occ_tail.format("C"), float(k), "C",
                                       max(c - 0.03, 0.01), c + 0.03))
        sl.puts.append(OptionQuoteRow("SELF" + occ_tail.format("P"), float(k), "P",
                                      max(p - 0.03, 0.01), p + 0.03))
    return sl


class _FakeTrading:
    def get_account(self):
        return types.SimpleNamespace(equity="100000", cash="100000",
                                     options_buying_power="200000",
                                     account_number="SELFTEST")

    def get_clock(self):
        now = dt.datetime.now(dt.timezone.utc)
        return types.SimpleNamespace(is_open=True, timestamp=now, next_open=now,
                                     next_close=now + dt.timedelta(hours=3))

    def get_all_positions(self):
        return []

    def get_orders(self, _req=None):
        return []


class _FakeMD:
    def __init__(self):
        self.trading = _FakeTrading()

    def spot(self, _s):
        return SPOT

    def recent_bars(self, _s, days: int = 12):
        out, close = [], SPOT * 0.98
        for i in range(10):
            pct = 0.4 if i % 2 else -0.2
            close *= 1 + pct / 100
            out.append({"date": (dt.date.today() - dt.timedelta(days=10 - i)).isoformat(),
                        "close": round(close, 2), "pct": pct})
        return out

    def chain_slices(self, _s, _spot):
        return [_slice()]

    def pick_expiry(self, slices, min_strikes: int = 6):
        return slices[0]


class _FakeAnalyst:
    """Disagrees upward by 12 points on every event — enough to trade."""

    def assess(self, symbol, spot, expiry, dte, bars, events, vol_context="", news=None):
        return {"stance": "selftest: constructive on dips",
                "events": [{"strike": e["strike"],
                            "p_above": min(e["implied_p"] + 0.12, 0.97),
                            "confidence": 0.8,
                            "rationale": "selftest synthetic divergence"}
                           for e in events]}


def _sandbox_paths() -> tuple[dict, "Path"]:
    """Point every file the cycle writes at a throwaway folder.

    The self-test used to write into the live journal/ and dashboard/ files,
    which polluted the record and once halted the live loop through
    journal/day_state.json. Returns the original paths so they can be restored.
    """
    tmp = Path(tempfile.mkdtemp(prefix="pythia-selftest-"))
    (tmp / "journal").mkdir()
    saved = {
        (_journal, "JOURNAL_DIR"): _journal.JOURNAL_DIR,
        (_journal, "TRADES"): _journal.TRADES,
        (_journal, "LETTERS"): _journal.LETTERS,
        (_risk, "DAY_STATE"): _risk.DAY_STATE,
        (_state, "STATE_PATH"): _state.STATE_PATH,
        (_state, "EQUITY_LOG"): _state.EQUITY_LOG,
    }
    _journal.JOURNAL_DIR = tmp / "journal"
    _journal.TRADES = tmp / "journal" / "decisions.jsonl"
    _journal.LETTERS = tmp / "journal" / "letters"
    _risk.DAY_STATE = tmp / "journal" / "day_state.json"
    _state.STATE_PATH = tmp / "dashboard" / "state.json"
    _state.EQUITY_LOG = tmp / "journal" / "equity.jsonl"
    return saved, tmp


def run_selftest(cfg: Config) -> int:
    saved, tmp = _sandbox_paths()
    try:
        return _run_selftest(cfg, tmp)
    finally:
        for (module, name), value in saved.items():
            setattr(module, name, value)
        shutil.rmtree(tmp, ignore_errors=True)


def _run_selftest(cfg: Config, tmp: "Path") -> int:
    cfg.universe = ["SELF"]
    bot = Pythia.__new__(Pythia)
    bot.cfg, bot.dry_run = cfg, True
    bot.md, bot.analyst = _FakeMD(), _FakeAnalyst()
    bot.gates, bot.journal = RiskGates(cfg), Journal(cfg)
    bot.executor, bot.last_gate_report = None, []

    bot.cycle()

    state_path = _state.STATE_PATH
    assert state_path.exists(), "state.json was not written"
    state = json.loads(state_path.read_text())
    decisions = state.get("decisions", [])
    dry = [d for d in decisions if d.get("action") == "dry_run"]
    assert dry, f"expected a dry_run decision, got {[d.get('action') for d in decisions]}"
    assert state["account"]["equity"] == 100000.0
    assert dry[0].get("gates"), "gate report missing from decision"
    assert all(g["passed"] for g in dry[0]["gates"]), \
        f"gates failed: {[g for g in dry[0]['gates'] if not g['passed']]}"

    print("SELFTEST PASS — full pipeline executed offline:")
    d = dry[0]
    print(f"  {d['symbol']} {d['structure']} x{d['contracts']} @ {d['limit_debit']}")
    print(f"  implied {d['implied_p']} -> inferred {d['inferred_p']} (edge {d['edge']})")
    print(f"  all 8 gates green, journal + dashboard state written to {tmp} (live files untouched)")
    return 0
