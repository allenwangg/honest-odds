"""Score a probability forecaster against a market benchmark, and check whether the result is real.

Standard library only, no keys, no network. Works on any forecast log, not just Pythia's.

Input: JSONL, one resolved binary forecast per line:
    {"id": "SPY>757@2026-09-01", "group": "SPY 2026-09-01",
     "p_model": 0.94, "p_market": 0.874, "outcome": 1}
`group` is the unit of independence: forecasts that resolve on the same draw
(strikes on one close, questions about one election) share a group.

    python -m pythia.scoring data/forecasts_scored.jsonl
    python -m pythia.scoring my_log.jsonl --exclude-flag stale_quote --seed 1

The report answers, in order:
  1. Brier for model and market, and the difference.
  2. Is it driven by a few rows? (leave-one-out influence, by row and by group)
  3. Does it survive treating groups as the unit? (cluster bootstrap)
  4. How much data would settle it? (power from the between-group spread)
  5. Is the model calibrated? (reliability table)
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

Z_ALPHA, Z_POWER = 1.96, 0.84          # two-sided 5%, 80% power


def brier(rows: list[dict], key: str) -> float:
    return sum((r[key] - r["outcome"]) ** 2 for r in rows) / len(rows)


def gap(rows: list[dict]) -> float:
    """Brier(model) - Brier(market). Negative means the model is better."""
    return brier(rows, "p_model") - brier(rows, "p_market")


def groups(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        out[str(r.get("group", r.get("id")))].append(r)
    return dict(out)


def influence(rows: list[dict], by_group: bool = False, top: int = 5) -> list[tuple[str, float]]:
    """How much the pooled gap moves toward zero (or past it) when each row/group is dropped.

    Positive = dropping it makes the model look worse, i.e. it was carrying the result."""
    base = gap(rows)
    units = groups(rows) if by_group else {str(r.get("id", i)): [r] for i, r in enumerate(rows)}
    out = []
    for name, members in units.items():
        rest = [r for r in rows if not any(r is m for m in members)]
        if rest:
            out.append((name, gap(rest) - base))
    return sorted(out, key=lambda x: -x[1])[:top]


def cluster_bootstrap(rows: list[dict], n: int = 20000, seed: int = 0) -> dict:
    g = list(groups(rows).values())
    rng = random.Random(seed)
    draws = sorted(gap([r for grp in rng.choices(g, k=len(g)) for r in grp]) for _ in range(n))
    return {"lo": draws[int(0.025 * n)], "hi": draws[int(0.975 * n) - 1],
            "p_ge_0": sum(d >= 0 for d in draws) / n, "groups": len(g)}


def power(rows: list[dict], effects: tuple[float, ...] = (0.01, 0.02)) -> dict:
    """Groups needed to detect a per-group Brier improvement, from the observed between-group s.d."""
    per_group = [gap(v) for v in groups(rows).values()]
    if len(per_group) < 3:
        return {"groups": len(per_group), "sd": None, "needed": {}}
    sd = statistics.stdev(per_group)
    return {"groups": len(per_group), "mean": statistics.mean(per_group), "sd": sd,
            "needed": {e: math.ceil(((Z_ALPHA + Z_POWER) * sd / e) ** 2) for e in effects}}


def reliability(rows: list[dict], key: str = "p_model", bins: int = 5) -> list[dict]:
    out = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        sel = [r for r in rows if lo <= r[key] < hi or (b == bins - 1 and r[key] == 1.0)]
        if sel:
            out.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": len(sel),
                        "mean_p": sum(r[key] for r in sel) / len(sel),
                        "observed": sum(r["outcome"] for r in sel) / len(sel)})
    return out


def report(rows: list[dict], title: str = "Forecast scoring report", seed: int = 0) -> str:
    bm, bp = brier(rows, "p_market"), brier(rows, "p_model")
    boot, pw = cluster_bootstrap(rows, seed=seed), power(rows)
    L = [f"# {title}", "",
         f"{len(rows)} resolved forecasts in {boot['groups']} independent groups.", "",
         "| | Brier (lower is better) |", "|---|---|",
         f"| Market | {bm:.4f} |", f"| Model | {bp:.4f} |",
         f"| Difference | {bp - bm:+.4f} ({100 * (bp - bm) / bm:+.0f}%) |" if bm else "", "",
         "## Is it driven by a few forecasts?", "",
         "Change in the gap if each one is dropped (positive = it was carrying the result):", ""]
    for name, d in influence(rows):
        L.append(f"- row `{name}`: {d:+.4f}")
    for name, d in influence(rows, by_group=True, top=3):
        L.append(f"- group `{name}`: {d:+.4f}")
    L += ["", "## Does it survive treating groups as the unit?", "",
          f"Cluster bootstrap 95% interval for Brier(model) - Brier(market): "
          f"[{boot['lo']:+.4f}, {boot['hi']:+.4f}]; {boot['p_ge_0']:.1%} of resamples at or above zero."
          + (" With fewer than 10 groups this interval is rough." if boot["groups"] < 10 else ""), ""]
    if pw["sd"] is not None:
        L += ["## How much data would settle it?", "",
              f"Between-group s.d. of the gap: {pw['sd']:.4f} (mean {pw['mean']:+.4f}, from {pw['groups']} groups)."]
        for e, k in pw["needed"].items():
            L.append(f"- detect a true improvement of {e} per group at 80% power: ~{k} groups")
        L.append("")
    L += ["## Calibration of the model", "", "| Stated p | n | Mean stated | Observed |", "|---|---|---|---|"]
    for b in reliability(rows):
        L.append(f"| {b['bin']} | {b['n']} | {b['mean_p']:.2f} | {b['observed']:.2f} |")
    return "\n".join(l for l in L if l is not None) + "\n"


def load(path: str | Path) -> list[dict]:
    rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    for r in rows:
        for k in ("p_model", "p_market", "outcome"):
            r[k] = float(r[k])
        if not (0 <= r["p_model"] <= 1 and 0 <= r["p_market"] <= 1 and r["outcome"] in (0.0, 1.0)):
            raise ValueError(f"bad row: {r}")
    return rows


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    ap.add_argument("--exclude-flag", action="append", default=[],
                    help="drop rows where this field is true (set it before outcomes are known)")
    ap.add_argument("--title", default="Forecast scoring report")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    rows = [r for r in load(a.path) if not any(r.get(f) for f in a.exclude_flag)]
    print(report(rows, a.title, a.seed))


if __name__ == "__main__":
    main()
