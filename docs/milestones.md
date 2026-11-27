# Coder model: production milestones

**Product:** a local coding model a programmer can use for ordinary work. Embabel is the first domain we can score with a compiler and a planner, not the whole product.

**Delivery stays in `slm-setup`.** That repo is the MCP bridge. This program is the model. Do not put training into the bridge until a later decision says so.

**Order is the plan.** A later milestone does not start because an earlier one looks slow. LoRA waits until retrieval has been measured on the same tasks.

Source brief: [research-plan.md](research-plan.md) (baseline, RAG, holdout, verified synthetic data, LoRA, A/B/C/D).

Preprint track (does not reorder milestones): [paper-calendar-2026.md](paper-calendar-2026.md). Paper v1 (DOI by **31 Mar 2027**) uses the `slm-setup` layered MCP eval plus Embabel M1–M3 A-vs-B; M4/M5 are optional inside that window only if frozen by late February.

## Training corpus

Pin these before any adapter run. The same pins feed retrieval (M3) and verified training examples (M5). Holdout tasks stay out of the training split.

| Source | What to pin |
| --- | --- |
| Embabel Guide | Official [embabel/guide](https://github.com/embabel/guide). Read it for training. Do not open a pull request against it. |
| Embabel DICE | Official [embabel/dice](https://github.com/embabel/dice) (Domain-Integrated Context Engineering). |
| Embabel documentation | Official user guide at [docs.embabel.com](https://docs.embabel.com) (agent guide). |
| Learning sites | [jmjava/embabel-v1-learning](https://github.com/jmjava/embabel-v1-learning) (cheat sheet, walkthrough, lessons). |
| Embabel cookbook | Official cookbook at [docs.embabel.com](https://docs.embabel.com) (`embabel-cookbook`). |
| Spring patterns | Pattern cards mined from Spring usage in official `embabel/guide`, official `embabel/dice`, and `embabel-v1-learning` (`java-demo`, `kotlin-demo`, `templates`). Each card cites the source file it came from. |
| Kotlin patterns | Pattern cards mined the same way from Kotlin in official `embabel/dice` and `embabel-v1-learning` (`kotlin-demo`, `templates`). Each card cites the source file it came from. |

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

- [x] M0: Freeze the general-coding floor (task list and the drop that fails a release)
- [x] M0: Freeze the Embabel gain (the specialist metrics and the lift that counts)
- [x] M0: Freeze host budget (7B–14B first; 32B only after the runner is stable)

Exit: [m0-bars.md](m0-bars.md) is the page. The checker rejects a later edit that is not an amendment.

### M0.5 — Example ledger (no GPU)

- [x] M0.5: One row per public Embabel source + learning repo, with pins ([example-ledger.md](example-ledger.md))
- [x] M0.5: Freeze the first 20 tasks from the gap list (paths + checks only) — [benchmark/tasks/](../benchmark/tasks/) E01–E20
- [x] M0.5: Author one known-bad fixture specification — [KB01](../benchmark/fixtures/known-bad/KB01-missing-action-dependency.md)

Exit: a gap list that can become `benchmark/tasks/` without a live model. The no-GPU track finished; Halo is on Linux as of 2026-11-26. **Met 2026-11-25** (specs only; runner is M2).

### M1 — One reproducible baseline

- [ ] M1: Install one official 7B–14B coding tag and validate inference on the Halo Ollama host (`host_class=halo-395`)
- [ ] M1: Pin one Embabel commit
- [ ] M1: Score the first 20 Embabel tasks and save the raw run

Exit: a run id with model, quant, prompt, commit, and scores. The permanent base model is still not chosen.

### M2 — A runner that rejects a bad answer

- [x] M2: Run extract, isolated project, compile, and tests unattended on those 20 tasks
- [x] M2: Keep a known-bad fixture in the suite and show that it fails

Exit: the same command can score a model and can fail a broken one. Halo is on Linux; live scoring uses `host_class=halo-395` (fixtures still valid for CI).

### M3 — Retrieval before weights

- [ ] M3: Re-run the same 20 tasks with retrieval over Guide, DICE, the docs, the learning site, the cookbook, and the Spring and Kotlin pattern cards
- [ ] M3: Record compile rate, hallucinated APIs, and full success for base vs retrieval
- [ ] M3: Decide whether the remaining gap is prompting, retrieval, or weights

Exit: a written A-vs-B result on the untrained base. The product guide is added later, on the already trained model. Expanding toward 100 tasks waits on this.

### M4 — Lock the holdout

- [ ] M4: Write the official base-model shortlist into the protocol before any development score. Upload the protocol to Zenodo **before any holdout scoring** (see [protocol/preregistration.md](protocol/preregistration.md); operator upload only; complete [internal publication-review checklist](../internal/publication-review.md) first — that file is not part of the Zenodo package)
- [ ] M4: The prefixes 500, 1,000, 2,000, 4,000, 8,000, and 14,000 are locked in the protocol before authoring
- [ ] M4: Build the admission checker (one area label, executable oracle, source pin, not a near-duplicate)
- [ ] M4: Independently author and seal the combined holdout of 742 executable tasks (371+371; area counts from admitted-pool shares, not subtracted from training supply); `analysis seal-study` before prefix cut; commit manifest hash before scoring
- [ ] M4: Score middle (M) and ceiling (L) reference baselines under configs A and B on DEV (comparison only)
- [ ] M4 (legacy bar): the earlier 100-task draft remains a pilot until the combined holdout reaches 742
- [ ] M4: Add a general-coding holdout large enough to catch a specialist that lost ordinary Java/Kotlin
- [ ] M4: Keep benchmark tasks out of every training directory

Exit: a frozen split. Near-duplicates of holdout tasks are rejected before training.

### M5 — Verified data, then the smallest adapter

- [ ] M5: Extract Spring and Kotlin pattern cards from Guide, DICE, and the learning demos, each card citing its source file
- [ ] M5: Produce ≥14,000 clean admitted training examples (feasibility high risk until oracle admission); cut locked prefixes only after seal (`build-prefixes` requires admission receipt)
- [ ] M5: Adapt the selected base on the combined prefix list
- [ ] M5: Score the six prefixes on the sealed 742-task holdout
- [ ] M5: Report each prefix step, and keep the run only if the M0 general floor still holds

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

## Drivine milestones (parallel order; paper Part C)

Same arms and selected model tags as Embabel; corpus and holdout live in [jmjava/drivine-slm](https://github.com/jmjava/drivine-slm). Do not mark done until the exit criteria are met.

### D1 — Harness that rejects a bad answer (parallel M2)

- [ ] D1: Build Drivine runner: extract code; parse, compile or query-execute against pinned Drivine; fixture assertions; fail tasks with no executable oracle for confirmatory holdout
- [ ] D1: Pilot ~20 executable tasks scored once (exploratory only)

Exit: a command can pass a good answer and fail a known-bad one. No confirmatory row yet.

### D2 — Clean baseline on pilot (parallel M1)

- [ ] D2: Score the Embabel-selected shareable tag on Drivine pilot tasks without retrieval or adapter

Exit: run id with pins recorded. Permanent base is still chosen on Embabel DEV only.

### D3 — Retrieval before weights (parallel M3)

- [ ] D3: Re-run the same pilot with Drivine retrieval pack; record full_task_success vs clean baseline

Exit: written A-vs-B on pilot. Adapter waits on the written gap.

### D4 — Lock the Drivine holdout (parallel M4)

- [ ] D4: Drivine tasks inside the combined 742-task holdout are executable; commit the manifest hash before scoring
- [ ] D4: Exclude `data/drivine_instruct.json` (100 training/DEV pairs) via near-duplicate rule

Exit: frozen Drivine split disjoint from the 100 instruct pairs.

### D5 — One domain-specific adapter (parallel M5)

- [ ] D5: Drivine examples sit on the same ordered list as Embabel examples, disjoint from the combined holdout
- [ ] D5: Score the six prefixes on the sealed 742-task holdout using the Embabel-selected base tag

Exit: one A/B/C/D table on the combined holdout. One adapter trains on the combined list.

## Standing rules

- Do not start at M5.
- Do not overwrite an experiment directory.
- Do not choose the permanent base model from a single chat session.
- Three-host lab (**25 Nov 2026 switch**): Phase 3 measure and Embabel inference on **Halo / GEEKOM 395** first (`host_class=halo-395`). Downstairs NVIDIA is fallback only. IDE workstation = MCP only — **no paper inference** there. Require `host_class` on every results row.
