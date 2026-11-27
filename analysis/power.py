"""McNemar power / sample size (paired binary)."""

from __future__ import annotations

import math
from functools import lru_cache
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


def _binomial_pmf(n: int, probability: float) -> list[float]:
    if probability <= 0.0:
        return [1.0] + [0.0] * n
    if probability >= 1.0:
        return [0.0] * n + [1.0]
    logs = [
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(probability)
        + (n - k) * math.log1p(-probability)
        for k in range(n + 1)
    ]
    peak = max(logs)
    scaled = [math.exp(value - peak) for value in logs]
    total = sum(scaled)
    return [value / total for value in scaled]


@lru_cache(maxsize=None)
def _conditional_rejection_probability(
    discordant: int,
    success_probability: float,
    alpha: float,
) -> float:
    null = _binomial_pmf(discordant, 0.5)
    tail = 0.0
    critical: int | None = None
    for successes in range(discordant, -1, -1):
        tail += null[successes]
        if tail <= alpha + 1e-15:
            critical = successes
        else:
            break
    if critical is None:
        return 0.0
    alternative = _binomial_pmf(discordant, success_probability)
    return sum(alternative[critical:])


def exact_unconditional_mcnemar_power(
    n: int,
    delta: float,
    *,
    p_d: float = 0.3,
    alpha: float = 0.05,
) -> float:
    """Exact unconditional power for the one-sided paired McNemar test.

    The alternative assigns probabilities ``(p_d-delta)/2`` and
    ``(p_d+delta)/2`` to the two discordant directions, then averages the
    exact conditional rejection probability over the binomial number of
    discordant pairs.
    """
    if n < 1:
        raise ValueError("n must be positive")
    if not 0.0 < delta <= p_d <= 1.0:
        raise ValueError("need 0 < delta <= p_d <= 1")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0,1)")
    favorable_given_discordant = (p_d + delta) / (2.0 * p_d)
    discordant_pmf = _binomial_pmf(n, p_d)
    return sum(
        probability
        * _conditional_rejection_probability(
            discordant,
            favorable_given_discordant,
            alpha,
        )
        for discordant, probability in enumerate(discordant_pmf)
    )


def exact_mcnemar_n_required(
    delta: float,
    *,
    p_d: float = 0.3,
    alpha: float = 0.05,
    power: float = 0.8,
) -> int:
    """Smallest n reaching target exact unconditional one-sided power."""
    if not 0.0 < power < 1.0:
        raise ValueError("power must be in (0,1)")
    approximate = mcnemar_n_required(
        delta,
        p_d=p_d,
        alpha=alpha,
        power=power,
        two_sided=False,
    )
    n = max(1, approximate - 100)
    while exact_unconditional_mcnemar_power(n, delta, p_d=p_d, alpha=alpha) < power:
        n += 1
    while n > 1 and exact_unconditional_mcnemar_power(
        n - 1,
        delta,
        p_d=p_d,
        alpha=alpha,
    ) >= power:
        n -= 1
    return n


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
    for n in (20, 100, 186, 742):
        rows.append(
            {
                "n": n,
                "detectable_delta_one_sided_0.05_power_0.80": round(
                    detectable_difference(n, p_d=p_d, two_sided=False), 3
                ),
                "assumption_p_d": p_d,
            }
        )
    for delta in (0.05, 0.10):
        rows.append(
            {
                "target_delta": delta,
                "sidedness": "one_sided",
                "n_required": mcnemar_n_required(delta, p_d=p_d, two_sided=False),
                "method": "normal_approximation",
                "assumption_p_d": p_d,
            }
        )
    rows.append(
        {
            "n": 742,
            "target_delta": 0.05,
            "sidedness": "one_sided",
            "method": "exact_unconditional",
            "normal_approximation_n": mcnemar_n_required(0.05, p_d=p_d, two_sided=False),
            "exact_unconditional_power": round(
                exact_unconditional_mcnemar_power(742, 0.05, p_d=p_d),
                6,
            ),
            "exact_n_required_for_power_0.80": exact_mcnemar_n_required(
                0.05,
                p_d=p_d,
            ),
            "assumption_p_d": p_d,
            "note": "742 is the normal-approximation planning size, not exact 80% power",
        }
    )
    return rows