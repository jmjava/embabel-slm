"""Non-inferiority lower bound via cluster bootstrap on paired differences."""

from __future__ import annotations

import random


def non_inferiority_lower_bound(
    deltas_pp: list[float],
    *,
    margin_pp: float,
    n_resamples: int = 10000,
    seed: int = 20260227,
    alpha: float = 0.05,
) -> tuple[float, bool]:
    """One-sided 95% lower bound on mean difference (percentage points).

    Returns (lower_bound, passes_ni) where passes_ni is True when lower_bound > -margin_pp.
    """
    if not deltas_pp:
        return float("-inf"), False
    mean = sum(deltas_pp) / len(deltas_pp)
    rng = random.Random(seed)
    n = len(deltas_pp)
    boots: list[float] = []
    for _ in range(n_resamples):
        sample = [deltas_pp[rng.randrange(n)] for _ in range(n)]
        boots.append(sum(sample) / n)
    boots.sort()
    lo_idx = int(alpha * n_resamples)
    lo_idx = max(0, min(lo_idx, n_resamples - 1))
    lower = boots[lo_idx]
    return lower, lower > -margin_pp