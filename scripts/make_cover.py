#!/usr/bin/env python3
"""Generate the cover image (1600x900) — synthetic curve if no keys/data."""
import math, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, PANEL, LINE = "#12161B", "#191F26", "#2A323B"
PARCH, FADED, GOLD, SLATE = "#E7E1D3", "#8B94A0", "#CBA84C", "#7C93A6"

def ncdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
S, T, VOL = 500.0, 3/252, 0.18
ks = [S + i * 0.5 for i in range(-24, 25)]
ps = [ncdf((math.log(S/k) - VOL*VOL/2*T) / (VOL*math.sqrt(T))) * 100 for k in ks]

fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=INK)
ax = fig.add_axes([0.08, 0.12, 0.86, 0.52], facecolor=INK)
ax.plot(ks, ps, color=GOLD, lw=3.5, solid_capstyle="round")
ax.fill_between(ks, ps, 0, color=GOLD, alpha=0.07)
ax.axvline(S, color=SLATE, ls="--", lw=1.2, alpha=0.8)
ax.text(S + 0.4, 88, "spot", color=SLATE, fontsize=13, family="monospace")
k_mark = 505.0
p_mark = ncdf((math.log(S/k_mark) - VOL*VOL/2*T) / (VOL*math.sqrt(T))) * 100
ax.plot([k_mark], [p_mark], marker="D", ms=11, mfc=INK, mec=SLATE, mew=2.5)
ax.plot([k_mark], [min(p_mark + 13, 97)], marker="o", ms=12, color=GOLD)
ax.plot([k_mark, k_mark], [p_mark, p_mark + 13], color=GOLD, lw=2, alpha=0.6)
ax.text(k_mark + 0.6, p_mark + 5.5, "the disagreement", color=PARCH,
        fontsize=13, family="monospace")
for spine in ax.spines.values(): spine.set_color(LINE)
ax.tick_params(colors=FADED, labelsize=11)
ax.set_ylim(0, 100); ax.set_xlim(ks[0], ks[-1])
ax.set_ylabel("P( close above K )  %", color=FADED, fontsize=12, family="monospace")
fig.text(0.08, 0.87, "PYTHIA", color=PARCH, fontsize=52, family="serif",
         fontweight="bold")
fig.text(0.082, 0.795, "the options chain is a prediction market",
         color=GOLD, fontsize=19, family="monospace")
fig.text(0.08, 0.045, "Alpaca AI Trading Agents Hackathon · Aug 28 – Sep 4 2026 · built solo, gated eightfold",
         color=FADED, fontsize=12, family="monospace")
out = Path(sys.argv[1] if len(sys.argv) > 1 else "cover.png")
fig.savefig(out, facecolor=INK)
print(f"saved {out}")
