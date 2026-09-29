# Paper calendar: 1 Nov 2026 → 31 Dec 2026

Ship a citable preprint that **proves or disproves** whether the local coding model is useful under a frozen evaluation contract. Negative results count. Overclaiming does not.

Companion docs:

- [citation-workflow.md](citation-workflow.md) — how citations are acquired, stored, and cited
- [paper/outline.md](paper/outline.md) — section skeleton and claim gates
- [paper/references/seed.bib](paper/references/seed.bib) — starter BibTeX (fill during W2)
- [research-plan.md](research-plan.md) — long research program (RAG / LoRA / A–D)
- [milestones.md](milestones.md) — production milestone order (do not skip)
- Upstream methods object: [`slm-setup` evaluation protocol](https://github.com/jmjava/slm-setup/blob/main/docs/evaluation-protocol.md)

---

## Venue decision (lock in Week 1)

| Option | Use when | Notes |
| --- | --- | --- |
| **Zenodo (primary)** | Always available; want a DOI by NYE | Reserve DOI before final PDF. Resource type: *Publication → Preprint*. Files immutable after Publish — version for fixes. |
| **TechRxiv (contingency)** | Submissions reopen before camera-ready | IEEE engineering/CS preprint server. **As of late 2026, submissions have been closed** during a platform transition (last visible uploads ~Mar 2026). Check [techrxiv.org](https://www.techrxiv.org/) in W1 and again in W8. Do not block the calendar on it. |
| **arXiv cs.SE / cs.AI (optional second)** | You have endorsement / institutional path | Strong discovery. Can deposit *after* Zenodo DOI exists and cite both as related identifiers. |

**Decision rule:** draft and typeset for **IEEE conference style** (`IEEEtran`, 2-column, ~6–8 pages). That package is acceptable on Zenodo and matches TechRxiv/IEEE norms if TechRxiv returns. Do not wait for a journal CFP.

**Zenodo package shape (target):**

1. `paper.pdf` — camera-ready preprint (DOI string already printed)
2. `paper-source.zip` — LaTeX + figures + `.bib` (or pointer to git tag)
3. `artifact-manifest.md` — git SHAs for `embabel-slm` and `slm-setup`, model tags/digests, corpus version, harness command lines
4. Optional: anonymized summary tables (JSON/CSV). **No** hostnames, `.env`, secrets, or raw completions unless scrubbed and intentional

License: prefer **CC BY 4.0** for the preprint PDF; keep code under the repo LICENSE; state both in Zenodo metadata.

---

## What this window can prove (scope lock)

### Paper v1 — ship by 31 Dec 2026 (required)

**Question:** When a premium agent delegates a bounded coding edit to a private local SLM over MCP, **does the model work**, and **which failure layer fires** when it does not?

**Methods object (already exists):** layered scorer in `slm-setup`
(`transport → format → structure → behavior`), fixture corpus, harness
(`pass@1` vs `pass@end`), apply-gate state machine.

**Evidence required by freeze date (Fri 5 Dec):**

| Evidence | Source | Gate |
| --- | --- | --- |
| Scorer correctness | Fixture / known-fail suite in CI | Must stay green |
| Live layer-conditional rates | Repeated `run_harness.py --backend live` on pinned tags | ≥3 independent live sessions, same corpus version |
| Prompt-contract effect | `whitespace_extract` vs `whitespace_extract_vague` | Same oracle, report structure Δ |
| Claim boundaries | Written limitations paragraph | Matches [evaluation-protocol.md](https://github.com/jmjava/slm-setup/blob/main/docs/evaluation-protocol.md) “may / may not claim” |

**Allowed verdicts:** works under contract / works only with repair-escalation / fails a named layer / inconclusive for lack of live N. All are publishable if measured.

**Forbidden claims in v1:** Embabel “expert” ability, Halo-only speedups, general coding SOTA, that a live Cursor session routed correctly, LoRA gains.

### Paper v2 seed — stretch only (do not block NYE)

If M1–M3 from [milestones.md](milestones.md) finish with a written A-vs-B (base vs retrieval) on the first 20 Embabel tasks, add a short **Results appendix** or a separate short note. Full A/B/C/D + LoRA is **after** NYE.

---

## Week-by-week plan

Dates assume week starts Monday. Treat each Friday as a hard checkpoint.

### W1 — 1–7 Nov · Scope, venue, bibliography machine

**Goals**

- Freeze Paper v1 claim sentence and non-claims (paste into [paper/outline.md](paper/outline.md)).
- Confirm Zenodo account + ORCID; reserve nothing yet (reserve DOI in W8).
- Recheck TechRxiv submission status; record date of check in this file’s changelog.
- Stand up citation stack (see [citation-workflow.md](citation-workflow.md)): Zotero (or JabRef) → Better BibTeX → `docs/paper/references/library.bib`.
- Create LaTeX skeleton under `docs/paper/src/` using `IEEEtran` conference mode (title/abstract placeholders only).

**Exit**

- One-page **claim freeze** committed.
- Empty `library.bib` + seed tags imported.
- Venue = Zenodo primary written in outline.

### W2 — 8–14 Nov · Formal citation acquisition

**Goals**

- Run the structured literature sweep in [citation-workflow.md](citation-workflow.md) (MCP agents, SLM-as-tool, code repair eval, RAG-for-code, PEFT coding models — only cite what the paper needs).
- Target **25–40** working bibliography entries for v1; mark each `must-cite` / `background` / `drop`.
- Prefer DOI → BibTeX from Crossref/DataCite; verify every URL resolves; prefer versioned arXiv IDs.
- Write Related Work bullet map: 1 sentence per cluster, 3–6 clusters.

**Exit**

- `library.bib` has ≥25 entries with DOI or stable URL.
- Related-work outline section filled (bullets, not prose yet).

### W3 — 15–21 Nov · Methods freeze + reproduce

**Goals**

- Freeze corpus version (git SHA of `slm-setup` eval suite).
- Freeze model tags: official Ollama library tags only; record digests.
- Reproduce fixture protocol cloud-safe; then schedule live sessions on the private host.
- Draft Methods: layers table, harness policy, what is stub vs live.
- Start Embabel M0/M1 only if it does not steal live-eval time from Paper v1.

**Exit**

- Methods draft complete enough that a stranger could re-run the fixture path.
- Live run calendar booked (who, which machine, which tags).

### W4 — 22–28 Nov · Collect results (light writing)

**Goals**

- Execute live harness runs; write dated notes (no hostnames/secrets).
- Build result tables: layer-conditional rates, `pass@1` / `pass@end`, escalation fraction, vague-vs-precise prompt Δ.
- Capture 2–4 anonymized failure exemplars (one per layer where possible).
- Thanksgiving week: prefer measurement over prose.

**Exit**

- Results tables exist as committed Markdown/CSV under `experiments/paper-v1/`.
- Go/no-go: enough live N to support a verdict? If no, schedule makeup runs in W5 and narrow claims.

### W5 — 29 Nov – 5 Dec · First full draft

**Goals**

- Write Intro, Methods, Results, Limitations in full sentences.
- Abstract last (150–200 words): problem → method → finding → boundary.
- Insert figures: system diagram (MCP bridge + layers), results bar/table.
- Freeze numbers: no quiet edits after this Friday without a version note.

**Exit**

- Complete draft PDF (rough typesetting OK).
- Claim freeze still true after seeing numbers (or claims revised *explicitly*).

### W6 — 6–12 Dec · Related work + polish

**Goals**

- Expand Related Work from the W2 map; every `must-cite` appears in text.
- Discussion: what failed, cheap interventions (prompt vs retrieval vs weights) per research-plan guiding principle.
- Copy-edit pass; check every number against `experiments/paper-v1/`.
- Stretch only: if Embabel A-vs-B exists, draft appendix; else omit.

**Exit**

- Near-final PDF; bibliography compiles; no unresolved `?` citations.

### W7 — 13–19 Dec · Internal review + artifact pack

**Goals**

- External-ish read: someone not the author marks overclaims.
- Build Zenodo artifact list; scrub logs.
- Diff claims against evaluation-protocol “may not claim” list.
- Prepare author metadata (ORCID, affiliation, keywords).

**Exit**

- Review notes addressed or explicitly deferred.
- `artifact-manifest.md` filled with SHAs and commands.

### W8 — 20–26 Dec · Camera-ready + deposit draft

**Goals**

- Reserve Zenodo DOI; put DOI on title page / footer; rebuild PDF.
- Upload draft record (Save draft, do **not** Publish yet).
- Final figure DPI/legibility check; IEEE column overflow check.
- Recheck TechRxiv; if open and desired, prepare parallel upload *after* Zenodo DOI exists.

**Exit**

- Zenodo draft with PDF + source + manifest; DOI reserved and printed.

### W9 — 27–31 Dec · Publish

**Goals**

- Final 30-minute claim audit.
- Publish Zenodo record → DOI resolves.
- Tag git repos (`paper-v1-zenodo`); link DOI in README.
- Optional: announce + open issues for Paper v2 (Embabel A/B/C/D).

**Exit**

- Live DOI. Paper either supports usefulness under contract or documents where it fails. Done.

---

## Parallel experiment track (does not own the calendar)

Keep milestone order. Paper v1 does not require LoRA.

| Window | Allowed embabel-slm work | Stop if |
| --- | --- | --- |
| W1–W3 | M0 claim page; M1 single baseline run | Blocks live MCP rates |
| W4–W6 | M2 runner; M3 retrieval A-vs-B on 20 tasks | Numbers not written down |
| W7–W9 | Write A-vs-B appendix only if table exists | Temptation to start M5 |

---

## Paper format checklist (IEEE-style preprint)

Use `IEEEtran` conference class unless a later venue forces otherwise.

| Element | Practice |
| --- | --- |
| Length | Aim 6–8 pages + refs; Zenodo has no hard page limit but short beats sprawling |
| Abstract | One paragraph, ≤250 words, no citations, no undefined acronyms |
| Keywords | 4–6: e.g. local LLM, MCP, code repair, evaluation, SLM |
| Structure | Intro → Related Work → Method → Experimental Setup → Results → Discussion → Limitations → Conclusion → Refs |
| Citations | IEEE numeric `[1]`; BibTeX via `IEEEtran` style |
| Figures | Vector or ≥300 dpi; captions below; every figure referenced in text |
| Tables | Layer rates and model configs; every table referenced |
| Reproducibility | SHAs, model tags/digests, prompts, seeds, hardware class (no LAN detail) |
| Ethics / safety | No secrets in artifacts; treat model output as untrusted (already product policy) |
| Negative results | Report layer failures; do not rename them as “qualitative insights” |

Suggested title pattern (pick one in W1):

- *Layered Evaluation of Local Coding SLMs Exposed as MCP Tools*
- *When Does a Private Coding SLM Help? Failure Layers under MCP Delegation*

---

## Claim freeze template (fill in W1)

```text
Claim: On corpus <id> @ sha <sha>, with models <tags>, under harness <policy>,
the local SLM achieves <pass@end / layer rates>, which <supports / does not support>
usefulness for <bounded task class>.

Non-claims: <list from evaluation-protocol>

Success definition (pre-registered): <e.g. behavior pass@end ≥ X on executable cases
without counting stub timings as GPU latency>
```

Paste the filled version into [paper/outline.md](paper/outline.md).

---

## Risk register

| Risk | Mitigation |
| --- | --- |
| TechRxiv still closed | Zenodo primary; check twice, never block |
| Not enough live GPU sessions | Narrow to fixture + fewer live cases; label inconclusive |
| Scope creep into LoRA | Hard stop: M5 after DOI |
| Citation pile without reading | `must-cite` cap 15; every cite has a one-line “used for” note in Zotero |
| Numbers drift after draft | Freeze Friday W5; later changes = new Zenodo version |
| Overclaim from one accepted retry | Report `pass@1` separate from `pass@end` |

---

## Changelog

| Date | Note |
| --- | --- |
| 2026-09-29 | Initial Nov–NYE calendar; Zenodo primary after TechRxiv submission outage reports |
