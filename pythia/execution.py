"""Order execution through the Alpaca Trading API (paper).

Spreads go up as a single multi-leg (MLEG) limit order at the net debit —
atomic fills, no legging risk. Alpaca's convention for MLEG limit orders:
a positive limit_price is a net debit. Client order ids are deterministic
per (day, structure) so a crashed-and-restarted cycle can't double-enter.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import logging

from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderClass, OrderSide, PositionIntent, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, OptionLegRequest

from .config import Config
from .structures import TradePlan

log = logging.getLogger("pythia.execution")


def _client_order_id(plan: TradePlan) -> str:
    """Deterministic within a 30-minute bucket: a crashed-and-restarted cycle
    can't double-enter, but a setup whose stale order was cancelled can be
    retried in a later bucket without a duplicate-id rejection."""
    now = dt.datetime.now(dt.timezone.utc)
    bucket = now.strftime("%Y%m%d%H") + ("a" if now.minute < 30 else "b")
    raw = f"{bucket}|{plan.opp.symbol}|{plan.structure}|{plan.opp.direction}"
    return "pythia-" + hashlib.sha1(raw.encode()).hexdigest()[:16]


class Executor:
    def __init__(self, cfg: Config, trading: TradingClient):
        self.cfg = cfg
        self.trading = trading

    def submit(self, plan: TradePlan) -> dict:
        coid = _client_order_id(plan)
        try:
            if len(plan.legs) > 1:
                legs = []
                for leg in plan.legs:
                    legs.append(OptionLegRequest(
                        symbol=leg.symbol,
                        ratio_qty=1,
                        side=OrderSide.BUY if leg.side == "buy" else OrderSide.SELL,
                        position_intent=(PositionIntent.BUY_TO_OPEN if leg.side == "buy"
                                         else PositionIntent.SELL_TO_OPEN),
                    ))
                req = LimitOrderRequest(
                    qty=plan.contracts,
                    order_class=OrderClass.MLEG,
                    time_in_force=TimeInForce.DAY,
                    limit_price=plan.limit_debit,
                    legs=legs,
                    client_order_id=coid,
                )
            else:
                leg = plan.legs[0]
                req = LimitOrderRequest(
                    symbol=leg.symbol,
                    qty=plan.contracts,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                    limit_price=plan.limit_debit,
                    client_order_id=coid,
                )
            order = self.trading.submit_order(req)
            log.info("submitted %s x%d @ %.2f (%s) id=%s",
                     plan.structure, plan.contracts, plan.limit_debit,
                     plan.opp.symbol, order.id)
            return {"status": "submitted", "order_id": str(order.id), "client_order_id": coid}
        except APIError as err:
            msg = str(err)
            low = msg.lower()
            if any(w in low for w in ("increment", "tick", "penny")) and plan.limit_debit % 0.05:
                import math as _m
                plan.limit_debit = round(_m.ceil(plan.limit_debit / 0.05) * 0.05, 2)
                log.warning("price-increment reject; retrying at %.2f", plan.limit_debit)
                try:
                    req.limit_price = plan.limit_debit
                    req.client_order_id = coid + "t"
                    order = self.trading.submit_order(req)
                    return {"status": "submitted", "order_id": str(order.id),
                            "client_order_id": coid + "t"}
                except APIError as err2:
                    msg = str(err2)
            if "client_order_id" in msg or "duplicate" in msg.lower():
                log.warning("duplicate order suppressed (%s)", coid)
                return {"status": "duplicate", "client_order_id": coid}
            log.error("order rejected: %s", msg)
            return {"status": "rejected", "error": msg[:300], "client_order_id": coid}

    def flatten_all(self) -> None:
        log.warning("FLATTEN: closing all positions and cancelling open orders")
        self.trading.close_all_positions(cancel_orders=True)
