# Pre-registration: example dose and practical gain (Embabel and Drivine holdouts)

Registered-report style protocol for one combined holdout on **two domains**: Embabel (Part B) and Drivine (Part C). The **742 holdout tasks are independently authored executable benchmark tasks** (371 Embabel + 371 Drivine), not units selected or subtracted from the training corpus. Training feasibility requires **≥14,000 clean admitted** training examples on one ordered list; holdout area counts are weighted from clean admitted training shares but **do not consume or cap** training supply. Admitted examples keep one pre-registered area label and are placed on that list. Every training size is a prefix of the list. The same sealed 742 tasks are scored after each prefix. Area labels build the mix. An area breakdown is reported with the result and is not its own 742-task exam. Arms, quantization, `num_ctx`, decoding, and model **selection** are shared. Retrieval and the host-ceiling model are reference measurements, not the dose. Inference for every scored row uses **Ollama** on `host_class=halo-395`. This document is the normative protocol; [analysis-plan.md](analysis-plan.md) gives estimators and tests. The dose ladder is [combined-dose-plan.md](combined-dose-plan.md). Machine-checkable parameters sit in the JSON block below.

**Publication gate (operator checklist):** No Zenodo upload until the operator's internal publication-review checklist is complete.

**Protocol status:** This text is normative in-repo as of `frozen_on` below. Holdout size (742 combined, 371 Embabel + 371 Drivine), domain and area allocation rules, training-pool exhaustion, primary/replication training-seed inference, MinHash parameters, formatter id, and Drivine pilot-vs-confirmatory harness flags are **resolved** in this text. It is **not** sealed for confirmatory scoring while preregistration blockers in the JSON remain open (oracle admission, clean-unit feasibility, exact area/source holdout counts, 742 sealed tasks, shortlist tags/digests, selected-tokenizer counts, hyperparameter values, Drivine confirmatory oracles/pilots, manifest hash, scored runs, Zenodo DOI). The public registered freeze takes effect at **Zenodo upload**; record the Zenodo DOI in a later `amend(prereg):` entry (not before upload).

---

## Title

Does the full nested training prefix raise the combined holdout score over the smallest prefix?

---

## Research question

**Confirmatory:** On one sealed holdout of 742 tasks, does the 14,000-example prefix raise full-task success over the 500-example prefix on the same tasks, under the frozen model and training recipe?

**Exploratory (dose-curve):** Adjacent prefix steps (500→1,000, 1,000→2,000, 2,000→4,000, 4,000→8,000, 8,000→14,000) describe monotonicity and local gain along the ladder. They are not separate confirmatory hypotheses.

Embabel labels are generation, repair, planning, transformation, refactor, and integration. Drivine labels are generation, repair, query, graph-RAG, and integration. The combined holdout has **742** tasks allocated **371 Embabel** and **371 Drivine**. Within each domain, every registered area receives at least **10** holdout tasks for exploratory visibility; each domain's remaining tasks are allocated in proportion to **clean admitted-pool** shares using deterministic Hamilton (largest-remainder) apportionment. Exact integer area counts and per-area source counts are frozen before holdout authoring (blocker until populated). Area slices remain exploratory and are not individually powered.

The training ordered list uses **admitted-pool** shares at every prefix. If a target area runs out of eligible units while building the list or a prefix, take every eligible unit from that area and redistribute its unfilled slots among non-exhausted areas in proportion to their remaining eligible supply, using deterministic largest remainder. Record expected and realized shares at every prefix. Never duplicate or pad an exhausted area.

The named prefixes are 500, 1,000, 2,000, 4,000, 8,000, and 14,000. The sizes through 8,000 come from starts of 500, 1,000, and 2,000 at multipliers 1, 2, 4, and 8. The maximum was reduced from 16,000 to 14,000 after oracle admission of 15,014 clean examples, leaving 1,014 above the cap for later rejects. A size outside that list is not part of the claim.

Model tags for S, M, and L are chosen **only** on the Embabel DEV split. Drivine uses those same tags; Drivine outcomes do not re-pick the base, middle, or ceiling.

---

## Hypotheses (confirmatory)

