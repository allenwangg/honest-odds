#!/usr/bin/env python3
"""Offline robustness check for CALIBRATION.md. No API keys, no network.

Scores the same 37 forecasts as scripts/calibrate.py (last forecast per
symbol/expiry/strike, SPY and QQQ), then asks how much of the result survives:
  1. dropping the four 0DTE quotes on Aug 31 that the model itself flagged as
     stale (market "probability" ~0.49 on strikes 1-2.5% in the money),
  2. scoring by cluster (symbol x expiry), since strikes sharing one close
     are not independent draws,
  3. a cluster bootstrap of the Brier difference.

Settlement data lives in data/closes.json, with sources.

    python scripts/robustness.py
"""
import json, random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = [json.loads(l) for l in (ROOT / "journal" / "decisions.jsonl").read_text().splitlines() if l.strip()]
settle = json.loads((ROOT / "data" / "closes.json").read_text())

def outcome(sym, expiry, strike):
    s = settle[sym][expiry]
    if "close" in s:
        return 1.0 if s["close"] > strike else 0.0
    lo, hi = s["bounds"]
    assert strike <= lo or strike >= hi, f"{sym} {expiry} {strike}: inside settlement bounds, need the real close"
    return 1.0 if strike <= lo else 0.0

last = {}
for r in rows:
    if r.get("symbol") in ("SPY", "QQQ") and all(k in r for k in ("expiry", "strike", "inferred_p", "implied_p")):
        last[(r["symbol"], r["expiry"], float(r["strike"]))] = r      # later rows overwrite: last of session
F = [dict(sym=k[0], exp=k[1], k=k[2], p=float(r["inferred_p"]), m=float(r["implied_p"]),
          o=outcome(*k), action=r.get("action")) for k, r in sorted(last.items())]

def brier(xs, f): return sum((x[f] - x["o"]) ** 2 for x in xs) / len(xs)

def line(name, xs):
    if not xs:
        return f"| {name} | 0 | | | |"
    bm, bp = brier(xs, "m"), brier(xs, "p")
    return f"| {name} | {len(xs)} | {bm:.4f} | {bp:.4f} | {100 * (bp - bm) / bm:+.0f}% |"

stale = lambda x: x["exp"] == "2026-08-31"          # the four 0DTE quotes at 0.477-0.492
clean = [x for x in F if not stale(x)]
print("| Subset | n | Market | Pythia | Δ |\n|---|---|---|---|---|")
for tag, S in (("as published", F), ("stale quotes removed", clean)):
    print(line(f"All ({tag})", S))
    print(line(f"Market 25-75% ({tag})", [x for x in S if .25 <= x["m"] <= .75]))
    print(line(f"Market 40-60% ({tag})", [x for x in S if .40 <= x["m"] <= .60]))
for name, sel in (("SPY", lambda x: x["sym"] == "SPY"), ("QQQ", lambda x: x["sym"] == "QQQ"),
                  ("More bullish than chain", lambda x: x["p"] > x["m"]),
                  ("More bearish than chain", lambda x: x["p"] < x["m"]),
                  ("Wings (market <15% or >85%)", lambda x: not .15 <= x["m"] <= .85),
                  ("Interior (market 15-85%)", lambda x: .15 <= x["m"] <= .85)):
    print(line(f"{name} (clean)", [x for x in clean if sel(x)]))

print("\nRemoved as stale:")
for x in F:
    if stale(x):
        print(f"  {x['sym']} {x['k']:.0f} {x['exp']}: market {x['m']:.3f}, Pythia {x['p']:.3f}, finished {'above' if x['o'] else 'below'}")
print("Forecasts where Pythia scored worse than the market:")
for x in F:
    if (x["p"] - x["o"]) ** 2 > (x["m"] - x["o"]) ** 2:
        print(f"  {x['sym']} {x['k']:.0f} {x['exp']}: market {x['m']:.3f}, Pythia {x['p']:.3f}, finished {'above' if x['o'] else 'below'} ({x['action']})")

for tag, S in (("as published", F), ("clean", clean)):
    C = defaultdict(list)
    for x in S:
        C[(x["sym"], x["exp"])].append(x)
    wins = sum(brier(v, "p") < brier(v, "m") for v in C.values())
    random.seed(0)
    keys, diffs = list(C), []
    for _ in range(20000):
        s = [x for k in random.choices(keys, k=len(keys)) for x in C[k]]
        diffs.append(brier(s, "p") - brier(s, "m"))
    diffs.sort()
    print(f"\nClusters ({tag}): {len(C)}; Pythia lower Brier in {wins}. "
          f"Cluster-bootstrap 95% CI for Brier(Pythia) - Brier(market): "
          f"[{diffs[500]:+.4f}, {diffs[19499]:+.4f}]; share of resamples >= 0: {sum(d >= 0 for d in diffs) / len(diffs):.1%}")

# Export in the generic format pythia/scoring.py reads, so the same checks run on
# this log or any other:  python -m pythia.scoring data/forecasts_scored.jsonl
out = ROOT / "data" / "forecasts_scored.jsonl"
with out.open("w") as f:
    for x in F:
        f.write(json.dumps({"id": f"{x['sym']}>{x['k']:g}@{x['exp']}", "group": f"{x['sym']} {x['exp']}",
                            "p_model": x["p"], "p_market": x["m"], "outcome": int(x["o"]),
                            "stale_quote": stale(x), "action": x["action"]}) + "\n")
print(f"\nwrote {out.relative_to(ROOT)} ({len(F)} rows)")
