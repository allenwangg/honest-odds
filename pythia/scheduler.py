"""The cycle: chain -> implied curve -> Claude assessment -> divergence ->
structure -> gates -> execution -> journal -> dashboard state. And the loop
that runs it during regular trading hours only.
"""
from __future__ import annotations

import datetime as dt
import logging
import time

from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest

from . import divergence, implied, structures
from .analyst import Analyst
from .config import Config
from .execution import Executor
from .journal import Journal
from .market_data import MarketData
from .risk import RiskGates
from .state import write_state

log = logging.getLogger("pythia")


def standalone_long_positions(option_positions: list) -> list:
    """Long option positions with no offsetting short in the same underlying+expiry
    (i.e., convex longs, not spread legs). Safe to close outright — no legging risk."""
    from .market_data import parse_occ
    shorts = set()
    for p in option_positions:
        try:
            if float(p.qty) < 0:
                root, expiry, _, _ = parse_occ(p.symbol)
                shorts.add((root, expiry))
        except Exception:
            continue
    out = []
    for p in option_positions:
        try:
            if float(p.qty) <= 0:
                continue
            root, expiry, _, _ = parse_occ(p.symbol)
            if (root, expiry) not in shorts:
                out.append(p)
        except Exception:
            continue
    return out


class Pythia:
    def __init__(self, cfg: Config, dry_run: bool = False):
        self.cfg = cfg
        self.dry_run = dry_run
        self.md = MarketData(cfg)
        self.analyst = Analyst(cfg)
        self.gates = RiskGates(cfg)
        self.executor = Executor(cfg, self.md.trading)
        self.journal = Journal(cfg)
        self.last_gate_report: list[dict] = []

    # ---------- one full cycle ----------

    def cycle(self) -> None:
        account = self.md.trading.get_account()
        equity = float(account.equity)
        halted, day_state = self.gates.check_circuit_breaker(equity)
        clock = self.md.trading.get_clock()
        positions = self.md.trading.get_all_positions()
        option_positions = [p for p in positions
                            if getattr(p.asset_class, "value", "") == "us_option"]
        self._cancel_stale_orders()
        if clock.is_open:
            self._bank_winners(option_positions)
        decisions_out: list[dict] = []

        entries_allowed = clock.is_open and not halted and not self._near_close(clock)
        if not entries_allowed:
            log.info("no new entries (open=%s halted=%s near_close=%s)",
                     clock.is_open, halted, self._near_close(clock))

        if entries_allowed:
            for symbol in self.cfg.universe:
                try:
                    decisions_out.extend(
                        self._evaluate_symbol(symbol, equity, option_positions))
                except Exception:
                    log.exception("symbol %s failed; continuing", symbol)

        recent = self.journal.decisions(limit=50)[::-1]  # newest first; includes this cycle
        write_state(account=account, clock=clock, positions=positions,
                    decisions=recent[:50],
                    gates=self.last_gate_report, halted=halted,
                    day_start_equity=day_state.get("day_start_equity", equity),
                    letter_excerpt=self.journal.latest_letter_excerpt())

    def _evaluate_symbol(self, symbol: str, equity: float, option_positions: list) -> list[dict]:
        out: list[dict] = []
        spot = self.md.spot(symbol)
        slices = self.md.chain_slices(symbol, spot)
        sl = self.md.pick_expiry(slices)
        if sl is None:
            log.info("%s: no usable expiry in window", symbol)
            return out

        # Chain integrity: stale quotes manufacture fake edges. Parity or bust.
        residual = implied.parity_residual(
            [r.strike for r in sl.calls], [r.mid for r in sl.calls],
            [r.strike for r in sl.puts], [r.mid for r in sl.puts], spot)
        if residual is not None and residual > self.cfg.max_parity_residual:
            log.warning("%s: parity residual $%.2f > $%.2f — chain looks stale, skipping",
                        symbol, residual, self.cfg.max_parity_residual)
            return out

        call_curve = implied.curve_from_calls([r.strike for r in sl.calls],
                                              [r.mid for r in sl.calls])
        put_curve = implied.curve_from_puts([r.strike for r in sl.puts],
                                            [r.mid for r in sl.puts])
        curve = implied.blend(call_curve, put_curve)
        if not curve:
            return out

        listed = sorted({r.strike for r in sl.calls})
        events = []
        for strike in implied.event_strikes(spot, listed, self.cfg.event_offsets):
            p = implied.prob_above(curve, strike)
            if p is not None:
                events.append({"strike": strike, "implied_p": round(p, 4)})
        if not events:
            return out
        steep = events[0]["implied_p"] - events[-1]["implied_p"]
        if len(events) >= 2 and steep < 0.25:
            log.warning("%s: implied curve is flat (%.2f drop across strikes) — "
                        "quotes unusable, skipping", symbol, steep)
            return out
        log.info("%s spot %.2f exp %s: implied %s", symbol, spot, sl.expiry,
                 {e['strike']: e['implied_p'] for e in events})

        bars = self.md.recent_bars(symbol)
        vol_context = self._vol_context(bars, sl, spot)
        try:
            news = self.md.recent_news(symbol)
        except Exception:
            news = []
        assessment = self.analyst.assess(symbol, spot, sl.expiry.isoformat(),
                                         sl.dte, bars, events, vol_context, news)
        if assessment is None:
            return out

        opps = divergence.find(symbol, sl.expiry, events, assessment, self.cfg)
        for opp in opps:
            plan = structures.build(opp, sl, equity, self.cfg, spot=spot)
            entry = {
                "symbol": symbol, "expiry": sl.expiry.isoformat(), "strike": opp.strike,
                "direction": opp.direction, "implied_p": round(opp.implied_p, 3),
                "inferred_p": round(opp.inferred_p, 3), "edge": round(opp.edge, 3),
                "confidence": round(opp.confidence, 2), "rationale": opp.rationale,
                "stance": assessment.get("stance", ""),
            }
            if plan is None:
                entry.update({"action": "skipped", "reason": "no viable structure/size"})
                self.journal.record(entry)
                out.append(entry)
                continue

            gate_results = self.gates.evaluate(plan, equity, option_positions)
            self.last_gate_report = [{"gate": g.gate, "passed": g.passed, "detail": g.detail}
                                     for g in gate_results]
            entry.update({
                "structure": plan.structure, "contracts": plan.contracts,
                "limit_debit": plan.limit_debit, "max_loss": plan.max_loss_total,
                "breakeven_p": round(plan.breakeven_prob, 3) if plan.width else None,
                "gates": self.last_gate_report,
            })

            if not RiskGates.approved(gate_results):
                failed = [g.gate for g in gate_results if not g.passed]
                entry.update({"action": "blocked", "reason": ", ".join(failed)})
                log.info("%s blocked by %s", plan.structure, failed)
            elif self.dry_run:
                entry.update({"action": "dry_run"})
                log.info("DRY RUN would submit: %s x%d @ %.2f",
                         plan.structure, plan.contracts, plan.limit_debit)
            else:
                result = self.executor.submit(plan)
                entry.update({"action": result["status"], **result})
            self.journal.record(entry)
            out.append(entry)
        if not opps:
            log.info("%s: no divergence past threshold", symbol)
        return out

    @staticmethod
    def _vol_context(bars: list[dict], sl, spot: float) -> str:
        """Realized vs implied: is the chain paying up for movement or asleep?"""
        pcts = [b["pct"] / 100 for b in bars[1:]]
        rv = None
        if len(pcts) >= 5:
            mean = sum(pcts) / len(pcts)
            var = sum((x - mean) ** 2 for x in pcts) / (len(pcts) - 1)
            rv = (var ** 0.5) * (252 ** 0.5) * 100
        atm = min(sl.calls, key=lambda r: abs(r.strike - spot), default=None)
        iv = atm.iv * 100 if (atm and atm.iv) else None
        parts = []
        if rv is not None:
            parts.append(f"10d realized vol {rv:.1f}%")
        if iv is not None:
            parts.append(f"ATM implied {iv:.1f}%")
        if rv is not None and iv is not None:
            parts.append(f"IV premium {iv - rv:+.1f} pts")
        return ", ".join(parts) or "(n/a)"

    def _cancel_stale_orders(self) -> None:
        """Unfilled limit orders go stale as the market moves; cancel ours so
        the next cycle reprices instead of resting at a dead level."""
        try:
            open_orders = self.md.trading.get_orders(
                GetOrdersRequest(status=QueryOrderStatus.OPEN))
        except Exception:
            log.exception("could not list open orders")
            return
        now = dt.datetime.now(dt.timezone.utc)
        for order in open_orders:
            if not str(order.client_order_id or "").startswith("pythia-"):
                continue
            submitted = getattr(order, "submitted_at", None)
            if submitted is None:
                continue
            age_min = (now - submitted).total_seconds() / 60
            if age_min > self.cfg.cancel_stale_after_min:
                log.info("cancelling stale order %s (%.0f min unfilled)", order.id, age_min)
                try:
                    self.md.trading.cancel_order_by_id(order.id)
                except Exception:
                    log.exception("cancel failed for %s", order.id)

    def _bank_winners(self, option_positions: list) -> None:
        """Final equity is the judged number. A convex long that doubled and
        round-trips back is the classic leaderboard death — so standalone longs
        up past the threshold get closed and banked. Runs even when halted:
        reducing risk is always allowed."""
        for p in standalone_long_positions(option_positions):
            plpc = float(p.unrealized_plpc or 0)
            if plpc >= self.cfg.take_profit_close_plpc:
                log.info("BANKING %s at %+.0f%% (%s)", p.symbol, plpc * 100,
                         "dry run" if self.dry_run else "closing")
                if not self.dry_run:
                    try:
                        self.md.trading.close_position(p.symbol)
                        self.journal.record({"symbol": p.symbol, "action": "banked",
                                             "unrealized_plpc": round(plpc, 3)})
                    except Exception:
                        log.exception("close failed for %s", p.symbol)

    def _near_close(self, clock) -> bool:
        if not clock.is_open:
            return False
        mins = (clock.next_close - dt.datetime.now(dt.timezone.utc)).total_seconds() / 60
        return mins <= self.cfg.risk.stop_entries_min_before_close

    # ---------- loop ----------

    def loop(self) -> None:
        log.info("Pythia loop: every %d min during RTH. Ctrl-C to stop; "
                 "touch KILL to halt entries.", self.cfg.cycle_minutes)
        while True:
            clock = self.md.trading.get_clock()
            if not clock.is_open:
                wait = (clock.next_open - dt.datetime.now(dt.timezone.utc)).total_seconds()
                wait = max(min(wait, 3600), 30)
                log.info("market closed; next open %s — sleeping %ds", clock.next_open, int(wait))
                time.sleep(wait)
                continue
            started = time.time()
            try:
                self.cycle()
            except Exception:
                log.exception("cycle failed; will retry next interval")
            elapsed = time.time() - started
            time.sleep(max(self.cfg.cycle_minutes * 60 - elapsed, 15))
