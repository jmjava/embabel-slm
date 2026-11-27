# Pre-registration: example dose and practical gain (Embabel and Drivine holdouts)

Registered-report style protocol for one combined holdout on **two domains**: Embabel (Part B) and Drivine (Part C). Admitted examples keep one pre-registered area label and are placed on one ordered list. Every training size is a prefix of that list. The same 742 tasks are scored after each prefix. Area labels build the mix. An area breakdown is reported with the result and is not its own 742-task exam. Arms, quantization, `num_ctx`, decoding, and model **selection** are shared. Retrieval and the host-ceiling model are reference measurements, not the dose. Inference for every scored row uses **Ollama** on `host_class=halo-395`. This document is the normative protocol; [analysis-plan.md](analysis-plan.md) gives estimators and tests. The dose ladder is [combined-dose-plan.md](combined-dose-plan.md). Machine-checkable parameters sit in the JSON block below.

**Publication gate (operator checklist):** No Zenodo upload until the operator's internal publication-review checklist is complete.

**Protocol freeze:** This text is normative in-repo as of `frozen_on` below. The registered freeze takes effect at **Zenodo upload** of this pre-registration; record the Zenodo DOI in a later `amend(prereg):` entry (not before upload).

---

## Title

Does a larger nested training set raise the combined holdout score?

---

## Research question

On one sealed holdout of 742 tasks, does each larger prefix of the ordered example list raise full-task success over the previous prefix? Embabel labels are generation, repair, planning, transformation, refactor, and integration. Drivine labels are generation, repair, query, graph-RAG, and integration. The list is drawn in the labeled-pool shares, not in equal area weights. The named prefixes are 500, 1,000, 2,000, 4,000, 8,000, and 16,000. They come from starts of 500, 1,000, and 2,000 at multipliers 1, 2, 4, and 8. A size outside that list is not part of the claim.

Model tags for S, M, and L are chosen **only** on the Embabel DEV split. Drivine uses those same tags; Drivine outcomes do not re-pick the base, middle, or ceiling.

---

## Hypotheses (confirmatory)

| ID | Where | Statement | Test |
| --- | --- | --- | --- |
| prefix_1000_minus_500 | Combined holdout | The 1,000-example prefix beats the 500-example prefix | One-sided exact McNemar |
| prefix_2000_minus_1000 | Combined holdout | The 2,000-example prefix beats the 1,000-example prefix | One-sided exact McNemar |
| prefix_4000_minus_2000 | Combined holdout | The 4,000-example prefix beats the 2,000-example prefix | One-sided exact McNemar |
| prefix_8000_minus_4000 | Combined holdout | The 8,000-example prefix beats the 4,000-example prefix | One-sided exact McNemar |
| prefix_16000_minus_8000 | Combined holdout | The 16,000-example prefix beats the 8,000-example prefix | One-sided exact McNemar |
| H4 | Both domains | General floor: the largest prefix holds the M0 general-coding floor versus zero examples | Per m0-bars rules; **one** gate, outside the prefix family |

**Headline estimand (per step):** the paired pass-rate difference on the 742 tasks, this prefix minus the previous prefix, with a cluster-bootstrap 95% CI. A step is proved when its one-sided test rejects after Holm correction across the five prefix steps. The study does not require all five tests to reject. A missed step is reported as not proved. The training example is a method, and the enclosing type signature is its frame.

Each admitted example carries exactly one pre-registered area label. The order is fixed before any score. Each larger prefix contains the smaller one. The mix follows the labeled pool at every prefix.

The 5-point difference in `docs/m0-bars.md` remains the release floor. It is not a second gate on these tests. **742** tasks on the combined holdout is the one-sided sample size for a true 5-point step (\(p_d=0.30\), \(\alpha=0.05\), power 0.80). The confidence interval is reported. It is not required to lie entirely above 5 points.

**What a later dose is not.** The holdout is scored once at these three doses. Adding examples after seeing the scores, then rescoring the same holdout, is not further evidence that more examples help.

