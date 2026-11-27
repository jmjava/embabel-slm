#!/usr/bin/env python3

import unittest

from analysis.mcnemar import exact_mcnemar_p_value_one_sided
from analysis.practices import (
    admit_example,
    admit_holdout,
    assign_doses,
    decide_steps,
    guide_may_attach,
    guide_practice_holds,
    holm_test_names,
    load_prereg,
    lock_prefixes,
    areas,
)


def _example(**overrides):
    record = {
        "domain": "embabel",
        "area": "generation",
        "executable_oracle": True,
        "source_file": "guide/actions.md",
        "source_pin": "abc123",
    }
    record.update(overrides)
    return record


class OneSidedMcNemarTests(unittest.TestCase):
    def test_favorable_tail_is_small(self):
        p = exact_mcnemar_p_value_one_sided(0, 8)
        self.assertAlmostEqual(p, 1 / 256)
        self.assertLess(p, 0.05)

    def test_unfavorable_tail_is_one(self):
        self.assertEqual(exact_mcnemar_p_value_one_sided(8, 0), 1.0)

    def test_negative_count_rejected(self):
        with self.assertRaises(ValueError):
            exact_mcnemar_p_value_one_sided(-1, 5)


class PracticeLockTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()

    def test_areas_and_holm_names(self):
        labels = areas(self.prereg)
        self.assertEqual(len(labels["embabel"]), 6)
        self.assertEqual(len(labels["drivine"]), 5)
        names = holm_test_names(self.prereg)
        self.assertEqual(len(names), 5)
        self.assertEqual(names[0], "prefix_1000_minus_500")
        self.assertEqual(names[-1], "prefix_16000_minus_8000")

    def test_guide_is_an_addon_after_training(self):
        self.assertTrue(guide_practice_holds(self.prereg))
        self.assertFalse(guide_may_attach(False))
        self.assertTrue(guide_may_attach(True))


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()

    def test_complete_example_is_admitted(self):
        self.assertEqual(admit_example(_example(), self.prereg), [])

    def test_example_refusals(self):
        self.assertIn(
            "authored_for_exactly_one_area",
            admit_example(_example(areas=["generation", "repair"]), self.prereg),
        )
        self.assertIn(
            "compiler_or_executable_oracle",
            admit_example(_example(executable_oracle=False), self.prereg),
        )
        self.assertIn(
            "source_file_and_pin_recorded",
            admit_example(_example(source_pin=""), self.prereg),
        )
        self.assertIn(
            "not_near_duplicate_of_holdout",
            admit_example(_example(near_duplicate_of_holdout=True), self.prereg),
        )
        self.assertIn(
            "random_pool_rejected",
            admit_example(_example(random_pool=True), self.prereg),
        )
        self.assertIn(
            "slice_label_from_pre_registered_set",
            admit_example(_example(area="query"), self.prereg),
        )

    def test_holdout_refusals(self):
        task = _example()
        self.assertIn(
            "manifest_hash_before_first_score",
            admit_holdout(task, self.prereg, manifest_hashed=False),
        )
        self.assertIn(
            "no_edit_after_first_model_output",
            admit_holdout(
                _example(edited_after_first_model_output=True),
                self.prereg,
                manifest_hashed=True,
            ),
        )
        self.assertIn(
            "slice_label_from_pre_registered_set",
            admit_holdout(_example(area="query"), self.prereg, manifest_hashed=True),
        )
        self.assertEqual(admit_holdout(task, self.prereg, manifest_hashed=True), [])


class DoseTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()

    def test_named_ladder(self):
        locked = lock_prefixes(self.prereg)
        self.assertEqual(locked["prefixes"], [500, 1000, 2000, 4000, 8000, 16000])
        self.assertEqual(locked["starts"], [500, 1000, 2000])
        self.assertEqual(locked["multipliers"], [1, 2, 4, 8])
        self.assertEqual(locked["holdout_min_tasks"], 742)

    def test_each_size_is_a_prefix_of_the_next(self):
        ids = [f"e{i}" for i in range(16000)]
        doses = assign_doses(ids, self.prereg)
        self.assertEqual(len(doses["500"]), 500)
        self.assertEqual(doses["16000"][:8000], doses["8000"])
        self.assertEqual(doses["1000"][:500], doses["500"])


class StepDecisionTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()

    def test_one_step_can_be_proved_alone(self):
        p_values = {name: 0.9 for name in holm_test_names(self.prereg)}
        p_values["prefix_1000_minus_500"] = 0.001
        decision = decide_steps(p_values, self.prereg)
        self.assertEqual(decision["proved_count"], 1)
        self.assertTrue(decision["steps"]["prefix_1000_minus_500"]["rejects"])
        self.assertFalse(decision["steps"]["prefix_16000_minus_8000"]["rejects"])
        self.assertFalse(decision["requires_every_step"])

    def test_missing_test_is_rejected(self):
        with self.assertRaises(ValueError):
            decide_steps({}, self.prereg)


if __name__ == "__main__":
    unittest.main()
