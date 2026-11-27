#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

from analysis.practices import areas, load_prereg, prefix_sizes
from analysis.pass_at import unbiased_pass_at_k
from analysis.study_results import (
    analyze_study_results,
    load_samples_jsonl,
    load_scores_jsonl,
    run_study_results,
)


def _synthetic_rows(prereg: dict) -> list[dict[str, object]]:
    prefixes = prefix_sizes(prereg)
    seeds = [20260227, 20260228, 20260229]
    labels = areas(prereg)
    tasks: list[tuple[str, str, str]] = []
    for domain in ("embabel", "drivine"):
        domain_areas = labels[domain]
        per_area = 371 // len(domain_areas)
        extra = 371 % len(domain_areas)
        counter = 0
        for area_index, area in enumerate(domain_areas):
            area_count = per_area + (1 if area_index < extra else 0)
            for _ in range(area_count):
                tasks.append((f"{domain}:{area}:{counter}", domain, area))
                counter += 1
    rows: list[dict[str, object]] = []
    for prefix in prefixes:
        for seed in seeds:
            for task_id, domain, area in tasks:
                passed = (hash((task_id, prefix, seed)) % 3) != 0
                rows.append(
                    {
                        "task_id": task_id,
                        "domain": domain,
                        "area": area,
                        "prefix_size": prefix,
                        "training_seed": seed,
                        "passed": passed,
                    }
                )
    return rows


