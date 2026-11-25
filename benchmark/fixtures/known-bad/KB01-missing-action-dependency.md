# KB01 — Known-bad: missing action dependency (must fail)

This fixture exists to prove the runner can **reject** a bad answer. A skipped
live run is not a pass. A model that “explains” without repairing must still fail
the automated checks.

## Intentional defect

- Goal `G` requires type `CreditAssessment`.
- Action `CollectCustomer` produces `Customer` only.
- **No** action produces `CreditAssessment`.
- A “solution” that only renames types or comments out the goal is invalid.

## Expected runner outcome

| Layer | Expected |
| --- | --- |
| extract | may succeed |
| compile | may succeed if the model leaves the broken graph intact |
| reachability / scenario | **FAIL** — goal remains unreachable |
| overall | **FAIL** (first_failure = planning/reachability or equivalent) |

## Cite

- Pattern source: `embabel/embabel-agent@3b9b74f494cb` planner semantics
- Ledger: [example-ledger.md](../../../docs/example-ledger.md) gap item 7

## Operator note

When the compile/test runner lands, commit a minimal broken project under
`benchmark/fixtures/known-bad/KB01/` (generated, not vendored Embabel sources)
and assert non-zero exit here. Until then, this spec is the freeze for M0.5.
