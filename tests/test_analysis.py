#!/usr/bin/env python3

import unittest

from analysis.bootstrap import cluster_bootstrap_ci
from analysis.gap_closure import gap_closure
from analysis.holm import holm_bonferroni
from analysis.mcnemar import exact_mcnemar_p_value
from analysis.pass_at import mean_pass_at_k, unbiased_pass_at_k
from analysis.power import (
    detectable_difference,
    exact_mcnemar_n_required,
    exact_unconditional_mcnemar_power,
    mcnemar_n_required,
    power_table,
)


class PassAtTests(unittest.TestCase):
    def test_unbiased_all_fail(self):
        self.assertAlmostEqual(unbiased_pass_at_k(0, 5, 5), 0.0)

    def test_unbiased_all_pass(self):
        self.assertAlmostEqual(unbiased_pass_at_k(5, 5, 5), 1.0)

    def test_mean(self):
        self.assertAlmostEqual(mean_pass_at_k([5, 0], 5, 5), 0.5)

    def test_unbiased_mixed_pass_at_five(self):
        self.assertAlmostEqual(unbiased_pass_at_k(1, 5, 5), 1.0)
        self.assertAlmostEqual(unbiased_pass_at_k(0, 5, 5), 0.0)

    def test_unbiased_pass_at_one(self):
        self.assertAlmostEqual(unbiased_pass_at_k(0, 5, 1), 0.0)
        self.assertAlmostEqual(unbiased_pass_at_k(5, 5, 1), 1.0)
        self.assertAlmostEqual(unbiased_pass_at_k(2, 5, 1), 0.4)

    def test_invalid_success_count_is_rejected(self):
        with self.assertRaises(ValueError):
            unbiased_pass_at_k(-1, 5, 1)
        with self.assertRaises(ValueError):
            unbiased_pass_at_k(6, 5, 1)


class McNemarTests(unittest.TestCase):
    def test_symmetric_small_p(self):
        p = exact_mcnemar_p_value(10, 2)
        self.assertLess(p, 0.05)


class HolmTests(unittest.TestCase):
    def test_monotone(self):
        adj = holm_bonferroni([0.01, 0.04, 0.03])
        self.assertEqual(len(adj), 3)
        self.assertGreaterEqual(adj[1], adj[0])


class BootstrapTests(unittest.TestCase):
    def test_ci_bounds(self):
        data = [0.0, 1.0] * 50
        _, lo, hi = cluster_bootstrap_ci(data, lambda xs: sum(xs) / len(xs), n_resamples=500, seed=1)
        self.assertLess(lo, hi)


class GapClosureTests(unittest.TestCase):
    def test_undefined_when_no_gap(self):
        n = 30
        sa = [False] * n
        sd = [True] * (n // 2) + [False] * (n - n // 2)
        la = [False] * n
        out = gap_closure(sa, sd, la, n_resamples=200, seed=1)
        self.assertFalse(out["G_defined"])


class PowerTests(unittest.TestCase):
    def test_n_for_10_points(self):
        n = mcnemar_n_required(0.10, p_d=0.3)
        self.assertGreaterEqual(n, 228)
        self.assertLessEqual(n, 236)

    def test_n_for_15_points(self):
        n = mcnemar_n_required(0.15, p_d=0.3)
        self.assertGreaterEqual(n, 104)
        self.assertLessEqual(n, 106)

    def test_detectable_at_20(self):
        d = detectable_difference(20, p_d=0.3)
        self.assertGreater(d, 0.33)
        self.assertLess(d, 0.37)

    def test_table_runs(self):
        rows = power_table()
        self.assertTrue(any(r.get("n") == 100 for r in rows))

    def test_one_sided_rows_match_the_protocol(self):
        self.assertEqual(mcnemar_n_required(0.05, p_d=0.3, two_sided=False), 742)
        self.assertEqual(mcnemar_n_required(0.10, p_d=0.3, two_sided=False), 186)
        rows = power_table()
        one_sided = {
            r["target_delta"]: r["n_required"]
            for r in rows
            if r.get("sidedness") == "one_sided" and r.get("method") != "exact_unconditional"
        }
        exact = next(r for r in rows if r.get("method") == "exact_unconditional")
        self.assertEqual(exact["normal_approximation_n"], 742)
        self.assertEqual(exact["exact_unconditional_power"], 0.783839)
        self.assertEqual(exact["exact_n_required_for_power_0.80"], 776)
        self.assertEqual(one_sided, {0.05: 742, 0.10: 186})
        detectable = {
            r["n"]: r["detectable_delta_one_sided_0.05_power_0.80"]
            for r in rows
            if "detectable_delta_one_sided_0.05_power_0.80" in r
        }
        self.assertAlmostEqual(detectable[742], 0.05, places=2)
        self.assertAlmostEqual(detectable[186], 0.10, places=2)

    def test_exact_one_sided_power_matches_protocol_wording(self):
        self.assertAlmostEqual(
            exact_unconditional_mcnemar_power(742, 0.05, p_d=0.3),
            0.783839,
            places=6,
        )
        self.assertEqual(exact_mcnemar_n_required(0.05, p_d=0.3), 776)

    def test_exact_holm_threshold_reference(self):
        self.assertAlmostEqual(
            exact_unconditional_mcnemar_power(1236, 0.05, p_d=0.3, alpha=0.01),
            0.80,
            places=2,
        )


if __name__ == "__main__":
    unittest.main()