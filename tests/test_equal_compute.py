#!/usr/bin/env python3

import json
import unittest
from pathlib import Path

from analysis.equal_compute import (
    EqualComputeBudget,
    EqualTokenSchedule,
    FrozenTrainingRecipe,
    RecipeNotFrozen,
    RepeatedPrefixSchedule,
    SealedPrefix,
    SealedPrefixTrainer,
    TrainingNotRun,
    assert_prefixes_nested,
    batch_sizes_that_repeat,
    budget_covering_one_pass,
)
from analysis.hashes import sha256_file
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
    values = {name: f"frozen-{name}" for name in (
        "base_model_tag_and_hash",
        "tokenizer",
        "sequence_length_and_truncation",
        "batch_and_gradient_accumulation",
        "optimizer",
        "learning_rate_and_schedule",
        "warmup",
        "lora_target_modules_rank_alpha_dropout",
        "precision",
        "dataset_shuffle_sampler_algorithm_and_seed_per_training_seed",
        "packing_policy",
        "truncation",
        "padding_and_loss_masking",
        "deterministic_kernel_settings_or_documented_nondeterminism",
        "framework_library_and_driver_versions",
        "checkpoint_selection",
        "primary_and_replication_seed_roles",
    )}
    return FrozenTrainingRecipe(values, budget)


class EqualComputeTests(unittest.TestCase):
    def test_budget_must_multiply_exactly(self):
        with self.assertRaises(ValueError):
            EqualComputeBudget(10, 4, 2)

    def test_empty_recipe_is_not_frozen(self):
        recipe = FrozenTrainingRecipe({})
        self.assertIn("tokenizer", recipe.missing())
        self.assertIn("non_padding_target_token_budget", recipe.missing())
        with self.assertRaises(RecipeNotFrozen):
            recipe.require_ready()

    def test_sealed_prefix_rejects_a_changed_byte(self):
        with self._temp_seal() as root:
            prefix = SealedPrefix.load(root, 2)
            self.assertEqual([row["example_id"] for row in prefix.records], ["a", "b"])
            path = root / "prefixes" / "prefix-2.jsonl"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                SealedPrefix.load(root, 2)

    def test_smaller_prefix_must_lead_the_larger_one(self):
        with self._temp_seal() as root:
            small = SealedPrefix.load(root, 2)
            large = SealedPrefix.load(root, 3)
            assert_prefixes_nested((large, small))
            swapped = SealedPrefix(
                size=2,
                records=(large.records[1], large.records[0]),
                sha256=small.sha256,
                prereg_sha256=small.prereg_sha256,
            )
            with self.assertRaises(ValueError):
                assert_prefixes_nested((swapped, large))

    def test_repetition_cycles_the_shorter_prefix(self):
        with self._temp_seal() as root:
            prefix = SealedPrefix.load(root, 2)
            budget = EqualComputeBudget(
                non_padding_target_tokens=12,
                effective_batch_tokens=4,
                optimizer_updates=3,
            )
            schedule = RepeatedPrefixSchedule.build(prefix, budget, lambda row: 2)
            self.assertEqual(schedule.optimizer_updates, 3)
            self.assertEqual(schedule.target_tokens, 12)
            self.assertEqual(
                [[row["example_id"] for row in batch] for batch in schedule.batches],
                [["a", "b"], ["a", "b"], ["a", "b"]],
            )

    def test_batch_sizes_that_return_to_the_start(self):
        self.assertEqual(batch_sizes_that_repeat([2, 2], max_batch=4), (2, 4))
        self.assertEqual(batch_sizes_that_repeat([2, 3], max_batch=5), (5,))
        self.assertEqual(batch_sizes_that_repeat([2, 3], max_batch=4), ())
        self.assertIn(4, batch_sizes_that_repeat([2, 2, 2], max_batch=4, max_cycles=2))

    def test_untileable_prefix_is_rejected(self):
        with self._temp_seal() as root:
            prefix = SealedPrefix.load(root, 2)
            budget = EqualComputeBudget(4, 4, 1)
            with self.assertRaises(ValueError):
                RepeatedPrefixSchedule.build(prefix, budget, lambda row: 3)

    def test_one_pass_budget_covers_the_capped_prefix(self):
        budget = budget_covering_one_pass([5, 5, 3], sequence_length=4)
        self.assertEqual(budget.effective_batch_tokens, 4)
        self.assertEqual(budget.optimizer_updates, 3)
        self.assertEqual(budget.non_padding_target_tokens, 12)

    def test_long_example_is_capped_and_split_across_equal_updates(self):
        with self._temp_seal() as root:
            prefix = SealedPrefix.load(root, 2)
            budget = EqualComputeBudget(6, 3, 2)
            schedule = EqualTokenSchedule.build(
                prefix,
                budget,
                lambda row: 5 if row["example_id"] == "a" else 2,
                sequence_length=4,
            )
            self.assertEqual(schedule.truncated_examples, 1)
            self.assertEqual(schedule.target_tokens, 6)
            self.assertEqual(
                [(span.example_index, span.start, span.end) for span in schedule.updates[0]],
                [(0, 0, 3)],
            )
            self.assertEqual(
                [(span.example_index, span.visit, span.start, span.end) for span in schedule.updates[1]],
                [(0, 0, 3, 4), (1, 0, 0, 2)],
            )

    def test_trainer_plans_and_does_not_fit(self):
        with self._temp_seal() as root:
            prefix = SealedPrefix.load(root, 2)
            budget = EqualComputeBudget(8, 4, 2)
            trainer = SealedPrefixTrainer(
                _ready_recipe(budget),
                prefix,
                lambda row: 2,
                sequence_length=2,
            )
            schedule = trainer.plan()
            self.assertEqual(schedule.target_tokens, 8)
            self.assertEqual(schedule.optimizer_updates, 2)
            self.assertEqual(schedule.truncated_examples, 0)
            with self.assertRaises(TrainingNotRun):
                trainer.train()

    def test_trainer_refuses_an_unfrozen_recipe(self):
        with self._temp_seal() as root:
            prefix = SealedPrefix.load(root, 2)
            trainer = SealedPrefixTrainer(
                FrozenTrainingRecipe({}),
                prefix,
                lambda row: 2,
                sequence_length=2,
            )
            with self.assertRaises(RecipeNotFrozen):
                trainer.plan()

    def _temp_seal(self):
        import tempfile

        root = Path(tempfile.mkdtemp(prefix="equal-compute-"))
        rows = [
            _record("a", "one\n"),
            _record("b", "two\n"),
            _record("c", "three\n"),
        ]
        _write_seal(root, {2: rows[:2], 3: rows})
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        return _Seal(root)


class _Seal:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> Path:
        return self.path

    def __exit__(self, *args: object) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
