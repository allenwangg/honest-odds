#!/usr/bin/env python3
"""pythia/scoring.py on hand-checkable data, plus the real Pythia log. No network, no keys."""
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pythia import scoring as S

def row(i, g, pm, pk, o, **kw):
    return dict(id=str(i), group=g, p_model=pm, p_market=pk, outcome=o, **kw)

# Brier by hand: model (0.9-1)^2=0.01, (0.2-0)^2=0.04 -> 0.025; market 0.25, 0.25 -> 0.25
rows = [row(1, "a", 0.9, 0.5, 1), row(2, "b", 0.2, 0.5, 0)]
assert abs(S.brier(rows, "p_model") - 0.025) < 1e-12
assert abs(S.gap(rows) - (0.025 - 0.25)) < 1e-12

# Influence flags the one broken benchmark quote that carries the result
rows = [row(i, f"g{i % 4}", 0.9, 0.85, 1) for i in range(20)] + [row("bad", "g0", 0.99, 0.49, 1)]
assert S.influence(rows)[0][0] == "bad", S.influence(rows)

# Bootstrap: groups, not rows, are resampled; identical groups give a zero-width interval
same = [row(i, f"g{i}", 0.8, 0.6, 1) for i in range(5)]
b = S.cluster_bootstrap(same, n=200)
assert b["groups"] == 5 and abs(b["lo"] - b["hi"]) < 1e-12 and b["p_ge_0"] == 0.0

# Power shrinks as the target effect grows
pw = S.power([row(i, f"g{i}", 0.6 + 0.05 * (i % 3), 0.6, i % 2) for i in range(12)])
assert pw["needed"][0.01] > pw["needed"][0.02] > 0

# Reliability bins cover every row
assert sum(b["n"] for b in S.reliability(rows)) == len(rows)

# CLI on the real log reproduces the published and corrected numbers
log = ROOT / "data" / "forecasts_scored.jsonl"
if log.exists():
    out = subprocess.run([sys.executable, "-m", "pythia.scoring", str(log)], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    assert "| Market | 0.0566 |" in out and "| Model | 0.0159 |" in out, out
    out = subprocess.run([sys.executable, "-m", "pythia.scoring", str(log), "--exclude-flag", "stale_quote"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert "| Market | 0.0317 |" in out and "| Model | 0.0177 |" in out, out

# Bad input is rejected, not silently scored
with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
    f.write(json.dumps(row(1, "a", 1.3, 0.5, 1)) + "\n")
try:
    S.load(f.name); raise AssertionError("accepted p_model=1.3")
except ValueError:
    pass

print("scoring: all checks passed")
