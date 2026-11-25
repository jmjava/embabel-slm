# embabel-slm

A local coding model for ordinary programmer work. Embabel is the first domain that can be scored with a compiler and a planner. Spring and Kotlin patterns, taken from real example source, are part of the same training set.

This repository is the Embabel model program. The MCP bridge that serves a local model to Cursor, Copilot, and Claude stays in [slm-setup](https://github.com/jmjava/slm-setup). Training does not go into that bridge.

The Drivine graph-client track (corpus + Halo AMD LoRA recipes) lives in [drivine-slm](https://github.com/jmjava/drivine-slm). Embabel depends on Drivine for graph RAG; keep the experiment directories separate and follow the same order: clean baseline and retrieval before weights.

## Read this first

- [docs/example-ledger.md](docs/example-ledger.md) — **start here when GPUs are busy**: pinned Embabel sources and the first gap list (no source copied).
- [benchmark/README.md](benchmark/README.md) — **M0.5 freeze**: first 20 Embabel tasks (E01–E20) + known-bad KB01 (paths and checks only).
- [docs/research-plan.md](docs/research-plan.md) — research question, phases, evaluation, and the controlled base / retrieval / LoRA experiment.
- [docs/milestones.md](docs/milestones.md) — the production bar and the milestone order. LoRA waits until retrieval has been measured on the same tasks.
- [docs/m0-bars.md](docs/m0-bars.md) — the frozen general-coding floor, Embabel gain, and host budget. A later run does not edit this page after the numbers look bad.
- [docs/paper-calendar-2026.md](docs/paper-calendar-2026.md) — Nov 2026–Mar 2027 preprint plan (Zenodo primary; TechRxiv contingency).
- [docs/citation-workflow.md](docs/citation-workflow.md) — formal citation acquisition, triage, and BibTeX rules.
- [docs/paper/outline.md](docs/paper/outline.md) — Paper v1 claim freeze and section skeleton.
- [experiments/paper-v1/README.md](experiments/paper-v1/README.md) — raw-data / freeze contract for the preprint.

## Training corpus

Pin these before any adapter run. The same pins feed retrieval and verified training examples. Holdout tasks stay out of the training split.

| Source | What to pin |
| --- | --- |
| Embabel Guide | Official [embabel/guide](https://github.com/embabel/guide). Read it for training. Do not open a pull request against it. |
| Embabel DICE | Official [embabel/dice](https://github.com/embabel/dice) |
| Embabel documentation | Official agent guide on [docs.embabel.com](https://docs.embabel.com) |
| Learning sites | [jmjava/embabel-v1-learning](https://github.com/jmjava/embabel-v1-learning) (cheat sheet, walkthrough, lessons) |
| Embabel cookbook | Official cookbook on [docs.embabel.com](https://docs.embabel.com) |
| Spring patterns | Pattern cards mined from Spring usage in official `embabel/guide`, official `embabel/dice`, and the learning demos. Each card cites the source file it came from. |
| Kotlin patterns | Pattern cards mined from Kotlin in official `embabel/dice` and the learning demos. Each card cites the source file it came from. |

Skip `.env` files, tokens, and local secrets when ingesting. A training example that only restates a doc page, with no code a compiler can accept or reject, does not count. A Spring or Kotlin pattern card with no source path stays out.

## Standing rules

- Do not start with fine-tuning.
- Do not overwrite an experiment directory.
- Do not choose the permanent base model from a single chat session.
- Official Ollama library tags only, until a later decision says otherwise.
- Model weights are not committed. See [models/README.md](models/README.md).
