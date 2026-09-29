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

**Forbidden claims:** Embabel “expert” without holdout; Halo-only speedups without a paired downstairs baseline when claiming a host upgrade; general coding SOTA; that a live Cursor session routed correctly; LoRA gains without the A/B/C/D table; any live rate implied to run on the IDE workstation.

---

## Hardware lab (three hosts)

**Work order matches `slm-setup`:** Phase 3 live measurement on a private GPU, then **T12 Part A (downstairs) first**, then Halo/395 only after downstairs is a known path (on, or explicitly abandoned). Do not start Halo bring-up as the first November engineering task.

Home-lab split (public-safe names only — no hostnames/LAN in commits):

| Role | Machine | Role in the paper |
| --- | --- | --- |
| **Workstation** | IDE + `local-coding-slm` MCP | Agent/MCP only. **No paper inference** — local Ollama on this machine is a non-starter. |
| **Downstairs** | Second PC — Windows + Ubuntu WSL2 + NVIDIA (**RTX 3060** and **RTX 4080-class**) + Ollama | **First hardware work** and **only pre-Halo inference**. Clear T12 Part A. Prefer **4080-class** for paper live rates; 3060 OK for smoke / light tags. |
| **Halo / 395** | Ryzen AI Max+ 395 (acquire ~Black Friday) | **After** downstairs is measuring. Preferred paper host once A13 is green. |