**Reference, not confirmatory:** retrieval versus the base; gap closure \(G\) versus the host ceiling (undefined when the ceiling-gap interval includes 0); ceiling contrasts.

**Multiplicity:** Holm–Bonferroni on the five one-sided McNemar tests named in the JSON, one for each successive prefix doubling. H4 is outside that family. A prefix is not added or removed after scores exist.

Exploratory: retrieval; size curve across S/M/L; ceiling contrasts; \(G\); quantization effect (Q4_K_M vs one Q8_0 row at dose 0).

---

## Design

### Arms and configs (shared across domains)

| Arm | Size band | Configs | Release / train |
| --- | --- | --- | --- |
| S (shareable) | Official 7–14B; peak memory ≤16 GB at Q4_K_M, 8192 ctx (measured) | A, B, C, D | Release base only from this band |
| M (middle) | One or two official 24–34B tags | A, B | Reference only; never release base; never trained |
| L (ceiling) | Largest official tag fitting Halo (dense ≤70B or MoE ≤120B total) | A, B | Reference only; never release base; never trained |

**Quantization:** Q4_K_M for every arm and config. One additional **Q8_0** row for the selected shareable base (config A only) to measure quantization effect.

**A/B/C/D** (arm S): A = base; B = guide retrieval on the untrained base; C = LoRA; D = the same guide attached to the already trained model. LoRA learns the admitted examples on the one ordered list: compiler-checked or executable, labeled with one area, and sourced. The guide does not train the model. It retrieves pages into the prompt at answer time, and on the product path it is added only after that adapter exists. Config B is the reference row that scores the guide before training. The guide does not fill a prefix. One adapter trains on the combined list. That list stays disjoint from the 742-task holdout.

### Model selection (pre-declared, Embabel DEV split only)

- **Shareable base (S):** Among official 7–14B shortlist tags that pass the memory tier on Embabel DEV, pick the tag with highest `full_task_success` under config A; ties → smaller measured peak memory.
- **Ceiling (L):** Among pre-listed ceiling shortlist tags that load on Halo under Q4_K_M, pick highest `full_task_success` under config A on Embabel DEV; ties → smaller peak memory.
- **Middle (M):** Operator picks one or two official 24–34B tags from a pre-listed shortlist before Embabel DEV scoring (documented in run meta; not data-driven after holdout).

Drivine confirmatory rows use the same S/M/L tags. Drivine scores do not alter selection.

Pilot results (Embabel E01–E20 + KB01; Drivine pilot executable tasks) **never** support confirmatory claims.

### Part B — Embabel splits

| Split | Use | Confirmatory |
| --- | --- | --- |
| Pilot | E01–E20 + KB01; may become DEV | No |
| DEV | Prompt, retrieval pack, **Embabel** adapter tuning; model shortlist selection | No |
| Holdout | 742 tasks in the combined exam; sealed manifest | Yes — one scored pass per prefix |

Before Embabel holdout scoring: commit **only** the sha256 of the canonical Embabel holdout task files. Each config is scored once with the frozen [analysis](../../analysis/) scripts. Near-duplicates between training/retrieval data and Embabel holdout are filtered (MinHash/Jaccard on normalized code+prompt; threshold in JSON). Each model's stated training cutoff vs Embabel release dates is recorded; a post-cutoff task subset flag supports contamination sensitivity analysis.

### Part C — Drivine splits

| Split | Use | Confirmatory |
| --- | --- | --- |
| DEV / training | `jmjava/drivine-slm` `data/drivine_instruct.json` (100 pairs); retrieval and **Drivine** adapter tuning | No — not a scored benchmark |
| Pilot | ~20 newly authored **executable** tasks; may be scored before holdout | No |
| Holdout | The same 742-task combined exam. Drivine tasks in it are executable | Yes — one scored pass per prefix |

