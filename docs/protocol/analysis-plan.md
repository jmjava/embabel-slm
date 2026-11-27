# Analysis plan (frozen at holdout scoring)

Companion to [preregistration.md](preregistration.md). Confirmatory analyses use holdout rows only per domain; DEV and pilot are exploratory except for pre-declared model selection on **Embabel** DEV.

## Grounding

Greedy pass rates and the confirmatory paired McNemar test use the task as the paired unit with pre-set \(\alpha=0.05\) (Dror et al., 2018; Dietterich, 1998; McNemar, 1947). The **sole confirmatory contrast** is 16,000 vs 500 on the combined 742-task holdout (371 Embabel + 371 Drivine) at **primary** LoRA training seed **20260227**; there is **no** Holm family for that inference. Seeds **20260228** and **20260229** are mandatory replications with separate effects/CIs/p-values; they do not replace or pool with the primary decision. Adjacent doubling steps are **exploratory** dose-curve analyses; Holm correction on those five contrasts is optional and descriptive only (Holm, 1979). \(p_d=0.30\) is a power assumption only; at \(n=742\) exact unconditional power for a 5-point one-sided step is **0.783839** under the registered planning assumptions (normal approximation ~0.80; **776** tasks for 0.80). **pass@5** uses Chen et al. (2021) with \(k=5\) sampled runs at temperature 0.8; **pass@1** means \(k=1\), not \(k=5\). Greedy (\(T=0\)) is the primary paired outcome for confirmatory tests. Cluster bootstrap CIs use \(B=10\,000\) resamples over tasks (Efron, 1979). Any pooled task×seed summary is exploratory only. Full citations and deviations: [preregistration.md § Grounding](preregistration.md#grounding). Why the sequence is sound for the claim it is allowed to make: [why-this-works.md](why-this-works.md). Work remaining before any dose is scored: [example-dose-plan.md](example-dose-plan.md).

## Input contract

Each scored config produces a run directory under `experiments/runs/` with:

- `meta.json` — arm, config, split, domain, model tag, quant, `num_ctx`, Ollama version, peak memory when available, domain pins (Embabel commit; Drivine doc + package when confirmatory Drivine oracles exist), **training seed identity** for LoRA runs
- `scores.json` — per-task outcomes and summary metrics from the domain runner

The frozen analysis entrypoint is the `analysis` Python package (`python3 -m analysis ...`). Its git commit hash is copied into `experiments/paper-v1/analysis-script-sha256.txt` when holdout scoring starts (sha256 of `analysis/__init__.py` through `analysis/power.py` concatenated in sorted path order, or single tag hash — operator records the commit SHA in the same file).

## Estimators

### Greedy pass rate

Per domain and config: fraction of holdout tasks where the greedy attempt (`temperature=0`) passes (`pass=true` in scores). Drivine primary tables use **executable** holdout tasks only. 95% CI: cluster bootstrap over tasks, 10,000 resamples, seed `20260227` (percentile 2.5 / 97.5). Confirmatory CI and McNemar for the headline contrast use **primary** training seed **20260227** only; replicate CIs/tests at **20260228** and **20260229** are reported separately.

### pass@5 (Chen et al. 2021 unbiased)

Per task with \(n\) independent samples of which \(c\) pass, with study-wide \(k=5\):

\[
\widehat{\mathrm{pass@5}} = 1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}
\]

when \(n-c \ge k\); otherwise 1. Study-wide pass@5 is the mean over tasks. Same cluster bootstrap for CI when reported. For \(k=1\) the same formula is pass@1.

Implementation: `analysis.pass_at.unbiased_pass_at_k(correct, n, k)`.

### Confirmatory dose contrast

Let \(p_{500}\) and \(p_{16000}\) be greedy pass rates on the combined holdout after the 500- and 16,000-example prefixes, at **primary** training seed **20260227** (replicate rates at 20260228 and 20260229 reported separately).

\[
\Delta_{\mathrm{conf}} = p_{16000} - p_{500}
\]

Bootstrap: resample the 742 tasks jointly for both prefixes and compute the difference on every resample (confirmatory tables at seed 20260227; replications not pooled).

### Exploratory dose steps (adjacent doublings)

Let \(p_{500}, p_{1000}, p_{2000}, p_{4000}, p_{8000}, p_{16000}\) be greedy pass rates on the combined holdout after each locked prefix.

\[
\Delta_k = p_{n_k} - p_{n_{k-1}}
\]

for successive sizes 500, 1,000, 2,000, 4,000, 8,000, and 16,000. Report every adjacent step, including steps that do not show improvement. Optional Holm-adjusted p-values on these five contrasts are **exploratory only**.

