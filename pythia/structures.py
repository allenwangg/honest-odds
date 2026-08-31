"""Turn a probability edge into a defined-risk options structure.

If Pythia thinks P(S > K) is HIGHER than implied  -> tight call debit spread
bracketing K (long the strike at/below K, short the next strike up). The spread's
price/width ratio is the market's binary quote; we buy it because we think the
true probability is higher. Mirror with put debit spreads for "below".

Everything is a net debit. Max loss = debit paid. Nothing here can be unbounded,
and the risk gates verify that independently.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import Config
from .divergence import Opportunity
from .market_data import ExpirySlice, OptionQuoteRow


@dataclass
class Leg:
    symbol: str
    side: str          # "buy" | "sell"
    row: OptionQuoteRow


@dataclass
class TradePlan:
    opp: Opportunity
    legs: list[Leg] = field(default_factory=list)
    contracts: int = 0
    width: float = 0.0
    net_mid: float = 0.0            # per-contract debit at mid
    net_conservative: float = 0.0   # long at ask, short at bid (worst realistic fill)
    limit_debit: float = 0.0        # what we'll actually post
    structure: str = ""

    @property
    def max_loss_total(self) -> float:
        return round(self.limit_debit * 100 * self.contracts, 2)

    @property
    def breakeven_prob(self) -> float:
        """Debit/width = the probability the market is charging for this binary."""
        return self.limit_debit / self.width if self.width else 1.0


def _bracket(rows: list[OptionQuoteRow], strike: float,
             min_width: float) -> tuple[OptionQuoteRow, OptionQuoteRow] | None:
    below = [r for r in rows if r.strike <= strike]
    if not below:
        return None
    lo = below[-1]
    above = [r for r in rows if r.strike >= lo.strike + min_width and r.strike > strike]
    if not above:
        return None
    return lo, above[0]


def build(opp: Opportunity, sl: ExpirySlice, equity: float, cfg: Config,
          spot: float | None = None) -> TradePlan | None:
    plan = TradePlan(opp=opp)

    # Convexity mode: on high-conviction edges, take the uncapped payoff of a
    # straight long option instead of the spread's width-capped binary. Costs
    # more theta, wins the right tail — which is what a 4-day leaderboard pays.
    convex = (cfg.convexity_mode
              and abs(opp.edge) >= cfg.convexity_min_edge
              and opp.confidence >= cfg.convexity_min_conf)

    min_width = cfg.min_spread_width_frac * opp.strike
    if cfg.allow_spreads and not convex:
        if opp.direction == "above":
            pair = _bracket(sl.calls, opp.strike, min_width)
            if not pair:
                return None
            long_row, short_row = pair
            plan.structure = f"call debit spread {long_row.strike}/{short_row.strike}"
        else:
            above = [r for r in sl.puts if r.strike >= opp.strike]
            if not above:
                return None
            long_row = above[0]
            lower = [r for r in sl.puts if r.strike <= long_row.strike - min_width]
            if not lower:
                return None
            short_row = lower[-1]
            plan.structure = f"put debit spread {long_row.strike}/{short_row.strike}"
        plan.legs = [Leg(long_row.symbol, "buy", long_row), Leg(short_row.symbol, "sell", short_row)]
        plan.width = abs(long_row.strike - short_row.strike)
        plan.net_mid = round(long_row.mid - short_row.mid, 2)
        plan.net_conservative = round(long_row.ask - short_row.bid, 2)
    else:
        rows = sl.calls if opp.direction == "above" else sl.puts
        anchor = spot if spot is not None else opp.strike
        if opp.direction == "above":
            otm = [r for r in rows if r.strike >= anchor]
            near = otm[0] if otm else None
        else:
            otm = [r for r in rows if r.strike <= anchor]
            near = otm[-1] if otm else None
        if near is None:
            return None
        kind = "call" if opp.direction == "above" else "put"
        plan.structure = f"{'convex ' if convex else ''}long {kind} {near.strike}"
        plan.legs = [Leg(near.symbol, "buy", near)]
        plan.width = 0.0
        plan.net_mid = round(near.mid, 2)
        plan.net_conservative = round(near.ask, 2)

    if plan.net_mid <= 0:
        return None
    friction = max(plan.net_conservative - plan.net_mid, 0.0)
    plan.limit_debit = round(plan.net_mid + max(cfg.slippage_buffer, cfg.cross_frac * friction), 2)
    if plan.width:
        if plan.limit_debit >= plan.width:
            return None
        if plan.limit_debit / plan.width > cfg.max_breakeven_prob:
            return None

    # Kelly-lite sizing on the edge, hard-capped by the per-trade risk budget.
    frac = min(max(cfg.kelly_scalar * abs(opp.edge) * opp.confidence, 0.0),
               cfg.risk.per_trade_max_frac)
    risk_dollars = equity * frac
    per_contract = plan.net_conservative * 100
    if per_contract <= 0:
        return None
    plan.contracts = int(risk_dollars // per_contract)
    if plan.contracts < 1:
        return None
    return plan
