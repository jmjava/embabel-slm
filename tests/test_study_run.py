#!/usr/bin/env python3

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from analysis.equal_compute import (
    RECIPE_FIELDS,
    EqualComputeBudget,
    FrozenTrainingRecipe,
    RecipeNotFrozen,
    TrainingNotRun,
    plan_equal_compute,
)
from analysis.hashes import sha256_file
from analysis.study_run import StudyRunPlan
from analysis.training_examples import FORMATTER_VERSION


def _record(example_id: str, response: str) -> dict[str, object]:
    return {
        "example_id": example_id,
        "prompt": "{\"domain\":\"embabel\"}",
        "response": response,
        "formatter_version": FORMATTER_VERSION,
    }


def _write_seal(root: Path, groups: dict[int, list[dict[str, object]]]) -> None:
    prefix_dir = root / "prefixes"
    prefix_dir.mkdir(parents=True)
    prefix_files: dict[str, dict[str, object]] = {}
    for size, rows in groups.items():
        path = prefix_dir / f"prefix-{size}.jsonl"
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        prefix_files[str(size)] = {
            "path": path.name,
            "records": size,
            "sha256": sha256_file(path),
        }
    prereg = "ab" * 32
    (prefix_dir / "manifest.json").write_text(
        json.dumps(
            {
                "prereg_sha256": prereg,
                "prefixes": sorted(groups),
                "prefix_files": prefix_files,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (root / "sealed-study-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sealed": True,
                "prereg_sha256": prereg,
                "prefixes": sorted(groups),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _ready_recipe(budget: EqualComputeBudget) -> FrozenTrainingRecipe:
    values = {name: f"frozen-{name}" for name in RECIPE_FIELDS}
    return FrozenTrainingRecipe(values, budget)


class StudyRunPlanTests(unittest.TestCase):
    def test_empty_recipe_does_not_read_the_seal(self):
        missing = Path(tempfile.mkdtemp(prefix="study-run-missing-"))
        shutil.rmtree(missing)
        planner = StudyRunPlan(FrozenTrainingRecipe({}), missing, lambda row: 1)
        with self.assertRaises(RecipeNotFrozen):
            planner.plan()
        self.assertFalse(missing.exists())

    def test_ready_recipe_plans_and_does_not_fit(self):
        root = Path(tempfile.mkdtemp(prefix="study-run-"))
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        rows = [
            _record("a", "one\n"),
            _record("b", "two\n"),
            _record("c", "three\n"),
        ]
        _write_seal(root, {2: rows[:2], 3: rows})
        recipe = _ready_recipe(EqualComputeBudget(8, 4, 2))
        counter = lambda row: 2
        planner = StudyRunPlan(recipe, root, counter, sequence_length=8192)
        planned = planner.plan()
        expected = plan_equal_compute(root, counter, 8192)
        self.assertEqual(planned["budget"], expected["budget"])
        with self.assertRaises(TrainingNotRun) as caught:
            planner.train()
        self.assertEqual(
            str(caught.exception),
            "the schedule is planned and no adapter was fit",
        )


if __name__ == "__main__":
    unittest.main()
