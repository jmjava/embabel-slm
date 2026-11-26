#!/usr/bin/env python3

import unittest

from analysis.bootstrap import cluster_bootstrap_ci
from analysis.gap_closure import gap_closure
from analysis.holm import holm_bonferroni
from analysis.mcnemar import exact_mcnemar_p_value
from analysis.pass_at import mean_pass_at_k, unbiased_pass_at_k
from analysis.power import detectable_difference, mcnemar_n_required, power_table


class PassAtTests(unittest.TestCase):
    def test_unbiased_all_fail(self):
        self.assertAlmostEqual(unbiased_pass_at_k(0, 5, 5), 0.0)

    def test_unbiased_all_pass(self):
        self.assertAlmostEqual(unbiased_pass_at_k(5, 5, 5), 1.0)

    def test_mean(self):
        self.assertAlmostEqual(mean_pass_at_k([5, 0], 5, 5), 0.5)


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


if __name__ == "__main__":
    unittest.main()