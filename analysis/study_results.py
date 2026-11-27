"""Analyze sealed holdout score JSONL per the registered protocol."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from analysis.jsonl_io import iter_physical_jsonl_lines
from analysis.pass_at import unbiased_pass_at_k

from analysis.bootstrap import cluster_bootstrap_ci
from analysis.design import align_binary_scores, holdout_domain_counts, training_seed_plan
from analysis.practices import (
    areas,
    confirmatory_contrast_name,
    descriptive_exploratory_steps,
    discordant_counts,
    exploratory_contrast_names,
    load_prereg,
    one_sided_step_p,
    prefix_sizes,
)


def _contrast_prefixes(name: str) -> tuple[int, int]:
    if not name.startswith("prefix_") or "_minus_" not in name:
        raise ValueError(f"unknown contrast name {name}")
    later_text, earlier_text = name.removeprefix("prefix_").split("_minus_", 1)
    return int(later_text), int(earlier_text)


def _normalize_row(raw: object, line: int) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError(f"line {line}: row must be a JSON object")
    required = ("task_id", "domain", "area", "prefix_size", "training_seed", "passed")
    for key in required:
        if key not in raw:
            raise ValueError(f"line {line}: missing field {key}")
    extra = set(raw) - set(required)
    if extra:
        raise ValueError(f"line {line}: unexpected fields {sorted(extra)}")
    task_id = raw["task_id"]
    domain = raw["domain"]
    area = raw["area"]
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError(f"line {line}: invalid task_id")
    if not isinstance(domain, str) or not isinstance(area, str):
        raise ValueError(f"line {line}: domain and area must be strings")
    if not isinstance(raw["passed"], bool):
        raise ValueError(f"line {line}: passed must be bool")
    try:
        prefix_size = int(raw["prefix_size"])
        training_seed = int(raw["training_seed"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"line {line}: invalid prefix_size or training_seed") from exc
    return {
        "task_id": task_id,
        "domain": domain,
        "area": area,
        "prefix_size": prefix_size,
        "training_seed": training_seed,
        "passed": raw["passed"],
    }


def load_scores_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen_cells: set[tuple[str, int, int]] = set()
    for line_number, stripped in iter_physical_jsonl_lines(path):
        raw = json.loads(stripped)
        row = _normalize_row(raw, line_number)
        cell = (str(row["task_id"]), int(row["prefix_size"]), int(row["training_seed"]))
        if cell in seen_cells:
            raise ValueError(f"line {line_number}: duplicate cell {cell}")
        seen_cells.add(cell)
        rows.append(row)
    if not rows:
        raise ValueError("empty scores file")
    return rows


def _registered_sample_decoding(prereg: dict) -> tuple[int, float, tuple[int, ...]]:
    decoding = prereg.get("decoding")
    if not isinstance(decoding, Mapping):
        raise ValueError("prereg missing decoding section")
    count = decoding.get("sample_count_k")
    temperature = decoding.get("sample_temperature")
    seeds = decoding.get("sample_seeds")
    if count != 5:
        raise ValueError("registered sample_count_k must be 5")
    if temperature != 0.8:
        raise ValueError("registered sample_temperature must be 0.8")
    if not isinstance(seeds, list):
        raise ValueError("registered sample_seeds invalid")
    sample_seeds = tuple(int(seed) for seed in seeds)
    if sample_seeds != (1, 2, 3, 4, 5):
        raise ValueError("registered sample_seeds must be [1, 2, 3, 4, 5]")
    if len(sample_seeds) != 5:
        raise ValueError("registered sample_seeds must have length 5")
    return 5, float(temperature), sample_seeds


def _normalize_sample_row(raw: object, line: int) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError(f"line {line}: row must be a JSON object")
    required = (
        "task_id",
        "domain",
        "area",
        "prefix_size",
        "training_seed",
        "sample_seed",
        "passed",
    )
    for key in required:
        if key not in raw:
            raise ValueError(f"line {line}: missing field {key}")
    extra = set(raw) - set(required)
    if extra:
        raise ValueError(f"line {line}: unexpected fields {sorted(extra)}")
    task_id = raw["task_id"]
    domain = raw["domain"]
    area = raw["area"]
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError(f"line {line}: invalid task_id")
    if not isinstance(domain, str) or not isinstance(area, str):
        raise ValueError(f"line {line}: domain and area must be strings")
    if not isinstance(raw["passed"], bool):
        raise ValueError(f"line {line}: passed must be bool")
    try:
        prefix_size = int(raw["prefix_size"])
        training_seed = int(raw["training_seed"])
        sample_seed = int(raw["sample_seed"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"line {line}: invalid numeric fields") from exc
    return {
        "task_id": task_id,
        "domain": domain,
        "area": area,
        "prefix_size": prefix_size,
        "training_seed": training_seed,
        "sample_seed": sample_seed,
        "passed": raw["passed"],
    }


def load_samples_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen_cells: set[tuple[str, int, int, int]] = set()
    for line_number, stripped in iter_physical_jsonl_lines(path):
        raw = json.loads(stripped)
        row = _normalize_sample_row(raw, line_number)
        cell = (
            str(row["task_id"]),
            int(row["prefix_size"]),
            int(row["training_seed"]),
            int(row["sample_seed"]),
        )
        if cell in seen_cells:
            raise ValueError(f"line {line_number}: duplicate cell {cell}")
        seen_cells.add(cell)
        rows.append(row)
    if not rows:
        raise ValueError("empty samples file")
    return rows


def validate_samples_grid(rows: Sequence[Mapping[str, object]], prereg: dict) -> dict[str, object]:
    sample_n, sample_temperature, sample_seeds = _registered_sample_decoding(prereg)
    plan = training_seed_plan(prereg)
    holdout_domain_counts(prereg)
    prefixes = prefix_sizes(prereg)
    seeds = list(plan["identities"])
    registered = areas(prereg)
    by_prefix_seed_task: dict[tuple[int, int], dict[str, dict[int, dict[str, object]]]] = {}
    metadata: dict[str, tuple[str, str]] = {}
    for row in rows:
        task_id = str(row["task_id"])
        prefix = int(row["prefix_size"])
        seed = int(row["training_seed"])
        sample_seed = int(row["sample_seed"])
        domain = str(row["domain"])
        area = str(row["area"])
        if prefix not in prefixes:
            raise ValueError(f"unregistered prefix {prefix}")
        if seed not in seeds:
            raise ValueError(f"unregistered training seed {seed}")
        if sample_seed not in sample_seeds:
            raise ValueError(f"unregistered sample seed {sample_seed}")
        if area not in registered.get(domain, ()):
            raise ValueError(f"unregistered area {domain}/{area}")
        cell_key = (prefix, seed)
        by_prefix_seed_task.setdefault(cell_key, {})
        by_task = by_prefix_seed_task[cell_key].setdefault(task_id, {})
        if sample_seed in by_task:
            raise ValueError(f"duplicate sample_seed {sample_seed} for {task_id} in cell {cell_key}")
        by_task[sample_seed] = dict(row)
        meta = (domain, area)
        if task_id in metadata and metadata[task_id] != meta:
            raise ValueError(f"metadata drift for task {task_id}")
        metadata[task_id] = meta
    expected_cells = [(prefix, seed) for prefix in prefixes for seed in seeds]
    missing_cells = [cell for cell in expected_cells if cell not in by_prefix_seed_task]
    if missing_cells:
        raise ValueError(f"missing prefix×seed sample cells {missing_cells[:3]}")
    reference: set[str] | None = None
    for cell in expected_cells:
        tasks = by_prefix_seed_task[cell]
        if len(tasks) != 742:
            raise ValueError(f"sample cell {cell} must have 742 tasks, saw {len(tasks)}")
        ids = set(tasks)
        if reference is None:
            reference = ids
        elif ids != reference:
            raise ValueError(f"sample task ids differ for cell {cell}")
        for task_id, samples in tasks.items():
            if set(samples) != set(sample_seeds):
                missing_seeds = sorted(set(sample_seeds) - set(samples))
                raise ValueError(
                    f"task {task_id} in cell {cell} missing sample_seeds {missing_seeds}"
                )
        domain_counts: dict[str, int] = {}
        for task_id in tasks:
            sample_row = tasks[task_id][sample_seeds[0]]
            domain = str(sample_row["domain"])
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        if domain_counts != {"embabel": 371, "drivine": 371}:
            raise ValueError(f"sample cell {cell} domain counts {domain_counts}")
    return {
        "tasks": len(reference or []),
        "prefixes": list(prefixes),
        "seeds": seeds,
        "cells": len(expected_cells),
        "samples_per_task": sample_n,
        "sample_seeds": list(sample_seeds),
        "sample_temperature": sample_temperature,
        "rows_per_cell": 742 * sample_n,
    }


def _per_task_pass_at_estimates(
    rows: Sequence[Mapping[str, object]],
    *,
    prefix_size: int,
    training_seed: int,
    sample_seeds: Sequence[int],
    k: int,
    n: int,
) -> list[float]:
    by_task: dict[str, list[bool]] = {}
    for row in rows:
        if int(row["prefix_size"]) != prefix_size or int(row["training_seed"]) != training_seed:
            continue
        task_id = str(row["task_id"])
        sample_seed = int(row["sample_seed"])
        by_task.setdefault(task_id, [])
        by_task[task_id].append((sample_seed, bool(row["passed"])))
    estimates: list[float] = []
    for task_id in sorted(by_task):
        entries = sorted(by_task[task_id], key=lambda pair: pair[0])
        if [seed for seed, _ in entries] != list(sample_seeds):
            raise ValueError(f"incomplete samples for task {task_id}")
        correct = sum(1 for _, passed in entries if passed)
        estimates.append(unbiased_pass_at_k(correct, n, k))
    return estimates


def compute_secondary_sampled_metrics(
    rows: Sequence[Mapping[str, object]],
    prereg: dict,
    *,
    n_resamples: int | None = None,
) -> dict[str, object]:
    """Per prefix×training_seed mean pass@1 and pass@5 with task bootstrap CIs."""
    sample_n, sample_temperature, sample_seeds = _registered_sample_decoding(prereg)
    stats = prereg["statistics"]
    bootstrap_seed = int(stats["bootstrap_seed"])
    resamples = int(n_resamples if n_resamples is not None else stats["bootstrap_resamples"])
    prefixes = prefix_sizes(prereg)
    seeds = list(training_seed_plan(prereg)["identities"])
    by_cell: list[dict[str, object]] = []
    for prefix in prefixes:
        for training_seed in seeds:
            pass1_estimates = _per_task_pass_at_estimates(
                rows,
                prefix_size=prefix,
                training_seed=training_seed,
                sample_seeds=sample_seeds,
                k=1,
                n=sample_n,
            )
            pass5_estimates = _per_task_pass_at_estimates(
                rows,
                prefix_size=prefix,
                training_seed=training_seed,
                sample_seeds=sample_seeds,
                k=5,
                n=sample_n,
            )
            if not pass1_estimates or len(pass1_estimates) != len(pass5_estimates):
                raise ValueError(f"missing sampled outcomes for prefix {prefix} seed {training_seed}")

            def _mean(values: Sequence[float]) -> float:
                return sum(values) / len(values)

            p1, p1_lo, p1_hi = cluster_bootstrap_ci(
                pass1_estimates,
                _mean,
                n_resamples=resamples,
                seed=bootstrap_seed,
            )
            p5, p5_lo, p5_hi = cluster_bootstrap_ci(
                pass5_estimates,
                _mean,
                n_resamples=resamples,
                seed=bootstrap_seed,
            )
            by_cell.append(
                {
                    "prefix_size": prefix,
                    "training_seed": training_seed,
                    "n_tasks": len(pass1_estimates),
                    "pass_at_1": {
                        "k": 1,
                        "n_samples_per_task": sample_n,
                        "estimator": "chen2021_unbiased",
                        "mean": p1,
                        "ci_95": {"lower": p1_lo, "upper": p1_hi},
                        "bootstrap_resamples": resamples,
                        "bootstrap_seed": bootstrap_seed,
                    },
                    "pass_at_5": {
                        "k": 5,
                        "n_samples_per_task": sample_n,
                        "estimator": "chen2021_unbiased",
                        "mean": p5,
                        "ci_95": {"lower": p5_lo, "upper": p5_hi},
                        "bootstrap_resamples": resamples,
                        "bootstrap_seed": bootstrap_seed,
                    },
                }
            )
    return {
        "status": "provided",
        "confirmatory": False,
        "role": "secondary_non_confirmatory",
        "inference_role": "descriptive_secondary_outcome",
        "estimator": "chen2021_unbiased",
        "decoding_temperature": sample_temperature,
        "sample_seeds": list(sample_seeds),
        "samples_per_task": sample_n,
        "note": "sampled pass@k does not affect confirmatory_decision; McNemar not applied",
        "by_prefix_training_seed": by_cell,
    }


def secondary_sampled_metrics_not_provided() -> dict[str, object]:
    return {
        "status": "not_provided",
        "confirmatory": False,
        "role": "secondary_non_confirmatory",
        "inference_role": "descriptive_secondary_outcome",
        "note": "sampled score JSONL was not supplied; no secondary pass@k analysis performed",
    }


def validate_scores_grid(rows: Sequence[Mapping[str, object]], prereg: dict) -> dict[str, object]:
    plan = training_seed_plan(prereg)
    holdout_domain_counts(prereg)
    prefixes = prefix_sizes(prereg)
    seeds = list(plan["identities"])
    registered = areas(prereg)
    by_cell: dict[tuple[int, int], dict[str, dict[str, object]]] = {}
    metadata: dict[str, tuple[str, str]] = {}
    for row in rows:
        task_id = str(row["task_id"])
        prefix = int(row["prefix_size"])
        seed = int(row["training_seed"])
        domain = str(row["domain"])
        area = str(row["area"])
        if prefix not in prefixes:
            raise ValueError(f"unregistered prefix {prefix}")
        if seed not in seeds:
            raise ValueError(f"unregistered training seed {seed}")
        if area not in registered.get(domain, ()):
            raise ValueError(f"unregistered area {domain}/{area}")
        cell_key = (prefix, seed)
        by_cell.setdefault(cell_key, {})
        if task_id in by_cell[cell_key]:
            raise ValueError(f"duplicate task_id {task_id} in cell {cell_key}")
        by_cell[cell_key][task_id] = dict(row)
        meta = (domain, area)
        if task_id in metadata and metadata[task_id] != meta:
            raise ValueError(f"metadata drift for task {task_id}")
        metadata[task_id] = meta
    expected_cells = [(prefix, seed) for prefix in prefixes for seed in seeds]
    missing_cells = [cell for cell in expected_cells if cell not in by_cell]
    if missing_cells:
        raise ValueError(f"missing prefix×seed cells {missing_cells[:3]}")
    reference = None
    for cell in expected_cells:
        tasks = by_cell[cell]
        if len(tasks) != 742:
            raise ValueError(f"cell {cell} must have 742 tasks, saw {len(tasks)}")
        ids = set(tasks)
        if reference is None:
            reference = ids
        elif ids != reference:
            raise ValueError(f"task ids differ for cell {cell}")
        domain_counts: dict[str, int] = {}
        for task_id in tasks:
            domain = str(tasks[task_id]["domain"])
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        if domain_counts != {"embabel": 371, "drivine": 371}:
            raise ValueError(f"cell {cell} domain counts {domain_counts}")
    return {
        "tasks": len(reference or []),
        "prefixes": list(prefixes),
        "seeds": seeds,
        "cells": len(expected_cells),
    }


def _rows_for_prefix_seed(
    rows: Sequence[Mapping[str, object]],
    *,
    prefix_size: int,
    training_seed: int,
) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in rows
        if int(row["prefix_size"]) == prefix_size and int(row["training_seed"]) == training_seed
    ]


def _paired_contrast(
    rows: Sequence[Mapping[str, object]],
    prereg: dict,
    *,
    later_prefix: int,
    earlier_prefix: int,
    training_seed: int,
    confirmatory: bool,
    role: str,
    contrast_name: str,
    n_resamples: int | None = None,
) -> dict[str, object]:
    stats = prereg["statistics"]
    alpha = float(stats["alpha_confirmatory"])
    bootstrap_seed = int(stats["bootstrap_seed"])
    resamples = int(n_resamples if n_resamples is not None else stats["bootstrap_resamples"])
    later_rows = _rows_for_prefix_seed(rows, prefix_size=later_prefix, training_seed=training_seed)
    earlier_rows = _rows_for_prefix_seed(rows, prefix_size=earlier_prefix, training_seed=training_seed)
    ids, later_passed, earlier_passed = align_binary_scores(later_rows, earlier_rows)
    n = len(ids)
    later_rate = sum(later_passed) / n
    earlier_rate = sum(earlier_passed) / n
    effect_pp = (later_rate - earlier_rate) * 100.0
    differences = [float(later) - float(earlier) for later, earlier in zip(later_passed, earlier_passed)]
    _, ci_lo, ci_hi = cluster_bootstrap_ci(
        differences,
        lambda xs: sum(xs) / len(xs) * 100.0,
        n_resamples=resamples,
        seed=bootstrap_seed,
    )
    b, c = discordant_counts(earlier_passed, later_passed)
    p_value = one_sided_step_p(earlier_passed, later_passed)
    return {
        "contrast": contrast_name,
        "confirmatory": confirmatory,
        "role": role,
        "training_seed": training_seed,
        "earlier_prefix": earlier_prefix,
        "later_prefix": later_prefix,
        "n_tasks": n,
        "pass_rate_earlier": earlier_rate,
        "pass_rate_later": later_rate,
        "effect_percentage_points": effect_pp,
        "discordant_b_earlier_wins": b,
        "discordant_c_later_wins": c,
        "p_value_one_sided": p_value,
        "alpha": alpha,
        "rejects": p_value <= alpha,
        "bootstrap_resamples": resamples,
        "bootstrap_seed": bootstrap_seed,
        "effect_ci_95_percentage_points": {
            "lower": ci_lo,
            "upper": ci_hi,
        },
    }


def validate_scores_against_seal(
    rows: Sequence[Mapping[str, object]],
    sealed_manifest: Mapping[str, object],
) -> None:
    holdout = sealed_manifest.get("holdout")
    if not isinstance(holdout, Mapping):
        raise ValueError("sealed manifest missing holdout section")
    expected_ids = holdout.get("task_ids")
    metadata = holdout.get("metadata_by_task")
    if not isinstance(expected_ids, list) or not isinstance(metadata, Mapping):
        raise ValueError("sealed manifest holdout metadata invalid")
    expected_set = {str(task_id) for task_id in expected_ids}
    scored_ids = {str(row["task_id"]) for row in rows}
    if scored_ids != expected_set:
        missing = sorted(expected_set - scored_ids)
        extra = sorted(scored_ids - expected_set)
        raise ValueError(
            f"score task_ids mismatch sealed holdout missing={missing[:5]} extra={extra[:5]}"
        )
    for row in rows:
        task_id = str(row["task_id"])
        meta = metadata.get(task_id)
        if not isinstance(meta, Mapping):
            raise ValueError(f"sealed manifest missing metadata for {task_id}")
        if str(row["domain"]) != str(meta.get("domain")) or str(row["area"]) != str(meta.get("area")):
            raise ValueError(f"score metadata drift for {task_id} vs sealed holdout")
    manifest_hash = holdout.get("manifest_sha256")
    if not isinstance(manifest_hash, str):
        raise ValueError("sealed manifest missing holdout manifest hash")


def analyze_study_results(
    rows: Sequence[Mapping[str, object]],
    prereg: dict | None = None,
    *,
    n_resamples: int | None = None,
    sealed_manifest: Mapping[str, object] | None = None,
    require_sealed_manifest: bool = False,
    sample_rows: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Validate grid and compute confirmatory, replication, and exploratory stats."""
    prereg = prereg or load_prereg()
    if require_sealed_manifest and sealed_manifest is None:
        raise ValueError("production study-results requires a sealed manifest")
    if sealed_manifest is not None:
        validate_scores_against_seal(rows, sealed_manifest)
    grid = validate_scores_grid(rows, prereg)
    plan = training_seed_plan(prereg)
    prefixes = prefix_sizes(prereg)
    primary_seed = int(plan["primary"])
    replication_seeds = list(plan["replications"])
    confirmatory_name = confirmatory_contrast_name(prereg)
    alpha = float(prereg["statistics"]["alpha_confirmatory"])

    confirmatory = _paired_contrast(
        rows,
        prereg,
        later_prefix=16000,
        earlier_prefix=500,
        training_seed=primary_seed,
        confirmatory=True,
        role="primary_confirmatory",
        contrast_name=confirmatory_name,
        n_resamples=n_resamples,
    )
    replications = [
        _paired_contrast(
            rows,
            prereg,
            later_prefix=16000,
            earlier_prefix=500,
            training_seed=seed,
            confirmatory=False,
            role="robustness_replication",
            contrast_name=confirmatory_name,
            n_resamples=n_resamples,
        )
        for seed in replication_seeds
    ]

    exploratory_steps: list[dict[str, object]] = []
    raw_p: dict[str, float] = {}
    for name in exploratory_contrast_names(prereg):
        later, earlier = _contrast_prefixes(name)
        step = _paired_contrast(
            rows,
            prereg,
            later_prefix=later,
            earlier_prefix=earlier,
            training_seed=primary_seed,
            confirmatory=False,
            role="exploratory_adjacent",
            contrast_name=name,
            n_resamples=n_resamples,
        )
        raw_p[name] = float(step["p_value_one_sided"])
        exploratory_steps.append(step)
    holm = descriptive_exploratory_steps(raw_p, prereg)

    primary_effects = [float(confirmatory["effect_percentage_points"])] + [
        float(rep["effect_percentage_points"]) for rep in replications
    ]
    pooled_exploratory = {
        "confirmatory": False,
        "role": "pooled_seed_summary_exploratory_only",
        "contrast": confirmatory_name,
        "later_prefix": 16000,
        "earlier_prefix": 500,
        "effect_percentage_points_mean": sum(primary_effects) / len(primary_effects),
        "effect_percentage_points_min": min(primary_effects),
        "effect_percentage_points_max": max(primary_effects),
        "seeds": [primary_seed, *replication_seeds],
        "note": "no pooled p-value; not seed-population inference",
    }

    decision = {
        "contrast": confirmatory_name,
        "alpha": alpha,
        "rejects": confirmatory["rejects"],
        "source": "primary_training_seed_only",
        "replication_results_alter_primary": False,
    }

    if sample_rows is not None:
        if sealed_manifest is not None:
            validate_scores_against_seal(sample_rows, sealed_manifest)
        sampled_grid = validate_samples_grid(sample_rows, prereg)
        secondary_sampled = compute_secondary_sampled_metrics(
            sample_rows,
            prereg,
            n_resamples=n_resamples,
        )
        secondary_sampled["grid"] = sampled_grid
    else:
        secondary_sampled = secondary_sampled_metrics_not_provided()

    return {
        "study_id": prereg.get("study_id"),
        "grid": grid,
        "prefixes": list(prefixes),
        "confirmatory_contrast": confirmatory,
        "replications": replications,
        "exploratory_adjacent_steps": exploratory_steps,
        "exploratory_adjacent_holm_descriptive": holm,
        "exploratory_pooled_primary_contrast_by_seed": pooled_exploratory,
        "confirmatory_decision": decision,
        "secondary_sampled_metrics": secondary_sampled,
    }


