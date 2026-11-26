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

**Part B — Embabel** (milestone order; required for v1 body if Part A is thin, preferred either way)

| Evidence | Milestone | Gate |
| --- | --- | --- |
| Frozen general + Embabel bars | M0 | One page that later runs cannot quietly edit |
| Reproducible baseline on 20 tasks | M1–M2 | Run id with model, quant, prompt, commit, scores; known-bad fixture fails |
| Base vs retrieval on same 20 | M3 | Written A-vs-B table (compile, hallucination, full success) |
| Holdout ≥200 + confirmatory arms table | M4–M5 | Manifest hash before scoring; one pass per config; cells missing at freeze → **not run** |

**Part C — Drivine** (parallel track beside Embabel in P3–P4; same numbers freeze)

| Evidence | Milestone | Gate |
| --- | --- | --- |
| Executable runner + pilot (~20) | D1–D2 | Pilot never confirmatory; harness records Drivine doc + package pins |
| Retrieval before adapter | D3 | Same 20 pilot tasks; written A-vs-B |
| Holdout ≥100 executable + one Drivine LoRA | D4–D5 | Same S/M/L tags as Embabel; per-domain adapter only; hash before scoring; missing at **Fri 27 Feb 2027** → **not run** |

**Allowed verdicts:** works under contract / works only with repair-escalation / fails a named layer / retrieval closes most of the Embabel gap / weights still needed / inconclusive. All publishable if measured.

**Forbidden claims:** Embabel “expert” without holdout; downstairs-vs-Halo speedups without paired rows when claiming a host upgrade; general coding SOTA; that a live Cursor session routed correctly; LoRA gains without the A/B/C/D table; any live rate implied to run on the IDE workstation.

---

## Hardware lab (three hosts)

**Host switch (25 Nov 2026):** the GEEKOM **Halo / Ryzen AI Max+ 395** is the **primary paper inference host**. Downstairs NVIDIA is **fallback only** if Halo Ollama or AMD acceleration fails. Do not wait on downstairs power to start Phase 3 live measurement.

Home-lab split (public-safe names only — no hostnames/LAN in commits):

| Role | Machine | Role in the paper |
| --- | --- | --- |
| **Workstation** | IDE + `local-coding-slm` MCP | Agent/MCP only. **No paper inference** — local Ollama on this machine is a non-starter. |
| **Halo / 395 (GEEKOM)** | Ryzen AI Max+ 395, Radeon 8060S-class, 128 GB unified | **Primary paper host.** Phase 3 live rates and Embabel M1–M3 inference. `host_class=halo-395`. |
| **Downstairs** | Second PC — Windows + Ubuntu WSL2 + NVIDIA (**RTX 3060** / **RTX 4080-class**) | **Fallback** if Halo is down or unaccelerated. Prefer 4080-class. Never average with Halo rows. |

