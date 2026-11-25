# Embabel first-20 benchmark (paths + checks only)

No live model required. Each task cites a ledger pin and names what the
future runner must extract, compile, and assert. **Do not copy framework
source into this tree** — only task prompts, stubs, and expected checks.

Pinned framework for this freeze: `embabel/embabel-agent@3b9b74f494cb`  
Companion sources: see [docs/example-ledger.md](../docs/example-ledger.md).

| Id | Category | File |
| --- | --- | --- |
| E01–E20 | generation / repair / planning / transform / refactor / integration | [tasks/](tasks/) |
| KB01 | known-bad (must fail) | [fixtures/known-bad/KB01-missing-action-dependency.md](fixtures/known-bad/KB01-missing-action-dependency.md) |

Next runner step (still no Halo required for stubbing): implement extract →
isolated project → compile → fail KB01 on purpose.
