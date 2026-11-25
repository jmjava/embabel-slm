# Embabel example ledger

First no-GPU milestone for the model program: one row per public source we may
cite for practice packs, retrieval, or verified training examples.

**Rules**

- Cite `repo@sha` and path. **Do not copy source** into this repo.
- `jmjava/embabel-v1-learning` is a personal compilation, not the complete set.
- Holdout / benchmark tasks must not be mined from the same files used as
  training cards without a written near-dupe check (see milestones M4–M5).
- Pins below are default-branch tips as of **2026-11-25**. Re-pin in the same
  week a pin moves before any scored run.

## Priority corpus (pin before any adapter)

| Source | Pin | Role | Gap vs learning repo | Notes |
| --- | --- | --- | --- | --- |
| [embabel/guide](https://github.com/embabel/guide) | `main@f92ba512b7da` (2026-11-08) | Official docs talk-to-the-docs | Official guide surface; learning repo may paraphrase | Primary retrieval + pattern cards |
| [embabel/dice](https://github.com/embabel/dice) | `main@c5f14b63ae9c` (2026-11-25) | Knowledge-graph / DICE library | Likely thin in personal learning notes | Kotlin-heavy; Spring patterns |
| [docs.embabel.com](https://docs.embabel.com) | _operator: capture dated snapshot URL_ | Agent guide + cookbook HTML | Docs drift vs git | Prefer git sources when both exist |
| [embabel/embabel-cookbook](https://github.com/embabel/embabel-cookbook) | `main@1b8e579f3f52` (2026-11-16) | Cookbook examples | May overlap learning demos | Compiler-checkable snippets |
| [jmjava/embabel-v1-learning](https://github.com/jmjava/embabel-v1-learning) | `main@45ea2e92c602` (2026-10-11) | Cheat sheet / walkthrough / lessons | Baseline personal set | Not authoritative alone |

## Framework + templates

| Source | Pin | Role | Gap vs learning repo | Notes |
| --- | --- | --- | --- | --- |
| [embabel/embabel-agent](https://github.com/embabel/embabel-agent) | `main@3b9b74f494cb` (2026-11-25) | Core JVM agent framework | Framework APIs beyond tutorials | Pin before any compile runner |
| [embabel/embabel-agent-examples](https://github.com/embabel/embabel-agent-examples) | `main@311ec52e3919` (2026-11-19) | Java/Kotlin examples | Broader than learning demos | First 20-task mine |
| [embabel/java-agent-template](https://github.com/embabel/java-agent-template) | `main@a4dbf9154229` (2026-10-10) | Java starter | Template scaffolding tasks | Generation / integration |
| [embabel/kotlin-agent-template](https://github.com/embabel/kotlin-agent-template) | `main@a89d998cbd9d` (2026-10-09) | Kotlin starter | Template scaffolding tasks | Generation / integration |
| [embabel/embabel-common](https://github.com/embabel/embabel-common) | _TBD next pin pass_ | Shared modules | Internal APIs | Secondary |
| [embabel/embabel-build](https://github.com/embabel/embabel-build) | _TBD_ | Build plugins | Build/config tasks | Secondary |

## RAG / graph / Drivine-adjacent

These matter for graph RAG claims and for linking to [drivine-slm](https://github.com/jmjava/drivine-slm). Still **cite-only** here.

| Source | Pin | Role | Gap vs learning repo | Notes |
| --- | --- | --- | --- | --- |
| [embabel/embabel-agent-rag-graph](https://github.com/embabel/embabel-agent-rag-graph) | `main@c9a531bbaa52` (2026-11-16) | Graph RAG store (Drivine4j) | Likely absent from learning repo | Ties Embabel ↔ Drivine |
| [embabel/embabel-agent-rag-store](https://github.com/embabel/embabel-agent-rag-store) | `main@ce62378346ad` (2026-04-15) | PgVector RAG | Alternate store | Compare retrieval backends |
| [embabel/embabel-agent-rag-neo-ogm](https://github.com/embabel/embabel-agent-rag-neo-ogm) | _TBD_ | Neo OGM RAG | Alternate store | Secondary |
| [embabel/urbot](https://github.com/embabel/urbot) | `main@23e8179ab884` (2026-07-21) | RAG chatbot template | End-to-end app | Integration tasks |
| [embabel/ragbot](https://github.com/embabel/ragbot) | _TBD_ | RAG demo | Demo depth | Secondary |
| [embabel/stashbot](https://github.com/embabel/stashbot) | _TBD_ | Doc assistant | Demo depth | Secondary |

## Agents / demos (task-mining candidates)

| Source | Pin | Role | Notes |
| --- | --- | --- | --- |
| [embabel/coding-agent](https://github.com/embabel/coding-agent) | `main@b0997231880d` (2026-03-20) | SE agentic flow | Repair / multi-file |
| [embabel/agent-gen](https://github.com/embabel/agent-gen) | _TBD_ | Meta-agent | Advanced; later |
| [embabel/decker](https://github.com/embabel/decker) | _TBD_ | Slides agent | Integration |
| [embabel/flicker](https://github.com/embabel/flicker) | _TBD_ | Movie finder | Demo |
| [embabel/tripper](https://github.com/embabel/tripper) | _TBD_ | Travel planner | Planning |
| [embabel/prepper](https://github.com/embabel/prepper) | _TBD_ | Meeting prep | Planning |
| [embabel/shepherd](https://github.com/embabel/shepherd) | _TBD_ | Community manager | Integration |
| [embabel/embabel-air](https://github.com/embabel/embabel-air) | _TBD_ | Airline chatbot | Demo |
| [embabel/impromptu](https://github.com/embabel/impromptu) | _TBD_ | Music + Neo4j | Graph + chat |
| [embabel/grouper](https://github.com/embabel/grouper) | _TBD_ | Focus groups | Demo |
| [embabel/modernizer](https://github.com/embabel/modernizer) | _TBD_ | Project modernizer | Refactor |
| [embabel/project-creator](https://github.com/embabel/project-creator) | _TBD_ | Project wizard | Scaffolding |
| [embabel/langgraph-patterns](https://github.com/embabel/langgraph-patterns) | _TBD_ | Comparison demos | Teaching contrast |

## Platform / tooling (usually not first 20 tasks)

| Source | Pin | Role |
| --- | --- | --- |
| [embabel/embabel-acceptance-tests](https://github.com/embabel/embabel-acceptance-tests) | _TBD_ | E2E acceptance — good for known-good fixtures, not training copy |
| [embabel/embabel-agent-intellij](https://github.com/embabel/embabel-agent-intellij) | _TBD_ | IDE plugin |
| [embabel/embabel-chat-store](https://github.com/embabel/embabel-chat-store) | _TBD_ | Chat persistence |
| [embabel/embabel-agent-tool-postgres](https://github.com/embabel/embabel-agent-tool-postgres) | _TBD_ | NL→SQL tool |
| [embabel/vaadin-components](https://github.com/embabel/vaadin-components) | _TBD_ | UI components |
| [embabel/jbang-catalog](https://github.com/embabel/jbang-catalog) | _TBD_ | JBang entrypoints |
| [embabel/embabel-llm-database](https://github.com/embabel/embabel-llm-database) | _TBD_ | Model DB |
| [embabel/awesome-embabel](https://github.com/embabel/awesome-embabel) | `main@9d92abc307c0` (2026-03-15) | Resource index |
| [embabel/blogs](https://github.com/embabel/blogs) / [publications](https://github.com/embabel/publications) | _TBD_ | Narrative only — not compiler-verified training |

## First gap list (draft — refine into 20 tasks next)

Derived from priority rows vs a personal learning compilation:

1. Official `@Action` / goal / condition shapes from `guide` + `embabel-agent` (not cheat-sheet paraphrases).
2. Planner reachability / missing-action diagnosis from framework tests or examples.
3. Spring Boot wiring from templates (`java-agent-template`, `kotlin-agent-template`).
4. DICE / knowledge-graph calls from `dice` (likely uncovered in learning notes).
5. Graph RAG ingest + `loadNearest`-style retrieval via `embabel-agent-rag-graph` (Drivine path).
6. Multi-file refactor across example modules (`embabel-agent-examples`).
7. Repair: broken annotation / unreachable goal fixtures (to be authored; known-bad must fail).
8. Transformation: imperative Spring service → Embabel actions (cookbook + examples).
9. Integration: REST trigger of an agent (templates / air / urbot).
10. Kotlin idioms from `dice` + kotlin template (separate from Java cards).

**Next no-GPU step:** freeze the first **20 tasks** from this gap list into
`benchmark/tasks/` (paths + expected checks only; no live model). One known-bad
fixture must be in that set before any Halo run.

## Ledger hygiene

| Date | Change |
| --- | --- |
| 2026-11-25 | Initial ledger; pinned priority repos; Halo Ubuntu blocked by Windows pureplay — no live rates yet |