| ID | Where | Statement | Test |
| --- | --- | --- | --- |
| prefix_14000_minus_500 | Combined holdout | The 14,000-example prefix beats the 500-example prefix | One-sided exact McNemar (greedy primary) |
| H4 | Both domains | General floor: the largest prefix holds the M0 general-coding floor versus zero examples | Per m0-bars rules; **one** gate, outside the prefix contrast |

**Headline estimand (confirmatory):** the paired pass-rate difference on the 742 tasks, 14,000-example prefix minus 500-example prefix, with a cluster-bootstrap 95% CI. At \(\alpha=0.05\), a primary result **rejects the no-improvement null** on this frozen benchmark at the primary seed when that one-sided exact McNemar test rejects. There is **no** Holm family for primary confirmatory inference. Always report the effect and CI; do not claim a practical 5-point improvement unless the interval or estimand wording explicitly warrants it (the 5-point step is a **planning assumption**, not a practical-significance gate).

Each admitted example carries exactly one pre-registered area label. The order is fixed before any score. Each larger prefix contains the smaller one. The mix follows admitted-pool shares with the exhaustion rule above.

**Training replication:** Every prefix is trained with **three matched LoRA training seeds**: **20260227**, **20260228**, and **20260229**, reused at all six prefix sizes. **20260227** is the sole predeclared **primary** seed for the powered one-sided exact McNemar **14,000 vs 500** confirmatory test. **20260228** and **20260229** are mandatory robustness replications. Report the primary effect and both replication effects, CIs, and p-values **separately**. Replication results do not replace, pool with, or rescue the primary decision. Any pooled task×seed summary is **exploratory only** (three seeds do not define a well-powered seed-population inference).

**Confirmatory claim wording:** Confirmatory inference is **conditional** on the frozen primary training seed, model, recipe, and explicitly weighted benchmark. Consistent replication seeds support robustness but not a universal causal scaling law.

**Compute budget (isolation of unique-example diversity):** At every prefix, training uses the **same** non-padding target-token budget, effective batch-token budget, and optimizer-update count. Smaller prefixes therefore **repeat** admitted examples more often within that fixed budget; the contrast isolates how many distinct admitted examples enter the adapter, not longer training on fewer items. Freeze the selected tokenizer and exact numeric budgets before training. Freeze before training: base model tag/hash, tokenizer, sequence length and truncation, batch and gradient accumulation, optimizer, learning rate and schedule, warmup, LoRA target modules/rank/alpha/dropout, precision, non-padding target and batch-token budgets, optimizer-update count, dataset shuffle/sampler algorithm and seed **per training seed**, packing policy, padding and loss masking, deterministic-kernel settings or documented nondeterminism, framework/library/driver versions, checkpoint selection, and primary/replication seed roles (values remain a blocker until populated).

The 5-point difference in `docs/m0-bars.md` remains the release floor. It is not a second gate on the confirmatory contrast. **742** tasks on the combined holdout size the one-sided test for a true 5-point step (\(p_d=0.30\), \(\alpha=0.05\)). Under those planning assumptions, **exact unconditional power is 0.783839** at \(n=742\); **776** tasks would reach 0.80 (the normal approximation ~0.80 is noted but not headline power). The confidence interval is reported. It is not required to lie entirely above 5 points.

**What a later dose is not.** The holdout is scored once at the six locked prefixes. Adding examples after seeing the scores, then rescoring the same holdout, is not further evidence that more examples help.

**Reference, not confirmatory:** retrieval versus the base; gap closure \(G\) versus the host ceiling (undefined when the ceiling-gap interval includes 0); ceiling contrasts; per-area holdout slices (exploratory visibility only—not powered area tests; no representativeness or monotonicity claim at every step).

**Exploratory dose-curve:** Adjacent prefix steps (1,000 vs 500 through 14,000 vs 8,000; the last step is not a doubling) may be reported with one-sided McNemar and bootstrap CIs. If adjusted p-values are shown, label them **exploratory**; Holm–Bonferroni across those five contrasts is **optional and descriptive only** and must not be read as confirmatory family-wise power. H4 is outside the dose ladder.

