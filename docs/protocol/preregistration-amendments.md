# Pre-registration amendments

This file records changes to `docs/protocol/preregistration.md`. Amendments are appended below; each edit to the normative page must record old and new sha256 and a reason of at least 80 characters.

## Amendment

- date: 2026-11-26
- old_sha256: 3aa22226b3ec325c1ee5ebcf3f098a84b340fa68f44004db48c08701ec4ac602
- new_sha256: 9dd29f15ba1d013b79e525e9130793f87fb70999820b6a80fbecf46b63396690
- reason: Before any holdout task is authored, the confirmatory exam is one combined holdout of 742 tasks and the training sizes are the nested prefixes 500, 1000, 2000, 4000, 8000, and 16000 from starts 500, 1000, and 2000. Area labels stay on examples for the mix and are not separate powered exams.

## Amendment

- date: 2026-11-26
- old_sha256: 9dd29f15ba1d013b79e525e9130793f87fb70999820b6a80fbecf46b63396690
- new_sha256: a56c884dc588b24049adab0ee4005a97270bbc18dcfd97fa50e95f6d57cc0658
- reason: Final second-review sync, revised in place: independent 742 holdout ontology, canonical audit 53,676→16,211 labeled + 34,247 review, 996 conflicting-label groups (2,093 review rows), ≥16,000 clean-admitted gate, mandatory seal-study path, fixed compute and randomness controls, sampled secondary validation, exact power 0.783839, and honest blockers.

## Amendment

- date: 2026-11-27
- old_sha256: a56c884dc588b24049adab0ee4005a97270bbc18dcfd97fa50e95f6d57cc0658
- new_sha256: 3a298f7fc38d240d83d3236bea312bac12336fcfd921fcb54a27c8097c7c1d94
- reason: Oracle admission on 2026-11-27 produced 15,014 clean examples, short of 16,000 because refusals.yaml statements are specified compiler rejections. The maximum prefix and clean-admitted floor drop from 16,000 to 14,000 before holdout authoring, leaving 1,014 admitted examples above the cap for later rejects. The confirmatory contrast is 14,000 versus 500.
