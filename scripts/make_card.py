#!/usr/bin/env python3
"""Generate a daily social card in Pythia's palette. Post images in ~10 seconds.

  python scripts/make_card.py --day 1 --symbol SPY --strike 505 \
      --implied 31 --inferred 44 --equity 103250 \
      --line "bought the 505/506 call spread, max loss $1,180"

Everything is optional except --symbol/--strike/--implied/--inferred.
Writes journal/card_dayN.png (or --out path).
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, LINE = "#12161B", "#2A323B"
PARCH, FADED, GOLD, SLATE = "#E7E1D3", "#8B94A0", "#CBA84C", "#7C93A6"
GAIN, LOSS = "#7BA886", "#C0655A"


def ncdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def synth_curve(spot: float, vol: float = 0.18, t: float = 3 / 252):
    ks = [spot * (1 + i * 0.001) for i in range(-28, 29)]
    ps = [ncdf((math.log(spot / k) - vol * vol / 2 * t) / (vol * math.sqrt(t))) * 100
          for k in ks]
    return ks, ps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--symbol", default="SPY")
    ap.add_argument("--strike", type=float, required=True)
    ap.add_argument("--implied", type=float, required=True, help="market %, e.g. 31")
    ap.add_argument("--inferred", type=float, required=True, help="Pythia %, e.g. 44")
    ap.add_argument("--spot", type=float, default=None)
    ap.add_argument("--equity", type=float, default=None)
    ap.add_argument("--line", default="", help="one line of context under the chart")
    ap.add_argument("--verdict", default="", help="e.g. 'yesterday: called 62%, closed above ✓'")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    spot = a.spot or a.strike * 0.99
    ks, ps = synth_curve(spot)

    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=INK)
    ax = fig.add_axes([0.07, 0.14, 0.88, 0.50], facecolor=INK)
    ax.plot(ks, ps, color=SLATE, lw=2.5, alpha=0.85)
    ax.fill_between(ks, ps, 0, color=SLATE, alpha=0.05)
    ax.axvline(spot, color=LINE, ls="--", lw=1.2)

    ax.plot([a.strike], [a.implied], marker="D", ms=15, mfc=INK, mec=SLATE, mew=3, zorder=5)
    ax.plot([a.strike], [a.inferred], marker="o", ms=16, color=GOLD, zorder=5)
    ax.plot([a.strike, a.strike], [a.implied, a.inferred], color=GOLD, lw=3, alpha=0.55, zorder=4)
    hi, lo = max(a.implied, a.inferred), min(a.implied, a.inferred)
    ax.annotate(f"{a.inferred - a.implied:+.0f} pts", xy=(a.strike, (hi + lo) / 2),
                xytext=(12, 0), textcoords="offset points", color=GOLD,
                fontsize=17, family="monospace", va="center")
    ax.text(a.strike, hi + 5, "PYTHIA", color=GOLD, fontsize=13, family="monospace", ha="center")
    ax.text(a.strike, lo - 9, "MARKET", color=SLATE, fontsize=13, family="monospace", ha="center")

    for s in ax.spines.values(): s.set_color(LINE)
    ax.tick_params(colors=FADED, labelsize=12)
    ax.set_ylim(0, 100)
    ax.set_ylabel("P( close above K )  %", color=FADED, fontsize=13, family="monospace")

    head = f"{a.symbol} above {a.strike:g}"
    fig.text(0.07, 0.885, head, color=PARCH, fontsize=44, family="serif", fontweight="bold")
    sub = f"market {a.implied:.0f}%   ·   Pythia {a.inferred:.0f}%"
    fig.text(0.072, 0.815, sub, color=GOLD, fontsize=21, family="monospace")

    if a.day:
        fig.text(0.95, 0.885, f"DAY {a.day}", color=FADED, fontsize=20,
                 family="monospace", ha="right")
    if a.equity is not None:
        pnl = a.equity - 100_000
        fig.text(0.95, 0.828, f"equity ${a.equity:,.0f}  ({pnl:+,.0f})",
                 color=GAIN if pnl >= 0 else LOSS, fontsize=16,
                 family="monospace", ha="right")
    if a.verdict:
        fig.text(0.95, 0.782, a.verdict, color=FADED, fontsize=14,
                 family="monospace", ha="right")

    foot = a.line or "defined-risk debit spread · 8 risk gates · every forecast graded"
    fig.text(0.07, 0.045, foot, color=FADED, fontsize=14, family="monospace")
    fig.text(0.95, 0.045, "PYTHIA · the options chain is a prediction market",
             color=LINE, fontsize=13, family="monospace", ha="right")

    out = Path(a.out) if a.out else \
        Path(__file__).resolve().parent.parent / "journal" / f"card_day{a.day or 0}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=INK)
    print(f"saved {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
