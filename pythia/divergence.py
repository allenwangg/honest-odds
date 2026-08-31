"""Compare market-implied vs Pythia-inferred probabilities and rank the gaps."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .config import Config


@dataclass
class Opportunity:
    symbol: str
    expiry: dt.date
    strike: float
    direction: str        # "above" (we think P(S>K) is higher than implied) or "below"
    implied_p: float      # market's P(S > K)
    inferred_p: float     # Pythia's P(S > K)
    confidence: float
    rationale: str

    @property
    def edge(self) -> float:
        return self.inferred_p - self.implied_p

    @property
    def score(self) -> float:
        return abs(self.edge) * self.confidence


def find(symbol: str, expiry: dt.date, implied_events: list[dict],
         assessment: dict, cfg: Config) -> list[Opportunity]:
    by_strike = {round(e["strike"], 2): e for e in assessment["events"]}
    opps: list[Opportunity] = []
    for ev in implied_events:
        strike = round(ev["strike"], 2)
        inferred = by_strike.get(strike)
        if not inferred:
            continue
        # Calibration shrinkage: pull the analyst toward the market prior by
        # (1 - edge_shrinkage). scripts/calibrate.py estimates the right λ
        # from resolved forecasts; 1.0 = trust the analyst's raw number.
        shrunk_p = ev["implied_p"] + cfg.edge_shrinkage * (inferred["p_above"] - ev["implied_p"])
        edge = shrunk_p - ev["implied_p"]
        if abs(edge) < cfg.edge_threshold or inferred["confidence"] < cfg.min_confidence:
            continue
        opps.append(Opportunity(
            symbol=symbol, expiry=expiry, strike=strike,
            direction="above" if edge > 0 else "below",
            implied_p=ev["implied_p"], inferred_p=round(shrunk_p, 4),
            confidence=inferred["confidence"], rationale=inferred["rationale"],
        ))
    opps.sort(key=lambda o: o.score, reverse=True)
    return opps[: cfg.max_trades_per_cycle]
