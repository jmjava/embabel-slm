# embabel-slm

A local coding model for ordinary programmer work. Embabel is the first domain that can be scored with a compiler and a planner. Spring and Kotlin patterns, taken from real example source, are part of the same training set.

This repository is the model program. The MCP bridge that serves a local model to Cursor, Copilot, and Claude stays in [slm-setup](https://github.com/jmjava/slm-setup). Training does not go into that bridge.

## Read this first

- [docs/research-plan.md](docs/research-plan.md) — research question, phases, evaluation, and the controlled base / retrieval / LoRA experiment.
- [docs/milestones.md](docs/milestones.md) — the production bar and the milestone order. LoRA waits until retrieval has been measured on the same tasks.

## Training corpus

Pin these before any adapter run. The same pins feed retrieval and verified training examples. Holdout tasks stay out of the training split.

| Source | What to pin |
| --- | --- |
| Embabel Guide | [jmjava/guide](https://github.com/jmjava/guide). Never open a pull request against `embabel/guide`. |
| Embabel DICE | [jmjava/dice](https://github.com/jmjava/dice) |
| Embabel documentation | Official agent guide on [docs.embabel.com](https://docs.embabel.com) |
| Learning sites | [jmjava/embabel-v1-learning](https://github.com/jmjava/embabel-v1-learning) (cheat sheet, walkthrough, lessons) |
| Embabel cookbook | Official cookbook on [docs.embabel.com](https://docs.embabel.com) |
| Spring patterns | Pattern cards mined from Spring usage in Guide, DICE, and the learning demos. Each card cites the source file it came from. |
| Kotlin patterns | Pattern cards mined from Kotlin in DICE and the learning demos. Each card cites the source file it came from. |

Skip `.env` files, tokens, and local secrets when ingesting. A training example that only restates a doc page, with no code a compiler can accept or reject, does not count. A Spring or Kotlin pattern card with no source path stays out.

## Standing rules

- Do not start with fine-tuning.
- Do not overwrite an experiment directory.
- Do not choose the permanent base model from a single chat session.
- Official Ollama library tags only, until a later decision says otherwise.
- Model weights are not committed. See [models/README.md](models/README.md).
