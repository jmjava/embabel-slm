# Plan: combined dose ladder

This is the dose ladder in [preregistration.md](preregistration.md). The confirmatory exam is one combined holdout. The training sizes are prefixes of one ordered list.

## Claim

One combined holdout of 742 tasks is scored after each training size. A later size is the earlier size plus more examples. The confirmatory result is that the later size passes more of those same 742 tasks. A true 5-point step on that exam is the gain this sample can detect about 80% of the time. Area labels stay on every example so the mix can be built. An area breakdown is reported with the result. It is not a separate 742-task test.

The general-coding release floor in `docs/m0-bars.md` stays a 5-point rule. This plan does not change it.

## One ordered list

Admitted examples are placed in one order before any score. Every training size is a prefix of that list. A later size contains the earlier size. The order is a seeded stratified draw so each prefix keeps the available-data mix as closely as the counts allow. The seed is written into the protocol with the amendment. It is not chosen after a score.

The holdout tasks are disjoint from every prefix. A labeled unit is not yet an admitted example and not yet a holdout task. Admission still requires one pre-registered area label, an executable oracle, a source file and pin, and rejection of a near-duplicate of the other split.

## Sizes

Three starting values are named now. For a start \(x\), the four sizes are \(1x\), \(2x\), \(4x\), and \(8x\): small, medium, large, and extra large.

| Start \(x\) | Small | Medium | Large | Extra large |
|---:|---:|---:|---:|---:|
| 500 | 500 | 1,000 | 2,000 | 4,000 |
| 1,000 | 1,000 | 2,000 | 4,000 | 8,000 |
| 2,000 | 2,000 | 4,000 | 8,000 | 16,000 |

These ladders share one list, so the distinct prefixes are 500, 1,000, 2,000, 4,000, 8,000, and 16,000. The confirmatory comparisons are the five successive doublings on that list. Holm correction covers those five tests. A size that is not in this table is not part of the claim.

16,000 training examples plus the 742 holdout tasks use 16,742 of the 19,614 labeled units. That leaves 2,872 labeled units spare for examples that fail admission. A start above 2,000 is not in this plan. \(8 \times 2{,}359\) would consume the entire remainder and leave no spare.

## Mix

The mix follows the labeled pool. It is not reweighted so that every area has the same count. The same shares apply at every prefix.

| Area | Share of every prefix |
|---|---:|
| Drivine query | 55.9% |
| Drivine generation | 16.0% |
| Drivine repair | 10.1% |
| Embabel integration | 4.5% |
| Drivine graph_rag | 4.1% |
| Embabel planning | 2.7% |
| Embabel transformation | 2.3% |
| Drivine integration | 2.2% |
| Embabel generation | 1.6% |
| Embabel repair | 0.5% |
| Embabel refactor | 0.1% |

A short prefix can contain no refactor example. That is a consequence of this mix. Refactor is still eligible for later prefixes when an admitted refactor example falls in the order.

The training example is a method. The enclosing type signature is stored with it as context. A whole type is kept when the file does not split into two methods. The pool is code. Prose is not an example.

## What is scored once

The 742 tasks are sealed before the first model output. Each of the six prefixes is scored on those tasks. Adding a seventh size after seeing those scores is a new study. The guide is retrieval after training. It does not fill a prefix.

## Before authoring

1. Admit examples and author the 742 tasks from the labeled code. Write the manifest hash before the first score.
2. Upload the protocol to Zenodo before any holdout score.
