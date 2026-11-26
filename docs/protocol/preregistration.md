# Pre-registration: two-domain gap-closure study (Embabel and Drivine holdouts)

Registered-report style protocol for the confirmatory comparison between shareable local models (arm S), optional middle reference models (arm M), and a Halo-fitting ceiling model (arm L) on **two domains**: Embabel (Part B) and Drivine (Part C). Arms, configs on S, quantization, `num_ctx`, decoding, and model **selection** are shared; each domain has its own holdout, paired tests, gap-closure estimand \(G\), and domain-specific LoRA adapter. Inference for every scored row uses **Ollama** on `host_class=halo-395`. This document is the normative protocol; [analysis-plan.md](analysis-plan.md) gives estimators and tests. Machine-checkable parameters sit in the JSON block below.

**Publication gate (operator checklist):** No Zenodo upload until the operator's internal publication-review checklist is complete.

**Protocol freeze:** This text is normative in-repo as of `frozen_on` below. The registered freeze takes effect at **Zenodo upload** of this pre-registration; record the Zenodo DOI in a later `amend(prereg):` entry (not before upload).

---

## Title

How much of the accuracy gap between a shareable local coding model and the best model that fits the paper host can domain retrieval plus a small per-domain adapter close on Embabel and Drivine holdouts?

---

## Research question

On sealed domain holdouts (Embabel ≥200 tasks across six categories; Drivine ≥100 executable tasks across generation, repair, query, graph-RAG, and integration), how much of the full-task-success gap between (a) the selected shareable 7–14B base under config A and (b) the selected ceiling model under config A is closed by the shareable stack at config D (retrieval + domain LoRA), relative to the ceiling at config A—**reported separately per domain**?

Model tags for S, M, and L are chosen **only** on the Embabel DEV split. Drivine uses those same tags; Drivine outcomes do not re-pick the base, middle, or ceiling.

---

## Hypotheses (confirmatory)

| ID | Domain | Statement | Test |
| --- | --- | --- | --- |
| H1 | Embabel | Ceiling exists: L-A > S-A | Two-sided McNemar on greedy paired outcomes |
| H2 | Embabel | Gap closure / NI: S-D non-inferior to L-A, margin **10** pp | One-sided 95% lower bound: (S-D − L-A) > −10 |
| H3 | Embabel | Fair comparison: S-D vs L-B | Two-sided paired comparison; CI on difference |
| H1 | Drivine | Ceiling exists: L-A > S-A | Two-sided McNemar on Drivine paired outcomes |
| H2 | Drivine | Gap closure / NI: S-D non-inferior to L-A, margin **15** pp | One-sided 95% lower bound: (S-D − L-A) > −15 |
| H3 | Drivine | Fair comparison: S-D vs L-B | Two-sided paired comparison; CI on difference |
| H4 | Both | General floor: S-D holds the M0 general-coding floor vs S-A | Per m0-bars rules; **one** confirmatory gate, not per-domain |

**Headline estimand (per domain):** gap closure \(G = (S\text{-}D - S\text{-}A) / (L\text{-}A - S\text{-}A)\) with cluster-bootstrap 95% CI. If the bootstrap CI for \((L\text{-}A - S\text{-}A)\) includes 0, \(G\) is **undefined** and reported as such. Comparing Embabel \(G\) vs Drivine \(G\) is **exploratory** only.

**Multiplicity:** Holm–Bonferroni on McNemar-related confirmatory tests for `embabel_H1`–`embabel_H3` and `drivine_H1`–`drivine_H3` (six tests). H4 is outside that family.

Exploratory: size curve across S/M/L; RAG effect (A vs B) per arm and domain; quantization effect (Q4_K_M vs one Q8_0 row on shareable base); cross-domain \(G\) comparison.

---

## Design

### Arms and configs (shared across domains)

| Arm | Size band | Configs | Release / train |
| --- | --- | --- | --- |
| S (shareable) | Official 7–14B; peak memory ≤16 GB at Q4_K_M, 8192 ctx (measured) | A, B, C, D | Release base only from this band |
| M (middle) | One or two official 24–34B tags | A, B | Reference only; never release base; never trained |
| L (ceiling) | Largest official tag fitting Halo (dense ≤70B or MoE ≤120B total) | A, B | Reference only; never release base; never trained |

**Quantization:** Q4_K_M for every arm and config. One additional **Q8_0** row for the selected shareable base (config A only) to measure quantization effect.

**A/B/C/D** (arm S): A = base; B = +retrieval; C = +LoRA; D = +retrieval+LoRA. **LoRA is per domain:** the Embabel adapter trains only on Embabel material disjoint from the Embabel holdout; the Drivine adapter trains only on Drivine material disjoint from the Drivine holdout. Configs C and D **never** share one adapter across domains.

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
| Holdout | ≥200 tasks, six categories; sealed manifest | Yes — exactly one scored pass per config |

