"""Alpaca market data: underlying context and organized option chains.

Paper-only by construction: the TradingClient is created with paper=True and
there is deliberately no code path to a live endpoint.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from alpaca.data.enums import OptionsFeed
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import OptionChainRequest, StockBarsRequest, StockLatestTradeRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient

from .config import Config


@dataclass
class OptionQuoteRow:
    symbol: str
    strike: float
    kind: str                 # "C" or "P"
    bid: float
    ask: float
    iv: float | None = None
    delta: float | None = None

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

    @property
    def spread_frac(self) -> float:
        m = self.mid
        return (self.ask - self.bid) / m if m > 0 else 1.0


@dataclass
class ExpirySlice:
    expiry: dt.date
    calls: list[OptionQuoteRow] = field(default_factory=list)   # sorted by strike
    puts: list[OptionQuoteRow] = field(default_factory=list)

    @property
    def dte(self) -> int:
        return (self.expiry - dt.date.today()).days


def parse_occ(symbol: str) -> tuple[str, dt.date, str, float]:
    """'SPY260904C00450000' -> ('SPY', date(2026,9,4), 'C', 450.0)"""
    strike = int(symbol[-8:]) / 1000.0
    kind = symbol[-9]
    ymd = symbol[-15:-9]
    expiry = dt.date(2000 + int(ymd[:2]), int(ymd[2:4]), int(ymd[4:6]))
    root = symbol[:-15]
    return root, expiry, kind, strike


class MarketData:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.trading = TradingClient(cfg.alpaca_key, cfg.alpaca_secret, paper=True)
        self.options = OptionHistoricalDataClient(cfg.alpaca_key, cfg.alpaca_secret)
        self.stocks = StockHistoricalDataClient(cfg.alpaca_key, cfg.alpaca_secret)
        self.feed = OptionsFeed.OPRA if cfg.options_feed == "opra" else OptionsFeed.INDICATIVE

    # ---------- underlying ----------

    def spot(self, symbol: str) -> float:
        trade = self.stocks.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=symbol))
        return float(trade[symbol].price)

    def recent_bars(self, symbol: str, days: int = 12) -> list[dict]:
        start = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days * 2)
        bars = self.stocks.get_stock_bars(
            StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start)
        )
        rows = []
        prev = None
        for bar in bars.data.get(symbol, [])[-days:]:
            close = float(bar.close)
            pct = (close / prev - 1) * 100 if prev else 0.0
            rows.append({"date": bar.timestamp.date().isoformat(), "close": round(close, 2),
                         "pct": round(pct, 2)})
            prev = close
        return rows

    # ---------- options ----------

    def chain_slices(self, symbol: str, spot: float) -> list[ExpirySlice]:
        """Fetch the near-dated chain and organize it into per-expiry slices."""
        today = dt.date.today()
        req = OptionChainRequest(
            underlying_symbol=symbol,
            feed=self.feed,
            expiration_date_gte=today + dt.timedelta(days=self.cfg.min_dte),
            expiration_date_lte=today + dt.timedelta(days=self.cfg.max_dte),
            strike_price_gte=round(spot * 0.94, 2),
            strike_price_lte=round(spot * 1.06, 2),
        )
        snapshots = self.options.get_option_chain(req)
        slices: dict[dt.date, ExpirySlice] = {}
        for occ, snap in snapshots.items():
            quote = getattr(snap, "latest_quote", None)
            if quote is None:
                continue
            bid, ask = float(quote.bid_price or 0), float(quote.ask_price or 0)
            # one-sided quotes (no bid) make the mid half of true value and
            # flatten the whole curve to 0.5 — refuse them at the source
            if ask <= 0 or bid < self.cfg.risk.min_bid:
                continue
            _, expiry, kind, strike = parse_occ(occ)
            greeks = getattr(snap, "greeks", None)
            row = OptionQuoteRow(
                symbol=occ, strike=strike, kind=kind, bid=bid, ask=ask,
                iv=float(snap.implied_volatility) if getattr(snap, "implied_volatility", None) else None,
                delta=float(greeks.delta) if greeks and getattr(greeks, "delta", None) is not None else None,
            )
            sl = slices.setdefault(expiry, ExpirySlice(expiry=expiry))
            (sl.calls if kind == "C" else sl.puts).append(row)
        for sl in slices.values():
            sl.calls.sort(key=lambda r: r.strike)
            sl.puts.sort(key=lambda r: r.strike)
        return sorted(slices.values(), key=lambda s: s.expiry)

    def pick_expiry(self, slices: list[ExpirySlice], min_strikes: int = 6) -> ExpirySlice | None:
        """Nearest expiry with enough listed strikes on both sides to build a curve."""
        for sl in slices:
            if sl.dte < self.cfg.min_dte:
                continue
            if len(sl.calls) >= min_strikes and len(sl.puts) >= min_strikes:
                return sl
        return None
