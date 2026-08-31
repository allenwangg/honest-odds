#!/usr/bin/env python3
"""The implied-probability math must recover known probabilities from
synthetic Black-Scholes prices. No network, no keys."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia import implied

def norm_cdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def bs_call(s, k, t, vol, r=0.0):
    if t <= 0: return max(s - k, 0.0)
    d1 = (math.log(s / k) + (r + vol * vol / 2) * t) / (vol * math.sqrt(t))
    d2 = d1 - vol * math.sqrt(t)
    return s * norm_cdf(d1) - k * math.exp(-r * t) * norm_cdf(d2)

def bs_put(s, k, t, vol, r=0.0):
    return bs_call(s, k, t, vol, r) - s + k * math.exp(-r * t)

S, T, VOL = 500.0, 3 / 252, 0.18
strikes = [round(S + d, 1) for d in range(-15, 16)]  # $1-wide, like SPY
calls = [bs_call(S, k, T, VOL) for k in strikes]
puts  = [bs_put(S, k, T, VOL) for k in strikes]

cc = implied.curve_from_calls(strikes, calls)
pc = implied.curve_from_puts(strikes, puts)
curve = implied.blend(cc, pc)
assert curve, "curve should not be empty"

# recovered P(S>K) must match N(d2) closely at several strikes
for k in [S - 5, S, S + 5]:
    d2 = (math.log(S / k) - VOL * VOL / 2 * T) / (VOL * math.sqrt(T))
    truth = norm_cdf(d2)
    est = implied.prob_above(curve, k)
    assert abs(est - truth) < 0.02, f"K={k}: est {est:.3f} vs truth {truth:.3f}"
    print(f"K={k:<6} truth={truth:.3f} recovered={est:.3f}  ok")

# monotonicity and bounds
ps = [p for _, p in curve]
assert all(ps[i] >= ps[i + 1] - 1e-9 for i in range(len(ps) - 1)), "must be non-increasing"
assert all(0 < p < 1 for p in ps)

# noisy mids (crossed a bit) must still give a legal curve
noisy = [c + (0.03 if i % 3 == 0 else -0.02) for i, c in enumerate(calls)]
nc = implied.curve_from_calls(strikes, noisy)
nps = [p for _, p in nc]
assert all(nps[i] >= nps[i + 1] - 1e-9 for i in range(len(nps) - 1))
assert all(0 < p < 1 for p in nps)
print("noisy-input cleanup ok")

# event strike snapping
ev = implied.event_strikes(500.0, [float(k) for k in range(485, 516)], [-0.01, 0.0, 0.01])
assert ev == [495.0, 500.0, 505.0], ev
print("event strikes ok")
print("ALL IMPLIED TESTS PASSED")

# put-call parity residual: clean BS chain ~0; corrupted chain flagged
clean = implied.parity_residual(strikes, calls, strikes, puts, S)
assert clean is not None and clean < 0.02, clean
stale = implied.parity_residual(strikes, calls, strikes, [p + 0.8 for p in puts], S)
assert stale > 0.5, stale
print(f"parity residual: clean {clean:.3f}, stale {stale:.3f} — detector works")