**Scope of confirmatory claim:** Restricted to the explicitly weighted, sealed combined benchmark under the frozen model, recipe, and **primary training seed**—not universal causality, not guaranteed monotonic improvement across every adjacent step, not confirmatory per-area gains, and not a population inference over training seeds (replications are reported separately).

Exploratory (other): retrieval; size curve across S/M/L; ceiling contrasts; \(G\); quantization effect (Q4_K_M vs one Q8_0 row at dose 0).

### Preregistration blockers (open)

- **Exact integer area holdout counts and per-area source counts** (frozen before holdout authoring).
- **Official S/M/L shortlist tags** in the JSON before Embabel DEV scoring.
- **Holdout manifest** sha256 committed before first score.
- **Feasibility recount** after executable-oracle admission, provenance-group splitting, near-duplicate filtering, and independent holdout authoring/validation: training needs **≥14,000 clean admitted** examples; holdout does not subtract from that supply. **Deterministic audit (current):** **53,676** raw candidates → **16,211** uniquely labeled exact-code targets + **34,247** review rows. **4,315** extra exact-code copies were removed across **3,543** duplicate groups. **996** conflicting-label groups were quarantined as **2,093** review rows, not 996 rows. *(Historical: 19,392 and 17,212 were intermediate noncanonical counts.)* Oracle admission on 2026-11-27 produced **15,014** clean examples. That is **1,014** above the **14,000** cap, held back for later rejects. Near-duplicate filtering and the other gates can still lower the count. If the clean count falls below 14,000, reduce the 14,000 maximum prefix before sealing.
- **Mandatory production seal:** `python3 -m analysis seal-study` performs evidence-backed admission, independent holdout validation/allocation, provenance disjointness, MinHash+exact Jaccard, prefix construction, receipts/hashes, and publishes the sealed directory by rename. The admission receipt hashes the canonical `admitted.jsonl` bytes. `build-prefixes` requires an admission receipt; `study-results` requires the sealed manifest. Physical-line JSONL handles U+2028/U+2029. Scoring is bound to exact task IDs/domain/area from the seal. A sealed receipt does not prove an oracle process was executed; real oracle runs remain absent.
- **Real oracle evidence / admission** joined to exact code hashes, repo/pin, canonical argv hash, successful exit, and output/artifact hashes (`python3 -m analysis admit`; **real oracle runs still absent**).
- **Selected-tokenizer token counts** for training budget (lexical/char diagnostics are reported; selected-tokenizer counts remain blocked).
- **742 authored/sealed holdout tasks** and manifest hash before first score.
- **Drivine confirmatory package/JVM oracles**, ~20 pilot executable task set, Ollama batch wiring for confirmatory rows (pilot runner exists in `jmjava/drivine-slm`; confirmatory harness incomplete).
- **Scored confirmatory runs** (live paper-scored rows **0**).
- **Training hyperparameter values** (base model/tag/hash through checkpoint selection and seed roles) frozen before training.
- **Zenodo DOI** after upload (public protocol freeze).

**Provenance groups:** Split related units by **file, fixture, or class** (not whole repository); semantic families must be authored when applicable so **no provenance group may span training and holdout**.

**Sampled secondary validation (implemented):** When an optional samples JSONL is present, it must contain seeds **1..5** for every task/prefix/training seed and is **seal-bound**. Reports include Chen **pass@1** (\(k=1\)) and **pass@5** (\(k=5\)) with bootstrap CIs; sampled secondary results **never** change the primary decision.

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

The 100 instruction pairs in `drivine_instruct.json` are excluded from the Drivine holdout by the same near-duplicate rule as Embabel. **`jmjava/drivine-slm` ships a pilot executable runner** (`python/drivine_runner`) with known-good/known-bad stdlib pilot tasks and tests; that runner does **not** complete confirmatory scoring. **No Drivine confirmatory scored row exists** until confirmatory package/JVM oracles, the ~20 pilot executable set for development, the 371-task Drivine holdout, and Ollama batch wiring for confirmatory rows are complete.

Before Drivine holdout scoring: commit the holdout manifest hash. Record **drivine.org** doc pin and **Drivine package** pin in run meta when confirmatory oracles exist; training-cutoff vs those dates is recorded like Embabel.

