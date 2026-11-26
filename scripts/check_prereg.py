#!/usr/bin/env python3
"""Lock the pre-registration protocol. A later edit fails unless it is an explicit amendment."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE_PATH = ROOT / "docs" / "protocol" / "preregistration.md"
AMEND_PATH = ROOT / "docs" / "protocol" / "preregistration-amendments.md"

EXPECTED_SHA256 = "3aa22226b3ec325c1ee5ebcf3f098a84b340fa68f44004db48c08701ec4ac602"

LOCK_PATHS = (
    "docs/protocol/preregistration.md",
    "docs/protocol/preregistration-amendments.md",
    "scripts/check_prereg.py",
    ".github/workflows/prereg.yml",
)

PAPER_TRACK_FORBIDDEN_SUBSTRINGS = ("kiln", "jasper")

PAPER_TRACK_RELATIVE_DIRS = (
    "docs/protocol",
    "docs/paper",
    "experiments/paper-v1",
)

POISON_PREFIXES = (
    "experiments/runs/",
    "benchmark/tasks/",
)

START = "<!-- prereg:start -->"
END = "<!-- prereg:end -->"

EXPECTED_PREREG = {
    "frozen_on": "2026-11-25",
    "study_id": "two-domain-example-dose-v1",
    "inference_backend": "ollama",
    "inference_host_class": "halo-395",
    "quant_default": "Q4_K_M",
    "quant_sensitivity_row": "Q8_0",
    "quant_sensitivity_applies": "shareable_base_config_A_only",
    "num_ctx": 8192,
    "arms": {
        "S": {
            "parameter_billions_min": 7,
            "parameter_billions_max": 14,
            "peak_memory_gb_max_q4_k_m": 16,
            "configs": ["A", "B", "C", "D"],
        },
        "M": {
            "parameter_billions_min": 24,
            "parameter_billions_max": 34,
            "configs": ["A", "B"],
        },
        "L": {
            "dense_max_billion_parameters": 70,
            "moe_max_billion_parameters_total": 120,
            "configs": ["A", "B"],
        },
    },
    "configs": {
        "A": {"retrieval": False, "lora": False},
        "B": {"retrieval": True, "lora": False},
        "C": {"retrieval": False, "lora": True},
        "D": {"retrieval": True, "lora": True},
    },
    "lora_per_domain": True,
    "selection_rules": {
        "metric": "full_task_success",
        "tie_break": "smaller_peak_memory_gb",
        "split_for_selection": "dev",
        "config_for_selection": "A",
        "selection_domain": "embabel",
    },
    "splits": {
        "confirmatory_split": "holdout",
        "dev_allows_tuning": True,
        "model_selection_domain": "embabel",
        "embabel": {
            "part": "B",
            "pilot_task_ids": "E01-E20,KB01",
            "holdout_min_tasks": 742,
            "holdout_min_tasks_scope": "per_area",
            "holdout_area_count": 6,
            "holdout_categories": 6,
        },
        "drivine": {
            "part": "C",
            "corpus_repo": "jmjava/drivine-slm",
            "dev_training_file": "data/drivine_instruct.json",
            "dev_training_pairs_count": 100,
            "dev_excluded_from_holdout": True,
            "pilot_executable_min_tasks": 20,
            "holdout_min_tasks": 742,
            "holdout_min_tasks_scope": "per_area",
            "holdout_area_count": 5,
            "holdout_category_labels": [
                "generation",
                "repair",
                "query",
                "graph_rag",
                "integration",
            ],
            "primary_executable_only": True,
            "harness_exists": False,
            "confirmatory_scored_rows": 0,
            "holdout_manifest_sha256": None,
        },
    },
    "decoding": {
        "greedy_temperature": 0,
        "sample_temperature": 0.8,
        "sample_count_k": 5,
        "sample_seeds": [1, 2, 3, 4, 5],
        "top_p": 0.95,
    },
    "statistics": {
        "alpha_confirmatory": 0.05,
        "holm_tests": [
            "embabel_generation_H1",
            "embabel_generation_H2",
            "embabel_repair_H1",
            "embabel_repair_H2",
            "embabel_planning_H1",
            "embabel_planning_H2",
            "embabel_transformation_H1",
            "embabel_transformation_H2",
            "embabel_refactor_H1",
            "embabel_refactor_H2",
            "embabel_integration_H1",
            "embabel_integration_H2",
            "drivine_generation_H1",
            "drivine_generation_H2",
            "drivine_repair_H1",
            "drivine_repair_H2",
            "drivine_query_H1",
            "drivine_query_H2",
            "drivine_graph_rag_H1",
            "drivine_graph_rag_H2",
            "drivine_integration_H1",
            "drivine_integration_H2",
        ],
        "areas": {
            "embabel": ["generation", "repair", "planning", "transformation", "refactor", "integration"],
            "drivine": ["generation", "repair", "query", "graph_rag", "integration"],
        },
        "example_doses": {
            "unit": "compiler_verified_examples_authored_for_one_area",
            "assignment": "authored_for_exactly_one_area",
            "random_pool_rejected": True,
            "nested_within_area": True,
            "within_area_order_seed": 20260227,
            "counts_per_area_locked_before_authoring": True,
            "counts_per_area": None,
        },
        "confirmatory_contrast": "larger_nested_dose_minus_previous_dose_within_area",
        "confirmatory_comparisons": {
            "H1": "area_dose_mid_minus_area_dose_0",
            "H2": "area_dose_full_minus_area_dose_mid",
        },
        "confirmatory_unit": "every_pre_registered_area",
        "increment_decision": "holm_reject_later_dose_beats_previous",
        "release_floor_percentage_points": 5,
        "release_floor_role": "general_coding_drop_limit_not_the_increment_test",
        "slice_holdout_n_for_5_point_step": 742,
        "confidence_bound_above_5_points": "reported_not_required",
        "data_quality": {
            "planned_before_any_model_score": True,
            "example_admission": [
                "slice_label_from_pre_registered_set",
                "compiler_or_executable_oracle",
                "source_file_and_pin_recorded",
                "not_near_duplicate_of_holdout",
                "authored_for_exactly_one_area",
                "dose_membership_by_pre_fixed_within_area_order",
            ],
            "holdout_admission": [
                "slice_label_before_any_model_output",
                "executable_oracle_required",
                "manifest_hash_before_first_score",
                "no_edit_after_first_model_output",
            ],
            "presentation": "every_preregistered_area_and_dose_including_non_improvements",
        },
        "retrieval_role": "exploratory",
        "guide": {
            "when": "after_the_area_adapter_is_trained",
            "what_it_does": "retrieves_pages_into_the_prompt",
            "what_lora_does": "learns_the_admitted_examples",
            "product_config": "D",
            "reference_config_before_training": "B",
            "fills_an_example_dose": False,
        },
        "confirmatory_sidedness": "one_sided_greater",
        "powered_difference_percentage_points": 5,
        "powered_difference_role": "sample_size_assumption_not_a_second_gate",
        "bootstrap_resamples": 10000,
        "bootstrap_seed": 20260227,
        "mcnemar_discordant_proportion_assumed": 0.3,
        "pass_at_k_estimator": "chen2021_unbiased",
        "g_estimand_per_domain": "exploratory",
        "ceiling_contrasts": "exploratory",
        "cross_domain_comparison": "exploratory",
    },
    "contamination": {
        "near_duplicate_jaccard_threshold": 0.8,
        "near_duplicate_method": "minhash_jaccard_normalized_prompt_and_code",
    },
    "freeze": {
        "numbers_freeze_date": "2027-02-27",
        "doi_target_date": "2027-03-31",
    },
    "hypotheses_confirmatory": ["H1", "H2", "H4"],
    "publication_gate_internal_review_required": True,
    "protocol_freeze": {
        "effective_at": "zenodo_upload",
        "zenodo_doi": None,
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_prereg(text: str) -> dict:
    start = text.index(START)
    end = text.index(END)
    block = text[start + len(START) : end]
    fence = "```json"
    opening = block.index(fence) + len(fence)
    closing = block.index("```", opening)
    return json.loads(block[opening:closing])


def page_problems(text: str) -> list[str]:
    problems: list[str] = []
    digest = sha256_bytes(text.encode("utf-8"))
    if digest != EXPECTED_SHA256:
        problems.append(f"preregistration sha256 is {digest}, freeze is {EXPECTED_SHA256}")
    try:
        parsed = extract_prereg(text)
    except (ValueError, json.JSONDecodeError) as exc:
        problems.append(f"normative JSON block unreadable: {exc}")
        return problems
    if parsed != EXPECTED_PREREG:
        problems.append("normative JSON does not match frozen prereg values")
    return problems


def scan_paper_track_forbidden(
    *,
    repo_root: Path | None = None,
    relative_dirs: tuple[str, ...] | None = None,
) -> list[str]:
    """Fail on kiln or jasper in paper-track text artifacts (case-insensitive)."""
    root = repo_root or ROOT
    dirs = relative_dirs or PAPER_TRACK_RELATIVE_DIRS
    problems: list[str] = []
    for rel in dirs:
        base = root / rel
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json", ".csv", ".bib", ".tex"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            lowered = text.lower()
            for token in PAPER_TRACK_FORBIDDEN_SUBSTRINGS:
                if token in lowered:
                    problems.append(
                        f"paper-track file {path.relative_to(root)} "
                        f"mentions forbidden substring {token!r}"
                    )
    return problems


def _one_amendment(extra: str, old_sha: str, new_sha: str) -> list[str]:
    problems: list[str] = []
    headings = [line for line in extra.splitlines() if line == "## Amendment"]
    if len(headings) != 1:
        problems.append("append exactly one ## Amendment section")
        return problems
    if f"old_sha256: {old_sha}" not in extra:
        problems.append("amendment must record the old sha256")
    if f"new_sha256: {new_sha}" not in extra:
        problems.append("amendment must record the new sha256")
    reason = ""
    for line in extra.splitlines():
        if line.startswith("- reason:"):
            reason = line[len("- reason:") :].strip()
    if len(reason) < 80:
        problems.append("amendment reason must be at least 80 characters")
    return problems


def assess_edit(
    base_page: bytes | None,
    head_page: bytes | None,
    base_amend: bytes | None,
    head_amend: bytes | None,
    changed_paths: list[str],
    pr_title: str,
) -> list[str]:
    if not any(path in LOCK_PATHS for path in changed_paths):
        return []
    problems: list[str] = []
    if any(path.startswith(POISON_PREFIXES) for path in changed_paths):
        problems.append("a prereg change also touches holdout tasks or scored runs")
    if base_page is None:
        amend_text = (head_amend or b"").decode("utf-8")
        if any(line == "## Amendment" for line in amend_text.splitlines()):
            problems.append("the initial freeze includes an amendment")
        return problems
    if not (pr_title or "").startswith("amend(prereg):"):
        problems.append("pull request title must start with amend(prereg):")
    if base_amend is None or head_amend is None or not head_amend.startswith(base_amend):
        problems.append("preregistration-amendments.md must keep existing bytes and append")
        return problems
    extra = head_amend[len(base_amend) :].decode("utf-8")
    problems.extend(
        _one_amendment(extra, sha256_bytes(base_page), sha256_bytes(head_page or b""))
    )
    return problems


def check_workspace() -> list[str]:
    if not PAGE_PATH.is_file():
        return ["docs/protocol/preregistration.md is missing"]
    text = PAGE_PATH.read_text(encoding="utf-8")
    problems = page_problems(text)
    if "publication_gate_internal_review_required" not in text:
        problems.append("preregistration must include publication_gate_internal_review_required")
    problems.extend(scan_paper_track_forbidden())
    return problems


def self_test() -> int:
    problems = check_workspace()
    mutated = PAGE_PATH.read_text(encoding="utf-8").replace('"holdout_min_tasks": 742', '"holdout_min_tasks": 50', 1)
    if not page_problems(mutated):
        problems.append("quiet edit of holdout_min_tasks was accepted")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        planted = root / "experiments" / "paper-v1" / "evil.md"
        planted.parent.mkdir(parents=True)
        planted.write_text("kiln", encoding="utf-8")
        if not scan_paper_track_forbidden(repo_root=root, relative_dirs=("experiments/paper-v1",)):
            problems.append("paper-track kiln guard accepted a planted mention")
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print("prereg holds")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    problems = check_workspace()
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print("prereg holds")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))