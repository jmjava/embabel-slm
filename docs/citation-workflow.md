# Citation acquisition workflow

Formal process for Paper v1 (Nov 2026 – Mar 2027). Goal: every citation in the PDF is **acquired once**, **stored with provenance**, **triaged**, and **used for a named purpose** — not scraped into a pile.

Calendar: [paper-calendar-2026.md](paper-calendar-2026.md). Outline: [paper/outline.md](paper/outline.md). Bib seed: [paper/references/seed.bib](paper/references/seed.bib).

---

## Tooling (pick once in W1)

| Layer | Choice | Rule |
| --- | --- | --- |
| Library | **Zotero** (preferred) or JabRef | One group library: `embabel-slm-paper-v1` |
| Sync to git | **Better BibTeX** → export `docs/paper/references/library.bib` | Export on change; commit bib with prose |
| Style | `IEEEtran.bst` / BibLaTeX IEEE | Match LaTeX skeleton |
| PDF store | Zotero storage or `docs/paper/references/pdfs/` (gitignored if large) | Prefer DOI link over committing PDFs |
| DOI lookup | Crossref, DataCite, Semantic Scholar, OpenAlex | Never hand-type DOIs from memory |

`.gitignore` already should ignore large PDFs; keep only `.bib` and short `notes/*.md` in git.

---

## Acquisition protocol (every source)

For each candidate paper/software/spec:

1. **Capture** — browser connector or DOI paste into Zotero.
2. **Normalize** — title case; full author list; year; venue; DOI or arXiv id; URL; abstract.
3. **Provenance note** (Zotero “Extra” or `note`):
   - `found_via:` search query or citation chain
   - `found_date:` ISO date
   - `used_for:` one of `method`, `baseline`, `related-mcp`, `related-slm`, `related-eval`, `related-rag`, `ethics`, `drop`
   - `status:` `must-cite` | `background` | `drop` | `unread`
4. **Read gate** — do not mark `must-cite` until abstract + relevant section are read.
5. **Export** — Better BibTeX citation key scheme: `authYearShortTitle` (e.g. `chen2021evaluating`).
6. **Verify** — open DOI/URL once; fix broken entries before W6.

### BibTeX field minimum

```bibtex
@inproceedings{key,
  author    = {...},
  title     = {...},
  booktitle = {...},
  year      = {...},
  doi       = {...},
  url       = {https://doi.org/...}
}
```

Software / datasets:

```bibtex
@software{key,
  author  = {...},
  title   = {...},
  year    = {...},
  url     = {...},
  version = {...}
}
```

Preprints: use `@article` or `@misc` with `eprint` / `archivePrefix = {arXiv}`. Prefer the **version** you actually read (`arXiv:xxxx.xxxxxvN`).

---

## Search plan (W2)

Run these queries; stop when diminishing returns (same papers recur). Log queries in `docs/paper/references/search-log.md`.

### Cluster A — MCP / tool-using agents

- `Model Context Protocol` MCP LLM tool
- LLM agents tool use evaluation benchmark
- Cursor Copilot agent tool delegation (careful: prefer primary docs + papers over blogs)

### Cluster B — Local / small coding models

- small language model code generation evaluation
- local LLM software engineering
- quantized coding model repair compile

### Cluster C — Code evaluation methodology

- execution-based code generation evaluation HumanEval
- SWE-bench repair
- pass@k code models
- layered evaluation structure behavior (our framing; cite nearest neighbors)

### Cluster D — RAG and specialization (background for v1; core for v2)

- retrieval augmented code generation
- repository-level code completion RAG
- LoRA QLoRA code fine-tuning

### Cluster E — Systems / privacy

- on-prem LLM developer tools
- untrusted LLM output software supply chain

**Cap:** ≤40 items in `library.bib` for v1; ≤15 `must-cite`. Everything else stays `background` or `drop`.

---

## Triage rubric

| Status | Meaning | Action |
| --- | --- | --- |
| `must-cite` | Supports a sentence in Intro/Related/Method | Appears in PDF bibliography |
| `background` | Informed thinking; not needed in text | Keep in Zotero; omit from final `.bib` export filter if noisy |
| `drop` | Off-topic, low quality, or duplicate | Tag and ignore |
| `unread` | Captured, not yet gated | Clear before W6 or demote to `drop` |

Duplicate detection: same DOI → merge. Same idea, weaker venue → keep stronger, note the other in Extra.

---

## In-text citation rules

- Cite **methods and benchmarks** you compare against, not every adjacent blog.
- First mention of a system (Ollama, MCP, Embabel): cite primary doc or paper once.
- Do not cite your own dated lab notes as peer literature; point to Zenodo artifacts / git tags instead.
- Secondary citations (“as cited in”): avoid; get the primary.
- Self-cite only the Zenodo DOI / prior preprint if it exists.

IEEE numeric order in text; bibliography sorted as IEEEtran expects (order of citation or alphabetical per bst — follow the bst you ship).

---

## Formal software / corpus citation

Cite runnable artifacts as first-class:

| Artifact | How to cite |
| --- | --- |
| `slm-setup` eval corpus + protocol | git tag + commit SHA; Zenodo related identifier after deposit |
| Model weights | Official Ollama library tag + digest from run notes (not a random GGUF URL) |
| Embabel pins | Official repo + commit (Guide, DICE) per milestones |
| This preprint | Reserved Zenodo DOI (W8) |

Add BibTeX `@software` / `@misc` entries for your own repos at camera-ready so others can cite the artifact pack.

---

## Citation checkpoints (aligned to paper calendar)

| When | Checkpoint |
| --- | --- |
| Early Nov (W1) | Library empty but tooling live; `seed.bib` imported |
| Mid–late Nov (W2–W3) | ≥25 entries; search-log filled; Related Work map |
| Early Dec (W5) | `unread` must-cites cleared; caps respected |
| Draft phase (W18–W19) | Every draft citation key resolves; only `must-cite` (+ method refs) in PDF |
| Camera-ready (W21) | DOIs verified; Zenodo related works linked |

---

## Anti-patterns

- Pasting GPT-generated BibTeX without opening the DOI
- Citing a survey for a specific empirical claim instead of the original paper
- Inflating Related Work past one column without new distinctions
- Adding RAG/LoRA citations to v1 when those experiments are not in the paper
- Committing secrets or private hostnames inside PDF annotations or Extra fields
