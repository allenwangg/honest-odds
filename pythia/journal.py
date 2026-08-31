"""Decision journal: every decision (traded or not) as JSONL, plus daily fund letters.

The journal is the write-up, the demo narration, and the engagement content.
An agent that can show its reasoning trail beats a black box on the
'creativity' axis, whatever the P&L says.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

from .config import ROOT, Config
from .llm import complete

log = logging.getLogger("pythia.journal")
JOURNAL_DIR = ROOT / "journal"
TRADES = JOURNAL_DIR / "decisions.jsonl"
LETTERS = JOURNAL_DIR / "letters"

LETTER_SYSTEM = """You are the portfolio manager writing Pythia's daily letter —
a short, honest, lightly wry note in the voice of a quant PM who reads the
options chain like a prediction market. 250-400 words. Structure: what the
market believed, where we disagreed, what we did about it, what it cost or
paid, one lesson. Never hype. Numbers over adjectives. Sign off as 'Pythia'."""


class Journal:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        JOURNAL_DIR.mkdir(exist_ok=True)
        LETTERS.mkdir(exist_ok=True)

    def record(self, entry: dict) -> None:
        entry = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(), **entry}
        with TRADES.open("a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def decisions(self, day: dt.date | None = None, limit: int = 200) -> list[dict]:
        if not TRADES.exists():
            return []
        rows = []
        for line in TRADES.read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if day and not row.get("ts", "").startswith(day.isoformat()):
                continue
            rows.append(row)
        return rows[-limit:]

    def fund_letter(self, day: dt.date | None = None, account_summary: dict | None = None) -> Path:
        day = day or dt.date.today()
        rows = self.decisions(day)
        payload = {
            "date": day.isoformat(),
            "account": account_summary or {},
            "decisions": rows[:60],
        }
        text = complete(LETTER_SYSTEM,
                        "Today's journal as JSON:\n" + json.dumps(payload, default=str),
                        self.cfg, max_tokens=900)
        path = LETTERS / f"{day.isoformat()}.md"
        path.write_text(f"# Pythia daily letter — {day.isoformat()}\n\n{text}\n")
        log.info("fund letter written: %s", path)
        return path

    def latest_letter_excerpt(self, chars: int = 700) -> str:
        letters = sorted(LETTERS.glob("*.md"))
        if not letters:
            return ""
        return letters[-1].read_text()[:chars]
