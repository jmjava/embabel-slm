# Related Work notes (Paper v1)

Working draft for outline §II. Distinguish our contribution in one line per
cluster. Full BibTeX lives in [seed.bib](seed.bib); acquisition log in
[search-log.md](search-log.md).

Provisional claim freeze: [outline.md](../outline.md).

---

## Cluster A — MCP / tool-using agents

| Key | Distinction from us |
| --- | --- |
| `anthropic2024mcp`, `mcp2024spec` | Protocol origin; we treat MCP as fixed transport |
| `gao2025mcpradar` | Scores tool choice / multi-dim tool use; we **fix the tool** and score edit layers |
| `fan2025mcptoolbenchpp` | Large MCP tool marketplace; we measure delegated coding edits, not tool catalog breadth |
| `wang2025mcpbench` | Multi-server planning / cross-tool trajectories; we do not evaluate tool retrieval |
| `wu2025mcpmark` | CRUD stress on live MCP servers; closest neighbor on realism, still tool-selection oriented |

**Our line:** layered fail (transport → format → structure → behavior) on a pinned
coding MCP server, with `pass@1` vs `pass@end` under fast→repair→strong.

## Cluster B — Code gen / repair benchmarks

| Key | Distinction |
| --- | --- |
| `chen2021evaluating` | HumanEval / pass@k; we inherit execution framing, not function-completion tasks |
| `jimenez2024swebench` | Real GitHub issues; we are MCP-delegated bounded edits, not full issue resolve |
| `xu2025swecompass` | Broad agentic coding taxonomy; we report layer-conditional MCP rates only |

## Cluster C — Local / small coding models

Background only until Halo live tags are pinned. Cite product/docs lightly;
prefer measured open models once digests exist. Do not claim SLM SOTA.

## Cluster D — RAG / LoRA (Embabel appendix / v2)

| Key | Role |
| --- | --- |
| `lewis2020rag` | Retrieval framing for Embabel A-vs-B |
| `hu2022lora` | Adapter method if M5 lands inside paper window |

## Cluster E — Embabel / Drivine domain

Software cites (`embabel`, `slmsetup2026`, `embabelslm2026`). Domain papers TBD;
do not invent academic Embabel citations.

---

## Cap

≤15 must-cite in camera-ready; ≤40 in working bib. Prefer unread → drop over
unread → must-cite.
