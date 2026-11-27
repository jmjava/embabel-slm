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

EXPECTED_SHA256 = "3a298f7fc38d240d83d3236bea312bac12336fcfd921fcb54a27c8097c7c1d94"

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

EXPECTED_PREREG = {'frozen_on': '2026-11-25',
 'study_id': 'two-domain-example-dose-v1',
 'inference_backend': 'ollama',
 'inference_host_class': 'halo-395',
 'quant_default': 'Q4_K_M',
 'quant_sensitivity_row': 'Q8_0',
 'quant_sensitivity_applies': 'shareable_base_config_A_only',
 'num_ctx': 8192,
 'arms': {'S': {'parameter_billions_min': 7,
                'parameter_billions_max': 14,
                'peak_memory_gb_max_q4_k_m': 16,
                'configs': ['A', 'B', 'C', 'D']},
          'M': {'parameter_billions_min': 24, 'parameter_billions_max': 34, 'configs': ['A', 'B']},
          'L': {'dense_max_billion_parameters': 70, 'moe_max_billion_parameters_total': 120, 'configs': ['A', 'B']}},
 'configs': {'A': {'retrieval': False, 'lora': False},
             'B': {'retrieval': True, 'lora': False},
             'C': {'retrieval': False, 'lora': True},
             'D': {'retrieval': True, 'lora': True}},
 'lora_per_domain': False,
 'selection_rules': {'metric': 'full_task_success',
                     'tie_break': 'smaller_peak_memory_gb',
                     'split_for_selection': 'dev',
                     'config_for_selection': 'A',
                     'selection_domain': 'embabel'},
 'splits': {'confirmatory_split': 'holdout',
            'dev_allows_tuning': True,
            'model_selection_domain': 'embabel',
            'holdout_min_tasks': 742,
            'holdout_min_tasks_scope': 'combined',
            'holdout_domain_tasks': {'embabel': 371, 'drivine': 371},
            'holdout_tasks_independently_authored_executable_benchmark': True,
            'holdout_area_counts_weighted_from_clean_admitted_training_shares': True,
            'holdout_does_not_consume_or_cap_training_supply': True,
            'min_clean_admitted_training_examples': 14000,
            'holdout_area_allocation': {'minimum_tasks_per_registered_area_per_domain': 10,
                                        'remainder_method': 'hamilton_largest_remainder_on_clean_admitted_pool_shares',
                                        'area_slices_exploratory_not_powered': True,
                                        'exact_counts_frozen_before_holdout_authoring': True},
            'embabel': {'part': 'B', 'pilot_task_ids': 'E01-E20,KB01', 'holdout_categories': 6, 'holdout_tasks': 371},
            'drivine': {'part': 'C',
                        'corpus_repo': 'jmjava/drivine-slm',
                        'dev_training_file': 'data/drivine_instruct.json',
                        'dev_training_pairs_count': 100,
                        'dev_excluded_from_holdout': True,
                        'pilot_executable_min_tasks': 20,
                        'holdout_category_labels': ['generation', 'repair', 'query', 'graph_rag', 'integration'],
                        'primary_executable_only': True,
                        'pilot_harness_exists': True,
                        'confirmatory_harness_complete': False,
                        'confirmatory_package_oracle_complete': False,
                        'confirmatory_scored_rows': 0,
                        'holdout_manifest_sha256': None,
                        'holdout_tasks': 371}},
 'training_formatter_version': 'embabel-slm-code-sft-v1',
 'training_formatter_role': 'code_only_prompt_exact_admitted_code_response_no_prose',
 'selected_tokenizer_token_counts_blocker': True,
 'decoding': {'greedy_temperature': 0,
              'sample_temperature': 0.8,
              'sample_count_k': 5,
              'sample_seeds': [1, 2, 3, 4, 5],
              'top_p': 0.95},
 'statistics': {'alpha_confirmatory': 0.05,
                'exploratory_adjacent_contrasts': ['prefix_1000_minus_500',
                                                   'prefix_2000_minus_1000',
                                                   'prefix_4000_minus_2000',
                                                   'prefix_8000_minus_4000',
                                                   'prefix_14000_minus_8000'],
                'exploratory_holm_adjustment': 'optional_descriptive_not_confirmatory_fwer',
                'areas': {'embabel': ['generation', 'repair', 'planning', 'transformation', 'refactor', 'integration'],
                          'drivine': ['generation', 'repair', 'query', 'graph_rag', 'integration']},
                'example_doses': {'unit': 'admitted_example_on_one_ordered_list',
                                  'assignment': 'authored_for_exactly_one_area',
                                  'random_pool_rejected': True,
                                  'nested_prefixes': True,
                                  'order_seed': 20260227,
                                  'starts': [500, 1000, 2000],
                                  'multipliers': [1, 2, 4, 8],
                                  'prefixes': [500, 1000, 2000, 4000, 8000, 14000],
                                  'mix': 'admitted_pool_shares',
                                  'area_exhaustion_redistribution': 'largest_remainder_among_non_exhausted_by_remaining_eligible_supply',
                                  'record_expected_and_realized_shares_at_every_prefix': True,
                                  'never_duplicate_or_pad_exhausted_area': True,
                                  'equal_area_weights': False,
                                  'grain': 'method',
                                  'counts_locked_before_authoring': True},
                'confirmatory_contrast': 'prefix_14000_minus_prefix_500_on_combined_holdout',
                'confirmatory_comparisons': {'prefix_14000_minus_500': 'prefix_14000_minus_prefix_500'},
                'confirmatory_unit': 'combined_holdout',
                'increment_decision': 'one_sided_mcnemar_reject_14000_beats_500',
                'training_seeds_matched_count': 3,
                'training_seed_identities': [20260227, 20260228, 20260229],
                'training_seed_identities_frozen_across_prefixes': True,
                'primary_confirmatory_training_seed': 20260227,
                'mandatory_replication_training_seeds': [20260228, 20260229],
                'replication_results_do_not_replace_primary_decision': True,
                'pooled_task_by_training_seed_summaries_exploratory_only': True,
                'training_compute_budget': 'identical_non_padding_target_token_budget_effective_batch_token_budget_and_optimizer_update_count_at_every_prefix',
                'training_hyperparameters_frozen_before_training': ['base_model_tag_and_hash',
                                                                    'tokenizer',
                                                                    'sequence_length_and_truncation',
                                                                    'batch_and_gradient_accumulation',
                                                                    'optimizer',
                                                                    'learning_rate_and_schedule',
                                                                    'warmup',
                                                                    'lora_target_modules_rank_alpha_dropout',
                                                                    'precision',
                                                                    'non_padding_target_token_budget',
                                                                    'effective_batch_token_budget',
                                                                    'optimizer_update_count',
                                                                    'dataset_shuffle_sampler_algorithm_and_seed_per_training_seed',
                                                                    'packing_policy',
                                                                    'truncation',
                                                                    'padding_and_loss_masking',
                                                                    'deterministic_kernel_settings_or_documented_nondeterminism',
                                                                    'framework_library_and_driver_versions',
                                                                    'checkpoint_selection',
                                                                    'primary_and_replication_seed_roles'],
                'training_hyperparameter_values_populated': False,
                'training_estimand_note': 'smaller_prefixes_repeat_admitted_examples_more_often_within_fixed_token_and_update_budgets',
                'corpus_audit_raw_candidates': 53676,
                'labeled_units_current_count': 16211,
                'labeled_units_routed_to_review': 34247,
                'exact_duplicate_candidates_removed': 4315,
                'exact_duplicate_candidate_groups': 3543,
                'conflicting_label_exact_duplicate_groups': 996,
                'conflicting_label_review_rows': 2093,
                'clean_admitted_examples_2026_11_27': 15014,
                'clean_admitted_surplus_above_14000_prefix': 1014,
                'maximum_prefix_reduced_from_16000_to_14000': True,
                'labeled_units_intermediate_counts_historical_note': '19_392_and_17_212_were_intermediate_noncanonical_audit_counts',
                'confirmatory_mcnemar_training_seed': 20260227,
                'confirmatory_claim_conditional_on_primary_seed_model_recipe_benchmark': True,
                'labeled_units_are_not_clean_until_admission': True,
                'feasibility_not_established_until_admission_and_independent_holdout_seal': True,
                'feasibility_recompute_after': ['executable_oracle_admission',
                                                'provenance_clustering',
                                                'near_duplicate_filtering',
                                                'independent_holdout_authoring_and_validation'],
                'maximum_prefix_reduced_if_clean_admitted_below_14000': True,
                'sampled_secondary_validation': {'implemented': True,
                                                   'samples_jsonl_seeds_1_through_5_per_task_prefix_and_training_seed_when_present': True,
                                                   'samples_jsonl_seal_bound': True,
                                                   'pass_at_1_k_1_bootstrap_ci': True,
                                                   'pass_at_5_k_5_bootstrap_ci': True,
                                                   'never_changes_primary_decision': True},
                'preregistration_blockers': ['real_oracle_evidence_admission',
                                             'clean_unit_feasibility_recount',
                                             'exact_integer_area_holdout_counts_and_source_counts',
                                             '742_authored_sealed_holdout_tasks',
                                             'official_s_m_l_shortlist_tags_and_digests',
                                             'selected_tokenizer_token_counts',
                                             'training_hyperparameter_values',
                                             'drivine_confirmatory_package_oracles_and_pilot_task_set',
                                             'holdout_manifest_sha256',
                                             'scored_confirmatory_runs',
                                             'zenodo_doi'],
                'provenance_group_splitting': {'required': True,
                                               'groups': ['file', 'fixture', 'class', 'semantic_family_as_appropriate'],
                                               'scope_note': 'not_whole_repository',
                                               'rule': 'no_provenance_group_may_span_training_and_holdout'},
                'power_planning_exact_unconditional_at_n_742': 0.783839,
                'power_planning_exact_n_for_0_80_unconditional': 776,
                'power_planning_normal_approximation_at_n_742': 0.8,
                'power_planning_headline_exact_unconditional_rounded': 0.78,
                'release_floor_percentage_points': 5,
                'release_floor_role': 'general_coding_drop_limit_not_the_increment_test',
                'slice_holdout_n_for_5_point_step': 742,
                'confidence_bound_above_5_points': 'reported_not_required',
                'data_quality': {'planned_before_any_model_score': True,
                                 'example_admission': ['slice_label_from_pre_registered_set',
                                                       'compiler_or_executable_oracle',
                                                       'evidence_joined_to_exact_code_hashes_repo_pin_canonical_argv_hash_success_exit_and_output_artifact_hashes',
                                                       'source_file_and_pin_recorded',
                                                       'not_near_duplicate_of_holdout',
                                                       'authored_for_exactly_one_area',
                                                       'dose_membership_by_pre_fixed_prefix_order'],
                                 'holdout_admission': ['independently_authored_executable_tasks_not_subtracted_from_training_supply',
                                                       'slice_label_before_any_model_output',
                                                       'executable_oracle_required',
                                                       'manifest_hash_before_first_score',
                                                       'no_edit_after_first_model_output'],
                                 'presentation': 'every_prefix_step_including_non_improvements'},
                'retrieval_role': 'exploratory',
                'guide': {'when': 'after_the_adapter_is_trained',
                          'what_it_does': 'retrieves_pages_into_the_prompt',
                          'what_lora_does': 'learns_the_admitted_examples',
                          'product_config': 'D',
                          'reference_config_before_training': 'B',
                          'fills_an_example_dose': False},
                'confirmatory_sidedness': 'one_sided_greater',
                'powered_difference_percentage_points': 5,
                'powered_difference_role': 'sample_size_assumption_not_a_second_gate',
                'bootstrap_resamples': 10000,
                'bootstrap_seed': 20260227,
                'mcnemar_discordant_proportion_assumed': 0.3,
                'pass_at_k_estimator': 'chen2021_unbiased',
                'g_estimand_per_domain': 'exploratory',
                'ceiling_contrasts': 'exploratory',
                'cross_domain_comparison': 'exploratory'},
 'contamination': {'near_duplicate_jaccard_threshold': 0.8,
                   'near_duplicate_method': 'minhash_jaccard_normalized_prompt_and_code',
                   'minhash_shingle_size_tokens': 5,
                   'minhash_num_perm': 128,
                   'minhash_lsh_bands': 32,
                   'minhash_lsh_rows_per_band': 4,
                   'minhash_permutation_seed': 'embabel-slm-minhash-v1',
                   'minhash_exhaustive_pairwise_default': False,
                   'minhash_lsh_approx_candidate_recall_at_jaccard_threshold_note': 'high_probabilistic_recall_not_exhaustive_unless_exhaustive_pairwise_mode'},
 'freeze': {'numbers_freeze_date': '2027-02-27', 'doi_target_date': '2027-03-31'},
 'hypotheses_confirmatory': ['prefix_14000_minus_500', 'H4'],
 'publication_gate_internal_review_required': True,
 'protocol_freeze': {'effective_at': 'zenodo_upload', 'zenodo_doi': None},
 'analysis_production_path': {'mandatory_seal_command': 'python3 -m analysis seal-study',
                              'build_prefixes_requires_admission_receipt': True,
                              'study_results_requires_sealed_manifest': True,
                              'jsonl_physical_line_handles_u2028_u2029': True,
                              'scoring_bound_to_sealed_task_ids_domain_and_area': True,
                              'real_oracle_runs_still_absent': True}}



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