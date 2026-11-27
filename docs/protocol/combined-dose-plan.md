# Plan: combined dose ladder

This is the dose ladder in [preregistration.md](preregistration.md). The confirmatory exam is one combined holdout. The training sizes are prefixes of one ordered list.

## Claim

One combined holdout of **742** **independently authored** tasks (**371 Embabel + 371 Drivine**) is scored after each training size. Holdout tasks are **not** subtracted from the training supply; training feasibility requires **≥14,000 clean admitted** examples on one ordered list. A later size is the earlier size plus more examples. The **confirmatory** result is whether the **14,000-example** prefix passes more of those same 742 tasks than the **500-example** prefix on training seed **20260227**, under identical non-padding target-token, effective batch-token, and optimizer-update budgets at every prefix and three matched training seeds (**20260227**, **20260228**, **20260229**) per prefix. A 5-point planning step on that exam is what \(n=742\) was sized for with **exact unconditional power 0.783839** (\(p_d=0.30\), one-sided \(\alpha=0.05\); **776** tasks for 0.80). Within each domain, every registered area gets at least **10** holdout tasks; remaining domain tasks use Hamilton apportionment on clean admitted-pool shares. Area holdout slices are exploratory only. Training-list mix uses admitted-pool shares with deterministic largest-remainder redistribution when an area exhausts (never pad or duplicate exhausted areas). An area breakdown is reported with the result. It is not a separate powered 742-task test per area.

Adjacent doublings along the ladder are **exploratory** dose-curve analyses, not five confirmatory hypotheses.

The general-coding release floor in `docs/m0-bars.md` stays a 5-point rule. This plan does not change it.

## One ordered list

Admitted examples are placed in one order before any score. Every training size is a prefix of that list. A later size contains the earlier size. The order is a seeded stratified draw so each prefix keeps the available-data mix as closely as the counts allow. The seed is written into the protocol with the amendment. It is not chosen after a score.

The holdout tasks are disjoint from every prefix. A **labeled** unit is not yet an admitted example and not yet a holdout task. Admission still requires one pre-registered area label, an executable oracle, a source file and pin, rejection of a near-duplicate of the other split, and **provenance-group splitting** (file, class, fixture, or semantic family as appropriate) so related units cannot cross training and holdout.

## Training seeds and compute budget

Train every prefix with **three matched LoRA training seeds** **20260227**, **20260228**, and **20260229**; freeze and reuse the same identities across prefix sizes. **20260227** is the sole primary seed for the powered confirmatory McNemar (14,000 vs 500); **20260228** and **20260229** are mandatory replications reported separately (no pooling for the primary decision; pooled task×seed summaries are exploratory only). Hold **identical** non-padding target-token, effective batch-token, and optimizer-update budgets at every prefix; smaller prefixes repeat examples more often. Freeze the selected tokenizer, numeric budgets, and full randomness/software controls before training (see preregistration JSON).

## Sizes

Three starting values are named now. For a start \(x\), the four sizes are \(1x\), \(2x\), \(4x\), and \(8x\): small, medium, large, and extra large.

| Start \(x\) | Small | Medium | Large | Extra large |
|---:|---:|---:|---:|---:|
| 500 | 500 | 1,000 | 2,000 | 4,000 |
| 1,000 | 1,000 | 2,000 | 4,000 | 8,000 |
| 2,000 | 2,000 | 4,000 | 8,000 | 16,000 |

The table is the unreduced start-times-multiplier ladder. Its 16,000 cell is 2,000×8 and is not a registered prefix. Oracle admission of 15,014 clean examples reduced that maximum to 14,000. The registered prefixes are 500, 1,000, 2,000, 4,000, 8,000, and 14,000. The **confirmatory** comparison is **14,000 vs 500** only. The four doublings through 8,000 and the reduced step from 8,000 to 14,000 are exploratory. A size outside that registered list is not part of the claim.

**Feasibility (provisional):** Training requires **≥14,000 clean admitted** examples; the 742 holdout tasks are authored separately and do not consume training supply. **Audit (current):** **53,676** raw candidates → **16,211** uniquely labeled exact-code targets + **34,247** review rows. **4,315** extra exact-code copies were removed across **3,543** duplicate groups. **996** of those groups had conflicting domain/area labels and were quarantined as **2,093** review rows, not 996 rows. *(Historical: 19,392 and 17,212 were intermediate noncanonical counts.)* Oracle admission on 2026-11-27 produced **15,014** clean examples, **1,014** above the 14,000 cap. Near-duplicate filtering and the other gates can still lower the count. If the clean count falls below 14,000, **reduce the 14,000 maximum** before sealing. Mandatory path: `python3 -m analysis seal-study` (then `build-prefixes` with admission receipt; `study-results` with sealed manifest). The seal directory is published by rename so a failed replacement does not delete the previous output first.

**Open blockers:** Real oracle runs; clean-unit feasibility recount; exact integer area holdout counts; 742 authored/sealed holdout tasks; shortlist tags/digests; selected-tokenizer counts; frozen hyperparameter and randomness values; Drivine confirmatory package/JVM oracles and ~20 pilot set; holdout manifest; scored confirmatory rows (**0**); Zenodo DOI.

## Mix (training list — admitted pool)

The training ordered list follows **admitted-pool** shares. It is not reweighted so that every area has the same count. The same shares apply at every prefix subject to the exhaustion rule in preregistration. The table below is the current **labeled-target** mix from `balance.json` (16,211 labeled rows), for planning only until admission and area counts are frozen. Holdout counts follow these shares but do not cap training supply.

| Area | Share of labeled targets |
|---|---:|
| Drivine query | 55.7% |
| Drivine generation | 17.9% |
| Drivine repair | 6.0% |
| Embabel integration | 5.4% |
| Drivine graph_rag | 4.9% |
| Embabel planning | 3.3% |
| Embabel transformation | 2.8% |
| Embabel generation | 2.0% |
| Drivine integration | 1.4% |
| Embabel repair | 0.5% |
| Embabel refactor | 0.1% |

A short prefix can contain no refactor example. That is a consequence of this mix. Refactor is still eligible for later prefixes when an admitted refactor example falls in the order.

The training example is a method. The enclosing type signature is stored with it as context. A whole type is kept when the file does not split into two methods. The pool is code. Prose is not an example.

## What is scored once

The 742 tasks are sealed before the first model output. Each of the six prefixes is scored on those tasks (with three training seeds per prefix). Adding a seventh size after seeing those scores is a new study. The guide is retrieval after training. It does not fill a prefix.

## Before authoring

1. Admit examples and author the 742 combined holdout tasks (371+371) per frozen area counts. Write the manifest hash before the first score.
2. Populate exact area counts, shortlist tags, and training hyperparameters in preregistration.
3. Upload the protocol to Zenodo before any holdout score.