### Confounds held fixed

Same system prompt and task prompts per domain, `num_ctx=8192`, greedy and sampled decoding parameters, same top-k for B/D within each domain's retrieval pack, same runner class per domain, domain pins (Embabel commit; Drivine doc + package), Ollama version recorded per run.

---

## Outcomes

**Primary:** `full_task_success` on the combined holdout. **Greedy** (\(T=0\), one run per task) is the primary paired outcome for confirmatory McNemar. **pass@5** uses Chen et al.’s unbiased pass@k estimator with \(k=5\) independent samples at \(T=0.8\) (`sample_count_k` in JSON); **pass@1** means \(k=1\), not \(k=5\). Greedy and pass@5 are reported separately. Drivine tasks in the denominator are executable only.

**Secondary:** domain-specific automated metrics; general-coding floor tasks (H4); accuracy per GB peak memory; tokens/s; latency.

Human-judged explanation items: written rubric, two blinded raters, Cohen's κ reported; not in Drivine primary denominator.

---

## Sample size and power

**Combined exam:** holdout = 742 tasks. Drivine tasks in that exam must be executable. The sole confirmatory test is one-sided (14,000 vs 500). Under \(p_d \approx 0.30\), \(\alpha=0.05\), and \(\delta=0.05\), `mcnemar_n_required(0.05, two_sided=False)` is 742 for that contrast on this exam (**742** was the normal-approximation design value). **Exact unconditional power** at \(n=742\) is about **78.4%** (~0.784); exact \(n\) for 80% unconditional power is **776**. The headline planning figure remains **~78%** exact, not the normal approximation **~80%**. Reproduce with `python3 -m analysis power`. All six prefixes share the same exam for exploratory dose-curve contrasts.

| \(n\) | Detectable \(\delta\), one-sided (approx., \(p_d=0.30\)) |
| --- | --- |
| 20 | ~0.31 (pilot only) |
| 100 | ~0.14 |
| 186 | ~0.10 (one-sided n for δ=0.10) |
| 742 | ~0.05 (one-sided n for δ=0.05) |

Reproduce tables with `python3 -m analysis power`.

---

## Analysis plan (summary)

Per-task paired design: one greedy run (\(T=0\)) plus \(k=5\) sampled runs (\(T=0.8\), fixed sample seeds) for pass@5. Cluster bootstrap (10,000 resamples, fixed seed `20260227`) for 95% CIs on the confirmatory contrast and on exploratory adjacent steps. One-sided exact McNemar on greedy passes for **prefix_14000_minus_500** at training seed **20260227** (confirmatory). Replicate McNemar/CIs at seeds **20260228** and **20260229** reported separately; no pooling for the primary decision. Adjacent doublings are exploratory; Holm on those five is optional/descriptive only. Retrieval, \(G\), and ceiling contrasts are exploratory. Effect sizes with CIs, not p-values alone. Full detail: [analysis-plan.md](analysis-plan.md). Frozen script hash recorded in run manifest at holdout freeze.

---

## Exclusion and failure rules

- Transport or runner errors: **one** rerun; if still failing, count as task fail — never drop tasks post hoc.
- Missing completion: fail.
- Config not finished on a domain holdout by numbers freeze: reported as **not run** in Paper v1 (see timeline).

---

## Contamination controls

Near-duplicate filter before training using deterministic MinHash LSH on **5-token shingles**, **128** permutations (`embabel-slm-minhash-v1` seed), **32 bands × 4 rows**, then **exact Jaccard ≥ 0.8** on normalized prompt+code (default LSH mode; exhaustive pairwise mode exists when complete candidate recall is required—do not claim exhaustive recall unless that mode is used). Implement via `python3 -m analysis dedup`. Holdout manifest hash committed pre-scoring per domain; training-cutoff vs task-date flags for sensitivity; `drivine_instruct.json` excluded from Drivine holdout by the same rule.

## Training example formatter (frozen)

Selected SFT formatter: **`embabel-slm-code-sft-v1`** — code-only prompt context (domain, area, language, grain, class frame/method or fixture context); response is the exact admitted method/class/query code with **no** prose or model-generated descriptions. Lexical and character diagnostics are reported; **selected-tokenizer counts remain a blocker** before training seals.

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

