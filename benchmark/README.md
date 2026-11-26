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

Runner (M2): `python3 -m runner score --fixture-dir benchmark/fixtures/scoring-stubs`
scores E01–E20 from stubs; `python3 -m runner selftest` asserts KB01 fails reachability
and `benchmark/fixtures/known-good/E01-good.md` passes when `mvn` is on PATH.
Machine-readable prompts live in [specs/](specs/); frozen task `.md` files stay unchanged.
