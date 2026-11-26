# Plan: make the example-dose claim solid

The confirmatory claim is that examples written for each pre-registered area incrementally raise that area's holdout score. A mixed or random pool is not a dose. This page is the work required before any dose is scored. Normative numbers live in [preregistration.md](preregistration.md).

## What is already fixed

- One base model, chosen on the Embabel development split, then used on both domains.
- Examples are authored for exactly one area. Embabel areas: generation, repair, planning, transformation, refactor, integration. Drivine areas: generation, repair, query, graph-RAG, integration.
- Within an area the doses are nested. The middle dose is a prefix of that area's list. The per-area counts are still null and must be written before any example is authored.
- Each larger dose is compared with the previous dose on that area's tasks. Every area is in the Holm family (22 tests). A pooled mix is not the claim.
- The holdout is scored once. A dose chosen after those scores needs a new confirmation set.
- Retrieval and the host ceiling are references. They are not the dose.
- LoRA learns the admitted examples. The guide is an add-on after that training: it retrieves pages into the prompt of the already trained model (config D). Config B scores the guide on the untrained base as a reference. The guide does not fill an example dose.

## What is still weak

**742 tasks in each area is the 5-point sample.** That is 4,452 Embabel holdout tasks and 3,710 executable Drivine holdout tasks. The old mixed doses (0, 100, 500 and 0, 25, 100) are not the plan. Per-area example counts are still null. Each area is reported on its own. The study does not require all 22 tests to reject.

**No checked citation yet says that these dose counts should work.** The paired test is McNemar. The dose counts and the 5-point bar are choices in this protocol. Before Zenodo, add one read citation on score versus number of training examples. Do not copy dose counts out of that paper.

**The example pools do not exist as frozen subsets.** Embabel's 500 compiler-verified examples are a milestone, not a file. Drivine's 100 instruction pairs exist and are training material only. Neither pool has a frozen id list for the middle dose.

**The same holdout cannot be used to invent the next dose.** Development scoring may guide how examples are written. It may not pick the confirmatory subset after seeing holdout numbers.

## Closing the five gaps

Do these in order. A later step does not start by relaxing an earlier one.

1. **Success rule.** An area is proved when both of its dose steps reject after Holm correction across the 22 tests. Each area is reported. The study does not require all 22 rejections. This sentence is now in the pre-registration.
2. **Example counts.** Write one middle count and one full count into `counts_per_area`. Use the same pair for every area. The full count is at least twice the middle count. Do this before authoring. Drivine's existing 100 training pairs cannot fill five area doses. New area-authored examples are required.
3. **Admission checker.** `analysis/practices.py` admits an example or a holdout task only when it has one pre-registered area label, an executable oracle for that area, and a source pin, and it is not a near-duplicate of the other split. Within an area, the middle dose is the pre-fixed prefix of the full list. Reject anything that fails. Do not keep an item because a model liked it.
4. **Seal the holdouts.** Author the tasks for each area up to the locked per-area minimum. At a 5-point planning delta that minimum is 742 tasks in each area. Commit the manifest hash. Do not edit a task after the first model output.
5. **Public lock.** Write the official base-model shortlist into the protocol before any development score. Upload the protocol to Zenodo before any holdout score.

## What this paper will not add

A fourth dose. A non-nested "different 100." A retrieval pack standing in for examples. A claim that the confidence interval cleared 5 points unless the interval actually does.