**Constraints (not findings from the literature).** Shareable arm eligibility (7–14B parameters, peak memory ≤16 GB at Q4_K_M and `num_ctx=8192`) defines who can run the release model; it is not an estimated optimum from any paper. The five-point difference in `docs/m0-bars.md` is the release floor: a full dose that drops more than 5 points on general coding fails. It is not the test that a dose step improved. The holdout minimum of 742 tasks is the normal-approximation planning size for a 5-point one-sided difference. Exact unconditional power at that size is about **0.783839**; **776** tasks are required for exact 80% power under the same assumptions. 742 is not an 80% exact-power design and it is not an estimated optimum. Official S, M, and L shortlist tags are not locked in the JSON yet; the shortlist must be written into this protocol before any Embabel DEV scoring, and selection uses only the pre-registered rule above.

**Pre-registration and timing.** Hypotheses, sample size, and analysis are specified before confirmatory scores (Nosek et al., 2018). The public timestamp is Zenodo upload of this document; that upload has not happened, and no holdout row is scored before it.

**Reproducibility and budget reporting.** We pin model tag, digest, seed, context length, and decoding per run (Pineau et al., 2021). We report the evaluation budget and hyperparameters, not only the best number, including fixed `num_ctx=8192` and fixed decoding (Dodge et al., 2019).

**Quantization.** Q4_K_M is the shared default quantization (Dettmers and Zettlemoyer, 2023, k-bit inference scaling laws). The single Q8_0 row on shareable config A is our pre-registered sensitivity check, not a result from that paper.

**Decoding and pass@k.** Sampled holdout attempts use temperature 0.8 as in Chen et al. (2021) HumanEval sampling; greedy stays at temperature 0. We use Chen et al.’s unbiased pass@k estimator with \(k=5\) (**pass@5**). With \(k=1\) the same estimator is **pass@1**; the study’s sampled budget is five draws per task, not pass@1. Chen et al. drew far more than five samples per task in HumanEval.

**Retrieval and adapters.** Retrieval augmentation follows Lewis et al. (2020). Domain LoRA follows Hu et al. (2022); a run that uses QLoRA also cites Dettmers et al. (2023, QLoRA)—we do not label a LoRA-only run as QLoRA. LoRA is the training step: it learns the admitted examples. The guide is an add-on after that training: config D attaches retrieval to the already trained model. Config B is still measured on the untrained base first, because Ovadia et al. (2024) found RAG outperformed unsupervised fine-tuning for injecting corpus knowledge on factual QA; their tasks were not code and their fine-tune was continued pretraining, not LoRA, so that measurement order is supportive precedent, not a replication. The product use of the guide remains the add-on on the trained model.

**Executable outcomes and controls.** Drivine holdout tasks require executable oracles in the spirit of real-issue benchmarks (Jimenez et al., 2024); we do not use the SWE-bench task set. KB01 is a known-bad negative control after the Defects4J precedent (Just et al., 2014): a skipped or errored check layer is not a pass.

**Repair and cascades.** We pre-register exactly one repair sample and report greedy success separately from any repair-augmented rate and separately from pass@5 so repair gains cannot hide in a single headline (Olausson et al., 2024). The fast→one repair→strong policy is inspired by LLM cascades (Chen et al., 2024, FrugalGPT); our policy is fixed with no learned quality scorer.

**Paired inference.** Greedy confirmatory test uses exact McNemar on paired pass/fail for 14,000 vs 500 at the **primary** training seed 20260227 (Dietterich, 1998; McNemar, 1947). We pre-set \(\alpha=0.05\), name the contrast, and treat the paired task as the unit (Dror et al., 2018). Seeds 20260228 and 20260229 are mandatory replication runs reported separately; pooled task×seed summaries are exploratory only.

**Multiplicity.** There is no Holm family for the primary confirmatory inference. Holm (1979) may be cited only for **optional** descriptive adjustment of exploratory adjacent-doubling p-values; it does not confer confirmatory family-wise power on those five contrasts.

