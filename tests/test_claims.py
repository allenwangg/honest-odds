#!/usr/bin/env python3
"""The README's result section, recomputed from the committed forecast log, so a number there
cannot drift from the data. No network, no keys."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pythia import scoring as S

section = (ROOT / "README.md").read_text().split("## Result, honestly stated", 1)[1].split("\n## ", 1)[0]
rows = [r for r in S.load(ROOT / "data" / "forecasts_scored.jsonl") if not r.get("stale_quote")]
signed = lambda x: f"{x:+.4f}".replace("-", "−")

assert len(rows) == 33 and "33 resolved forecasts" in section
boot = S.cluster_bootstrap(rows)                      # 20,000 draws, seed 0, as in the README
assert boot["groups"] == 6 and "6 independent groups" in section
bm, bp = S.brier(rows, "p_market"), S.brier(rows, "p_model")
assert f"| {bm:.4f} |" in section and f"| {bp:.4f} |" in section, (bm, bp)
assert f"{signed(bp - bm)} [{signed(boot['lo'])}, {signed(boot['hi'])}]" in section
assert f"{boot['p_ge_0']:.0%} of resamples" in section
group, carried = S.influence(rows, by_group=True, top=1)[0]
assert group == "QQQ 2026-09-01" and f"by {signed(carried)} of the {signed(bp - bm)}" in section
assert f"about {S.power(rows)['needed'][0.02]} groups" in section
print("README result section matches data/forecasts_scored.jsonl")
