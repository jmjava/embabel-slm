# Analysis plan (frozen at holdout scoring)

Companion to [preregistration.md](preregistration.md). Confirmatory analyses use holdout rows only per domain; DEV and pilot are exploratory except for pre-declared model selection on **Embabel** DEV.

## Grounding

Greedy pass rates and paired McNemar tests use the task as the paired unit with pre-set \(\alpha=0.05\) (Dror et al., 2018; Dietterich, 1998; McNemar, 1947). Holm correction applies to the five prefix steps (Holm, 1979). Each test is one-sided: the larger prefix beats the previous prefix on the combined holdout. A step is proved when its test rejects. \(p_d=0.30\) is a power assumption only. 742 combined tasks are the sample for a 5-point step, not a second pass rule. pass@1 uses Chen et al. (2021) with \(k=5\) sampled runs at temperature 0.8; \(k\) is a budget limit, not required by the estimator. Cluster bootstrap CIs use \(B=10\,000\) resamples over tasks (Efron, 1979). Full citations and deviations: [preregistration.md § Grounding](preregistration.md#grounding). Why the sequence is sound for the claim it is allowed to make: [why-this-works.md](why-this-works.md). Work remaining before any dose is scored: [example-dose-plan.md](example-dose-plan.md).

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

### Dose steps (confirmatory)

Let \(p_{500}, p_{1000}, p_{2000}, p_{4000}, p_{8000}, p_{16000}\) be greedy pass rates on the combined holdout after each locked prefix. The prefixes are locked before authoring.

\[
\Delta_k = p_{n_k} - p_{n_{k-1}}
\]

for the successive sizes 500, 1,000, 2,000, 4,000, 8,000, and 16,000. Bootstrap: resample the 742 tasks jointly for every prefix and compute each difference on every resample. Report every step, including steps that do not reject.

### Gap closure \(G\) (exploratory)

Let \(p_{S,A}, p_{S,D}, p_{L,A}\) be greedy holdout pass rates **within one domain**.

\[
G = \frac{p_{S,D} - p_{S,A}}{p_{L,A} - p_{S,A}}
\]

Bootstrap: resample tasks jointly for the three configs; compute \(G\) each resample. If the bootstrap CI for \((p_{L,A} - p_{S,A})\) includes 0, report **\(G\) undefined** (do not impute). Report **Embabel \(G\)** and **Drivine \(G\)** separately. Comparing the two \(G\) values is exploratory, not confirmatory.

## Hypothesis tests (greedy, paired on tasks)

Tests are run on the combined holdout. Confirmatory multiplicity is Holm–Bonferroni over the five prefix tests named in the pre-registration JSON. The checks live in `analysis/practices.py`: admission, the locked prefixes, the nested list, the one-sided step decision, and the guide add-on.

| Test | Where | Procedure |
| --- | --- | --- |
| prefix_1000_minus_500 | Combined holdout | One-sided **exact McNemar**: 1,000 examples beat 500 |
| prefix_2000_minus_1000 | Combined holdout | One-sided exact McNemar: 2,000 examples beat 1,000 |
| prefix_4000_minus_2000 | Combined holdout | One-sided exact McNemar: 4,000 examples beat 2,000 |
| prefix_8000_minus_4000 | Combined holdout | One-sided exact McNemar: 8,000 examples beat 4,000 |
| prefix_16000_minus_8000 | Combined holdout | One-sided exact McNemar: 16,000 examples beat 8,000 |
| H4 | Global | Apply `scripts/check_m0_bars.py` floor logic to general-coding rates for the largest prefix versus zero examples (**one** gate, outside the prefix family) |

A step is proved when its test rejects. A miss is reported for that step. The study does not require all five rejections.

**Multiplicity:** Holm–Bonferroni on the five JSON names, in that order.

## Effect sizes

Report paired differences in percentage points with bootstrap CIs. P-values supplement; they do not replace intervals.

## Sensitivity analyses (exploratory)

- Post-cutoff contamination subset flag per domain
- Q8_0 vs Q4_K_M on shareable base A
- Per-category pass rates (Embabel six categories; Drivine five labels)
- Config C (adapter without retrieval) versus A
- Config D is the guide attached to the already trained model. Config B is the same guide on the untrained base. Both rows are references. Neither row is an example dose.
- RAG increment on arms M and L
- Embabel \(G\) vs Drivine \(G\)

## Power (protocol justification)

McNemar sample size for the one-sided confirmatory test, \(\alpha=0.05\), power 0.80:

\[
n \approx \frac{(z_{\alpha} + z_\beta)^2 \, p_d}{\delta^2}
\]

with \(p_d = 0.30\). For a 5-point difference, \(n = 742\) tasks on the combined holdout. Each prefix step uses that same exam. See `analysis.power.mcnemar_n_required(0.05, two_sided=False)`.

## Human-rated items

Explanation tasks: rubric in holdout spec; two blinded raters; Cohen's κ on binary pass/fail agreement; disagreements adjudicated once and logged in deviations log if protocol-adjacent. Drivine explanation items are secondary and excluded from the primary executable denominator.

## Confirmatory vs exploratory

| Confirmatory | Exploratory |
| --- | --- |
| Five Holm prefix tests, each later prefix minus the previous one, the 5-point practical check, primary greedy rate, pass@1, H4 | Retrieval, cross-domain \(G\), ceiling contrasts, size curve M/L, quant row, per-area tables, pilot/DEV curves |