"""Market-implied probabilities from option prices. Pure functions, no I/O.

The idea (and the whole product thesis): under the risk-neutral measure,
P(S_T > K) ~= -dC/dK  — the negative slope of the call-price curve in strike.
A tight call spread around K is literally a binary contract on "S above K".
So the options chain *is* a prediction market; we just read its prices.

We estimate the slope with finite differences between adjacent listed strikes,
after forcing no-arbitrage monotonicity on the input mids, and blend the same
estimate derived from puts (P(S_T > K) = 1 - dP/dK) for robustness.
"""
from __future__ import annotations

from bisect import bisect_left

PMIN, PMAX = 0.005, 0.995


def _pav_up(values: list[float]) -> list[float]:
    """Isotonic regression (pool-adjacent-violators). A single bad quote gets
    averaged into its neighbours instead of capping the entire curve."""
    blocks: list[list[float]] = []
    for v in values:
        blocks.append([v, 1.0])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            s, c = blocks.pop()
            blocks[-1][0] += s
            blocks[-1][1] += c
    out: list[float] = []
    for s, c in blocks:
        out.extend([s / c] * int(c))
    return out


def _monotone_down(values: list[float]) -> list[float]:
    return [-v for v in _pav_up([-v for v in values])]


def _monotone_up(values: list[float]) -> list[float]:
    return _pav_up(values)


def curve_from_calls(strikes: list[float], mids: list[float]) -> list[tuple[float, float]]:
    """[(K_mid, P(S>K_mid)), ...] from call mids via -dC/dK at strike midpoints."""
    if len(strikes) < 3:
        return []
    mids = _monotone_down(mids)
    curve = []
    for i in range(len(strikes) - 1):
        dk = strikes[i + 1] - strikes[i]
        if dk <= 0:
            continue
        p = (mids[i] - mids[i + 1]) / dk          # -dC/dK
        k_mid = (strikes[i] + strikes[i + 1]) / 2
        curve.append((k_mid, min(max(p, PMIN), PMAX)))
    return _clean(curve)


def curve_from_puts(strikes: list[float], mids: list[float]) -> list[tuple[float, float]]:
    """P(S>K) = 1 - dP/dK from put mids (puts rise with strike)."""
    if len(strikes) < 3:
        return []
    mids = _monotone_up(mids)
    curve = []
    for i in range(len(strikes) - 1):
        dk = strikes[i + 1] - strikes[i]
        if dk <= 0:
            continue
        p = 1.0 - (mids[i + 1] - mids[i]) / dk
        k_mid = (strikes[i] + strikes[i + 1]) / 2
        curve.append((k_mid, min(max(p, PMIN), PMAX)))
    return _clean(curve)


def _clean(curve: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not curve:
        return []
    ps = _monotone_down([p for _, p in curve])
    return [(k, min(max(p, PMIN), PMAX)) for (k, _), p in zip(curve, ps)]


def blend(call_curve: list[tuple[float, float]],
          put_curve: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Average the two estimates on the call curve's strike grid."""
    if not call_curve:
        return put_curve
    if not put_curve:
        return call_curve
    blended = []
    for k, pc in call_curve:
        pp = prob_above(put_curve, k)
        blended.append((k, (pc + pp) / 2 if pp is not None else pc))
    return _clean(blended)


def prob_above(curve: list[tuple[float, float]], strike: float) -> float | None:
    """Linear interpolation of P(S>K) at an arbitrary strike."""
    if not curve:
        return None
    ks = [k for k, _ in curve]
    if strike <= ks[0]:
        return curve[0][1]
    if strike >= ks[-1]:
        return curve[-1][1]
    i = bisect_left(ks, strike)
    k0, p0 = curve[i - 1]
    k1, p1 = curve[i]
    w = (strike - k0) / (k1 - k0)
    return p0 + w * (p1 - p0)


def parity_residual(call_strikes: list[float], call_mids: list[float],
                    put_strikes: list[float], put_mids: list[float],
                    spot: float) -> float | None:
    """Median |(C − P) − (S − K)| across matched strikes.

    For short-dated options (rates/divs ≈ 0) put-call parity pins C − P to
    S − K almost exactly. On a healthy chain the residual is pennies; on a
    stale indicative feed it blows out — and stale quotes manufacture fake
    'edges'. If this is large, the chain is lying and we trade nothing."""
    puts = {round(k, 2): m for k, m in zip(put_strikes, put_mids)}
    residuals = []
    for k, c in zip(call_strikes, call_mids):
        p = puts.get(round(k, 2))
        if p is None:
            continue
        residuals.append(abs((c - p) - (spot - k)))
    if len(residuals) < 5:
        return None
    residuals.sort()
    return residuals[len(residuals) // 2]


def event_strikes(spot: float, listed: list[float], offsets: list[float]) -> list[float]:
    """Nearest listed strikes to spot*(1+offset) for each configured offset."""
    picked = []
    for off in offsets:
        target = spot * (1 + off)
        nearest = min(listed, key=lambda k: abs(k - target))
        if nearest not in picked:
            picked.append(nearest)
    return sorted(picked)
