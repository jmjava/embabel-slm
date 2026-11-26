"""Holm–Bonferroni adjustment."""

from __future__ import annotations


def holm_bonferroni(p_values: list[float]) -> list[float]:
    """Return adjusted p-values in the same order as input."""
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * m
    running = 0.0
    for rank, (idx, p) in enumerate(indexed, start=1):
        adj = (m - rank + 1) * p
        running = max(running, adj)
        adjusted[idx] = min(1.0, running)
    return adjusted