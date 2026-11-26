"""Chen et al. 2021 unbiased pass@k estimator."""

from __future__ import annotations

import math


def _comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return 0.0
    return float(math.comb(n, k))


def unbiased_pass_at_k(correct: int, n: int, k: int) -> float:
    """Unbiased pass@k for one task with `correct` successes in `n` samples."""
    if n < k or k < 1:
        raise ValueError("need n >= k >= 1")
    failed = n - correct
    if failed < k:
        return 1.0
    return 1.0 - _comb(failed, k) / _comb(n, k)


def mean_pass_at_k(correct_counts: list[int], n: int, k: int) -> float:
    if not correct_counts:
        return 0.0
    return sum(unbiased_pass_at_k(c, n, k) for c in correct_counts) / len(correct_counts)