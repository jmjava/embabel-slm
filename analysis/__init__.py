"""Holdout statistics for the Embabel two-arm study (stdlib only)."""

from analysis.bootstrap import cluster_bootstrap_ci
from analysis.gap_closure import gap_closure
from analysis.holm import holm_bonferroni
from analysis.mcnemar import exact_mcnemar_p_value, exact_mcnemar_p_value_one_sided
from analysis.non_inferiority import non_inferiority_lower_bound
from analysis.pass_at import mean_pass_at_k, unbiased_pass_at_k
from analysis.power import detectable_difference, mcnemar_n_required, power_table
from analysis.practices import (
    admit_example,
    admit_holdout,
    assign_doses,
    decide_steps,
    guide_may_attach,
    guide_practice_holds,
    load_prereg,
    lock_prefixes,
)

__all__ = [
    "unbiased_pass_at_k",
    "mean_pass_at_k",
    "cluster_bootstrap_ci",
    "exact_mcnemar_p_value",
    "exact_mcnemar_p_value_one_sided",
    "load_prereg",
    "admit_example",
    "admit_holdout",
    "lock_prefixes",
    "assign_doses",
    "decide_steps",
    "guide_practice_holds",
    "guide_may_attach",
    "holm_bonferroni",
    "non_inferiority_lower_bound",
    "gap_closure",
    "mcnemar_n_required",
    "detectable_difference",
    "power_table",
]