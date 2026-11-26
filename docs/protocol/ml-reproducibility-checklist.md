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
| Random seeds | Known — 1..5 for samples | `meta.json` |
| Analysis script hash | TBD at holdout freeze | `experiments/paper-v1/analysis-script-sha256.txt` |
| Raw completions | Local only; scrub before public artifact | gitignored `raw/` |
| Negative results | Required — all configs reported | tables in `experiments/paper-v1/` |