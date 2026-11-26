# Paper v1 experiment freeze

Committed summaries only. Raw `eval-runs/` stay in `slm-setup` (gitignored). No hostnames, LAN addresses, secrets, or raw completions.

## Publication gate

**No Zenodo upload (pre-registration, preprint, or artifact) may include Kiln / slm-kiln content without Jasper's written review.**

## Freeze status

| Field | Value |
| --- | --- |
| Corpus repo | `jmjava/slm-setup` |
| Corpus SHA | _TBD after next pin_ |
| Protocol doc | `docs/protocol/preregistration.md` |
| Confirmatory arms | **S** (shareable 7–14B, configs A–D), **M** (24–34B, A/B), **L** (ceiling, A/B) |
| Inference backend | **Ollama** on `halo-395` for confirmatory rows |
| Quant default | Q4_K_M; one Q8_0 sensitivity row on shareable base config A |
| Fast model tag + digest | _TBD_ (starter candidate `qwen3.5:9b`) |
| Strong model tag + digest | _TBD_ (starter candidate `devstral-small-2`) |
| Live sessions completed | 0 |
| Paper host | **`halo-395` (GEEKOM)** — primary as of 25 Nov 2026 |
| Fallback host | `downstairs-4080` (3060 secondary) only if Halo AMD placement fails |
| IDE workstation | MCP only — inference non-starter |
| Halo Ubuntu bring-up | **Blocked temporarily** — machine on Windows pureplay; resume Ubuntu when free |
| Holdout manifest SHA256 | _TBD — commit before first holdout score_ |
| Holdout min tasks | 200 (confirmatory) |
| Part A (MCP) freeze | target Fri 9 Jan 2027 |
| All-numbers freeze | target Fri 27 Feb 2027 |
| DOI deadline | 31 Mar 2027 |

## Raw-data contract (research quality)

Every live or Embabel scored run writes a **new** directory (never overwrite):

| Artifact | Required |
| --- | --- |
| `meta.json` | model tag, digest, quant, prompt id, corpus/repo SHAs, `host_class`, `arm`, `config`, `split`, `num_ctx`, Ollama version, peak memory GB when available, decoding block |
| `scores.json` / JSONL | layer outcomes, pass@1, greedy pass, first_failure |
| `raw/` | greedy + `sample1..k` outputs (local only; scrub before Zenodo) |
| `notes.md` | operator observations, no LAN/hostname |

Zenodo gets scrubbed tables + `artifact-manifest.md`. Negative results count.

## Result tables

Add CSV/Markdown here after live runs, e.g.:

- `layer-rates.md`
- `pass-at.md`
- `prompt-contract.md`
- `embabel-arms-holdout.md` (S/M/L after holdout)
- `gap-closure-G.md`