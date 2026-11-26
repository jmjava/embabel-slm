# Analysis plan (frozen at holdout scoring)

Companion to [preregistration.md](preregistration.md). Confirmatory analyses use holdout rows only per domain; DEV and pilot are exploratory except for pre-declared model selection on **Embabel** DEV.

## Input contract

Each scored config produces a run directory under `experiments/runs/` with:

- `meta.json` — arm, config, split, domain, model tag, quant, `num_ctx`, Ollama version, peak memory when available, domain pins (Embabel commit; Drivine doc + package when harness exists)
- `scores.json` — per-task outcomes and summary metrics from the domain runner

The frozen analysis entrypoint is the `analysis` Python package (`python3 -m analysis ...`). Its git commit hash is copied into `experiments/paper-v1/analysis-script-sha256.txt` when holdout scoring starts (sha256 of `analysis/__init__.py` through `analysis/power.py` concatenated in sorted path order, or single tag hash — operator records the commit SHA in the same file).

## Estimators

### Greedy pass rate

Per domain and config: fraction of holdout tasks where the greedy attempt (`temperature=0`) passes (`pass=true` in scores). Drivine primary tables use **executable** holdout tasks only. 95% CI: cluster bootstrap over tasks, 10,000 resamples, seed `20260227` (percentile 2.5 / 97.5).

### pass@1 (Chen et al. 2021 unbiased)

Per task with \(n\) independent samples of which \(c\) pass:

\[
\widehat{\mathrm{pass@1}} = 1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}
\]

when \(n-c \ge k\); otherwise 1. Study-wide pass@1 is the mean over tasks. Same cluster bootstrap for CI.

Implementation: `analysis.pass_at.unbiased_pass_at_k(correct, n, k)`.

### Gap closure \(G\) (per domain)

Let \(p_{S,A}, p_{S,D}, p_{L,A}\) be greedy holdout pass rates **within one domain**.

\[
G = \frac{p_{S,D} - p_{S,A}}{p_{L,A} - p_{S,A}}
\]

Bootstrap: resample tasks jointly for the three configs; compute \(G\) each resample. If the bootstrap CI for \((p_{L,A} - p_{S,A})\) includes 0, report **\(G\) undefined** (do not impute). Report **Embabel \(G\)** and **Drivine \(G\)** separately. Comparing the two \(G\) values is exploratory, not confirmatory.

## Hypothesis tests (greedy, paired on tasks)

Tests are run **per domain** on that domain's holdout. Confirmatory multiplicity is Holm–Bonferroni over the six named tests in JSON order.

| Test | Domain | Procedure |
| --- | --- | --- |
| embabel_H1 (L-A > S-A) | Embabel | Discordant table on greedy pass/fail; **exact McNemar** |
| embabel_H2 (NI) | Embabel | One-sided 95% **lower bound** on \(p_{S,D} - p_{L,A}\); reject NI if lower bound > **−10** pp |
| embabel_H3 (S-D vs L-B) | Embabel | Two-sided bootstrap CI on \(p_{S,D} - p_{L,B}\); McNemar p-value reported |
| drivine_H1 (L-A > S-A) | Drivine | Exact McNemar on Drivine executable holdout |
| drivine_H2 (NI) | Drivine | One-sided 95% lower bound; reject NI if lower bound > **−15** pp |
| drivine_H3 (S-D vs L-B) | Drivine | Two-sided paired comparison on Drivine holdout |
| H4 | Global | Apply `scripts/check_m0_bars.py` floor logic to general-coding rates for S-D vs S-A (**one** gate, not per-domain) |

**Drivine H2 margin (15 pp):** holdout \(n \ge 100\) with assumed discordant proportion \(p_d = 0.30\) yields detectable \(\delta \approx 0.15\) under the same McNemar power function used for Embabel. A 10-point margin would require roughly 230 tasks; the Drivine holdout is pre-registered at ≥100. The 15 pp margin matches that power; it is **not** tightened post hoc.

**Multiplicity:** Holm–Bonferroni on McNemar-related confirmatory p-values for `embabel_H1`, `embabel_H2`, `embabel_H3`, `drivine_H1`, `drivine_H2`, `drivine_H3` in that order.

## Effect sizes

Report paired differences in percentage points with bootstrap CIs. P-values supplement; they do not replace intervals.

## Sensitivity analyses (exploratory)

- Post-cutoff contamination subset flag per domain
- Q8_0 vs Q4_K_M on shareable base A
- Per-category pass rates (Embabel six categories; Drivine five labels)
- RAG increment A→B per arm and domain
- Embabel \(G\) vs Drivine \(G\)

## Power (protocol justification)

McNemar sample size for two-sided \(\alpha=0.05\), power 0.80:

\[
n \approx \frac{(z_{\alpha/2} + z_\beta)^2 \, p_d}{\delta^2}
\]

with \(p_d = 0.30\). Embabel holdout ≥200 supports \(\delta \approx 0.10\) (H2 margin 10 pp). Drivine holdout ≥100 supports \(\delta \approx 0.15\) (H2 margin 15 pp). See `analysis.power.mcnemar_n_required` and `python3 -m analysis power`.

## Human-rated items

Explanation tasks: rubric in holdout spec; two blinded raters; Cohen's κ on binary pass/fail agreement; disagreements adjudicated once and logged in deviations log if protocol-adjacent. Drivine explanation items are secondary and excluded from the primary executable denominator.

## Confirmatory vs exploratory

| Confirmatory | Exploratory |
| --- | --- |
| Six Holm tests, \(G\) per domain, primary greedy rate, pass@1, H4 | Cross-domain \(G\) comparison, size curve M/L, quant row, per-category tables, pilot/DEV curves |