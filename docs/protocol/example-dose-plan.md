# Plan: make the example-dose claim solid

The confirmatory claim is that each larger prefix of one ordered example list raises the pass rate on one combined holdout of 742 tasks. The ladder is [combined-dose-plan.md](combined-dose-plan.md). Normative numbers live in [preregistration.md](preregistration.md).

## What is fixed

- One base model, chosen on the Embabel development split, then used on both subjects.
- Every admitted example has exactly one area label. Embabel labels: generation, repair, planning, transformation, refactor, integration. Drivine labels: generation, repair, query, graph-RAG, integration.
- The mix follows the labeled pool. Areas are not reweighted to equal shares.
- The training example is a method. The enclosing type signature is its frame.
- One ordered list. The prefixes are 500, 1,000, 2,000, 4,000, 8,000, and 16,000. They are the sizes produced by starts of 500, 1,000, and 2,000 at multipliers 1, 2, 4, and 8.
- Each larger prefix contains the smaller one. The five successive doublings are the Holm family. A missed step is reported. The study does not require all five rejections.
- The holdout is scored once. A size chosen after those scores needs a new confirmation set.
- Retrieval and the host ceiling are references. They are not a prefix.
- LoRA learns the admitted examples on that list. The guide is an add-on after that training.

## What is still open

The 742 tasks are not authored yet. The ordered list of admitted examples is not frozen yet. A checked citation on score versus number of training examples is still required before Zenodo. Development scoring may guide how examples are written. It may not pick a confirmatory prefix after seeing holdout numbers.

## Before any score

1. Admit examples only when they have one pre-registered area label, an executable oracle, and a source pin, and they are not a near-duplicate of the holdout.
2. Place admitted examples in the seeded order and cut the six prefixes.
3. Author the 742 combined holdout tasks. Drivine tasks in that exam are executable. Commit the manifest hash. Do not edit a task after the first model output.
4. Upload the protocol to Zenodo before any holdout score.