Before Embabel holdout scoring: commit **only** the sha256 of the canonical Embabel holdout task files. Each config is scored once with the frozen [analysis](../../analysis/) scripts. Near-duplicates between training/retrieval data and Embabel holdout are filtered (MinHash/Jaccard on normalized code+prompt; threshold in JSON). Each model's stated training cutoff vs Embabel release dates is recorded; a post-cutoff task subset flag supports contamination sensitivity analysis.

### Part C — Drivine splits

| Split | Use | Confirmatory |
| --- | --- | --- |
| DEV / training | `jmjava/drivine-slm` `data/drivine_instruct.json` (100 pairs); retrieval and **Drivine** adapter tuning | No — not a scored benchmark |
| Pilot | ~20 newly authored **executable** tasks; may be scored before holdout | No |
| Holdout | ≥100 newly authored **executable** tasks; generation, repair, query, graph-RAG, integration | Yes — exactly one scored pass per config |

**Primary Drivine outcome:** `full_task_success` on **executable** tasks only. The Drivine runner extracts code; a task passes only when parse, compile or query-execute against a pinned Drivine, and fixture assertions succeed. Tasks with no executable oracle **cannot** enter the confirmatory holdout. Explanation items are secondary (written rubric, two blinded raters, Cohen's κ); they are **not** in the primary denominator.

The 100 instruction pairs in `drivine_instruct.json` are excluded from the Drivine holdout by the same near-duplicate rule as Embabel. **No Drivine scored confirmatory row exists yet**; the Drivine harness does not exist at protocol freeze.

Before Drivine holdout scoring: commit the holdout manifest hash. Record **drivine.org** doc pin and **Drivine package** pin in run meta when the harness is built; training-cutoff vs those dates is recorded like Embabel.

### Confounds held fixed

Same system prompt and task prompts per domain, `num_ctx=8192`, greedy and sampled decoding parameters, same top-k for B/D within each domain's retrieval pack, same runner class per domain, domain pins (Embabel commit; Drivine doc + package), Ollama version recorded per run.

---

## Outcomes

**Primary (per domain):** `full_task_success` on domain holdout (greedy and pass@1 via Chen et al. unbiased estimator). Drivine primary denominator is executable tasks only.

**Secondary:** domain-specific automated metrics; general-coding floor tasks (H4); accuracy per GB peak memory; tokens/s; latency.

Human-judged explanation items: written rubric, two blinded raters, Cohen's κ reported; not in Drivine primary denominator.

---

## Sample size and power

**Embabel:** holdout ≥200 tasks. McNemar paired binary assumption \(p_d \approx 0.30\). At \(n \approx 230\), detectable marginal \(\delta \approx 0.10\); H2 margin **10** percentage points.

**Drivine:** holdout ≥100 executable tasks. Under the **same** \(p_d \approx 0.30\) and the protocol power function, \(n=100\) supports detectable \(\delta \approx 0.15\), not 0.10. H2 margin for Drivine is therefore **15** percentage points, stated explicitly and not tightened later.

| \(n\) | Detectable \(\delta\) (approx., \(p_d=0.30\)) |
| --- | --- |
| 20 | ~0.35 (pilot only) |
| 100 | ~0.15 |
| 230 | ~0.10 |
| 236 | ~0.10 (n required for δ=0.10) |
| 941 | ~0.05 |

Reproduce tables with `python3 -m analysis power`.

---

## Analysis plan (summary)

Per-task paired design per domain: one greedy run (\(T=0\)) plus \(k\) sampled runs (\(T=0.8\), fixed seeds). Cluster bootstrap (10,000 resamples, fixed seed) for 95% CIs. Exact McNemar on greedy passes. Holm–Bonferroni across six domain-labeled tests. \(G\) reported per domain. Effect sizes with CIs, not p-values alone. Full detail: [analysis-plan.md](analysis-plan.md). Frozen script hash recorded in run manifest at holdout freeze.

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

**Constraints (not findings from the literature).** Shareable arm eligibility (7–14B parameters, peak memory ≤16 GB at Q4_K_M and `num_ctx=8192`) defines who can run the release model; it is not an estimated optimum from any paper. The five-point general-coding floor in `docs/m0-bars.md` is an operational release rule frozen before any scored holdout run; it is not the confirmatory non-inferiority detection threshold (those margins are 10 pp on Embabel and 15 pp on Drivine from the power assumption below). Official S, M, and L shortlist tags are not locked in the JSON yet; the shortlist must be written into this protocol before any Embabel DEV scoring, and selection uses only the pre-registered rule above.

**Pre-registration and timing.** Hypotheses, sample size, and analysis are specified before confirmatory scores (Nosek et al., 2018). The public timestamp is Zenodo upload of this document; that upload has not happened, and no holdout row is scored before it.

**Reproducibility and budget reporting.** We pin model tag, digest, seed, context length, and decoding per run (Pineau et al., 2021). We report the evaluation budget and hyperparameters, not only the best number, including fixed `num_ctx=8192` and fixed decoding (Dodge et al., 2019).

**Quantization.** Q4_K_M is the shared default quantization (Dettmers and Zettlemoyer, 2023, k-bit inference scaling laws). The single Q8_0 row on shareable config A is our pre-registered sensitivity check, not a result from that paper.

**Decoding and pass@1.** Sampled holdout attempts use temperature 0.8 as in Chen et al. (2021) HumanEval sampling; greedy stays at temperature 0. We use Chen et al.’s unbiased pass@k estimator for pass@1. We pre-register \(k=5\) as a compute budget; their estimator is valid for any \(k\), and they drew far more than five samples per task.

**Retrieval and adapters.** Retrieval augmentation follows Lewis et al. (2020). Domain LoRA follows Hu et al. (2022); a run that uses QLoRA also cites Dettmers et al. (2023, QLoRA)—we do not label a LoRA-only run as QLoRA. Config B is measured before any adapter because Ovadia et al. (2024) found RAG outperformed unsupervised fine-tuning for injecting corpus knowledge on factual QA; their tasks were not code and their fine-tune was continued pretraining, not LoRA, so we treat the ordering as supportive precedent, not a direct replication.

**Executable outcomes and controls.** Drivine holdout tasks require executable oracles in the spirit of real-issue benchmarks (Jimenez et al., 2024); we do not use the SWE-bench task set. KB01 is a known-bad negative control after the Defects4J precedent (Just et al., 2014): a skipped or errored check layer is not a pass.

**Repair and cascades.** We pre-register exactly one repair sample and report greedy pass@1 separately from any repair-augmented rate so repair gains cannot hide in a single headline (Olausson et al., 2024). The fast→one repair→strong policy is inspired by LLM cascades (Chen et al., 2024, FrugalGPT); our policy is fixed with no learned quality scorer.

**Paired inference.** Greedy confirmatory tests use exact McNemar on paired pass/fail (Dietterich, 1998; McNemar, 1947). We pre-set \(\alpha=0.05\), name each test, and treat the paired task as the unit (Dror et al., 2018).

**Multiplicity.** Holm’s sequential rejective procedure controls the six confirmatory McNemar-related tests (Holm, 1979).

**Non-inferiority margins.** H2 uses fixed margins of 10 pp (Embabel, \(n \ge 200\)) and 15 pp (Drivine, \(n \ge 100\)) with one-sided bounds against those margins, following non-inferiority reporting practice (Piaggio et al., 2012). \(p_d=0.30\) for McNemar power is a planning assumption, not an estimate from data.

**Bootstrap intervals.** Cluster bootstrap with \(B=10\,000\) resamples over tasks uses percentile intervals (Efron, 1979). \(B=10\,000\) is pre-registered here; resampling is over tasks as the paired unit (Dror et al., 2018; Dietterich, 1998).

**Contamination.** Near-duplicate separation of training or retrieval material from holdout uses MinHash/Jaccard on normalized prompt and code (Lee et al., 2022). The Jaccard threshold 0.8 is pre-registered in this protocol and is not attributed to Lee et al.

---

<!-- prereg:start -->

```json
{
  "frozen_on": "2026-11-25",
  "study_id": "two-domain-gap-closure-v1",
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
  "lora_per_domain": true,
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
    "embabel": {
      "part": "B",
      "pilot_task_ids": "E01-E20,KB01",
      "holdout_min_tasks": 200,
      "holdout_categories": 6
    },
    "drivine": {
      "part": "C",
      "corpus_repo": "jmjava/drivine-slm",
      "dev_training_file": "data/drivine_instruct.json",
      "dev_training_pairs_count": 100,
      "dev_excluded_from_holdout": true,
      "pilot_executable_min_tasks": 20,
      "holdout_min_tasks": 100,
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
      "embabel_H1",
      "embabel_H2",
      "embabel_H3",
      "drivine_H1",
      "drivine_H2",
      "drivine_H3"
    ],
    "h2_margin_percentage_points": {
      "embabel": 10,
      "drivine": 15
    },
    "h2_sidedness": "one_sided_lower",
    "bootstrap_resamples": 10000,
    "bootstrap_seed": 20260227,
    "mcnemar_discordant_proportion_assumed": 0.3,
    "pass_at_k_estimator": "chen2021_unbiased",
    "g_estimand_per_domain": true,
    "cross_domain_g_comparison": "exploratory"
  },
  "contamination": {
    "near_duplicate_jaccard_threshold": 0.8,
    "near_duplicate_method": "minhash_jaccard_normalized_prompt_and_code"
  },
  "freeze": {
    "numbers_freeze_date": "2027-02-27",
    "doi_target_date": "2027-03-31"
  },
  "hypotheses_confirmatory": ["H1", "H2", "H3", "H4"],
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