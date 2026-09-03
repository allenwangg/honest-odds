"""The inference side: Claude forms independent probability estimates.

Design rules:
- The analyst sees the market-implied numbers (that IS the trade: divergence),
  but is explicitly instructed to reason to its own estimate first.
- Output is strict JSON, schema-validated and clamped. Any parse or validation
  failure returns None and the cycle trades nothing. Fail closed, always.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from .config import ROOT, Config
from .llm import complete

log = logging.getLogger("pythia.analyst")

SYSTEM = """You are Pythia, a disciplined probabilistic forecaster for short-dated
equity index and single-name options. You estimate P(underlying closes above K at
expiry) for specific strikes. You think like a superforecaster: base rates first,
then adjust for the current regime, price action, and any scheduled catalysts in
the notes. You are calibrated — a 0.60 from you should be right 60% of the time.
You know the market-implied probabilities and you respect them: they are your
prior, and you deviate only when you can articulate why. Small divergences are
normal; large confident divergences are rare. Overconfidence loses money.
Respond with STRICT JSON only. No markdown, no code fences, no prose outside JSON."""

PROMPT_TEMPLATE = """UNDERLYING: {symbol}   SPOT: {spot}   EXPIRY: {expiry} ({dte} DTE)
VOL REGIME: {vol}
LATEST HEADLINES (Alpaca News, newest first; may be empty):
{news}

RECENT DAILY BARS (date, close, pct change):
{bars}

MACRO / CATALYST NOTES (human-maintained, may be empty):
{macro}

MARKET-IMPLIED PROBABILITIES (from the options chain, P(S > K) at expiry):
{events}

TASK: For each strike above, give YOUR independent probability that {symbol}
closes ABOVE that strike at expiry, plus a confidence (0-1) in your estimate
relative to the market's, and a one-sentence rationale (<=200 chars).

Return exactly this JSON shape:
{{"events": [{{"strike": <number>, "p_above": <0..1>, "confidence": <0..1>,
"rationale": "<string>"}}], "stance": "<one sentence overall view>"}}"""


class Analyst:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def _macro_notes(self) -> str:
        path = ROOT / "notes" / "macro.md"
        if path.exists():
            return path.read_text().strip()[:4000]
        return "(none)"

    def assess(self, symbol: str, spot: float, expiry: str, dte: int,
               bars: list[dict], events: list[dict],
               vol_context: str = "(n/a)",
               news: list[str] | None = None) -> dict | None:
        """events: [{"strike": float, "implied_p": float}] -> validated assessment or None."""
        bars_txt = "\n".join(f"  {b['date']}  {b['close']}  {b['pct']:+.2f}%" for b in bars) or "  (none)"
        events_txt = "\n".join(f"  K={e['strike']}: implied P(above) = {e['implied_p']:.3f}"
                               for e in events)
        prompt = PROMPT_TEMPLATE.format(symbol=symbol, spot=round(spot, 2), expiry=expiry,
                                        dte=dte, bars=bars_txt, macro=self._macro_notes(),
                                        events=events_txt, vol=vol_context,
                                        news="\n".join(f"  {h}" for h in (news or [])) or "  (none)")
        for attempt in (1, 2):
            try:
                suffix = "" if attempt == 1 else \
                    "\n\nREMINDER: reply with ONLY the JSON object. No other text."
                text = complete(SYSTEM, prompt + suffix, self.cfg,
                                max_tokens=self.cfg.analyst_max_tokens)
                result = self._validate(text, events)
                if result is not None:
                    return result
                log.warning("analyst output invalid (attempt %d)", attempt)
            except Exception:
                log.exception("analyst call failed (attempt %d)", attempt)
        log.error("analyst failed twice — trading nothing this cycle (fail closed)")
        return None

    def _validate(self, text: str, events: list[dict]) -> dict | None:
        text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            log.error("analyst returned non-JSON output — fail closed")
            return None
        if not isinstance(data, dict) or not isinstance(data.get("events"), list):
            log.error("analyst JSON missing 'events' list — fail closed")
            return None
        wanted = {round(float(e["strike"]), 2) for e in events}
        clean = []
        for ev in data["events"]:
            try:
                strike = round(float(ev["strike"]), 2)
                p = float(ev["p_above"])
                conf = float(ev["confidence"])
            except (KeyError, TypeError, ValueError):
                continue
            if strike not in wanted or not (0 <= p <= 1) or not (0 <= conf <= 1):
                continue
            clean.append({"strike": strike,
                          "p_above": min(max(p, 0.01), 0.99),
                          "confidence": min(max(conf, 0.0), 1.0),
                          "rationale": str(ev.get("rationale", ""))[:220]})
        if not clean:
            log.error("analyst JSON had no valid events — fail closed")
            return None
        return {"events": clean, "stance": str(data.get("stance", ""))[:300]}
