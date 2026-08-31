"""Risk gates. Every trade passes ALL of these or it does not exist.

G1  Defined-risk only     — net debit, bounded max loss, never a naked short
G2  Per-trade budget      — max loss <= per_trade_max_frac of equity
G3  Portfolio heat        — open option cost basis + new debit <= heat cap
G4  Daily circuit breaker — drawdown from day-start equity halts new entries
G5  Liquidity             — real bids on every leg, spreads within tolerance
G6  Kill switch           — a KILL file in the repo root halts everything
G7  Concentration         — per-underlying exposure cap
G8  Sanity                — probabilities and prices internally consistent

The gates are deliberately dumb: no model, no ML, no LLM. The intelligence
upstream can be wrong; these cannot be argued with. LLM output that fails
schema validation never even reaches them (the analyst fails closed).
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import dataclass

from .config import ROOT, Config
from .structures import TradePlan

log = logging.getLogger("pythia.risk")
DAY_STATE = ROOT / "journal" / "day_state.json"
KILL_FILE = ROOT / "KILL"


@dataclass
class GateResult:
    gate: str
    passed: bool
    detail: str


class RiskGates:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    # ---------- day state / circuit breaker ----------

    def day_state(self, equity: float) -> dict:
        today = dt.date.today().isoformat()
        state = {}
        if DAY_STATE.exists():
            try:
                state = json.loads(DAY_STATE.read_text())
            except json.JSONDecodeError:
                state = {}
        if state.get("date") != today:
            state = {"date": today, "day_start_equity": equity, "halted": False}
            self._save(state)
        return state

    def check_circuit_breaker(self, equity: float) -> tuple[bool, dict]:
        state = self.day_state(equity)
        start = state.get("day_start_equity") or equity
        drawdown = (start - equity) / start if start else 0.0
        if drawdown >= self.cfg.risk.daily_loss_halt_frac and not state.get("halted"):
            state["halted"] = True
            self._save(state)
            log.warning("CIRCUIT BREAKER: day drawdown %.2f%% >= %.2f%% — halting new entries",
                        drawdown * 100, self.cfg.risk.daily_loss_halt_frac * 100)
        return bool(state.get("halted")), state

    def _save(self, state: dict) -> None:
        DAY_STATE.parent.mkdir(parents=True, exist_ok=True)
        DAY_STATE.write_text(json.dumps(state, indent=2))

    # ---------- the gates ----------

    def evaluate(self, plan: TradePlan, equity: float, option_positions: list) -> list[GateResult]:
        r = self.cfg.risk
        results: list[GateResult] = []

        # G6 first: kill switch beats everything
        killed = KILL_FILE.exists()
        results.append(GateResult("G6 kill switch", not killed,
                                  "KILL file present" if killed else "clear"))

        # G1 defined risk
        is_debit = plan.limit_debit > 0
        buy_legs = sum(1 for leg in plan.legs if leg.side == "buy")
        sell_legs = sum(1 for leg in plan.legs if leg.side == "sell")
        covered = sell_legs == 0 or (buy_legs >= sell_legs and plan.width > 0)
        results.append(GateResult("G1 defined risk", is_debit and covered,
                                  f"debit {plan.limit_debit:.2f}, {buy_legs}L/{sell_legs}S, width {plan.width}"))

        # G2 per-trade budget
        budget = equity * r.per_trade_max_frac
        results.append(GateResult("G2 per-trade budget", plan.max_loss_total <= budget,
                                  f"max loss ${plan.max_loss_total:,.0f} vs budget ${budget:,.0f}"))

        # G3 portfolio heat (long-debit book: cost basis is the max-loss proxy)
        open_heat = sum(abs(float(p.cost_basis or 0)) for p in option_positions)
        heat_cap = equity * r.portfolio_heat_frac
        results.append(GateResult("G3 portfolio heat",
                                  open_heat + plan.max_loss_total <= heat_cap,
                                  f"open ${open_heat:,.0f} + new ${plan.max_loss_total:,.0f} vs cap ${heat_cap:,.0f}"))

        # G4 circuit breaker
        halted, _ = self.check_circuit_breaker(equity)
        results.append(GateResult("G4 circuit breaker", not halted,
                                  "halted for the day" if halted else "clear"))

        # G5 liquidity
        liq_ok, liq_detail = True, []
        for leg in plan.legs:
            if leg.row.bid < r.min_bid:
                liq_ok, _ = False, liq_detail.append(f"{leg.row.symbol} no bid")
            elif leg.row.spread_frac > r.max_spread_frac:
                liq_ok, _ = False, liq_detail.append(
                    f"{leg.row.symbol} spread {leg.row.spread_frac:.0%}")
        results.append(GateResult("G5 liquidity", liq_ok, "; ".join(liq_detail) or "tight"))

        # G7 concentration per underlying — correlation-aware: SPY and QQQ are
        # ~0.9 correlated, so they share one bucket (with a modestly larger cap)
        under = plan.opp.symbol
        index_bucket = {"SPY", "QQQ"}
        bucket = index_bucket if under in index_bucket else {under}
        bucket_mult = 1.5 if len(bucket) > 1 else 1.0
        open_under = sum(abs(float(p.cost_basis or 0)) for p in option_positions
                         if any(str(p.symbol).startswith(b) for b in bucket))
        under_cap = equity * r.per_underlying_frac * bucket_mult
        results.append(GateResult("G7 concentration",
                                  open_under + plan.max_loss_total <= under_cap,
                                  f"{'/'.join(sorted(bucket))}: ${open_under:,.0f} + ${plan.max_loss_total:,.0f} vs ${under_cap:,.0f}"))

        # G8 sanity: our own edge math must survive the actual entry price
        be = plan.breakeven_prob if plan.width else None
        if be is not None:
            wants_above = plan.opp.direction == "above"
            edge_at_fill = (plan.opp.inferred_p - be) if wants_above else ((1 - plan.opp.inferred_p) - be)
            sane = 0 < be < 1 and edge_at_fill > 0
            detail = f"breakeven p {be:.2f} vs inferred {plan.opp.inferred_p:.2f}"
        else:
            sane = plan.limit_debit > 0
            detail = "single leg debit"
        results.append(GateResult("G8 sanity", sane, detail))

        return results

    @staticmethod
    def approved(results: list[GateResult]) -> bool:
        return all(g.passed for g in results)