Only **one** inference host is active at a time (`OLLAMA_BASE_URL` via localhost or SSH forward). MCP tool names never change. See [halo-ryzen-ai.md](https://github.com/jmjava/slm-setup/blob/main/examples/halo-ryzen-ai.md) and [downstairs-wsl-gpu.md](https://github.com/jmjava/slm-setup/blob/main/examples/downstairs-wsl-gpu.md).

### Timeline

| Window | Active inference host | What runs |
| --- | --- | --- |
| **Late Nov 2026 (now)** | **Halo** | Ubuntu + Ollama on Halo; SSH forward; A13; first scrubbed live harness rows (`host_class=halo-395`) |
| Dec 2026 – early Jan 2027 | Halo | Part A live N; Embabel M1 scaffolding |
| Mid-Jan → Mar | Halo (downstairs only if Halo fails) | Part A freeze, Embabel M1–M3, optional M5 |
| Through March | Log host class every row | Never mix downstairs / Halo timings in one average |

### Rules

- **Halo first for paper rows.** **Never** plan paper live rows on the IDE workstation.
- Do **not** claim downstairs latency/memory from Halo runs (or the reverse).
- If Halo ROCm/Vulkan placement fails, fall back to downstairs and label rows `downstairs-4080` / `downstairs-3060`; DOI still 31 Mar.
- Paper Setup: GPU **class** only (395-class / 4080-class / 3060); no hostname, LAN, or purchase detail.
- Results tables: `host_class` ∈ `{halo-395, downstairs-4080, downstairs-3060}` (no `workstation` inference class). Prefer a Halo-only Part A freeze when A13 is green.

### Halo bring-up checklist (primary — target: immediate)

1. Box powered; Linux usable; NVMe fast path confirmed.
2. Ollama install; note AMD backend actually used (ROCm or Vulkan).
3. Pull official starter tags only; short chat confirms accelerated placement.
4. Workstation `ssh -L` → Halo localhost:11434; gitignored `.env` points at the forward.
5. Re-run `check_deployment_safety.py` + acceptance A1–A7, A11–A12; record A13.
6. One scrubbed Halo smoke row in dated notes with `host_class=halo-395`.

### Downstairs fallback checklist (only if Halo cannot serve live rates)

1. Host powered when needed; treat “no route” as host down.
2. Ollama on WSL localhost; official starter tags; `ollama ps` after one chat.
3. Workstation SSH local forward; `.env` → forwarded loopback URL.
4. A4-style check: workstation reaches model through SSH; unauthorized LAN client does not.
5. Scrubbed live rows with `host_class=downstairs-4080` (or `downstairs-3060`).

---

## Phase overview

| Phase | Dates | Focus | Hard exit |
| --- | --- | --- | --- |
| **P0 Setup** | 1–14 Nov 2026 | Claim freeze; **Halo bring-up** (A13 + first live rows) | Halo smoke on corpus; claim page; Zotero |
| **P1 Literature** | 15 Nov – 5 Dec 2026 | Citations + Related Work; Halo Part A N | ≥25 bib entries; live N growing on Halo |
| **P2 MCP measure** | 6 Dec 2026 – 9 Jan 2027 | Finish Part A on Halo (`host_class=halo-395`) | Part A tables frozen |
| **P3 Embabel + Drivine setup** | 10 Jan – 6 Feb 2027 | M0→M3; D1 harness + pilot if ready | Written Embabel A-vs-B; Drivine pilot exploratory |
| **P4 Holdout depth** | 7–27 Feb 2027 | M4–M5 and/or D4–D5 **or** deepen Part A N | Go/no-go Fri 27 Feb: freeze *all* paper numbers; absent cells **not run** |
| **P5 Draft** | 28 Feb – 13 Mar 2027 | Full prose + figures | Complete draft PDF |
| **P6 Camera-ready** | 14–27 Mar 2027 | Review, artifacts, reserve DOI | Zenodo draft ready |
| **P7 Publish** | 28–31 Mar 2027 | Publish DOI | Live DOI |

Fridays remain checkpoints. **Halo is the live paper host** as of 25 Nov 2026. Late Dec / New Year favor measurement over writing.

---

## Week-by-week plan

Dates assume week starts Monday.

### W1 — 1–7 Nov · Halo primary + claim freeze

**Goals**

- **First engineering work:** Halo Ubuntu Ollama, workstation `ssh -L`, A4-style check, A13 path. IDE-machine Ollama is out of scope. Downstairs is fallback only.
- Freeze Paper v1 claim sentence and non-claims (paste into [paper/outline.md](paper/outline.md)).
- Confirm Zenodo account + ORCID; reserve nothing yet (reserve DOI in mid-Mar).
- Recheck TechRxiv submission status; record date of check in this file’s changelog.
- Stand up citation stack (see [citation-workflow.md](citation-workflow.md)): Zotero (or JabRef) → Better BibTeX → `docs/paper/references/library.bib`.
- Create LaTeX skeleton under `docs/paper/src/` using `IEEEtran` conference mode (title/abstract placeholders only).

**Exit:** Halo reachable through SSH forward **or** written blocker with downstairs fallback plan; claim freeze committed; seed bib imported.

### W2 — 8–14 Nov · Halo live smoke + citations

**Goals**

- Complete **Halo bring-up checklist**; land first scrubbed live harness / `run_eval.py --live` row (`host_class=halo-395`).
- Run structured literature sweep (MCP agents, SLM-as-tool, code repair eval, RAG-for-code, PEFT coding models).
- Target **25–40** working bibliography entries; mark `must-cite` / `background` / `drop`.
- Prefer DOI → BibTeX from Crossref/DataCite; verify URLs; prefer versioned arXiv IDs.

**Exit:** Halo A13 path with at least one live row **or** explicit downstairs-fallback note; `library.bib` ≥15 entries underway.

### W3 — 15–21 Nov · Literature + Related Work map

**Goals**

- Finish toward ≥25 entries with DOI or stable URL.
- Write Related Work bullet map: 1 sentence per cluster, 3–6 clusters (MCP / code eval / local SLM / RAG / PEFT).
- Draft M0 bars (general floor + Embabel gain) if not already frozen.

**Exit:** Related-work outline filled (bullets); M0 draft exists.

### W4 — 22–28 Nov · Black Friday / 395 arrive (Thanksgiving: light prose)

**Goals**

- **Hardware:** Halo is the active paper host; keep Ubuntu + Ollama healthy. Do not start paper training on day one.
- Keep a downstairs fallback path documented — do not invent workstation rates if Halo drops.
- Freeze `slm-setup` corpus SHA intent (may re-pin once more before P2 exit).
- Draft Methods: layers table, harness policy, stub vs live.
- Prefer reading + measurement logistics over heavy writing this week.

**Exit:** Methods outline ready; Halo A13 status written (green or downstairs fallback).

### W5 — 29 Nov – 5 Dec · Literature gate + Halo campaign

**Goals**

- Clear `unread` must-cites; cap `must-cite` ≤15 for Part A, allow +10 for Embabel/RAG/LoRA clusters.
- Confirm official Ollama tags for live work; record planned digests.
- **Halo:** confirm AMD backend, starter tags, accelerated placement; keep SSH forward from workstation.
- Use downstairs only if Halo cannot place models on the 8060S-class GPU.

**Exit:** citation gate closed; model shortlist written; Halo smoke with `host_class=halo-395` **or** explicit downstairs-fallback note.

### W6 — 6–12 Dec · MCP live campaign (Halo)

**Goals**

- Pin corpus SHA; pin model tags + digests.
- Keep Halo A1–A7 / A11–A13 green; point gitignored `.env` at the Halo SSH forward.
- Run fixture protocol cloud-safe; live harness sessions on the **Halo paper host**.
- Book remaining live slots through early January.

**Exit:** at least one live session logged (scrubbed notes) with `host_class=halo-395`.

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

- Install/validate one 7B–14B official tag on the **Halo paper host** (`host_class=halo-395`; downstairs only if Halo failed — say which).
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
| P0–P1 | **Halo A13 + live rows**; M0 text | Paper inference on the IDE workstation |
| P2 | M1 light only after Halo Part A N exists | Blocks Part A N; mixing hosts in one table |
| P3 | M1–M3 required path on Halo | Skipping runner / overwriting runs |
| P4 | M4 or one M5 **or** neither (M5 on Halo 128 GB class) | Starting M5 without written M3 gap |
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
| Halo ROCm/Vulkan painful or DOA | Part A + M1–M3 on downstairs 4080-class fallback; label `host_class`; DOI still 31 Mar |
| Halo SSH forward down | Treat as host down; do not invent workstation rates |
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
| 2026-11-25 | **Host switch:** GEEKOM Halo / 395 becomes primary paper inference host; downstairs NVIDIA demoted to fallback only |
