"""Read a sealed prefix and repeat it to a frozen equal-compute budget.

This module does not choose a base model, a tokenizer, or the three budget
numbers. Those stay empty until a frozen recipe supplies them. It does not
fit an adapter.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from analysis.hashes import sha256_file
from analysis.jsonl_io import iter_physical_jsonl_lines
from analysis.seal import load_sealed_manifest
from analysis.training_examples import FORMATTER_VERSION

RECIPE_FIELDS: tuple[str, ...] = (
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
)

TargetTokenCount = Callable[[Mapping[str, object]], int]


class RecipeNotFrozen(ValueError):
    """A paper run was asked for before every frozen field had a value."""

    def __init__(self, missing: Sequence[str]) -> None:
        self.missing = tuple(missing)
        joined = ", ".join(self.missing)
        super().__init__(f"training recipe is not frozen; missing {joined}")


class TrainingNotRun(RuntimeError):
    """The schedule is ready and no adapter was fit."""


@dataclass(frozen=True)
class EqualComputeBudget:
    """The three numbers that must match at every prefix size."""

    non_padding_target_tokens: int
    effective_batch_tokens: int
    optimizer_updates: int

    def __post_init__(self) -> None:
        for name in (
            "non_padding_target_tokens",
            "effective_batch_tokens",
            "optimizer_updates",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive int")
        product = self.optimizer_updates * self.effective_batch_tokens
        if product != self.non_padding_target_tokens:
            raise ValueError(
                "optimizer updates times the effective batch token budget "
                "must equal the non-padding target token budget"
            )


@dataclass(frozen=True)
class FrozenTrainingRecipe:
    """Named recipe fields. Empty strings are not values."""

    values: Mapping[str, str]
    budget: EqualComputeBudget | None = None

    def missing(self) -> tuple[str, ...]:
        absent = [
            name
            for name in RECIPE_FIELDS
            if not str(self.values.get(name, "")).strip()
        ]
        if self.budget is None:
            absent.extend(
                (
                    "non_padding_target_token_budget",
                    "effective_batch_token_budget",
                    "optimizer_update_count",
                )
            )
        return tuple(absent)

    def require_ready(self) -> None:
        missing = self.missing()
        if missing:
            raise RecipeNotFrozen(missing)


@dataclass(frozen=True)
class SealedPrefix:
    """One prefix file whose bytes match the sealed prefix manifest."""

    size: int
    records: tuple[Mapping[str, object], ...]
    sha256: str
    prereg_sha256: str

    @classmethod
    def load(cls, seal_dir: Path, size: int) -> SealedPrefix:
        seal_dir = Path(seal_dir)
        sealed = load_sealed_manifest(seal_dir / "sealed-study-manifest.json")
        prefix_manifest_path = seal_dir / "prefixes" / "manifest.json"
        prefix_manifest = json.loads(prefix_manifest_path.read_text(encoding="utf-8"))
        if not isinstance(prefix_manifest, dict):
            raise ValueError("prefix manifest must be a JSON object")
        sealed_prereg = str(sealed.get("prereg_sha256", ""))
        prefix_prereg = str(prefix_manifest.get("prereg_sha256", ""))
        if not sealed_prereg or sealed_prereg != prefix_prereg:
            raise ValueError("sealed manifest and prefix manifest name different prereg hashes")
        if size not in list(sealed.get("prefixes") or []):
            raise ValueError(f"prefix size {size} is not in the sealed study")
        listed = (prefix_manifest.get("prefix_files") or {}).get(str(size))
        if not isinstance(listed, dict):
            raise ValueError(f"prefix manifest has no file for {size}")
        relative = str(listed.get("path") or "")
        path = seal_dir / "prefixes" / relative
        digest = sha256_file(path)
        if digest != listed.get("sha256"):
            raise ValueError(f"prefix-{size}.jsonl hash does not match the sealed manifest")
        records = _load_prefix_records(path)
        if len(records) != int(listed.get("records", -1)) or len(records) != size:
            raise ValueError(f"prefix-{size}.jsonl record count does not match {size}")
        return cls(
            size=size,
            records=tuple(records),
            sha256=digest,
            prereg_sha256=sealed_prereg,
        )


def batch_sizes_that_repeat(
    counts: Sequence[int],
    *,
    max_batch: int | None = None,
    max_cycles: int = 2,
) -> tuple[int, ...]:
    """Greedy prefix-order batch sizes that return to the first example.

    The first batch is a prefix sum of ``counts``. Sizes above ``max_batch``
    are left out. The walk stops after ``max_cycles`` passes through the
    sequence, so a tile that appears only later is not reported. The sum of
    one full pass is reported when it is inside the cap, because that batch
    contains every example once and then returns to the start.
    """
    if not counts:
        return ()
    if max_cycles < 1:
        raise ValueError("max_cycles must be a positive int")
    parsed: list[int] = []
    for count in counts:
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("token counts must be positive ints")
        parsed.append(count)
    total = sum(parsed)
    ceiling = total if max_batch is None else max_batch
    if ceiling < 1:
        return ()
    largest = max(parsed)
    found: list[int] = []
    if largest <= total <= ceiling and _returns_to_start(parsed, total, max_cycles):
        found.append(total)
    running = 0
    for count in parsed:
        running += count
        if running >= total or running > ceiling or running < largest:
            continue
        if _returns_to_start(parsed, running, max_cycles):
            found.append(running)
    return tuple(sorted(set(found)))


def _returns_to_start(counts: Sequence[int], batch: int, max_cycles: int) -> bool:
    total = len(counts)
    cursor = 0
    limit = total * max_cycles
    while cursor < limit:
        filled = 0
        while filled < batch:
            if cursor >= limit:
                return False
            nxt = counts[cursor % total]
            if filled + nxt > batch:
                return False
            filled += nxt
            cursor += 1
        if cursor % total == 0:
            return True
    return False


def assert_prefixes_nested(prefixes: Sequence[SealedPrefix]) -> None:
    """Each smaller prefix is the leading example ids of each larger one."""
    ordered = tuple(sorted(prefixes, key=lambda item: item.size))
    for earlier, later in zip(ordered, ordered[1:]):
        later_ids = [str(row["example_id"]) for row in later.records]
        earlier_ids = [str(row["example_id"]) for row in earlier.records]
        if later_ids[: len(earlier_ids)] != earlier_ids:
            raise ValueError(
                f"prefix {earlier.size} is not a leading slice of prefix {later.size}"
            )


@dataclass(frozen=True)
class RepeatedPrefixSchedule:
    """Prefix order, cycled, tiled into equal token batches.

    This does not shuffle. The shuffle algorithm is a separate frozen field
    and is not applied here.
    """

    prefix_size: int
    budget: EqualComputeBudget
    batches: tuple[tuple[Mapping[str, object], ...], ...]
    batch_tokens: tuple[int, ...]

    @property
    def optimizer_updates(self) -> int:
        return len(self.batches)

    @property
    def target_tokens(self) -> int:
        return sum(self.batch_tokens)

    @classmethod
    def build(
        cls,
        prefix: SealedPrefix,
        budget: EqualComputeBudget,
        count_target_tokens: TargetTokenCount,
    ) -> RepeatedPrefixSchedule:
        if not prefix.records:
            raise ValueError("prefix is empty")
        batches: list[tuple[Mapping[str, object], ...]] = []
        batch_tokens: list[int] = []
        cursor = 0
        total = len(prefix.records)
        for _update in range(budget.optimizer_updates):
            batch: list[Mapping[str, object]] = []
            filled = 0
            while filled < budget.effective_batch_tokens:
                record = prefix.records[cursor % total]
                tokens = count_target_tokens(record)
                if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 1:
                    raise ValueError("target token count must be a positive int")
                if filled + tokens > budget.effective_batch_tokens:
                    if not batch:
                        raise ValueError(
                            "one example has more target tokens than the effective batch budget"
                        )
                    raise ValueError(
                        "prefix token sizes do not tile the effective batch token budget"
                    )
                batch.append(record)
                filled += tokens
                cursor += 1
            batches.append(tuple(batch))
            batch_tokens.append(filled)
        return cls(
            prefix_size=prefix.size,
            budget=budget,
            batches=tuple(batches),
            batch_tokens=tuple(batch_tokens),
        )


@dataclass(frozen=True)
class TokenSpan:
    """Leading-token slice of one visit to a sealed example."""

    example_index: int
    visit: int
    start: int
    end: int

    @property
    def tokens(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class EqualTokenSchedule:
    """Same token count and update count on every prefix.

    Each visit keeps at most ``sequence_length`` leading target tokens and
    drops the tail. Updates then consume exactly the batch budget, continuing
    into the next example and the next visit. No padding is added.
    """

    prefix_size: int
    sequence_length: int
    budget: EqualComputeBudget
    updates: tuple[tuple[TokenSpan, ...], ...]
    truncated_examples: int

    @property
    def optimizer_updates(self) -> int:
        return len(self.updates)

    @property
    def target_tokens(self) -> int:
        return sum(span.tokens for update in self.updates for span in update)

    @classmethod
    def build(
        cls,
        prefix: SealedPrefix,
        budget: EqualComputeBudget,
        count_target_tokens: TargetTokenCount,
        sequence_length: int,
    ) -> EqualTokenSchedule:
        if isinstance(sequence_length, bool) or not isinstance(sequence_length, int) or sequence_length < 1:
            raise ValueError("sequence_length must be a positive int")
        if not prefix.records:
            raise ValueError("prefix is empty")
        eligible: list[int] = []
        truncated = 0
        for record in prefix.records:
            tokens = count_target_tokens(record)
            if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 1:
                raise ValueError("target token count must be a positive int")
            if tokens > sequence_length:
                truncated += 1
            eligible.append(min(tokens, sequence_length))
        total = len(eligible)
        example_index = 0
        offset = 0
        visit = 0
        updates: list[tuple[TokenSpan, ...]] = []
        for _update in range(budget.optimizer_updates):
            need = budget.effective_batch_tokens
            spans: list[TokenSpan] = []
            while need:
                available = eligible[example_index] - offset
                take = min(need, available)
                spans.append(
                    TokenSpan(
                        example_index=example_index,
                        visit=visit,
                        start=offset,
                        end=offset + take,
                    )
                )
                need -= take
                offset += take
                if offset == eligible[example_index]:
                    example_index += 1
                    offset = 0
                    if example_index == total:
                        example_index = 0
                        visit += 1
            updates.append(tuple(spans))
        return cls(
            prefix_size=prefix.size,
            sequence_length=sequence_length,
            budget=budget,
            updates=tuple(updates),
            truncated_examples=truncated,
        )


def budget_covering_one_pass(counts: Sequence[int], sequence_length: int) -> EqualComputeBudget:
    """One context-sized batch, repeated until the largest prefix is covered once.

    ``sequence_length`` is both the cap on an example and the effective batch.
    The returned target-token count is that batch times the update count, so
    every smaller prefix can use the same budget by cycling.
    """
    if isinstance(sequence_length, bool) or not isinstance(sequence_length, int) or sequence_length < 1:
        raise ValueError("sequence_length must be a positive int")
    eligible = 0
    for count in counts:
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("token counts must be positive ints")
        eligible += min(count, sequence_length)
    if eligible < 1:
        raise ValueError("prefix has no eligible target tokens")
    updates = (eligible + sequence_length - 1) // sequence_length
    return EqualComputeBudget(updates * sequence_length, sequence_length, updates)


def plan_equal_compute(
    seal_dir: Path,
    count_target_tokens: TargetTokenCount,
    sequence_length: int = 8192,
) -> dict[str, object]:
    """Plan every sealed prefix under the budget that covers the largest one."""
    seal_dir = Path(seal_dir)
    sealed = load_sealed_manifest(seal_dir / "sealed-study-manifest.json")
    sizes = [int(size) for size in sealed.get("prefixes") or []]
    if not sizes:
        raise ValueError("sealed study has no prefixes")
    prefixes = [SealedPrefix.load(seal_dir, size) for size in sizes]
    assert_prefixes_nested(prefixes)
    largest = max(prefixes, key=lambda item: item.size)
    budget = budget_covering_one_pass(
        [count_target_tokens(row) for row in largest.records],
        sequence_length,
    )
    planned: dict[str, object] = {}
    for prefix in prefixes:
        schedule = EqualTokenSchedule.build(
            prefix,
            budget,
            count_target_tokens,
            sequence_length,
        )
        if schedule.target_tokens != budget.non_padding_target_tokens:
            raise ValueError(f"prefix {prefix.size} missed the shared token budget")
        if schedule.optimizer_updates != budget.optimizer_updates:
            raise ValueError(f"prefix {prefix.size} missed the shared update count")
        planned[str(prefix.size)] = {
            "records": prefix.size,
            "truncated_examples": schedule.truncated_examples,
            "target_tokens": schedule.target_tokens,
            "optimizer_updates": schedule.optimizer_updates,
        }
    return {
        "sequence_length": sequence_length,
        "prereg_sha256": largest.prereg_sha256,
        "budget": {
            "non_padding_target_tokens": budget.non_padding_target_tokens,
            "effective_batch_tokens": budget.effective_batch_tokens,
            "optimizer_updates": budget.optimizer_updates,
        },
        "prefixes": planned,
    }


class SealedPrefixTrainer:
    """Plan one sealed prefix under a frozen recipe. Do not fit weights."""

    def __init__(
        self,
        recipe: FrozenTrainingRecipe,
        prefix: SealedPrefix,
        count_target_tokens: TargetTokenCount,
        sequence_length: int,
    ) -> None:
        self.recipe = recipe
        self.prefix = prefix
        self.count_target_tokens = count_target_tokens
        self.sequence_length = sequence_length

    def plan(self) -> EqualTokenSchedule:
        self.recipe.require_ready()
        if self.recipe.budget is None:
            raise RecipeNotFrozen(("equal_compute_budget",))
        return EqualTokenSchedule.build(
            self.prefix,
            self.recipe.budget,
            self.count_target_tokens,
            self.sequence_length,
        )

    def train(self) -> None:
        self.plan()
        raise TrainingNotRun(
            "the repeated schedule is planned; this class does not fit an adapter"
        )


def plan_equal_compute_cli(argv: list[str]) -> int:
    if len(argv) not in (1, 3) or (len(argv) == 3 and argv[1] != "--sequence-length"):
        print(
            "usage: python3 -m analysis plan-equal-compute SEAL_DIR [--sequence-length N]",
            file=sys.stderr,
        )
        return 2
    sequence_length = 8192
    if len(argv) == 3:
        sequence_length = int(argv[2])
    summary = plan_equal_compute(
        Path(argv[0]),
        lambda row: int(row["lexical_token_count"]),
        sequence_length,
    )
    summary["counter"] = "lexical_token_count"
    summary["counter_note"] = (
        "Lexical counts are the stored diagnostic. Replace this counter with the "
        "selected tokenizer before treating the budget numbers as frozen."
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _load_prefix_records(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for line_number, line in iter_physical_jsonl_lines(path):
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path.name}:{line_number} is not an object")
        example_id = row.get("example_id")
        if not isinstance(example_id, str) or not example_id:
            raise ValueError(f"{path.name}:{line_number} missing example_id")
        if example_id in seen:
            raise ValueError(f"{path.name} repeats example_id {example_id}")
        seen.add(example_id)
        if row.get("formatter_version") != FORMATTER_VERSION:
            raise ValueError(f"{path.name}:{line_number} formatter is not {FORMATTER_VERSION}")
        prompt = row.get("prompt")
        response = row.get("response")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"{path.name}:{line_number} missing prompt")
        if not isinstance(response, str) or not response.strip():
            raise ValueError(f"{path.name}:{line_number} missing response")
        records.append(row)
    return records