Only **one** inference host is active at a time (`OLLAMA_BASE_URL` via localhost or SSH forward). MCP tool names never change. See [downstairs-wsl-gpu.md](https://github.com/jmjava/slm-setup/blob/main/examples/downstairs-wsl-gpu.md) and [halo-ryzen-ai.md](https://github.com/jmjava/slm-setup/blob/main/examples/halo-ryzen-ai.md).

### Timeline

| Window | Active inference host | What runs |
| --- | --- | --- |
| **1–14 Nov (first work)** | **Downstairs** | Power on, SSH forward, A4, first scrubbed live harness rows — this unblocks Phase 3 measure |
| 15–21 Nov | Downstairs | Continue Part A live N; citations/Methods in parallel |
| ~22–28 Nov (BF) | Downstairs stays the live path; **395 arrives** | Unbox only — do not abandon downstairs mid-campaign |
| 29 Nov – 12 Dec | Downstairs for rates; Halo bring-up in parallel | A13 on 395; switch paper host only when green |
| Mid-Dec → Mar | Halo if A13 green; else **keep downstairs** | Part A freeze, Embabel M1–M3, optional M5 |
| Through March | Log host class every row | Never mix 3060 / 4080 / Halo timings in one average |

### Rules

- **Downstairs first.** Halo is not the November kickoff. **Never** plan paper live rows on the IDE workstation — it has no usable inference GPU.
- Do **not** delay claim freeze or literature waiting on Halo; **do** clear downstairs before calling Phase 3 “measured.”
- Do **not** claim Halo latency/memory from downstairs runs.
- Downstairs was previously **blocked on host power** — first exit is power-on + SSH + one live row (prefer 4080-class for that row).
- If the 395 slips past mid-December, **Part A + M1–M3 stay on downstairs**; Halo becomes a systems appendix — DOI still 31 Mar.
- Paper Setup: GPU **class** only (3060 / 4080-class / 395-class); no hostname, LAN, or purchase detail.
- Results tables: `host_class` ∈ `{downstairs-3060, downstairs-4080, halo-395}` (no `workstation` inference class).

### Downstairs clear checklist (first work — target exit: Fri 14 Nov)

1. Host powered when needed; treat “no route” as host down.
2. Ollama on WSL localhost; official starter tags; `ollama ps` after one chat.
3. Workstation SSH local forward; `.env` → forwarded loopback URL.
4. A4-style check: workstation reaches model through SSH; unauthorized LAN client does not.
5. One scrubbed live harness or `run_eval.py --live` row with `host_class=downstairs-4080` (or `downstairs-3060` if that is all that is up).

### Halo bring-up checklist (after downstairs is clear — target exit: Fri 12 Dec)

1. Box powered; Linux usable; NVMe fast path confirmed.
2. Ollama install; note AMD backend actually used (ROCm or Vulkan).
3. Pull official starter tags only; short chat confirms accelerated placement.
4. Workstation `ssh -L` → Halo localhost:11434; gitignored `.env` points at the forward.
5. Re-run `check_deployment_safety.py` + acceptance A1–A7, A11–A12; record A13.
6. One scrubbed Halo smoke row in dated notes.

---

## Phase overview

| Phase | Dates | Focus | Hard exit |
| --- | --- | --- | --- |
| **P0 Setup** | 1–14 Nov 2026 | Claim freeze + **downstairs first** (T12 Part A clear + first live rows) | Downstairs smoke on corpus; claim page; Zotero |
| **P1 Literature** | 15 Nov – 5 Dec 2026 | Citations + Related Work; downstairs Part A N; **395 ~BF** (unbox only) | ≥25 bib entries; live N growing on downstairs |
| **P2 MCP measure** | 6 Dec 2026 – 9 Jan 2027 | Finish Part A on downstairs; switch to Halo only if A13 green | Part A tables frozen |
| **P3 Embabel A–B** | 10 Jan – 6 Feb 2027 | M0→M3 on paper host (Halo preferred) | Written A-vs-B on 20 tasks |
| **P4 Optional depth** | 7–27 Feb 2027 | M4 and/or one M5 **or** deepen Part A N | Go/no-go Fri 27 Feb: freeze *all* paper numbers |
| **P5 Draft** | 28 Feb – 13 Mar 2027 | Full prose + figures | Complete draft PDF |
| **P6 Camera-ready** | 14–27 Mar 2027 | Review, artifacts, reserve DOI | Zenodo draft ready |
| **P7 Publish** | 28–31 Mar 2027 | Publish DOI | Live DOI |

Fridays remain checkpoints. **W1–W2 downstairs first** per slm-setup. Thanksgiving / Black Friday week is for receiving the 395 only after downstairs is already measuring. Late Dec / New Year favor measurement over writing.

---

## Week-by-week plan

Dates assume week starts Monday.

### W1 — 1–7 Nov · Downstairs first + claim freeze

**Goals**

- **First engineering work:** downstairs power, WSL Ollama on **4080-class** (3060 secondary), workstation `ssh -L`, A4-style check (T12 Part A). IDE-machine Ollama is out of scope.
- Freeze Paper v1 claim sentence and non-claims (paste into [paper/outline.md](paper/outline.md)).
- Confirm Zenodo account + ORCID; reserve nothing yet (reserve DOI in mid-Mar).
- Recheck TechRxiv submission status; record date of check in this file’s changelog.
- Stand up citation stack (see [citation-workflow.md](citation-workflow.md)): Zotero (or JabRef) → Better BibTeX → `docs/paper/references/library.bib`.
- Create LaTeX skeleton under `docs/paper/src/` using `IEEEtran` conference mode (title/abstract placeholders only).

**Exit:** downstairs reachable through SSH forward **or** written blocker; claim freeze committed; seed bib imported.

### W2 — 8–14 Nov · Downstairs live smoke + citations

**Goals**

- Complete **downstairs clear checklist**; land first scrubbed live harness / `run_eval.py --live` row on **4080-class** when possible (`host_class=downstairs-4080`).
- Run structured literature sweep (MCP agents, SLM-as-tool, code repair eval, RAG-for-code, PEFT coding models).
- Target **25–40** working bibliography entries; mark `must-cite` / `background` / `drop`.
- Prefer DOI → BibTeX from Crossref/DataCite; verify URLs; prefer versioned arXiv IDs.

**Exit:** T12 Part A unblocked with at least one live row **or** explicit abandonment note; `library.bib` ≥15 entries underway.

### W3 — 15–21 Nov · Literature + Related Work map

**Goals**

- Finish toward ≥25 entries with DOI or stable URL.
- Write Related Work bullet map: 1 sentence per cluster, 3–6 clusters (MCP / code eval / local SLM / RAG / PEFT).
- Draft M0 bars (general floor + Embabel gain) if not already frozen.

**Exit:** Related-work outline filled (bullets); M0 draft exists.

### W4 — 22–28 Nov · Black Friday / 395 arrive (Thanksgiving: light prose)

**Goals**

- **Hardware:** order/receive Ryzen AI Max+ 395 (Halo-class) around Black Friday; unbox; get a bootable Linux + disk layout. Do not start paper training on day one.
- Keep **downstairs** available — do not tear down the SSH forward mid Part A.
- Freeze `slm-setup` corpus SHA intent (may re-pin once more before P2 exit).
- Draft Methods: layers table, harness policy, stub vs live.
- Prefer reading + hardware logistics over heavy writing this week.

**Exit:** Methods outline ready; box **in hand or slip date written** (if slip → Part A stays on downstairs).

### W5 — 29 Nov – 5 Dec · Literature gate + Halo bring-up

**Goals**

- Clear `unread` must-cites; cap `must-cite` ≤15 for Part A, allow +10 for Embabel/RAG/LoRA clusters.
- Confirm official Ollama tags for live work; record planned digests.
- **Halo:** Ollama + AMD backend validation; starter tags; accelerated placement check; start SSH forward from workstation (see Halo checklist above).
- Continue downstairs live rows if Halo is not A13-green yet.

**Exit:** citation gate closed; model shortlist written; Halo smoke **or** explicit “paper host = downstairs” note.

### W6 — 6–12 Dec · MCP live campaign (Halo if A13 green, else downstairs)

**Goals**

- Pin corpus SHA; pin model tags + digests.
- Finish Halo A1–A7 / A11–A13 if not done; point gitignored `.env` at the active SSH forward.
- Run fixture protocol cloud-safe; first live harness sessions on the **paper host**.
- Book remaining live slots through early January.

**Exit:** at least one live session logged (scrubbed notes) with `host_class` recorded.

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

- Install/validate one 7B–14B official tag on the **paper host** (Halo if A13 green; else downstairs 4080-class — say which GPU).
- Pin Embabel commit; score first 20 tasks; isolated compile/test runner.
- Keep known-bad fixture; show it fails.

**Exit:** baseline run id saved under `experiments/` with host class.

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
| P0–P1 | **Downstairs first** (T12 Part A + live rows); M0 text; Halo unbox only after BF | Starting Halo before downstairs is cleared |
| P2 | M1 light only after downstairs Part A N exists | Blocks Part A N; mixing hosts in one table |
| P3 | M1–M3 required path on paper host | Skipping runner / overwriting runs |
| P4 | M4 or one M5 **or** neither (M5 prefers Halo 128 GB class) | Starting M5 without written M3 gap |
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
| 395 box late / DOA / ROCm painful | Part A + M1–M3 on downstairs 4080-class; Halo as appendix; DOI still 31 Mar |
| Downstairs still powered off | Clear in W1–W2; **blocks** paper live rates (no workstation fallback) |
| Not enough live GPU sessions | Use Dec–early Jan makeup weeks; narrow Part A claims |
| Embabel M3 slips past early Feb | Ship Part A + partial baseline; do not invent RAG numbers |
| Scope creep into unfinished LoRA | Hard cut Fri 27 Feb; M5 only with written M3 gap |
| Citation pile without reading | `must-cite` caps; every cite has `used_for` in Zotero |
| Numbers drift after draft | Freeze Fri 27 Feb; later changes = new Zenodo version |
| Overclaim from one accepted retry | Report `pass@1` separate from `pass@end` |
| Mixing host timings | `host_class` on every results row; never average across 3060 / 4080 / Halo |

---

## Changelog

| Date | Note |
| --- | --- |
| 2026-09-29 | Initial Nov–NYE calendar; Zenodo primary after TechRxiv submission outage reports |
| 2026-09-29 | Deadline moved to **31 Mar 2027**; phased P0–P7 plan; Embabel A-vs-B in required path; M4/M5 stretch inside window |
| 2026-09-29 | Plan Ryzen AI Max+ 395 acquisition ~Black Friday; workstation until Halo A13; host column on all live rows |
| 2026-09-29 | Three-host lab: workstation + downstairs NVIDIA/WSL (pre-395) + Halo; clear downstairs T12 Part A in early Nov |
| 2026-09-29 | Align with slm-setup: downstairs is **first work**; Halo only after T12 Part A is a known path |
| 2026-09-29 | IDE workstation = MCP only (inference non-starter); downstairs GPUs are RTX 3060 + RTX 4080-class |
