"""Cluster (task-level) bootstrap confidence intervals."""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence


def cluster_bootstrap_ci(
    values: Sequence[float],
    statistic: Callable[[Sequence[float]], float],
    *,
    n_resamples: int = 10000,
    seed: int = 20260227,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """Return (point_estimate, lower, upper) percentile CI."""
    if not values:
        return 0.0, 0.0, 0.0
    point = statistic(values)
    rng = random.Random(seed)
    n = len(values)
    boot: list[float] = []
    for _ in range(n_resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        boot.append(statistic(sample))
    boot.sort()
    lo_idx = int((alpha / 2) * n_resamples)
    hi_idx = int((1 - alpha / 2) * n_resamples) - 1
    lo_idx = max(0, min(lo_idx, n_resamples - 1))
    hi_idx = max(0, min(hi_idx, n_resamples - 1))
    return point, boot[lo_idx], boot[hi_idx]