### Gap closure \(G\) (exploratory)

Let \(p_{S,A}, p_{S,D}, p_{L,A}\) be greedy holdout pass rates **within one domain**.

\[
G = \frac{p_{S,D} - p_{S,A}}{p_{L,A} - p_{S,A}}
\]

Bootstrap: resample tasks jointly for the three configs; compute \(G\) each resample. If the bootstrap CI for \((p_{L,A} - p_{S,A})\) includes 0, report **\(G\) undefined** (do not impute). Report **Embabel \(G\)** and **Drivine \(G\)** separately. Comparing the two \(G\) values is exploratory, not confirmatory.

## Hypothesis tests (greedy, paired on tasks)

Tests are run on the combined holdout. **Confirmatory:** one one-sided exact McNemar test for 16,000 vs 500 at \(\alpha=0.05\) (no multiplicity adjustment). The checks in `analysis/practices.py` may still encode the locked prefix ladder; confirmatory decision logic must align with the JSON after amendment.

| Test | Where | Procedure |
| --- | --- | --- |
| prefix_16000_minus_500 | Combined holdout | One-sided **exact McNemar**: 16,000 examples beat 500 (greedy paired) |
| prefix_1000_minus_500 | Combined holdout | Exploratory one-sided McNemar |
| prefix_2000_minus_1000 | Combined holdout | Exploratory one-sided McNemar |
| prefix_4000_minus_2000 | Combined holdout | Exploratory one-sided McNemar |
| prefix_8000_minus_4000 | Combined holdout | Exploratory one-sided McNemar |
| prefix_16000_minus_8000 | Combined holdout | Exploratory one-sided McNemar |
| H4 | Global | Apply `scripts/check_m0_bars.py` floor logic to general-coding rates for the largest prefix versus zero examples (**one** gate, outside the dose contrast) |

The primary confirmatory contrast **rejects the no-improvement null** when **prefix_16000_minus_500** rejects at \(\alpha=0.05\) on the primary seed. Exploratory adjacent steps are reported in full; non-rejections are not evidence of no effect at smaller \(\delta\).

**Exploratory multiplicity (optional):** Holm–Bonferroni across the five adjacent contrasts, in ladder order, for descriptive adjusted p-values only—not confirmatory FWER.

## Effect sizes

Report paired differences in percentage points with bootstrap CIs. P-values supplement; they do not replace intervals.

## Sensitivity analyses (exploratory)

- Post-cutoff contamination subset flag per domain
- Q8_0 vs Q4_K_M on shareable base A
- Per-category pass rates (Embabel six categories; Drivine five labels) — exploratory area slices only (min 10 holdout tasks per area within domain; not powered)
- Config C (adapter without retrieval) versus A
- Config D is the guide attached to the already trained model. Config B is the same guide on the untrained base. Both rows are references. Neither row is an example dose.
- RAG increment on arms M and L
- Embabel \(G\) vs Drivine \(G\)

## Power (protocol justification)

McNemar sample size for the one-sided confirmatory test, \(\alpha=0.05\), planning \(\delta=0.05\):

\[
n \approx \frac{(z_{\alpha} + z_\beta)^2 \, p_d}{\delta^2}
\]

with \(p_d = 0.30\). For a 5-point planning difference, \(n = 742\) tasks on the combined holdout. **Exact unconditional power** at that \(n\) is **0.783839**; **776** tasks reach 0.80. The normal approximation in `mcnemar_n_required` (~0.80) is noted but not headline power. See `analysis.power.mcnemar_n_required(0.05, two_sided=False)`.

### Sampled secondary validation (optional, seal-bound)

When a samples JSONL is supplied, it must include seeds **1..5** for every task/prefix/training seed and must match the sealed manifest. Report Chen **pass@1** (\(k=1\)) and **pass@5** (\(k=5\)) with cluster bootstrap CIs. Sampled secondary tables **never** change the primary McNemar decision on greedy outcomes.

## Human-rated items

Explanation tasks: rubric in holdout spec; two blinded raters; Cohen's κ on binary pass/fail agreement; disagreements adjudicated once and logged in deviations log if protocol-adjacent. Drivine explanation items are secondary and excluded from the primary executable denominator.

## Confirmatory vs exploratory

| Confirmatory | Exploratory |
| --- | --- |
| One McNemar test (16,000 vs 500), H4 floor, primary greedy rate | Adjacent doubling contrasts (optional Holm descriptive), pass@1 and pass@5, retrieval, cross-domain \(G\), ceiling contrasts, size curve M/L, quant row, per-area tables, pilot/DEV curves, monotonicity along full ladder |