def dumps_deterministic_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def run_study_results(
    path: Path,
    prereg: dict | None = None,
    *,
    n_resamples: int | None = None,
    sealed_manifest_path: Path | None = None,
    require_sealed_manifest: bool = False,
    samples_path: Path | None = None,
) -> dict[str, object]:
    rows = load_scores_jsonl(path)
    sample_rows = load_samples_jsonl(samples_path) if samples_path is not None else None
    sealed_manifest = None
    if sealed_manifest_path is not None:
        from analysis.seal import load_sealed_manifest

        sealed_manifest = load_sealed_manifest(sealed_manifest_path)
    return analyze_study_results(
        rows,
        prereg,
        n_resamples=n_resamples,
        sealed_manifest=sealed_manifest,
        require_sealed_manifest=require_sealed_manifest,
        sample_rows=sample_rows,
    )


def study_results_cli(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit(
            "usage: python3 -m analysis study-results SCORES.jsonl "
            "--sealed-manifest PATH [--samples SAMPLES.jsonl]"
        )
    path = Path(argv[0])
    sealed_path: Path | None = None
    samples_path: Path | None = None
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--sealed-manifest":
            index += 1
            if index >= len(argv):
                raise SystemExit("study-results --sealed-manifest requires a path")
            sealed_path = Path(argv[index])
        elif token == "--samples":
            index += 1
            if index >= len(argv):
                raise SystemExit("study-results --samples requires a path")
            samples_path = Path(argv[index])
        else:
            raise SystemExit(f"unknown study-results option {token}")
        index += 1
    if sealed_path is None:
        raise SystemExit("study-results requires --sealed-manifest")
    result = run_study_results(
        path,
        sealed_manifest_path=sealed_path,
        require_sealed_manifest=True,
        samples_path=samples_path,
    )
    print(dumps_deterministic_json(result), end="")
    return 0