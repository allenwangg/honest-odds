#!/usr/bin/env python3
"""Print (and save) the market-implied probability curve for an underlying.
Great video B-roll: 'here is SPY's probability distribution, read off the chain.'
Usage: python scripts/show_curve.py SPY
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia.config import Config
from pythia.market_data import MarketData
from pythia import implied

symbol = (sys.argv[1] if len(sys.argv) > 1 else "SPY").upper()
cfg = Config.load(); cfg.require_keys(need_anthropic=False)
md = MarketData(cfg)
spot = md.spot(symbol)
sl = md.pick_expiry(md.chain_slices(symbol, spot))
if sl is None:
    sys.exit("no usable expiry")
curve = implied.blend(
    implied.curve_from_calls([r.strike for r in sl.calls], [r.mid for r in sl.calls]),
    implied.curve_from_puts([r.strike for r in sl.puts], [r.mid for r in sl.puts]))
print(f"{symbol} spot {spot:.2f} — P(close above K) at {sl.expiry} ({sl.dte} DTE)\n")
for k, p in curve:
    bar = "#" * int(p * 40)
    mark = " <- spot" if abs(k - spot) == min(abs(x - spot) for x, _ in curve) else ""
    print(f"  {k:8.1f}  {p*100:5.1f}%  {bar}{mark}")
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ks, ps = zip(*curve)
    plt.figure(figsize=(8, 4.2), facecolor="#12161B")
    ax = plt.gca(); ax.set_facecolor("#12161B")
    plt.plot(ks, [p * 100 for p in ps], color="#CBA84C", lw=2)
    plt.axvline(spot, color="#7C93A6", ls="--", lw=1)
    plt.title(f"{symbol}: market-implied P(close above K), {sl.expiry}", color="#E7E1D3")
    plt.xlabel("strike", color="#8B94A0"); plt.ylabel("%", color="#8B94A0")
    ax.tick_params(colors="#8B94A0")
    for s in ax.spines.values(): s.set_color("#2A323B")
    out = Path(__file__).resolve().parent.parent / "journal" / f"curve_{symbol}.png"
    out.parent.mkdir(exist_ok=True)
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#12161B")
    print(f"\nsaved {out}")
except ImportError:
    print("\n(pip install matplotlib for the PNG version)")
