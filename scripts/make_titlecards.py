#!/usr/bin/env python3
"""Generate video title cards in Pythia's palette.

    python3 scripts/make_titlecards.py            # all cards -> archive/hackathon/video/cards/
    python3 scripts/make_titlecards.py --vertical # 1080x1920 for Shorts

Cut these in at the start, between sections, and at the end. Three seconds
each is plenty.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, LINE = "#12161B", "#2A323B"
PARCH, FADED, GOLD = "#E7E1D3", "#8B94A0", "#CBA84C"

CARDS = [
    ("01_open", "PYTHIA", "the options chain is a prediction market", ""),
    ("02_hidden", "every option price", "is a probability in disguise", ""),
    ("03_curve", "the whole curve", "P( close above K ) at every strike", "Breeden–Litzenberger, 1978"),
    ("04_disagree", "the disagreement", "market says X.  Pythia says Y.", "that gap is the trade"),
    ("05_gates", "eight gates", "no model. no LLM. not negotiable.", "the smart part can be wrong"),
    ("06_graded", "every forecast graded", "Brier scored when it resolves", "against reality and against the market"),
    ("07_end", "PYTHIA", "built solo · paper trading only", "github.com/allenwangg/pythia"),
]


def draw(name: str, big: str, sub: str, foot: str, vertical: bool, outdir: Path) -> Path:
    size = (10.8, 19.2) if vertical else (19.2, 10.8)
    fig = plt.figure(figsize=size, dpi=100, facecolor=INK)
    serif = big.isupper() and len(big) < 12
    big_size = 62 if vertical else 96
    fig.text(0.5, 0.60, big, color=PARCH, ha="center", va="center",
             fontsize=big_size, family="serif" if serif else "monospace",
             fontweight="bold" if serif else "normal")
    fig.text(0.5, 0.47, sub, color=GOLD, ha="center", va="center",
             fontsize=26 if vertical else 34, family="monospace")
    if foot:
        fig.text(0.5, 0.38, foot, color=FADED, ha="center", va="center",
                 fontsize=18 if vertical else 24, family="monospace")
    # hairline rules above and below, for a bit of structure
    for y in (0.68, 0.30):
        fig.add_artist(plt.Line2D([0.22, 0.78], [y, y], color=LINE, lw=1.5,
                                  transform=fig.transFigure))
    out = outdir / f"{name}{'_v' if vertical else ''}.png"
    fig.savefig(out, facecolor=INK)
    plt.close(fig)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vertical", action="store_true", help="1080x1920 for Shorts")
    ap.add_argument("--outdir", default=None)
    a = ap.parse_args()
    outdir = Path(a.outdir) if a.outdir else Path(__file__).resolve().parent.parent / "archive" / "hackathon" / "video" / "cards"
    outdir.mkdir(parents=True, exist_ok=True)
    for name, big, sub, foot in CARDS:
        print("saved", draw(name, big, sub, foot, a.vertical, outdir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
