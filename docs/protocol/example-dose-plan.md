# Plan: make the example-dose claim solid

The confirmatory claim is that the **16,000-example prefix** of one ordered example list raises the pass rate on one combined holdout of **742 independently authored** tasks (**371 Embabel + 371 Drivine**) over the **500-example** prefix at **primary** LoRA seed **20260227**, under three matched training seeds (**20260227**, **20260228**, **20260229**) and identical non-padding target-token, batch-token, and optimizer-update budgets at every prefix. The ladder is [combined-dose-plan.md](combined-dose-plan.md). Normative numbers live in [preregistration.md](preregistration.md).

## What is fixed

- One base model, chosen on the Embabel development split, then used on both subjects.
- Every admitted example has exactly one area label. Embabel labels: generation, repair, planning, transformation, refactor, integration. Drivine labels: generation, repair, query, graph-RAG, integration.
- Combined holdout **371+371**; within each domain, **≥10** holdout tasks per registered area; Hamilton remainder on clean admitted-pool shares; area slices exploratory only.
- Training list mix follows **admitted-pool** shares with largest-remainder redistribution when an area exhausts (never pad or duplicate exhausted areas). Record expected and realized shares at every prefix.
- The training example is a method. The enclosing type signature is its frame.
- One ordered list. The prefixes are 500, 1,000, 2,000, 4,000, 8,000, and 16,000. They are the sizes produced by starts of 500, 1,000, and 2,000 at multipliers 1, 2, 4, and 8.
- Each larger prefix contains the smaller one. **Confirmatory:** 16,000 vs 500 only. **Exploratory:** the five adjacent doublings (optional descriptive Holm only).
- Three matched LoRA training seeds **20260227** (primary McNemar), **20260228**, **20260229** (mandatory separate replications); same identities across prefix sizes.
- Identical non-padding target-token, effective batch-token, and optimizer-update budgets at every prefix (smaller prefixes repeat examples more often).
- Full randomness/software controls frozen before training (shuffle/sampler+seed per training seed, packing, truncation, padding/loss masking, deterministic kernels or documented nondeterminism, framework/library/driver versions).
- Provenance-group splitting so no file/class/fixture/semantic family spans training and holdout.
- The holdout is scored once. A size chosen after those scores needs a new confirmation set.
- Retrieval and the host ceiling are references. They are not a prefix.
- LoRA learns the admitted examples on that list. The guide is an add-on after that training.

## What is still open

The 742 holdout tasks are not authored/sealed yet. The ordered list of admitted examples is not frozen yet. **Audit (current):** **53,676** raw → **16,211** uniquely labeled exact-code targets + **34,247** review; only **211** provisional labeled units over the **≥16,000 clean admitted** training gate—feasibility **high risk and not established**. **Real oracle runs**, **seal-study** seal, **exact integer area holdout counts**, **holdout manifest**, **clean-unit feasibility**, **selected-tokenizer counts**, **Drivine confirmatory oracles**, **training hyperparameter and randomness values**, **scored confirmatory runs**, and **Zenodo DOI** remain blockers. A checked citation on score versus number of training examples is still required before Zenodo. Development scoring may guide how examples are written. It may not pick a confirmatory prefix after seeing holdout numbers. If clean admitted count falls below 16,000, reduce the 16,000 maximum before sealing.

## Frozen analysis pipeline (stdlib)

Mandatory production path: `python3 -m analysis seal-study` (evidence-backed admission, independent holdout validation/allocation, provenance disjointness, MinHash+exact Jaccard, prefix construction, receipts/hashes, sealed directory published by rename). `build-prefixes` requires an admission receipt; `study-results` requires the sealed manifest. Supporting commands: `admit`, `dedup`, `power`. Training records use formatter **`embabel-slm-code-sft-v1`** (code-only context, exact admitted code response, no prose). Optional sampled secondary JSONL (seeds 1..5, seal-bound) reports pass@1 \(k=1\) and pass@5 \(k=5\) with bootstrap CIs; it never changes the primary decision.

## Before any score

1. Admit examples only when evidence joins exact code hashes, repo/pin, canonical argv hash, successful exit, and output/artifact hashes; apply provenance-group splitting by file/fixture/class (`analysis admit`, `analysis dedup`).
2. Author and seal the 742 combined holdout tasks (371+371) per frozen area counts; holdout is disjoint from training by provenance/near-duplicate gates, not supply subtraction (`analysis seal-study`).
3. Cut the six prefixes only after seal (`analysis build-prefixes` with admission receipt). Drivine tasks in the exam are executable. Commit the manifest hash. Do not edit a task after the first model output.
4. Populate exact area counts, S/M/L shortlist tags, and training hyperparameter values in preregistration.
5. Upload the protocol to Zenodo before any holdout score.