#!/usr/bin/env python3

import random
import unittest

from analysis.design import (
    allocate_holdout_areas,
    align_binary_scores,
    hamilton_largest_remainder,
    holdout_domain_counts,
    seeded_stratified_order,
    training_seed_plan,
    validate_provenance_disjoint,
)
from analysis.practices import areas, load_prereg, prefix_sizes


class HamiltonTests(unittest.TestCase):
    def test_minimum_and_exact_total(self):
        alloc = hamilton_largest_remainder(
            {"a": 3, "b": 7},
            10,
            minimum={"a": 2, "b": 3},
        )
        self.assertEqual(sum(alloc.values()), 10)
        self.assertGreaterEqual(alloc["a"], 2)
        self.assertGreaterEqual(alloc["b"], 3)

    def test_lexical_tie_break(self):
        first = hamilton_largest_remainder({"b": 1, "a": 1}, 3)
        second = hamilton_largest_remainder({"a": 1, "b": 1}, 3)
        self.assertEqual(first, second)
        self.assertEqual(first, {"a": 2, "b": 1})

    def test_capacity_overflow_redistribution(self):
        alloc = hamilton_largest_remainder(
            {"a": 50, "b": 50},
            30,
            capacity={"a": 5, "b": 25},
        )
        self.assertEqual(sum(alloc.values()), 30)
        self.assertEqual(alloc["a"], 5)
        self.assertEqual(alloc["b"], 25)

    def test_rejects_insufficient_total(self):
        with self.assertRaises(ValueError):
            hamilton_largest_remainder({"a": 1, "b": 1}, 5, minimum={"a": 3, "b": 3})


class HoldoutAllocationTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()

    def _counts(self, embabel_scale: int = 80, drivine_scale: int = 80) -> dict[tuple[str, str], int]:
        counts: dict[tuple[str, str], int] = {}
        for domain, labels in areas(self.prereg).items():
            scale = embabel_scale if domain == "embabel" else drivine_scale
            for index, area in enumerate(labels):
                counts[(domain, area)] = scale + index * 11
        return counts

    def test_domain_totals_and_minimums(self):
        allocation = allocate_holdout_areas(self._counts(), self.prereg)
        self.assertEqual(sum(allocation.values()), 742)
        for domain, labels in areas(self.prereg).items():
            self.assertEqual(sum(allocation[(domain, area)] for area in labels), 371)
            for area in labels:
                self.assertGreaterEqual(allocation[(domain, area)], 10)

    def test_refactor_weights_without_supply_cap(self):
        counts = self._counts(embabel_scale=12, drivine_scale=12)
        allocation = allocate_holdout_areas(counts, self.prereg)
        self.assertEqual(sum(allocation.values()), 742)
        embabel_refactor = allocation[("embabel", "refactor")]
        self.assertGreater(embabel_refactor, counts[("embabel", "refactor")])


class StratifiedOrderTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()
        self.largest = prefix_sizes(self.prereg)[-1]

    def _records(self, n: int, *, salt: int = 0) -> list[dict[str, object]]:
        labels = areas(self.prereg)
        records: list[dict[str, object]] = []
        domains = ("embabel", "drivine")
        for index in range(n):
            domain = domains[index % 2]
            area = labels[domain][index % len(labels[domain])]
            records.append({"id": f"u{salt}-{index:05d}", "domain": domain, "area": area})
        return records

    def test_order_is_deterministic_and_input_invariant(self):
        records_a = self._records(self.largest)
        random.shuffle(records_a)
        records_b = list(reversed(self._records(self.largest)))
        order_a, report_a = seeded_stratified_order(records_a, self.prereg)
        order_b, report_b = seeded_stratified_order(records_b, self.prereg)
        self.assertEqual(order_a, order_b)
        self.assertEqual(report_a["prefix_reports"].keys(), report_b["prefix_reports"].keys())

    def test_nested_prefixes_and_reports(self):
        order, report = seeded_stratified_order(self._records(self.largest), self.prereg)
        self.assertEqual(len(order), self.largest)
        for size in prefix_sizes(self.prereg):
            self.assertIn(str(size), report["prefix_reports"])

    def test_exhaustion_without_padding(self):
        records = self._records(self.largest)
        order, _ = seeded_stratified_order(records, self.prereg)
        self.assertEqual(len(set(order)), len(order))


class ProvenanceTests(unittest.TestCase):
    def test_rejects_cross_split_group(self):
        train = [{"id": "t1", "provenance_groups": ["file/a"]}]
        holdout = [{"id": "h1", "provenance_groups": ["file/a"]}]
        with self.assertRaises(ValueError):
            validate_provenance_disjoint(train, holdout)

    def test_valid_summary(self):
        train = [{"id": "t1", "provenance_groups": ["train/a"]}]
        holdout = [{"id": "h1", "provenance_groups": ["hold/a"]}]
        summary = validate_provenance_disjoint(train, holdout)
        self.assertEqual(summary["train_records"], 1)
        self.assertEqual(summary["holdout_records"], 1)


class AlignmentTests(unittest.TestCase):
    def test_mismatch_rejected(self):
        left = [{"task_id": "a", "passed": True}]
        right = [{"task_id": "b", "passed": False}]
        with self.assertRaises(ValueError):
            align_binary_scores(left, right)


class PreregPlanTests(unittest.TestCase):
    def test_training_seed_plan(self):
        prereg = load_prereg()
        plan = training_seed_plan(prereg)
        self.assertEqual(plan["count"], 3)
        self.assertEqual(plan["primary"], 20260227)
        counts = holdout_domain_counts(prereg)
        self.assertEqual(counts, {"embabel": 371, "drivine": 371})


if __name__ == "__main__":
    unittest.main()