**Primary Drivine outcome:** `full_task_success` on **executable** tasks only. The Drivine runner extracts code; a task passes only when parse, compile or query-execute against a pinned Drivine, and fixture assertions succeed. Tasks with no executable oracle **cannot** enter the confirmatory holdout. Explanation items are secondary (written rubric, two blinded raters, Cohen's κ); they are **not** in the primary denominator.

The 100 instruction pairs in `drivine_instruct.json` are excluded from the Drivine holdout by the same near-duplicate rule as Embabel. **No Drivine scored confirmatory row exists yet**; the Drivine harness does not exist at protocol freeze.

Before Drivine holdout scoring: commit the holdout manifest hash. Record **drivine.org** doc pin and **Drivine package** pin in run meta when the harness is built; training-cutoff vs those dates is recorded like Embabel.

### Confounds held fixed

Same system prompt and task prompts per domain, `num_ctx=8192`, greedy and sampled decoding parameters, same top-k for B/D within each domain's retrieval pack, same runner class per domain, domain pins (Embabel commit; Drivine doc + package), Ollama version recorded per run.

---

## Outcomes

**Primary:** `full_task_success` on the combined holdout (greedy and pass@1 via Chen et al. unbiased estimator). Drivine tasks in that denominator are executable only.

**Secondary:** domain-specific automated metrics; general-coding floor tasks (H4); accuracy per GB peak memory; tokens/s; latency.

Human-judged explanation items: written rubric, two blinded raters, Cohen's κ reported; not in Drivine primary denominator.

---

## Sample size and power

**Combined exam:** holdout = 742 tasks. Drivine tasks in that exam must be executable. The confirmatory tests are one-sided. Under \(p_d \approx 0.30\), \(\alpha=0.05\), and power 0.80, `mcnemar_n_required(0.05, two_sided=False)` is 742 for one 5-point step on this exam. The five prefix steps share that exam. The study does not require all five tests to reject.

| \(n\) | Detectable \(\delta\), one-sided (approx., \(p_d=0.30\)) |
| --- | --- |
| 20 | ~0.31 (pilot only) |
| 100 | ~0.14 |
| 186 | ~0.10 (one-sided n for δ=0.10) |
| 742 | ~0.05 (one-sided n for δ=0.05) |

Reproduce tables with `python3 -m analysis power`.

---

## Analysis plan (summary)

Per-task paired design: one greedy run (\(T=0\)) plus \(k\) sampled runs (\(T=0.8\), fixed seeds). Cluster bootstrap (10,000 resamples, fixed seed) for 95% CIs on each prefix step. One-sided exact McNemar on greedy passes for the five prefix doublings. Holm–Bonferroni across those five tests. Retrieval, \(G\), and ceiling contrasts are exploratory. Effect sizes with CIs, not p-values alone. Full detail: [analysis-plan.md](analysis-plan.md). Frozen script hash recorded in run manifest at holdout freeze.

---

## Exclusion and failure rules

- Transport or runner errors: **one** rerun; if still failing, count as task fail — never drop tasks post hoc.
- Missing completion: fail.
- Config not finished on a domain holdout by numbers freeze: reported as **not run** in Paper v1 (see timeline).

---

## Contamination controls

Near-duplicate filter before training; holdout manifest hash committed pre-scoring per domain; training-cutoff vs task-date flags for sensitivity; `drivine_instruct.json` excluded from Drivine holdout by near-duplicate rule.

---

## Timeline contingency

Paper v1 includes all pre-registered arms/configs on both domains where run. **Numbers freeze:** Fri 27 Feb 2027. **DOI target:** 31 Mar 2027. Any config not scored on a domain holdout by freeze → **not run**; no post-freeze holdout additions; freeze date does not slip to fit results.

---

## Deviations policy

Any deviation from this protocol is logged in [deviations-log.md](deviations-log.md) with date and reason — never silently.

---

## Inference backend

**Only Ollama** on `host_class=halo-395` produces rows used in confirmatory tables. Downstairs fallback may run diagnostics but is not averaged with Halo rows.

---

## Grounding

Confirmatory design choices below are grounded in cited prior work. Scope limits and deviations are stated when our setting differs.

**Constraints (not findings from the literature).** Shareable arm eligibility (7–14B parameters, peak memory ≤16 GB at Q4_K_M and `num_ctx=8192`) defines who can run the release model; it is not an estimated optimum from any paper. The five-point difference in `docs/m0-bars.md` is the release floor: a full dose that drops more than 5 points on general coding fails. It is not the test that a dose step improved. The holdout minimum of 742 tasks is the one-sided sample size for a 5-point difference on the combined exam. It is not an estimated optimum. Official S, M, and L shortlist tags are not locked in the JSON yet; the shortlist must be written into this protocol before any Embabel DEV scoring, and selection uses only the pre-registered rule above.

**Pre-registration and timing.** Hypotheses, sample size, and analysis are specified before confirmatory scores (Nosek et al., 2018). The public timestamp is Zenodo upload of this document; that upload has not happened, and no holdout row is scored before it.

**Reproducibility and budget reporting.** We pin model tag, digest, seed, context length, and decoding per run (Pineau et al., 2021). We report the evaluation budget and hyperparameters, not only the best number, including fixed `num_ctx=8192` and fixed decoding (Dodge et al., 2019).

**Quantization.** Q4_K_M is the shared default quantization (Dettmers and Zettlemoyer, 2023, k-bit inference scaling laws). The single Q8_0 row on shareable config A is our pre-registered sensitivity check, not a result from that paper.

**Decoding and pass@1.** Sampled holdout attempts use temperature 0.8 as in Chen et al. (2021) HumanEval sampling; greedy stays at temperature 0. We use Chen et al.’s unbiased pass@k estimator for pass@1. We pre-register \(k=5\) as a compute budget; their estimator is valid for any \(k\), and they drew far more than five samples per task.

**Retrieval and adapters.** Retrieval augmentation follows Lewis et al. (2020). Domain LoRA follows Hu et al. (2022); a run that uses QLoRA also cites Dettmers et al. (2023, QLoRA)—we do not label a LoRA-only run as QLoRA. LoRA is the training step: it learns the admitted examples. The guide is an add-on after that training: config D attaches retrieval to the already trained model. Config B is still measured on the untrained base first, because Ovadia et al. (2024) found RAG outperformed unsupervised fine-tuning for injecting corpus knowledge on factual QA; their tasks were not code and their fine-tune was continued pretraining, not LoRA, so that measurement order is supportive precedent, not a replication. The product use of the guide remains the add-on on the trained model.

**Executable outcomes and controls.** Drivine holdout tasks require executable oracles in the spirit of real-issue benchmarks (Jimenez et al., 2024); we do not use the SWE-bench task set. KB01 is a known-bad negative control after the Defects4J precedent (Just et al., 2014): a skipped or errored check layer is not a pass.

**Repair and cascades.** We pre-register exactly one repair sample and report greedy pass@1 separately from any repair-augmented rate so repair gains cannot hide in a single headline (Olausson et al., 2024). The fast→one repair→strong policy is inspired by LLM cascades (Chen et al., 2024, FrugalGPT); our policy is fixed with no learned quality scorer.

**Paired inference.** Greedy confirmatory tests use exact McNemar on paired pass/fail (Dietterich, 1998; McNemar, 1947). We pre-set \(\alpha=0.05\), name each test, and treat the paired task as the unit (Dror et al., 2018).

**Multiplicity.** Holm’s sequential rejective procedure controls the five confirmatory prefix tests (Holm, 1979).

**Example doses.** The five confirmatory tests are one-sided exact McNemar tests on the combined holdout: each larger prefix passes more of the same 742 tasks than the previous prefix (McNemar, 1947; Dietterich, 1998). The prefixes and the three starting values are written into this protocol before any example is authored (Dror et al., 2018). They are not taken from a data-scaling paper. A checked citation for score versus number of training examples is still required before Zenodo. \(p_d=0.30\) for McNemar power is a planning assumption, not an estimate from data. Ceiling comparisons are not non-inferiority tests. Piaggio et al. (2012) would apply only if a later amendment made a ceiling margin confirmatory.

**Bootstrap intervals.** Cluster bootstrap with \(B=10\,000\) resamples over tasks uses percentile intervals (Efron, 1979). \(B=10\,000\) is pre-registered here; resampling is over tasks as the paired unit (Dror et al., 2018; Dietterich, 1998).

**Contamination.** Near-duplicate separation of training or retrieval material from holdout uses MinHash/Jaccard on normalized prompt and code (Lee et al., 2022). The Jaccard threshold 0.8 is pre-registered in this protocol and is not attributed to Lee et al.

**Data quality, planned before any score.** An example or a holdout task is admitted only by rules written before any model score is used to keep it, drop it, or choose its area. The area label is one of the pre-registered labels. The example is written for that area. A random or off-area item does not fill the dose. Within an area, dose membership follows the pre-fixed order. A holdout task needs an executable oracle for that same area, and its wording is not edited after the first model output. Every pre-registered area and dose is reported, including areas that do not improve (Dodge et al., 2019; Nosek et al., 2018). An area or an example set chosen after scores is not the result that is presented.

---

<!-- prereg:start -->

```json
{
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
      "configs": ["A", "B", "C", "D"]
    },
    "M": {
      "parameter_billions_min": 24,
      "parameter_billions_max": 34,
      "configs": ["A", "B"]
    },
    "L": {
      "dense_max_billion_parameters": 70,
      "moe_max_billion_parameters_total": 120,
      "configs": ["A", "B"]
    }
  },
  "configs": {
    "A": {"retrieval": false, "lora": false},
    "B": {"retrieval": true, "lora": false},
    "C": {"retrieval": false, "lora": true},
    "D": {"retrieval": true, "lora": true}
  },
  "lora_per_domain": false,
  "selection_rules": {
    "metric": "full_task_success",
    "tie_break": "smaller_peak_memory_gb",
    "split_for_selection": "dev",
    "config_for_selection": "A",
    "selection_domain": "embabel"
  },
  "splits": {
    "confirmatory_split": "holdout",
    "dev_allows_tuning": true,
    "model_selection_domain": "embabel",
    "holdout_min_tasks": 742,
    "holdout_min_tasks_scope": "combined",
    "embabel": {
      "part": "B",
      "pilot_task_ids": "E01-E20,KB01",
      "holdout_categories": 6
    },
    "drivine": {
      "part": "C",
      "corpus_repo": "jmjava/drivine-slm",
      "dev_training_file": "data/drivine_instruct.json",
      "dev_training_pairs_count": 100,
      "dev_excluded_from_holdout": true,
      "pilot_executable_min_tasks": 20,
      "holdout_category_labels": [
        "generation",
        "repair",
        "query",
        "graph_rag",
        "integration"
      ],
      "primary_executable_only": true,
      "harness_exists": false,
      "confirmatory_scored_rows": 0,
      "holdout_manifest_sha256": null
    }
  },
  "decoding": {
    "greedy_temperature": 0,
    "sample_temperature": 0.8,
    "sample_count_k": 5,
    "sample_seeds": [1, 2, 3, 4, 5],
    "top_p": 0.95
  },
  "statistics": {
    "alpha_confirmatory": 0.05,
    "holm_tests": [
      "prefix_1000_minus_500",
      "prefix_2000_minus_1000",
      "prefix_4000_minus_2000",
      "prefix_8000_minus_4000",
      "prefix_16000_minus_8000"
    ],
    "areas": {
      "embabel": ["generation", "repair", "planning", "transformation", "refactor", "integration"],
      "drivine": ["generation", "repair", "query", "graph_rag", "integration"]
    },
    "example_doses": {
      "unit": "admitted_example_on_one_ordered_list",
      "assignment": "authored_for_exactly_one_area",
      "random_pool_rejected": true,
      "nested_prefixes": true,
      "order_seed": 20260227,
      "starts": [500, 1000, 2000],
      "multipliers": [1, 2, 4, 8],
      "prefixes": [500, 1000, 2000, 4000, 8000, 16000],
      "mix": "labeled_pool_shares",
      "equal_area_weights": false,
      "grain": "method",
      "counts_locked_before_authoring": true
    },
    "confirmatory_contrast": "later_prefix_minus_previous_prefix_on_combined_holdout",
    "confirmatory_comparisons": {
      "prefix_1000_minus_500": "prefix_1000_minus_prefix_500",
      "prefix_2000_minus_1000": "prefix_2000_minus_prefix_1000",
      "prefix_4000_minus_2000": "prefix_4000_minus_prefix_2000",
      "prefix_8000_minus_4000": "prefix_8000_minus_prefix_4000",
      "prefix_16000_minus_8000": "prefix_16000_minus_prefix_8000"
    },
    "confirmatory_unit": "combined_holdout",
    "increment_decision": "holm_reject_later_dose_beats_previous",
    "release_floor_percentage_points": 5,
    "release_floor_role": "general_coding_drop_limit_not_the_increment_test",
    "slice_holdout_n_for_5_point_step": 742,
    "confidence_bound_above_5_points": "reported_not_required",
    "data_quality": {
      "planned_before_any_model_score": true,
      "example_admission": [
        "slice_label_from_pre_registered_set",
        "compiler_or_executable_oracle",
        "source_file_and_pin_recorded",
        "not_near_duplicate_of_holdout",
        "authored_for_exactly_one_area",
        "dose_membership_by_pre_fixed_prefix_order"
      ],
      "holdout_admission": [
        "slice_label_before_any_model_output",
        "executable_oracle_required",
        "manifest_hash_before_first_score",
        "no_edit_after_first_model_output"
      ],
      "presentation": "every_prefix_step_including_non_improvements"
    },
    "retrieval_role": "exploratory",
    "guide": {
      "when": "after_the_adapter_is_trained",
      "what_it_does": "retrieves_pages_into_the_prompt",
      "what_lora_does": "learns_the_admitted_examples",
      "product_config": "D",
      "reference_config_before_training": "B",
      "fills_an_example_dose": false
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
    "cross_domain_comparison": "exploratory"
  },
  "contamination": {
    "near_duplicate_jaccard_threshold": 0.8,
    "near_duplicate_method": "minhash_jaccard_normalized_prompt_and_code"
  },
  "freeze": {
    "numbers_freeze_date": "2027-02-27",
    "doi_target_date": "2027-03-31"
  },
  "hypotheses_confirmatory": [
    "prefix_1000_minus_500",
    "prefix_2000_minus_1000",
    "prefix_4000_minus_2000",
    "prefix_8000_minus_4000",
    "prefix_16000_minus_8000",
    "H4"
  ],
  "publication_gate_internal_review_required": true,
  "protocol_freeze": {
    "effective_at": "zenodo_upload",
    "zenodo_doi": null
  }
}
```

<!-- prereg:end -->

## How a later change is allowed

`scripts/check_prereg.py` hashes this file. A pull request that edits this file, that script, or `.github/workflows/prereg.yml` passes only when:

- The pull request title starts with `amend(prereg):`.
- `docs/protocol/preregistration-amendments.md` keeps every earlier byte and appends one amendment with old sha256, new sha256, and reason (≥80 characters).
- Experiment runs, scores, and holdout task files stay untouched in the same pull request.

The first Zenodo upload of this page is the registered freeze (record the DOI via amendment). In-repo edits before that upload are pre-freeze corrections and are not amendments. After upload, only `amend(prereg):` changes are allowed.