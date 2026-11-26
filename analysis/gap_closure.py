"""Gap-closure estimand G with bootstrap CI."""

from __future__ import annotations

import random


def gap_closure(
    s_a: list[bool],
    s_d: list[bool],
    l_a: list[bool],
    *,
    n_resamples: int = 10000,
    seed: int = 20260227,
    alpha: float = 0.05,
) -> dict:
    """Per-task greedy pass vectors (aligned by index)."""

    def rate(v: list[bool]) -> float:
        return sum(v) / len(v) if v else 0.0

    def g_from_rates(p_sa: float, p_sd: float, p_la: float) -> float | None:
        denom = p_la - p_sa
        if denom == 0:
            return None
        return (p_sd - p_sa) / denom

    p_sa, p_sd, p_la = rate(s_a), rate(s_d), rate(l_a)
    point = g_from_rates(p_sa, p_sd, p_la)
    rng = random.Random(seed)
    n = len(s_a)
    boot_g: list[float] = []
    boot_denom: list[float] = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        sa = [s_a[i] for i in idx]
        sd = [s_d[i] for i in idx]
        la = [l_a[i] for i in idx]
        psa, psd, pla = rate(sa), rate(sd), rate(la)
        boot_denom.append(pla - psa)
        val = g_from_rates(psa, psd, pla)
        if val is not None:
            boot_g.append(val)
    boot_denom.sort()
    d_lo = boot_denom[int((alpha / 2) * n_resamples)]
    d_hi = boot_denom[int((1 - alpha / 2) * n_resamples) - 1]
    denom_includes_zero = d_lo <= 0 <= d_hi
    if denom_includes_zero or point is None:
        return {
            "G_point": None,
            "G_defined": False,
            "denom_ci_includes_zero": denom_includes_zero,
            "p_S_A": p_sa,
            "p_S_D": p_sd,
            "p_L_A": p_la,
        }
    boot_g.sort()
    lo = boot_g[int((alpha / 2) * len(boot_g))]
    hi = boot_g[int((1 - alpha / 2) * len(boot_g)) - 1]
    return {
        "G_point": point,
        "G_ci_lower": lo,
        "G_ci_upper": hi,
        "G_defined": True,
        "denom_ci_includes_zero": False,
        "p_S_A": p_sa,
        "p_S_D": p_sd,
        "p_L_A": p_la,
    }