"""McNemar power / sample size (paired binary)."""

from __future__ import annotations

import math
from statistics import NormalDist

_ND = NormalDist()


def _z(p: float) -> float:
    if p <= 0 or p >= 1:
        raise ValueError("p must be in (0,1)")
    return _ND.inv_cdf(p)


def mcnemar_n_required(
    delta: float,
    *,
    p_d: float = 0.3,
    alpha: float = 0.05,
    power: float = 0.8,
    two_sided: bool = True,
) -> int:
    """Sample size n for detecting marginal difference delta (proportion scale)."""
    if delta <= 0:
        raise ValueError("delta must be positive")
    z_a = _z(1 - alpha / 2) if two_sided else _z(1 - alpha)
    z_b = _z(power)
    n = (z_a + z_b) ** 2 * p_d / (delta**2)
    return int(math.ceil(n))


def detectable_difference(
    n: int,
    *,
    p_d: float = 0.3,
    alpha: float = 0.05,
    power: float = 0.8,
    two_sided: bool = True,
) -> float:
    z_a = _z(1 - alpha / 2) if two_sided else _z(1 - alpha)
    z_b = _z(power)
    return math.sqrt((z_a + z_b) ** 2 * p_d / n)


def power_table() -> list[dict]:
    p_d = 0.3
    rows = []
    for n in (20, 100, 230, 600, 941):
        rows.append(
            {
                "n": n,
                "detectable_delta_two_sided_0.05_power_0.80": round(
                    detectable_difference(n, p_d=p_d), 3
                ),
                "assumption_p_d": p_d,
            }
        )
    for delta, label in ((0.10, "~0.10"), (0.15, "~0.15")):
        rows.append(
            {
                "target_delta": delta,
                "target_delta_note": label,
                "n_required": mcnemar_n_required(delta, p_d=p_d),
                "assumption_p_d": p_d,
            }
        )
    return rows