**Example doses.** The sole confirmatory test is one-sided exact McNemar on the combined holdout: the 14,000-example prefix passes more of the same 742 tasks than the 500-example prefix (McNemar, 1947; Dietterich, 1998). Adjacent doublings are exploratory dose-curve analyses. The prefixes and the three starting values are written into this protocol before any example is authored (Dror et al., 2018). They are not taken from a data-scaling paper. Raghavendra, Nath, and Hendryx (2024) report that post-training benchmark score, including coding on HumanEval+, rose with the number of supervised-finetuning examples under a power-law fit (arXiv:2410.03717). Their runs are full-parameter supervised finetuning of Llama and Mistral models on public benchmarks for a fixed number of epochs. They are not this study's nested LoRA prefixes, equal token and update budget, or sealed holdout, and this protocol does not adopt their sizes or their power-law claim. \(p_d=0.30\) for McNemar power is a planning assumption, not an estimate from data; exact unconditional power at \(n=742\) is about 78%, not 80%. Ceiling comparisons are not non-inferiority tests. Piaggio et al. (2012) would apply only if a later amendment made a ceiling margin confirmatory.

**Bootstrap intervals.** Cluster bootstrap with \(B=10\,000\) resamples over tasks uses percentile intervals (Efron, 1979). \(B=10\,000\) is pre-registered here; resampling is over tasks as the paired unit (Dror et al., 2018; Dietterich, 1998).

