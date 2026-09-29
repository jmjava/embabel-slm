# Paper calendar: 1 Nov 2026 → 31 Mar 2027

Ship a citable preprint that **proves or disproves** whether the local coding model is useful under a frozen evaluation contract. Negative results count. Overclaiming does not. **Deadline: 31 March 2027** (not sooner).

Companion docs:

- [citation-workflow.md](citation-workflow.md) — how citations are acquired, stored, and cited
- [paper/outline.md](paper/outline.md) — section skeleton and claim gates
- [paper/references/seed.bib](paper/references/seed.bib) — starter BibTeX (fill during Nov)
- [research-plan.md](research-plan.md) — long research program (RAG / LoRA / A–D)
- [milestones.md](milestones.md) — production milestone order (do not skip)
- Upstream methods object: [`slm-setup` evaluation protocol](https://github.com/jmjava/slm-setup/blob/main/docs/evaluation-protocol.md)

---

## Venue decision (lock in early Nov)

| Option | Use when | Notes |
| --- | --- | --- |
| **Zenodo (primary)** | Always available; want a DOI by **31 Mar 2027** | Reserve DOI before final PDF. Resource type: *Publication → Preprint*. Files immutable after Publish — version for fixes. |
| **TechRxiv (contingency)** | Submissions reopen before camera-ready | IEEE engineering/CS preprint server. **As of late 2026, submissions have been closed** during a platform transition (last visible uploads ~Mar 2026). Check [techrxiv.org](https://www.techrxiv.org/) in Nov, Jan, and mid-Mar. Do not block the calendar on it. |
| **arXiv cs.SE / cs.AI (optional second)** | You have endorsement / institutional path | Strong discovery. Can deposit *after* Zenodo DOI exists and cite both as related identifiers. |

**Decision rule:** draft and typeset for **IEEE conference style** (`IEEEtran`, 2-column, ~6–10 pages). That package is acceptable on Zenodo and matches TechRxiv/IEEE norms if TechRxiv returns. Do not wait for a journal CFP.

**Zenodo package shape (target):**

1. `paper.pdf` — camera-ready preprint (DOI string already printed)
2. `paper-source.zip` — LaTeX + figures + `.bib` (or pointer to git tag)
3. `artifact-manifest.md` — git SHAs for `embabel-slm` and `slm-setup`, model tags/digests, corpus version, harness command lines
4. Optional: anonymized summary tables (JSON/CSV). **No** hostnames, `.env`, secrets, or raw completions unless scrubbed and intentional

License: prefer **CC BY 4.0** for the preprint PDF; keep code under the repo LICENSE; state both in Zenodo metadata.

---

## What this window can prove (scope lock)

With ~5 months, the shippable paper can cover **both** the MCP tool eval and the first Embabel specialization comparison. Still no requirement to finish full production (M7).

### Paper v1 — ship by 31 Mar 2027 (required)

**Core question:** Does a private local coding SLM work for bounded developer tasks, and what intervention (prompt contract, retrieval, or weights) actually moves the needle?

**Part A — MCP layered eval** (methods already exist in `slm-setup`)

When a premium agent delegates a bounded coding edit to a private local SLM over MCP, **does the model work**, and **which failure layer fires** when it does not?

Evidence gates (freeze target: **Fri 30 Jan 2027** for Part A numbers):

| Evidence | Source | Gate |
| --- | --- | --- |
| Scorer correctness | Fixture / known-fail suite in CI | Must stay green |
| Live layer-conditional rates | Repeated `run_harness.py --backend live` on pinned tags | ≥3 independent live sessions, same corpus version |
| Prompt-contract effect | `whitespace_extract` vs `whitespace_extract_vague` | Same oracle, report structure Δ |
| Claim boundaries | Written limitations paragraph | Matches evaluation-protocol “may / may not claim” |

**Part B — Embabel A-vs-B** (milestone order; required for v1 body if Part A is thin, preferred either way)

| Evidence | Milestone | Gate |
| --- | --- | --- |
| Frozen general + Embabel bars | M0 | One page that later runs cannot quietly edit |
| Reproducible baseline on 20 tasks | M1–M2 | Run id with model, quant, prompt, commit, scores; known-bad fixture fails |
| Base vs retrieval on same 20 | M3 | Written A-vs-B table (compile, hallucination, full success) |

**Part C — stretch inside the March deadline (do not block DOI)**

| Stretch | Milestone | Rule |
| --- | --- | --- |
| Holdout ≥100 Embabel tasks | M4 | Include if frozen by **Fri 13 Feb**; else omit |
| One LoRA/QLoRA + A/B/C/D table | M5 | Only if M3 gap is clearly “weights, not retrieval”; start by mid-Feb or cut |

**Allowed verdicts:** works under contract / works only with repair-escalation / fails a named layer / retrieval closes most of the Embabel gap / weights still needed / inconclusive. All publishable if measured.

**Forbidden claims:** Embabel “expert” without holdout; Halo-only speedups; general coding SOTA; that a live Cursor session routed correctly; LoRA gains without the A/B/C/D table.

---

## Phase overview

| Phase | Dates | Focus | Hard exit |
| --- | --- | --- | --- |
| **P0 Setup** | 1–14 Nov 2026 | Claim freeze, venue, citation machine, LaTeX skeleton | Claim page + Zotero live |
| **P1 Literature** | 15 Nov – 5 Dec 2026 | Citation acquisition + Related Work map | ≥25 bib entries; clusters mapped |
| **P2 MCP measure** | 6 Dec 2026 – 9 Jan 2027 | Corpus/model freeze; live harness rates | Part A tables in `experiments/paper-v1/` |
| **P3 Embabel A–B** | 10 Jan – 6 Feb 2027 | M0→M3; baseline vs retrieval | Written A-vs-B on 20 tasks |
| **P4 Optional depth** | 7–27 Feb 2027 | M4 and/or one M5 adapter **or** deepen Part A N | Go/no-go Fri 27 Feb: freeze *all* paper numbers |
| **P5 Draft** | 28 Feb – 13 Mar 2027 | Full prose + figures | Complete draft PDF |
| **P6 Camera-ready** | 14–27 Mar 2027 | Review, artifacts, reserve DOI | Zenodo draft ready |
| **P7 Publish** | 28–31 Mar 2027 | Publish DOI | Live DOI |

Fridays remain checkpoints. Holiday weeks (Thanksgiving, late Dec / New Year) favor measurement and reading over forced prose.

---

## Week-by-week plan

Dates assume week starts Monday.

### W1 — 1–7 Nov · Scope, venue, bibliography machine

**Goals**

- Freeze Paper v1 claim sentence and non-claims (paste into [paper/outline.md](paper/outline.md)).
- Confirm Zenodo account + ORCID; reserve nothing yet (reserve DOI in mid-Mar).
- Recheck TechRxiv submission status; record date of check in this file’s changelog.
- Stand up citation stack (see [citation-workflow.md](citation-workflow.md)): Zotero (or JabRef) → Better BibTeX → `docs/paper/references/library.bib`.
- Create LaTeX skeleton under `docs/paper/src/` using `IEEEtran` conference mode (title/abstract placeholders only).

**Exit:** claim freeze committed; seed bib imported; Zenodo = primary venue.

### W2 — 8–14 Nov · Citation acquisition starts

**Goals**

- Run structured literature sweep (MCP agents, SLM-as-tool, code repair eval, RAG-for-code, PEFT coding models).
- Target **25–40** working bibliography entries; mark `must-cite` / `background` / `drop`.
- Prefer DOI → BibTeX from Crossref/DataCite; verify URLs; prefer versioned arXiv IDs.

**Exit:** `library.bib` ≥15 entries underway; search-log started.

### W3 — 15–21 Nov · Literature + Related Work map

**Goals**

- Finish toward ≥25 entries with DOI or stable URL.
- Write Related Work bullet map: 1 sentence per cluster, 3–6 clusters (MCP / code eval / local SLM / RAG / PEFT).
- Draft M0 bars (general floor + Embabel gain) if not already frozen.

**Exit:** Related-work outline filled (bullets); M0 draft exists.

### W4 — 22–28 Nov · Methods draft (Thanksgiving: light)

**Goals**

- Freeze `slm-setup` corpus SHA intent (may re-pin once more before P2 exit).
- Draft Methods: layers table, harness policy, stub vs live.
- Prefer reading + light measurement over heavy writing this week.

**Exit:** Methods outline complete enough to expand later.

### W5 — 29 Nov – 5 Dec · Literature gate

**Goals**

- Clear `unread` must-cites; cap `must-cite` ≤15 for Part A, allow +10 for Embabel/RAG/LoRA clusters.
- Confirm official Ollama tags for live work; record planned digests.

**Exit:** citation W2/W3 gate closed; model shortlist written.

### W6 — 6–12 Dec · MCP live campaign begins

**Goals**

- Pin corpus SHA; pin model tags + digests.
- Run fixture protocol cloud-safe; first live harness sessions.
- Book remaining live slots through early January.

**Exit:** at least one live session logged (scrubbed notes).

### W7 — 13–19 Dec · Live rates continue

**Goals**

- Repeat live runs; build layer-conditional and `pass@1` / `pass@end` tables.
- Capture scrubbed failure exemplars (one per layer where possible).
- Start Embabel M1 if live campaign is on track (single baseline run).

**Exit:** draft Part A tables in `experiments/paper-v1/`.

### W8 — 20–26 Dec · Holiday measurement window

**Goals**

- Makeup live runs if N is low; do not force prose.
- Optional: Embabel pin + first 20-task scaffolding.

**Exit:** go/no-go note: Part A N sufficient by mid-Jan or narrow claims.

### W9 — 27 Dec 2026 – 2 Jan 2027 · Pause / light catch-up

**Goals**

- No new scope. Optional citation tidy or log scrubbing.

**Exit:** calendar still on track for P2 exit.

### W10 — 3–9 Jan · Part A freeze

**Goals**

- Finish ≥3 live sessions; freeze Part A numbers (or label inconclusive explicitly).
- Prompt-contract Δ table finalized.
- Embabel M0 committed if not already.

**Exit:** Part A tables frozen **or** written “inconclusive / limited N” claim revision.

### W11 — 10–16 Jan · Embabel baseline (M1–M2)

**Goals**

- Install/validate one 7B–14B official tag on current host.
- Pin Embabel commit; score first 20 tasks; isolated compile/test runner.
- Keep known-bad fixture; show it fails.

**Exit:** baseline run id saved under `experiments/`.

### W12 — 17–23 Jan · Retrieval build (M3 start)

**Goals**

- Ingest Guide / DICE / docs / learning / cookbook / pattern cards for retrieval.
- Re-run the **same** 20 tasks with retrieval.

**Exit:** raw A and B outputs on disk (not overwritten).

### W13 — 24–30 Jan · A-vs-B writeup

**Goals**

- Record compile rate, hallucinated APIs, full success for base vs retrieval.
- Decide in writing: remaining gap is prompting, retrieval, or weights.
- Recheck TechRxiv status.

**Exit:** M3 exit met — written A-vs-B result.

### W14 — 31 Jan – 6 Feb · Holdout vs adapter decision

**Goals**

- If expanding: start M4 toward 100 holdout tasks **or**
- If M3 says weights: sketch one LoRA/QLoRA plan (data pins, not training yet) **or**
- If deepening Part A: more live N / harder suite rates.

**Exit:** written choice for P4 (M4 / M5 / deepen-A / none).

### W15 — 7–13 Feb · Optional depth execution

**Goals**

- Execute the W14 choice. Do not start two heavy tracks at once.
- Begin Results section bullets from frozen Part A + A-vs-B.

**Exit:** mid-P4 progress note.

### W16 — 14–20 Feb · Optional depth continued

**Goals**

- Finish optional M4 sample or first adapter run if chosen.
- If adapter: score A/B/C/D on locked tasks; keep only if Embabel rises and M0 floor holds.

**Exit:** stretch results in or explicitly cut.

### W17 — 21–27 Feb · **All-numbers freeze**

**Goals**

- Freeze every number that will appear in the PDF.
- Cut anything not table-ready. No quiet post-freeze edits without a version note.
- Outline final section list (drop unused stretch).

**Exit:** numbers freeze Friday 27 Feb 2027.

### W18 — 28 Feb – 6 Mar · Full draft

**Goals**

- Write Intro, Methods, Setup, Results, Discussion, Limitations in full sentences.
- Abstract last (150–200 words).
- Figures: MCP+layers pipeline; Part A bars; Embabel A-vs-B table/figure.

**Exit:** complete draft PDF (rough typesetting OK).

### W19 — 7–13 Mar · Related work + polish

**Goals**

- Expand Related Work; every `must-cite` appears in text.
- Copy-edit; check every number against `experiments/paper-v1/`.
- Bibliography compiles; no unresolved citation keys.

**Exit:** near-final PDF.

### W20 — 14–20 Mar · Internal review + artifacts

**Goals**

- External-ish read for overclaims.
- Build Zenodo artifact list; scrub logs.
- Diff claims vs evaluation-protocol “may not claim.”
- Author metadata (ORCID, affiliation, keywords).

**Exit:** `artifact-manifest.md` filled; review notes addressed or deferred in writing.

### W21 — 21–27 Mar · Camera-ready + Zenodo draft

**Goals**

- Reserve Zenodo DOI; print on title page/footer; rebuild PDF.
- Upload draft (Save draft — do **not** Publish yet).
- Final figure/column checks; recheck TechRxiv for optional parallel deposit.

**Exit:** Zenodo draft complete; DOI reserved and printed.

### W22 — 28–31 Mar · Publish

**Goals**

- Final claim audit.
- Publish Zenodo → DOI resolves.
- Tag git (`paper-v1-zenodo`); link DOI in README.
- Open follow-ups (M6/M7 or journal expansion) as issues, not silent scope.

**Exit:** live DOI by **31 March 2027**.

---

## Parallel track rules

Keep milestone order. Do not start M5 because writing feels slow.

| Phase | Allowed embabel-slm work | Stop if |
| --- | --- | --- |
| P0–P1 | M0 only | Blocks citation gate |
| P2 | M1 light only after first live MCP session | Blocks Part A N |
| P3 | M1–M3 required path | Skipping runner / overwriting runs |
| P4 | M4 or one M5 **or** neither | Starting M5 without written M3 gap |
| P5–P7 | Writing and artifacts only | New experiments after 27 Feb freeze |

---

## Paper format checklist (IEEE-style preprint)

Use `IEEEtran` conference class unless a later venue forces otherwise.

| Element | Practice |
| --- | --- |
| Length | Aim 6–10 pages + refs (two result threads may need the upper end) |
| Abstract | One paragraph, ≤250 words, no citations, no undefined acronyms |
| Keywords | 4–6: e.g. local LLM, MCP, code repair, evaluation, SLM, RAG |
| Structure | Intro → Related Work → Method → Experimental Setup → Results → Discussion → Limitations → Conclusion → Refs |
| Citations | IEEE numeric `[1]`; BibTeX via `IEEEtran` style |
| Figures | Vector or ≥300 dpi; captions below; every figure referenced in text |
| Tables | Layer rates, Embabel A-vs-B, model configs |
| Reproducibility | SHAs, model tags/digests, prompts, seeds, hardware class (no LAN detail) |
| Ethics / safety | No secrets in artifacts; treat model output as untrusted |
| Negative results | Report layer / retrieval failures honestly |

Suggested title patterns (pick in W1; revise after A-vs-B):

- *Layered Evaluation of Local Coding SLMs Exposed as MCP Tools*
- *When Does a Private Coding SLM Help? Failure Layers and Retrieval on Embabel Tasks*

---

## Claim freeze template (fill in W1; revise after 27 Feb if numbers demand it)

```text
Claim: On corpus <id> @ sha <sha>, with models <tags>, under harness <policy>,
the local SLM achieves <pass@end / layer rates>, which <supports / does not support>
usefulness for <bounded task class>.

Embabel (if included): On pinned commit <sha>, base vs retrieval yields <Δ metrics>,
so the remaining gap is <prompt | retrieval | weights>.

Non-claims: <list from evaluation-protocol + no expert Embabel without holdout>

Success definition (pre-registered): <e.g. behavior pass@end ≥ X; Embabel full-success
lift under retrieval ≥ Y; pass@1 reported separately from pass@end>
```

Paste into [paper/outline.md](paper/outline.md).

---

## Risk register

| Risk | Mitigation |
| --- | --- |
| TechRxiv still closed | Zenodo primary; check in Nov/Jan/Mar; never block |
| Not enough live GPU sessions | Use Dec–early Jan makeup weeks; narrow Part A claims |
| Embabel M3 slips past early Feb | Ship Part A + partial baseline; do not invent RAG numbers |
| Scope creep into unfinished LoRA | Hard cut Fri 27 Feb; M5 only with written M3 gap |
| Citation pile without reading | `must-cite` caps; every cite has `used_for` in Zotero |
| Numbers drift after draft | Freeze Fri 27 Feb; later changes = new Zenodo version |
| Overclaim from one accepted retry | Report `pass@1` separate from `pass@end` |

---

## Changelog

| Date | Note |
| --- | --- |
| 2026-09-29 | Initial Nov–NYE calendar; Zenodo primary after TechRxiv submission outage reports |
| 2026-09-29 | Deadline moved to **31 Mar 2027**; phased P0–P7 plan; Embabel A-vs-B in required path; M4/M5 stretch inside window |
