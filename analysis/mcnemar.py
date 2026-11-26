"""Exact McNemar test for paired binary outcomes."""

from __future__ import annotations

import math


def _binom_cdf(k: int, n: int, p: float) -> float:
    if n < 0 or k < 0:
        return 1.0
    total = 0.0
    for i in range(k + 1):
        total += math.comb(n, i) * (p**i) * ((1 - p) ** (n - i))
    return total


def exact_mcnemar_p_value(b: int, c: int) -> float:
    """Two-sided exact p-value; b = A pass B fail, c = A fail B pass."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p_one = _binom_cdf(k, n, 0.5) * 2
    return min(1.0, p_one)


def exact_mcnemar_p_value_one_sided(b: int, c: int) -> float:
    """One-sided exact p-value for a pre-registered direction.

    ``c`` counts pairs that favor the later dose. ``b`` counts the opposite
    discordant pairs. The p-value is the upper binomial tail P(X >= c) under
    Bin(b + c, 0.5).
    """
    if b < 0 or c < 0:
        raise ValueError("counts must be non-negative")
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(c, n + 1))
    return min(1.0, tail / (2**n))