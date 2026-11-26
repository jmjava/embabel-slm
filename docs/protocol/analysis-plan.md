# Analysis plan (frozen at holdout scoring)

Companion to [preregistration.md](preregistration.md). Confirmatory analyses use holdout rows only; DEV and pilot are exploratory except for pre-declared model selection on DEV.

## Input contract

Each scored config produces a run directory under `experiments/runs/` with:

- `meta.json` — arm, config, split, model tag, quant, `num_ctx`, Ollama version, peak memory when available
- `scores.json` — per-task outcomes and summary metrics from the runner

The frozen analysis entrypoint is the `analysis` Python package (`python3 -m analysis ...`). Its git commit hash is copied into `experiments/paper-v1/analysis-script-sha256.txt` when holdout scoring starts (sha256 of `analysis/__init__.py` through `analysis/power.py` concatenated in sorted path order, or single tag hash — operator records the commit SHA in the same file).

## Estimators

### Greedy pass rate

Per config: fraction of holdout tasks where the greedy attempt (`temperature=0`) passes (`pass=true` in scores). 95% CI: cluster bootstrap over tasks, 10,000 resamples, seed `20260227` (percentile 2.5 / 97.5).

### pass@1 (Chen et al. 2021 unbiased)

Per task with \(n\) independent samples of which \(c\) pass:

\[
\widehat{\mathrm{pass@1}} = 1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}
\]

when \(n-c \ge k\); otherwise 1. Study-wide pass@1 is the mean over tasks. Same cluster bootstrap for CI.

Implementation: `analysis.pass_at.unbiased_pass_at_k(correct, n, k)`.

### Gap closure \(G\)

Let \(p_{S,A}, p_{S,D}, p_{L,A}\) be greedy holdout pass rates.

\[
G = \frac{p_{S,D} - p_{S,A}}{p_{L,A} - p_{S,A}}
\]

Bootstrap: resample tasks jointly for the three configs; compute \(G\) each resample. If the bootstrap CI for \((p_{L,A} - p_{S,A})\) includes 0, report **\(G\) undefined** (do not impute).

## Hypothesis tests (greedy, paired on tasks)

| Test | Procedure |
| --- | --- |
| H1 (L-A > S-A) | Build discordant table on greedy pass/fail; **exact McNemar** (binomial on min\((b,c\)) of discordant counts with \(n=b+c\)) |
| H2 (NI) | One-sided 95% **lower bound** on \(p_{S,D} - p_{L,A}\) via cluster bootstrap; reject NI if lower bound > −10 pp |
| H3 (S-D vs L-B) | Two-sided bootstrap CI on \(p_{S,D} - p_{L,B}\); McNemar p-value reported |
| H4 | Apply `scripts/check_m0_bars.py` floor logic to general-coding rates for S-D vs S-A |

**Multiplicity:** Holm–Bonferroni adjustment on exact McNemar p-values for H1, H2 (as proportion test), H3 in that order.

## Effect sizes

Report paired differences in percentage points with bootstrap CIs. P-values supplement; they do not replace intervals.

## Sensitivity analyses (exploratory)

- Post-cutoff contamination subset flag
- Q8_0 vs Q4_K_M on shareable base A
- Per-category pass rates (six categories)
- RAG increment A→B per arm

## Power (protocol justification)

McNemar sample size for two-sided \(\alpha=0.05\), power 0.80:

\[
n \approx \frac{(z_{\alpha/2} + z_\beta)^2 \, p_d}{\delta^2}
\]

with \(p_d = 0.30\). See `analysis.power.mcnemar_n_required` and `python3 -m analysis power`.

## Human-rated items

Explanation tasks: rubric in holdout spec; two blinded raters; Cohen's κ on binary pass/fail agreement; disagreements adjudicated once and logged in deviations log if protocol-adjacent.

## Confirmatory vs exploratory

| Confirmatory | Exploratory |
| --- | --- |
| H1–H4, \(G\), primary greedy rate, pass@1 | Size curve M/L, quant row, per-category tables, pilot/DEV curves |