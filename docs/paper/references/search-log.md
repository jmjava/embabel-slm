# Search log (Paper v1)

Record each literature search during W2+. One block per query.

## Template

```text
### YYYY-MM-DD — <cluster A/B/C/D/E>
Query: "..."
Engine: Scholar | Semantic Scholar | OpenAlex | other
Top keepers: <keys or titles>
Dropped: <reason>
```

## Entries

### 2026-11-25 — cluster A (MCP / tool-use)

Query: `MCP-RADAR Model Context Protocol benchmark LLM tool use`
Engine: web / arXiv abs
Top keepers: `gao2025mcpradar` (arXiv:2505.16700)
Dropped: blog roundups without primary paper

### 2026-11-25 — cluster A (MCP marketplace / multi-step)

Query: `MCPToolBench++ MCP-Bench MCPMark SWE-Compass arXiv`
Engine: web / arXiv API
Top keepers:
- `fan2025mcptoolbenchpp` (arXiv:2508.07575)
- `wang2025mcpbench` (arXiv:2508.20453)
- `wu2025mcpmark` (arXiv:2509.24002)
- `xu2025swecompass` (arXiv:2511.05459) — filed under related-eval
Dropped for must-cite (keep as unread/background until W6 read gate):
- MCP-AgentBench (arXiv:2509.09734)
- MCPEval (arXiv:2507.12806)
- MCP-Universe (arXiv:2508.14704)
- LiveMCPBench (arXiv:2508.01780)
Reason: same cluster as keepers; diminishing returns; cap ≤15 must-cite

### 2026-11-25 — cluster B (code eval, seed already held)

Query: confirm HumanEval + SWE-bench still must-cite framing
Engine: seed.bib review
Top keepers: `chen2021evaluating`, `jimenez2024swebench`
Dropped: none this pass

### Notes

- Related Work prose draft: [related-work.md](related-work.md)
- Seed file updated same day: [seed.bib](seed.bib)
- Status on new MCP papers: `unread` → promote to `must-cite` only after abstract + Methods skim
