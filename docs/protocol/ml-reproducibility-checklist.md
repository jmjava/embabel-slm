# ML reproducibility checklist (Paper v1 / holdout track)

Based on best practices for ML reproducibility. TBD items stay open until the first holdout run.

| Item | Status | Record location |
| --- | --- | --- |
| Code repository + commit SHA | Known — `embabel-slm` tag at freeze | `artifact-manifest.md` |
| Embabel dependency pin | Known — `embabel-agent-api:1.5.4` | `runner/config.py`, run `meta.json` |
| Benchmark task specs | Known — E01–E20 frozen | `benchmark/specs/` |
| Holdout manifest hash | TBD — commit before first holdout score | `experiments/paper-v1/holdout-manifest.sha256` |
| Pre-registration JSON | Known — [preregistration.md](preregistration.md) | Zenodo prereg deposit |
| Model tags (official Ollama library only) | TBD — shortlists on DEV | run `meta.json` |
| Quantization | Known — Q4_K_M; one Q8_0 sensitivity row | `meta.json` |
| Inference backend | Known — Ollama | `meta.json` |
| Hardware class | Known — `halo-395` | `meta.json` |
| Ollama version | TBD per run | `meta.json` |
| Decoding params | Known — prereg JSON | `meta.json` |
| Retrieval pack version | TBD at M3 | `meta.json` |
| LoRA adapter id | TBD at M5 | `meta.json` |
| Random seeds | Known — 1..5 for holdout samples (pass@5); LoRA training seeds **20260227** (primary confirmatory), **20260228**, **20260229** (mandatory replications) reused across prefix sizes | `meta.json` |
| Training compute budget | TBD — identical non-padding target-token, effective batch-token, and optimizer-update budgets at every prefix; tokenizer and numeric budgets frozen before training | training config + `meta.json` |
| Training randomness controls | TBD — shuffle/sampler+seed per training seed, packing, truncation, padding/loss masking, deterministic kernels or documented nondeterminism, framework/library/driver versions | training config + `meta.json` |
| Sealed study manifest | TBD — `python3 -m analysis seal-study` before prefix cut; `study-results` requires seal | `experiments/paper-v1/sealed-manifest.json` |
| Sampled secondary JSONL | Optional — seeds 1..5 per task/prefix/training seed when present; seal-bound; pass@1 k=1 and pass@5 k=5 with bootstrap CIs; never changes primary | samples JSONL + seal hash |
| Confirmatory vs replication inference | Known — primary McNemar/CI at seed 20260227 only; replications separate; pooled task×seed exploratory | `preregistration.md` JSON |
| Analysis script hash | TBD at holdout freeze | `experiments/paper-v1/analysis-script-sha256.txt` |
| Raw completions | Local only; scrub before public artifact | gitignored `raw/` |
| Negative results | Required — all configs reported | tables in `experiments/paper-v1/` |