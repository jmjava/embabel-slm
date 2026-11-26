# M0 bars

Frozen on 2026-10-07, before any scored run. This page is the general-coding floor, the Embabel gain, and the host budget. A later run keeps these numbers when the scores look bad. Changing them is an amendment, recorded in [m0-bars-amendments.md](m0-bars-amendments.md), and the checker rejects any other edit.

The block between the markers is normative. The prose states the same rules.

## General-coding floor

The floor is four tasks. Each one is scored on its own against the pinned base model, on the same tasks and the same runner.

| Task | A pass |
| --- | --- |
| tests | The runner compiles the model's test, and the test command accepts it. |
| repair | A tree that failed compile or test becomes a tree the runner accepts. |
| multi-file edit | The accepted edit changes more than one source file. |
| explanation | The answer names the failure cause the runner recorded. |

A release fails when any one of those four pass rates is more than 5 percentage points below the pinned base model. A 5 point drop still holds. A 6 point drop fails that task, and the release fails with it. The four rates are not averaged. A missing rate fails the release. A gain on one task does not fill in a drop on another.

These four tasks are the whole floor.

## Embabel gain

The specialist metrics are compile rate, full-task success, hallucinated-API rate, planner success, and repair iterations. The candidate is compared with its own pinned base model on the locked holdout.

The lift that counts is all five of these, together:

- Compile rate, full-task success, and planner success each rise by at least 5 percentage points.
- Hallucinated-API rate falls by at least 5 percentage points.
- Mean repair iterations are at most 80 percent of the base mean.

A movement on one metric does not count while another misses its lift. A metric that is not in this list does not count. When a higher-is-better rate is already above 95, that metric counts only if the candidate reaches 100. When the hallucinated-API rate is already below 5, that metric counts only if the candidate reaches 0. When the base mean of repair iterations is 0, the candidate mean must be 0.

## Host budget

The release-base band is 7B through 14B inclusive, counted as base parameters before quantization. A quantized 14B model is still 14B.

A shareable release in arm S must also fit the memory tier: peak GPU/unified memory at Q4_K_M with context length 8192 must be at most 16 GB, measured on `host_class=halo-395` and recorded on every scored row. A row above the tier is not a shareable-arm candidate.

The **reference** band is for middle and ceiling comparison arms only. Middle models are 24B through 34B inclusive. Ceiling models are up to 70B dense parameters or up to 120B total parameters for MoE architectures. Reference models are scored for comparison only: configs A and B, never a release base, never trained. They wait until `docs/runner-stable.md` exists as a JSON object with `runner_command`, `known_bad_fixture_failed` set to true, and `scoring_run_id`. Until that file is present and valid, reference sizes stay out.

Inference `host_class` values are `halo-395`, `downstairs-4080`, and `downstairs-3060`. **`halo-395` may carry a scored run immediately** (primary paper host). Downstairs hosts are fallback only. Do not average halo-395 rows with downstairs rows. The IDE workstation stays the MCP host. Every results row names its `host_class`.

<!-- m0-bars:start -->

```json
{
  "frozen_on": "2026-10-07",
  "general_coding_floor": {
    "tasks": ["tests", "repair", "multi_file_edit", "explanation"],
    "release_fail_drop_points": 5,
    "scope": "any_single_task",
    "averaging": "forbidden",
    "missing_score": "fail",
    "compare_to": "pinned_base_model_on_the_same_tasks"
  },
  "embabel_gain": {
    "metrics": [
      {"id": "compile_rate", "direction": "higher", "lift_points": 5},
      {"id": "full_task_success", "direction": "higher", "lift_points": 5},
      {"id": "hallucinated_api_rate", "direction": "lower", "lift_points": 5},
      {"id": "planner_success", "direction": "higher", "lift_points": 5},
      {"id": "repair_iterations", "direction": "lower", "max_percent_of_base": 80}
    ],
    "counts_when": "every_metric_meets_its_lift",
    "unlisted_metrics_count": false
  },
  "host_budget": {
    "release_base_min_billion_parameters": 7,
    "release_base_max_billion_parameters": 14,
    "shareable_peak_memory_gb_q4_k_m_8192": 16,
    "reference_middle_min_billion_parameters": 24,
    "reference_middle_max_billion_parameters": 34,
    "reference_ceiling_dense_max_billion_parameters": 70,
    "reference_ceiling_moe_max_billion_parameters_total": 120,
    "reference_allowed_configs": ["A", "B"],
    "reference_never_release_base": true,
    "reference_never_trained": true,
    "reference_only_after": "docs/runner-stable.md",
    "runner_stable_requires": ["runner_command", "known_bad_fixture_failed", "scoring_run_id"],
    "known_bad_fixture_failed_must_equal": true,
    "inference_hosts": ["halo-395"],
    "inference_hosts_fallback": ["downstairs-4080", "downstairs-3060"],
    "inference_host_primary": "halo-395",
    "inference_host_no_row_averaging_across_primary_and_fallback": true,
    "ide_workstation": "mcp_host",
    "quantization_uses_base_parameter_count": true
  }
}
```

<!-- m0-bars:end -->

## How a later change is allowed

`scripts/check_m0_bars.py` hashes this file and checks the rules above. A pull request that edits this file, that script, or `.github/workflows/m0-bars.yml` passes only when all of the following are true:

- The pull request title starts with `amend(m0-bars):`.
- `docs/m0-bars-amendments.md` keeps every earlier byte and appends one amendment.
- That amendment records the old sha256, the new sha256, and a reason.
- The same pull request leaves experiment runs, scores, training outputs, and benchmark results untouched.

The first commit that adds this page is the freeze. It is not an amendment.