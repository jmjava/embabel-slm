# Pre-registration: two-arm gap-closure study (Embabel holdout)

Registered-report style protocol for the confirmatory comparison between shareable local models (arm S), optional middle reference models (arm M), and a Halo-fitting ceiling model (arm L). Inference for every scored row uses **Ollama** on `host_class=halo-395`. This document is the normative protocol; [analysis-plan.md](analysis-plan.md) gives estimators and tests. Machine-checkable parameters sit in the JSON block below.

**Publication gate (operator checklist before any Zenodo upload of pre-registration, preprint, or artifact derived from this track):** No Zenodo upload (pre-registration, preprint, or artifact) may include Kiln / slm-kiln content without Jasper's written review.

---

## Title

How much of the accuracy gap between a shareable local coding model and the best model that fits the paper host can Embabel retrieval plus a small adapter close?

---

## Research question

On a sealed Embabel holdout (≥200 tasks, six categories), how much of the full-task-success gap between (a) the selected shareable 7–14B base under config A and (b) the selected ceiling model under config A is closed by the shareable stack at config D (retrieval + LoRA), relative to the ceiling at config A?

---

## Hypotheses (confirmatory)

| ID | Statement | Test |
| --- | --- | --- |
| H1 | A ceiling exists: L-A full-task-success > S-A | Two-sided McNemar on greedy paired outcomes; Holm-adjusted |
| H2 | Gap closure / non-inferiority: S-D is non-inferior to L-A with margin 10 percentage points | One-sided 95% lower bound: (S-D − L-A) > −10 |
| H3 | Fair comparison: S-D vs L-B | Two-sided paired comparison; CI on difference |
| H4 | General floor: S-D holds the M0 general-coding floor vs S-A | Per m0-bars rules; confirmatory gate for release claims |

**Headline estimand:** gap closure \(G = (S\text{-}D - S\text{-}A) / (L\text{-}A - S\text{-}A)\) with cluster-bootstrap 95% CI. If the bootstrap CI for \((L\text{-}A - S\text{-}A)\) includes 0, \(G\) is **undefined** and reported as such.

Exploratory: size curve across S/M/L; RAG effect (A vs B) per arm; quantization effect (Q4_K_M vs one Q8_0 row on shareable base).

---

## Design

### Arms and configs

| Arm | Size band | Configs | Release / train |
| --- | --- | --- | --- |
| S (shareable) | Official 7–14B; peak memory ≤16 GB at Q4_K_M, 8192 ctx (measured) | A, B, C, D | Release base only from this band |
| M (middle) | One or two official 24–34B tags | A, B | Reference only; never release base; never trained |
| L (ceiling) | Largest official tag fitting Halo (dense ≤70B or MoE ≤120B total) | A, B | Reference only; never release base; never trained |

**Quantization:** Q4_K_M for every arm and config. One additional **Q8_0** row for the selected shareable base (config A only) to measure quantization effect.

**A/B/C/D** (arm S) matches [research-plan.md](../research-plan.md): A = base; B = +retrieval; C = +LoRA; D = +retrieval+LoRA.

### Model selection (pre-declared, DEV split only)

- **Shareable base (S):** Among official 7–14B shortlist tags that pass the memory tier on DEV, pick the tag with highest `full_task_success` under config A; ties → smaller measured peak memory.
- **Ceiling (L):** Among pre-listed ceiling shortlist tags that load on Halo under Q4_K_M, pick highest `full_task_success` under config A on DEV; ties → smaller peak memory.
- **Middle (M):** Operator picks one or two official 24–34B tags from a pre-listed shortlist before DEV scoring (documented in run meta; not data-driven after holdout).

Pilot results (E01–E20 + KB01) and any DEV tuning **never** support confirmatory claims.

### Splits

| Split | Use | Confirmatory |
| --- | --- | --- |
| Pilot | E01–E20 + KB01; may become DEV | No |
| DEV | Prompt, retrieval pack, adapter tuning; model shortlist selection | No |
| Holdout | ≥200 tasks, six categories; sealed manifest | Yes — exactly one scored pass per config |

Before any holdout scoring: commit **only** the sha256 of the canonical holdout task files (manifest hash). Each config on holdout is scored once with the frozen [analysis](../../analysis/) scripts. Near-duplicates between training/retrieval data and holdout are filtered (MinHash/Jaccard on normalized code+prompt; threshold in JSON). Each model's stated training cutoff vs Embabel release dates is recorded; a post-cutoff task subset flag supports contamination sensitivity analysis.

### Confounds held fixed

Same system prompt and task prompts, `num_ctx=8192`, greedy and sampled decoding parameters, same retrieval pack and top-k for B/D, same runner and Embabel pin, Ollama version recorded per run.

---

## Outcomes

**Primary:** `full_task_success` on holdout (greedy and pass@1 via Chen et al. unbiased estimator).

