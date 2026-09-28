# Coder model: production milestones

**Product:** a local coding model a programmer can use for ordinary work. Embabel is the first domain we can score with a compiler and a planner, not the whole product.

**Delivery stays in `slm-setup`.** That repo is the MCP bridge. This program is the model. Do not put training into the bridge until a later decision says so.

**Order is the plan.** A later milestone does not start because an earlier one looks slow. LoRA waits until retrieval has been measured on the same tasks.

Source brief: [research-plan.md](research-plan.md) (baseline, RAG, holdout, verified synthetic data, LoRA, A/B/C/D).

## Training corpus

Pin these before any adapter run. The same pins feed retrieval (M3) and verified training examples (M5). Holdout tasks stay out of the training split.

| Source | What to pin |
| --- | --- |
| Embabel Guide | [jmjava/guide](https://github.com/jmjava/guide). Read it for training. Never open a pull request against `embabel/guide`. |
| Embabel DICE | [jmjava/dice](https://github.com/jmjava/dice) (Domain-Integrated Context Engineering). |
| Embabel documentation | Official user guide at [docs.embabel.com](https://docs.embabel.com) (agent guide). |
| Learning sites | [jmjava/embabel-v1-learning](https://github.com/jmjava/embabel-v1-learning) (cheat sheet, walkthrough, lessons). |
| Embabel cookbook | Official cookbook at [docs.embabel.com](https://docs.embabel.com) (`embabel-cookbook`). |
| Spring patterns | Pattern cards mined from Spring usage in Guide, DICE, and `embabel-v1-learning` (`java-demo`, `kotlin-demo`, `templates`). Each card cites the source file it came from. |
| Kotlin patterns | Pattern cards mined the same way from Kotlin in DICE and `embabel-v1-learning` (`kotlin-demo`, `templates`). Each card cites the source file it came from. |

Skip `.env` files, tokens, and local secrets when ingesting. Docs are retrieved at answer time and also turned into compiler-checked training examples. An example that only restates a doc page, with no code a compiler can accept or reject, does not count toward the 500.

Spring and Kotlin enter training as those pattern cards, not as the language manuals. A card with no source path stays out.

## What "production" means

A named build is a production candidate only when all of these are true:

- It beats its own base model on the locked Embabel holdout (compile rate, full-task success, hallucinated-API rate, planner success, repair iterations).
- It holds the general-coding floor from M0 (tests, repair, multi-file edit, explanation) inside the threshold set before any adapter is trained.
- A bad answer fails the runner. A known-bad fixture is part of the suite.
- Latency, peak memory, model id, quant, prompt, retrieval config, and raw outputs are recorded and not overwritten.
- An operator can point the existing `local-coding-slm` tools at it. Official Ollama library tags only, until a later decision allows something else.
- No claim of expert behavior without the holdout numbers attached.

Out of this program: pretraining from scratch, public Ollama, tunnels, and a second MCP server.

## Milestones

### M0 — Write the bar before any run

- [ ] M0: Freeze the general-coding floor (task list and the drop that fails a release)
- [ ] M0: Freeze the Embabel gain (the specialist metrics and the lift that counts)
- [ ] M0: Freeze host budget (7B–14B first; 32B only after the runner is stable)

Exit: one page a later run cannot quietly edit after the numbers look bad.

### M1 — One reproducible baseline

- [ ] M1: Install one official 7B–14B coding tag and validate inference on the current private Ollama host
- [ ] M1: Pin one Embabel commit
- [ ] M1: Score the first 20 Embabel tasks and save the raw run

Exit: a run id with model, quant, prompt, commit, and scores. The permanent base model is still not chosen.

### M2 — A runner that rejects a bad answer

- [ ] M2: Run extract, isolated project, compile, and tests unattended on those 20 tasks
- [ ] M2: Keep a known-bad fixture in the suite and show that it fails

Exit: the same command can score a model and can fail a broken one.

### M3 — Retrieval before weights

- [ ] M3: Re-run the same 20 tasks with retrieval over Guide, DICE, the docs, the learning site, the cookbook, and the Spring and Kotlin pattern cards
- [ ] M3: Record compile rate, hallucinated APIs, and full success for base vs retrieval
- [ ] M3: Decide whether the remaining gap is prompting, retrieval, or weights

Exit: a written A-vs-B result. Expanding toward 100 tasks waits on this.

### M4 — Lock the holdout

- [ ] M4: Reach at least 100 held-out tasks across generation, repair, planning, transformation, refactor, and integration
- [ ] M4: Add a general-coding holdout large enough to catch a specialist that lost ordinary Java/Kotlin
- [ ] M4: Keep benchmark tasks out of every training directory

Exit: a frozen split. Near-duplicates of holdout tasks are rejected before training.

### M5 — Verified data, then the smallest adapter

- [ ] M5: Extract Spring and Kotlin pattern cards from Guide, DICE, and the learning demos, each card citing its source file
- [ ] M5: Produce 500 compiler-verified training examples outside the holdout, drawn from Guide, DICE, the docs, the learning site, the cookbook, and those pattern cards
- [ ] M5: Run one LoRA or QLoRA on 7B or 14B aimed at the gap retrieval did not close
- [ ] M5: Record base, retrieval, adapter, and retrieval-plus-adapter on the locked holdout
- [ ] M5: Keep the adapter only if Embabel success rises and the M0 general floor still holds

Exit: the A/B/C/D table. An adapter that only memorizes docs retrieval should have supplied is discarded.

### M6 — Useful inside a real edit loop

- [ ] M6: Let the model generate, compile, read the failure, and repair, and record the iteration count
- [ ] M6: Pass one real multi-module scenario through the existing local-coding-slm tools

Exit: a failing tree becomes a passing tree. A single demo prompt does not close this.

### M7 — Name a production candidate

- [ ] M7: Publish `embabel-slm-<base>-<size>-<stage>-<version>` with a reproducibility record
- [ ] M7: Record latency and peak memory on the target host
- [ ] M7: Write the operator note for pointing the MCP bridge at that build

Exit: the strength claims cite the holdout. The general-coding floor still holds.

## Standing rules

- Do not start at M5.
- Do not overwrite an experiment directory.
- Do not choose the permanent base model from a single chat session.
- Halo is the target host when that machine is in use. M1 may run on the workstation Ollama that already works.