**Contamination.** Near-duplicate separation of training or retrieval material from holdout uses MinHash/Jaccard on normalized prompt and code (Lee et al., 2022), with the shingles/band parameters in the JSON block. The Jaccard threshold 0.8 is pre-registered in this protocol and is not attributed to Lee et al. LSH candidate generation is probabilistic; exact Jaccard confirms pairs at or above threshold.

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
      "configs": [
        "A",
        "B",
        "C",
        "D"
      ]
    },
    "M": {
      "parameter_billions_min": 24,
      "parameter_billions_max": 34,
      "configs": [
        "A",
        "B"
      ]
    },
    "L": {
      "dense_max_billion_parameters": 70,
      "moe_max_billion_parameters_total": 120,
      "configs": [
        "A",
        "B"
      ]
    }
  },
  "configs": {
    "A": {
      "retrieval": false,
      "lora": false
    },
    "B": {
      "retrieval": true,
      "lora": false
    },
    "C": {
      "retrieval": false,
      "lora": true
    },
    "D": {
      "retrieval": true,
      "lora": true
    }
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
    "holdout_domain_tasks": {
      "embabel": 371,
      "drivine": 371
    },
    "holdout_tasks_independently_authored_executable_benchmark": true,
    "holdout_area_counts_weighted_from_clean_admitted_training_shares": true,
    "holdout_does_not_consume_or_cap_training_supply": true,
    "min_clean_admitted_training_examples": 14000,
    "holdout_area_allocation": {
      "minimum_tasks_per_registered_area_per_domain": 10,
      "remainder_method": "hamilton_largest_remainder_on_clean_admitted_pool_shares",
      "area_slices_exploratory_not_powered": true,
      "exact_counts_frozen_before_holdout_authoring": true
    },
    "embabel": {
      "part": "B",
      "pilot_task_ids": "E01-E20,KB01",
      "holdout_categories": 6,
      "holdout_tasks": 371
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
      "pilot_harness_exists": true,
      "confirmatory_harness_complete": false,
      "confirmatory_package_oracle_complete": false,
      "confirmatory_scored_rows": 0,
      "holdout_manifest_sha256": null,
      "holdout_tasks": 371
    }
  },
  "training_formatter_version": "embabel-slm-code-sft-v1",
  "training_formatter_role": "code_only_prompt_exact_admitted_code_response_no_prose",
  "selected_tokenizer_token_counts_blocker": true,
  "decoding": {
    "greedy_temperature": 0,
    "sample_temperature": 0.8,
    "sample_count_k": 5,
    "sample_seeds": [
      1,
      2,
      3,
      4,
      5
    ],
    "top_p": 0.95
  },
  "statistics": {
    "alpha_confirmatory": 0.05,
    "exploratory_adjacent_contrasts": [
      "prefix_1000_minus_500",
      "prefix_2000_minus_1000",
      "prefix_4000_minus_2000",
      "prefix_8000_minus_4000",
      "prefix_14000_minus_8000"
    ],
    "exploratory_holm_adjustment": "optional_descriptive_not_confirmatory_fwer",
    "areas": {
      "embabel": [
        "generation",
        "repair",
        "planning",
        "transformation",
        "refactor",
        "integration"
      ],
      "drivine": [
        "generation",
        "repair",
        "query",
        "graph_rag",
        "integration"
      ]
    },
    "example_doses": {
      "unit": "admitted_example_on_one_ordered_list",
      "assignment": "authored_for_exactly_one_area",
      "random_pool_rejected": true,
      "nested_prefixes": true,
      "order_seed": 20260227,
      "starts": [
        500,
        1000,
        2000
      ],
      "multipliers": [
        1,
        2,
        4,
        8
      ],
      "prefixes": [
        500,
        1000,
        2000,
        4000,
        8000,
        14000
      ],
      "mix": "admitted_pool_shares",
      "area_exhaustion_redistribution": "largest_remainder_among_non_exhausted_by_remaining_eligible_supply",
      "record_expected_and_realized_shares_at_every_prefix": true,
      "never_duplicate_or_pad_exhausted_area": true,
      "equal_area_weights": false,
      "grain": "method",
      "counts_locked_before_authoring": true
    },
    "confirmatory_contrast": "prefix_14000_minus_prefix_500_on_combined_holdout",
    "confirmatory_comparisons": {
      "prefix_14000_minus_500": "prefix_14000_minus_prefix_500"
    },
    "confirmatory_unit": "combined_holdout",
    "increment_decision": "one_sided_mcnemar_reject_14000_beats_500",
    "training_seeds_matched_count": 3,
    "training_seed_identities": [
      20260227,
      20260228,
      20260229
    ],
    "training_seed_identities_frozen_across_prefixes": true,
    "primary_confirmatory_training_seed": 20260227,
    "mandatory_replication_training_seeds": [
      20260228,
      20260229
    ],
    "replication_results_do_not_replace_primary_decision": true,
    "pooled_task_by_training_seed_summaries_exploratory_only": true,
    "training_compute_budget": "identical_non_padding_target_token_budget_effective_batch_token_budget_and_optimizer_update_count_at_every_prefix",
    "training_hyperparameters_frozen_before_training": [
      "base_model_tag_and_hash",
      "tokenizer",
      "sequence_length_and_truncation",
      "batch_and_gradient_accumulation",
      "optimizer",
      "learning_rate_and_schedule",
      "warmup",
      "lora_target_modules_rank_alpha_dropout",
      "precision",
      "non_padding_target_token_budget",
      "effective_batch_token_budget",
      "optimizer_update_count",
      "dataset_shuffle_sampler_algorithm_and_seed_per_training_seed",
      "packing_policy",
      "truncation",
      "padding_and_loss_masking",
      "deterministic_kernel_settings_or_documented_nondeterminism",
      "framework_library_and_driver_versions",
      "checkpoint_selection",
      "primary_and_replication_seed_roles"
    ],
    "training_hyperparameter_values_populated": false,
    "training_estimand_note": "smaller_prefixes_repeat_admitted_examples_more_often_within_fixed_token_and_update_budgets",
    "corpus_audit_raw_candidates": 53676,
    "labeled_units_current_count": 16211,
    "labeled_units_routed_to_review": 34247,
    "exact_duplicate_candidates_removed": 4315,
    "exact_duplicate_candidate_groups": 3543,
    "conflicting_label_exact_duplicate_groups": 996,
    "conflicting_label_review_rows": 2093,
    "clean_admitted_examples_2026_11_27": 15014,
    "clean_admitted_surplus_above_14000_prefix": 1014,
    "maximum_prefix_reduced_from_16000_to_14000": true,
    "labeled_units_intermediate_counts_historical_note": "19_392_and_17_212_were_intermediate_noncanonical_audit_counts",
    "confirmatory_mcnemar_training_seed": 20260227,
    "confirmatory_claim_conditional_on_primary_seed_model_recipe_benchmark": true,
    "labeled_units_are_not_clean_until_admission": true,
    "feasibility_not_established_until_admission_and_independent_holdout_seal": true,
    "feasibility_recompute_after": [
      "executable_oracle_admission",
      "provenance_clustering",
      "near_duplicate_filtering",
      "independent_holdout_authoring_and_validation"
    ],
    "maximum_prefix_reduced_if_clean_admitted_below_14000": true,
    "sampled_secondary_validation": {
      "implemented": true,
      "samples_jsonl_seeds_1_through_5_per_task_prefix_and_training_seed_when_present": true,
      "samples_jsonl_seal_bound": true,
      "pass_at_1_k_1_bootstrap_ci": true,
      "pass_at_5_k_5_bootstrap_ci": true,
      "never_changes_primary_decision": true
    },
    "preregistration_blockers": [
      "real_oracle_evidence_admission",
      "clean_unit_feasibility_recount",
      "exact_integer_area_holdout_counts_and_source_counts",
      "742_authored_sealed_holdout_tasks",
      "official_s_m_l_shortlist_tags_and_digests",
      "selected_tokenizer_token_counts",
      "training_hyperparameter_values",
      "drivine_confirmatory_package_oracles_and_pilot_task_set",
      "holdout_manifest_sha256",
      "scored_confirmatory_runs",
      "zenodo_doi"
    ],
    "provenance_group_splitting": {
      "required": true,
      "groups": [
        "file",
        "fixture",
        "class",
        "semantic_family_as_appropriate"
      ],
      "scope_note": "not_whole_repository",
      "rule": "no_provenance_group_may_span_training_and_holdout"
    },
    "power_planning_exact_unconditional_at_n_742": 0.783839,
    "power_planning_exact_n_for_0_80_unconditional": 776,
    "power_planning_normal_approximation_at_n_742": 0.8,
    "power_planning_headline_exact_unconditional_rounded": 0.78,
    "release_floor_percentage_points": 5,
    "release_floor_role": "general_coding_drop_limit_not_the_increment_test",
    "slice_holdout_n_for_5_point_step": 742,
    "confidence_bound_above_5_points": "reported_not_required",
    "data_quality": {
      "planned_before_any_model_score": true,
      "example_admission": [
        "slice_label_from_pre_registered_set",
        "compiler_or_executable_oracle",
        "evidence_joined_to_exact_code_hashes_repo_pin_canonical_argv_hash_success_exit_and_output_artifact_hashes",
        "source_file_and_pin_recorded",
        "not_near_duplicate_of_holdout",
        "authored_for_exactly_one_area",
        "dose_membership_by_pre_fixed_prefix_order"
      ],
      "holdout_admission": [
        "independently_authored_executable_tasks_not_subtracted_from_training_supply",
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
    "near_duplicate_method": "minhash_jaccard_normalized_prompt_and_code",
    "minhash_shingle_size_tokens": 5,
    "minhash_num_perm": 128,
    "minhash_lsh_bands": 32,
    "minhash_lsh_rows_per_band": 4,
    "minhash_permutation_seed": "embabel-slm-minhash-v1",
    "minhash_exhaustive_pairwise_default": false,
    "minhash_lsh_approx_candidate_recall_at_jaccard_threshold_note": "high_probabilistic_recall_not_exhaustive_unless_exhaustive_pairwise_mode"
  },
  "freeze": {
    "numbers_freeze_date": "2027-02-27",
    "doi_target_date": "2027-03-31"
  },
  "hypotheses_confirmatory": [
    "prefix_14000_minus_500",
    "H4"
  ],
  "publication_gate_internal_review_required": true,
  "protocol_freeze": {
    "effective_at": "zenodo_upload",
    "zenodo_doi": null
  },
  "analysis_production_path": {
    "mandatory_seal_command": "python3 -m analysis seal-study",
    "build_prefixes_requires_admission_receipt": true,
    "study_results_requires_sealed_manifest": true,
    "jsonl_physical_line_handles_u2028_u2029": true,
    "scoring_bound_to_sealed_task_ids_domain_and_area": true,
    "real_oracle_runs_still_absent": true
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