**Secondary:** other m0-bars Embabel metrics; general-coding floor tasks; accuracy per GB peak memory; tokens/s; latency.

Human-judged explanation items: written rubric, two blinded raters, Cohen's κ reported.

---

## Sample size and power

Holdout size ≥200 tasks. Power justification uses **paired binary outcomes (McNemar)**. Assumption: discordant-pair proportion \(p_d \approx 0.30\). Approximate sample size \(n \approx (z_{\alpha/2} + z_\beta)^2 p_d / \delta^2\) for a two-sided \(\alpha=0.05\), power 0.80 detectable marginal difference \(\delta\):

| \(n\) | Detectable \(\delta\) (approx.) |
| --- | --- |
| 20 | ~0.35 (pilot only) |
| 100 | ~0.15 |
| 230 | ~0.10 |
| 236 | ~0.10 (n required for δ=0.10) |
| 941 | ~0.05 |

Hence holdout ≥200 supports a 10-point non-inferiority margin (H2); a 5-point detectable difference would require about **940** tasks under the same assumption (not ~600). Reproduce tables with `python3 -m analysis power`.

---

## Analysis plan (summary)

Per-task paired design: one greedy run (\(T=0\)) plus \(k\) sampled runs (\(T=0.2\), fixed seeds). Cluster bootstrap (10,000 resamples, fixed seed) for 95% CIs. Exact McNemar on greedy passes. Holm–Bonferroni across H1–H3. Effect sizes with CIs, not p-values alone. Full detail: [analysis-plan.md](analysis-plan.md). Frozen script hash recorded in run manifest at holdout freeze.

---

## Exclusion and failure rules

- Transport or runner errors: **one** rerun; if still failing, count as task fail — never drop tasks post hoc.
- Missing completion: fail.
- Config not finished on holdout by numbers freeze: reported as **not run** in Paper v1 (see timeline).

---

## Contamination controls

Near-duplicate filter before training; holdout manifest hash committed pre-scoring; training-cutoff vs task-date flags for sensitivity.

---

## Timeline contingency

Paper v1 includes all pre-registered arms/configs. **Numbers freeze:** Fri 27 Feb 2027. **DOI target:** 31 Mar 2027. Any config not scored on holdout by freeze → **not run**; no post-freeze holdout additions; freeze date does not slip to fit results.

---

## Deviations policy

Any deviation from this protocol is logged in [deviations-log.md](deviations-log.md) with date and reason — never silently.

---

## Inference backend

**Only Ollama** on `host_class=halo-395` produces rows used in confirmatory tables. Downstairs fallback may run diagnostics but is not averaged with Halo rows.

---

<!-- prereg:start -->

```json
{
  "frozen_on": "2026-11-25",
  "study_id": "embabel-two-arm-gap-closure-v1",
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
  "splits": {
    "pilot_task_ids": "E01-E20,KB01",
    "dev_allows_tuning": true,
    "holdout_min_tasks": 200,
    "holdout_categories": 6,
    "confirmatory_split": "holdout"
  },
  "decoding": {
    "greedy_temperature": 0,
    "sample_temperature": 0.2,
    "sample_count_k": 5,
    "sample_seeds": [1, 2, 3, 4, 5],
    "top_p": 0.95
  },
  "statistics": {
    "alpha_confirmatory": 0.05,
    "holm_tests": ["H1", "H2", "H3"],
    "h2_margin_percentage_points": 10,
    "h2_sidedness": "one_sided_lower",
    "bootstrap_resamples": 10000,
    "bootstrap_seed": 20260227,
    "mcnemar_discordant_proportion_assumed": 0.3,
    "pass_at_k_estimator": "chen2021_unbiased"
  },
  "contamination": {
    "near_duplicate_jaccard_threshold": 0.8,
    "near_duplicate_method": "minhash_jaccard_normalized_prompt_and_code"
  },
  "selection_rules": {
    "metric": "full_task_success",
    "tie_break": "smaller_peak_memory_gb",
    "split_for_selection": "dev",
    "config_for_selection": "A"
  },
  "freeze": {
    "numbers_freeze_date": "2027-02-27",
    "doi_target_date": "2027-03-31"
  },
  "hypotheses_confirmatory": ["H1", "H2", "H3", "H4"],
  "publication_gate_kiln_review_required": true
}
```

<!-- prereg:end -->

## How a later change is allowed

`scripts/check_prereg.py` hashes this file. A pull request that edits this file, that script, or `.github/workflows/prereg.yml` passes only when:

- The pull request title starts with `amend(prereg):`.
- `docs/protocol/preregistration-amendments.md` keeps every earlier byte and appends one amendment with old sha256, new sha256, and reason (≥80 characters).
- Experiment runs, scores, and holdout task files stay untouched in the same pull request.

The first commit that adds this page is the freeze. It is not an amendment.