def _synthetic_sample_rows(greedy_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    sample_rows: list[dict[str, object]] = []
    for row in greedy_rows:
        for sample_seed in (1, 2, 3, 4, 5):
            passed = (
                hash((row["task_id"], row["prefix_size"], row["training_seed"], sample_seed)) % 5
            ) != 0
            sample_rows.append(
                {
                    "task_id": row["task_id"],
                    "domain": row["domain"],
                    "area": row["area"],
                    "prefix_size": row["prefix_size"],
                    "training_seed": row["training_seed"],
                    "sample_seed": sample_seed,
                    "passed": passed,
                }
            )
    return sample_rows


class StudyResultsTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()
        self.rows = _synthetic_rows(self.prereg)

    def test_full_grid_analysis(self):
        out = analyze_study_results(self.rows, self.prereg, n_resamples=200)
        self.assertEqual(out["secondary_sampled_metrics"]["status"], "not_provided")
        self.assertFalse(out["secondary_sampled_metrics"]["confirmatory"])
        self.assertTrue(out["confirmatory_contrast"]["confirmatory"])
        self.assertEqual(out["confirmatory_contrast"]["training_seed"], 20260227)
        self.assertEqual(len(out["replications"]), 2)
        for rep in out["replications"]:
            self.assertFalse(rep["confirmatory"])
            self.assertEqual(rep["role"], "robustness_replication")
        self.assertFalse(out["exploratory_pooled_primary_contrast_by_seed"]["confirmatory"])
        self.assertNotIn("p_value", out["exploratory_pooled_primary_contrast_by_seed"])

    def test_missing_cell_rejected(self):
        broken = list(self.rows)
        broken.pop()
        with self.assertRaises(ValueError):
            analyze_study_results(broken, self.prereg, n_resamples=50)

    def test_metadata_drift_rejected(self):
        broken = list(self.rows)
        broken[0] = dict(broken[0])
        broken[0]["domain"] = "embabel" if broken[0]["domain"] != "embabel" else "drivine"
        with self.assertRaises(ValueError):
            analyze_study_results(broken, self.prereg, n_resamples=50)

    def test_primary_decision_not_altered_by_replications(self):
        out = analyze_study_results(self.rows, self.prereg, n_resamples=100)
        decision = out["confirmatory_decision"]
        self.assertEqual(decision["rejects"], out["confirmatory_contrast"]["rejects"])
        self.assertFalse(decision["replication_results_alter_primary"])

    def test_jsonl_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scores.jsonl"
            with path.open("w", encoding="utf-8") as handle:
                for row in self.rows:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
            loaded = load_scores_jsonl(path)
            self.assertEqual(len(loaded), len(self.rows))
            result = run_study_results(path, n_resamples=100)
            self.assertIn("confirmatory_contrast", result)
            self.assertEqual(result["secondary_sampled_metrics"]["status"], "not_provided")

    def test_secondary_sampled_metrics(self):
        samples = _synthetic_sample_rows(self.rows)
        baseline = analyze_study_results(self.rows, self.prereg, n_resamples=100)
        with_samples = analyze_study_results(
            self.rows,
            self.prereg,
            n_resamples=80,
            sample_rows=samples,
        )
        self.assertEqual(with_samples["secondary_sampled_metrics"]["status"], "provided")
        self.assertFalse(with_samples["secondary_sampled_metrics"]["confirmatory"])
        self.assertEqual(
            with_samples["secondary_sampled_metrics"]["role"],
            "secondary_non_confirmatory",
        )
        self.assertEqual(
            len(with_samples["secondary_sampled_metrics"]["by_prefix_training_seed"]),
            6 * 3,
        )
        cell = with_samples["secondary_sampled_metrics"]["by_prefix_training_seed"][0]
        self.assertEqual(cell["pass_at_1"]["k"], 1)
        self.assertEqual(cell["pass_at_5"]["k"], 5)
        self.assertEqual(cell["pass_at_1"]["n_samples_per_task"], 5)
        self.assertEqual(with_samples["confirmatory_decision"], baseline["confirmatory_decision"])

    def test_samples_do_not_alter_confirmatory_decision(self):
        greedy_fail = [dict(row, passed=False) for row in self.rows]
        sample_pass = _synthetic_sample_rows(greedy_fail)
        for row in sample_pass:
            row["passed"] = True
        greedy_out = analyze_study_results(greedy_fail, self.prereg, n_resamples=50)
        combined = analyze_study_results(
            greedy_fail,
            self.prereg,
            n_resamples=50,
            sample_rows=sample_pass,
        )
        self.assertFalse(greedy_out["confirmatory_contrast"]["rejects"])
        self.assertEqual(
            combined["confirmatory_decision"],
            greedy_out["confirmatory_decision"],
        )
        self.assertGreater(
            combined["secondary_sampled_metrics"]["by_prefix_training_seed"][0]["pass_at_5"]["mean"],
            0.99,
        )

    def test_missing_sample_seed_rejected(self):
        samples = _synthetic_sample_rows(self.rows)
        samples = [row for row in samples if not (row["sample_seed"] == 5 and row["prefix_size"] == 500)]
        with self.assertRaises(ValueError) as ctx:
            analyze_study_results(self.rows, self.prereg, n_resamples=20, sample_rows=samples)
        self.assertIn("missing sample_seeds", str(ctx.exception))

    def test_duplicate_sample_row_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "samples.jsonl"
            row = _synthetic_sample_rows(self.rows[:1])[0]
            body = json.dumps(row, sort_keys=True) + "\n" + json.dumps(row, sort_keys=True) + "\n"
            path.write_text(body, encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_samples_jsonl(path)
            self.assertIn("duplicate", str(ctx.exception))

    def test_unregistered_sample_seed_rejected(self):
        row = dict(_synthetic_sample_rows(self.rows[:1])[0], sample_seed=99)
        with self.assertRaises(ValueError) as ctx:
            analyze_study_results(self.rows, self.prereg, n_resamples=20, sample_rows=[row])
        self.assertIn("unregistered sample seed", str(ctx.exception))

    def test_sample_metadata_drift_rejected(self):
        samples = _synthetic_sample_rows(self.rows)
        samples[0] = dict(samples[0])
        samples[0]["area"] = "wrong-area"
        with self.assertRaises(ValueError):
            analyze_study_results(self.rows, self.prereg, n_resamples=20, sample_rows=samples)

    def test_samples_jsonl_loader_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "samples.jsonl"
            row = _synthetic_sample_rows(self.rows[:1])[0]
            row["extra"] = True
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_samples_jsonl(path)

    def test_sample_rows_require_exact_five_seeds(self):
        samples = _synthetic_sample_rows(self.rows)
        trimmed = [
            row
            for row in samples
            if not (
                row["task_id"] == self.rows[0]["task_id"]
                and row["prefix_size"] == 500
                and row["training_seed"] == 20260227
                and row["sample_seed"] == 3
            )
        ]
        with self.assertRaises(ValueError) as ctx:
            analyze_study_results(self.rows, self.prereg, n_resamples=20, sample_rows=trimmed)
        self.assertIn("missing sample_seeds", str(ctx.exception))

    def test_unbiased_estimator_all_pass_all_fail(self):
        self.assertAlmostEqual(unbiased_pass_at_k(5, 5, 5), 1.0)
        self.assertAlmostEqual(unbiased_pass_at_k(0, 5, 5), 0.0)
        self.assertAlmostEqual(unbiased_pass_at_k(0, 5, 1), 0.0)
        self.assertAlmostEqual(unbiased_pass_at_k(5, 5, 1), 1.0)


if __name__ == "__main__":
    unittest.main()