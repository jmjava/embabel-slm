# Paper v1 outline

Working title: **Layered Evaluation of Local Coding SLMs Exposed as MCP Tools**

Venue target: **Zenodo preprint** (IEEE `IEEEtran` conference formatting). TechRxiv only if submissions reopen. Ship by **31 Mar 2027**. Calendar: [paper-calendar-2026.md](../paper-calendar-2026.md).

---

## Claim freeze (provisional 25 Nov 2026; revise after numbers freeze Fri 27 Feb 2027)

```text
Claim: On the pinned slm-setup corpus @ sha <TBD>, with official Ollama tags
<fast=TBD, strong=TBD>, under the layered harness policy (fast → one repair → strong),
the local coding SLM on host_class=halo-395 achieves <pass@end / layer rates TBD>,
which <supports / does not support> usefulness for bounded MCP-delegated coding edits.
Embabel (Part B, pre-registered two-arm): on sealed holdout ≥200 tasks, gap closure G
between shareable arm S (config D) vs ceiling arm L (config A) is <G TBD> (or undefined
if L-A CI includes 0); confirmatory inference uses Ollama on halo-395 only.

Non-claims:
- General model quality / SOTA coding
- Host-upgrade speedups without paired rows (do not average halo-395 with downstairs-*)
- Live IDE agent actually routed or reviewed (scripted verdicts only)
- Embabel expert-level behavior without locked holdout and confirmatory prereg
- LoRA gains without a frozen A/B/C/D table on holdout
- Any live rate collected on the IDE workstation
- Pilot E01–E20 rows as confirmatory evidence

Pre-registered success definition (see docs/protocol/preregistration.md):
- H1–H4 and headline estimand G with bootstrap CI; Holm on H1–H3
- pass@1 (Chen unbiased) and greedy pass reported separately
- Part A: ≥3 independent live sessions, same corpus SHA, host_class=halo-395
- Embabel holdout: one scored pass per config; manifest hash committed before scoring
- Numbers freeze Fri 27 Feb 2027; DOI by 31 Mar 2027
```

Status: **PROVISIONAL** — metrics and SHAs still TBD until Halo Ubuntu live rows exist. Structure frozen so literature / Methods can proceed without GPU.

---

## Section skeleton

Target length: **6–10 pages** + references (MCP Part A + Embabel A-vs-B).

### Title + authors

- Title: no subtitle fluff; no symbols
- Authors + affiliation + ORCID
- Zenodo DOI footer (after W8 reserve)

### Abstract (write last, 150–200 words)

1. Problem: premium agents waste capacity / privacy on mechanical edits  
2. Approach: private local SLM over MCP; layered scoring  
3. Finding: one sentence with the headline rate / failure mode  
4. Boundary: what the result does *not* mean  

### Keywords

`local LLM`, `MCP`, `code repair`, `evaluation`, `software engineering`, `SLM`

### I. Introduction (~0.75–1 p)

- Mechanical coding edits vs premium model cost/privacy  
- Gap: tool benchmarks often score tool *choice* or final answer, not **where** a local coding edit fails  
- Contribution bullets (3 max):
  1. Layered eval contract (transport / format / structure / behavior)  
  2. Executable corpus + harness (`pass@1` vs `pass@end`)  
  3. Empirical verdict on pinned local tags under that contract  

### II. Related Work (~0.75–1 p)

Clusters (W2 seed pass 2026-11-25; promote must-cite after read gate in W6). Notes: [references/related-work.md](references/related-work.md).

| Cluster | Distinction from us | Seed keys |
| --- | --- | --- |
| Code gen / repair benchmarks | We score MCP tool outputs with layer-conditional fail | `chen2021evaluating`, `jimenez2024swebench`, `xu2025swecompass` |
| Tool-using / MCP agents | We fix the tool and measure edit layers, not tool selection | `anthropic2024mcp`, `gao2025mcpradar`, `fan2025mcptoolbenchpp`, `wang2025mcpbench`, `wu2025mcpmark` |
| Local / small coding models | We report usefulness under delegation + apply gate, not chat quality | _(pin live tags later)_ |
| RAG / fine-tuning for code | Embabel base-vs-retrieval (and optional LoRA) is in-scope for v1 if frozen by late Feb | `lewis2020rag`, `hu2022lora` |

### III. Method (~1.5–2 p)

- System: premium agent → stdio MCP `local_*` → private Ollama  
- Layers table (from evaluation protocol)  
- Corpus summary (case ids + what each isolates)  
- Harness policy: fast → one repair → strong; `pass@1` / `pass@end`  
- Apply gate: accept / rewrite / reject (scripted premium in CI)  
- What stub measures vs what live measures  

### IV. Experimental Setup (~0.75–1 p)

- Hardware class: primary `halo-395` (GEEKOM); fallback `downstairs-4080` / `downstairs-3060` — **host column on every live table**; IDE workstation is MCP-only (no inference rows); no hostname/LAN  
- Model tags + digests + context  
- Corpus / repo SHAs  
- Commands to reproduce fixture path; live path marked operator-only  
- Safety: official library tags; secrets never delegated  
- Host switch 25 Nov 2026: paper live rates target Halo; downstairs only if AMD placement fails

### V. Results (~1–1.5 p)

- Table: layer-conditional rates  
- Table: `pass@1` vs `pass@end` vs escalation rate  
- Prompt contract: precise vs vague on same oracle  
- Short failure exemplars (scrubbed)  
- Optional appendix pointer: Embabel A-vs-B  

### VI. Discussion (~0.5–0.75 p)

- Cheapest intervention suggested by the failure layer (prompt / retrieval / weights)  
- Relation to product rule: treat output as untrusted  
- What would change the verdict  

### VII. Limitations (~0.5 p)

Copy and tighten from evaluation-protocol “may not claim.” Explicit about live N, language coverage, and scripted reviewers.

### VIII. Conclusion (~0.25 p)

Restate verdict + Zenodo artifact pointer + next measurement (Embabel holdout / RAG).

### Acknowledgments (optional)

### References

IEEE numeric; only `must-cite` + method necessities.

---

## Figures / tables to produce

| ID | Content | Owner week |
| --- | --- | --- |
| Fig 1 | MCP + layer pipeline | draft phase (early Mar) |
| Fig 2 | Layer fail rates (bar) | after Part A freeze (early Jan) |
| Fig 3 | Embabel base vs retrieval | after M3 (late Jan) |
| Table I | Models / config | Dec–Jan |
| Table II | Corpus case summary | Dec |
| Table III | pass@1 / pass@end | early Jan |
| Table IV | Vague vs precise | early Jan |
| Table V | Embabel A-vs-B metrics | late Jan |

---

## Mapping to repos

| Paper part | Repo path |
| --- | --- |
| Methods / corpus | `jmjava/slm-setup` `docs/evaluation-protocol.md`, `src/local_coding_slm/eval/` |
| Live notes | `slm-setup` `docs/phase3-log.md` + dated results (scrubbed) |
| Longer research arc | this repo `docs/research-plan.md`, `docs/milestones.md` |
| Numbers freeze | `experiments/paper-v1/` in this repo |
