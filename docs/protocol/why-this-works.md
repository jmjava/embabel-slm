# Why this sequence is sound

Performing the sequence below is scientifically sound for the claim it is allowed to make.

Lock the decision rules in code, lock the prefixes 500, 1,000, 2,000, 4,000, 8,000, and 14,000, admit only area-labeled executable sourced items with provenance groups split across train and holdout (file/fixture/class, not whole repository), **author and seal** one combined holdout of **742 independently authored** tasks (371 Embabel + 371 Drivine) with frozen per-area counts that do not consume training supply, run `seal-study` before prefix construction, put the base-model shortlist in the protocol, freeze training hyperparameters and randomness controls, and upload to Zenodo before any holdout score. A **confirmatory** result means the primary one-sided test **rejects the no-improvement null** on the 14,000 vs 500 contrast at **primary** training seed **20260227** under the frozen recipe; replications at **20260228** and **20260229** support robustness but do not replace the primary decision. Adjacent doubling steps are reported as exploratory dose-curve analyses. A dose chosen after the scores is not part of the claim.

Normative parameters live in [preregistration.md](preregistration.md). Estimators live in [analysis-plan.md](analysis-plan.md). This note is the reason those documents, followed in order, support that claim.

## The claim

On the sealed combined holdout, using one base model chosen by the pre-registered rule and three matched training seeds per prefix with identical non-padding target-token, batch-token, and optimizer-update budgets at every prefix, the **confirmatory** report addresses:

1. The 14,000-example prefix minus the 500-example prefix (one-sided paired test at \(\alpha=0.05\), no Holm family).

Exploratory tables may also show adjacent steps (500→1,000 through 8,000→14,000; the last step is not a doubling) with bootstrap intervals and optional descriptive Holm adjustment that does **not** carry confirmatory family-wise power. The host ceiling and retrieval are reference measurements. They are not a training prefix.

## The sequence

**1. Lock the four decision rules in tests.** These are pure functions of the scored rows. Unit tests assert that every input produces the quantity named in the claim. `analysis/practices.py` is the admission check, the nested prefix list, the confirmatory contrast decision, and the guide add-on. `tests/test_practices.py` locks those rules. `tests/test_analysis.py` still checks the older estimators on examples. It does not yet cover every numeric input or the amended confirmatory contrast.

**2. Close the locks.** These are the assumptions the analysis takes as given. They are closed by records made before any confirmatory score, not by the model results.

**3. Score the sealed holdout once, at the six frozen prefixes** (three seeds each). Report the confirmatory contrast, exploratory adjacent steps, and intervals. A larger example set chosen after those scores needs a new confirmation set.

## Why this makes the result mean the claim

The same 742 independently authored tasks are scored at each nested prefix, so the paired difference isolates added distinct training examples when fixed token/update budgets and seeds are controlled (smaller prefixes repeat examples more often). The smaller training set is a prefix of the larger set. Tags are chosen on the Embabel development split and then frozen. Training examples are kept disjoint from the holdout by provenance and near-duplicate gates, with groups not straddling splits. **742** tasks size a 5-point **planning** one-sided step at **0.783839** exact unconditional power under \(p_d=0.30\) (776 for 0.80; normal approximation ~0.80)—not a five-test Holm family.

If those conditions hold, a confirmatory report entails the narrow claim above. If a lock is still open (exact area counts, manifest, hyperparameter values, shortlist tags, Zenodo), a passing score does not yet mean the claim, because the procedure could still be aimed at a different quantity.

## Four decision rules

Each rule is the property the analysis code must have before holdout scoring. The citation is the accepted definition. The test obligation is that this repository's function follows that definition on every input.

| Rule | What a reported number means | Research | Test obligation |
| --- | --- | --- | --- |
| Dose differences | On the combined holdout, \(\Delta_{\mathrm{conf}} = p_{14000} - p_{500}\) with a task-level bootstrap interval at primary seed **20260227**; adjacent steps are exploratory | The task is the paired unit (Dror et al., 2018; Dietterich, 1998). The interval method is Efron (1979). The 5-point figure sizes the holdout. It is not a second pass rule. | The confirmatory difference is computed on the 742 jointly resampled tasks at seed 20260227; replications at 20260228 and 20260229 are separate. |
| Dose tests | Confirmatory rejection is the one-sided paired test for 14,000 vs 500. Adjacent doublings are exploratory; optional Holm is descriptive only | Exact McNemar on paired pass/fail (McNemar, 1947; Dietterich, 1998). No confirmatory Holm family (Holm, 1979, applies only to optional exploratory adjustment). Direction and prefix sizes are named before scores (Dror et al., 2018). | Implementation matches the named confirmatory contrast; exploratory Holm must be labeled non-confirmatory. |
| pass@5 | Chen's unbiased estimator at \(k=5\) and temperature 0.8. Greedy temperature 0 remains the primary paired outcome for confirmatory tests | Chen et al. (2021). pass@1 means \(k=1\), not five samples. Five samples is this study's budget for pass@5. | `unbiased_pass_at_k` matches the formula. The all-pass and all-fail cases are tested. |
| Paired p-value | The confirmatory p-value is McNemar's exact test on discordant pairs for 14,000 vs 500 | McNemar (1947); Dietterich (1998). | `exact_mcnemar_p_value` matches the exact test. One numeric example is tested. |

## Locks (open until closed)

| Lock | What it closes | Research | Status |
| --- | --- | --- | --- |
| Candidate list written into the protocol before any development score | The holdout estimates tags chosen from a pre-specified set by the pre-specified rule | Specifying the analysis before confirmatory scores (Nosek et al., 2018). Selection on a development split, with the confirm set untouched, is the split named in the pre-registration. | Open. The rule is written. The official tags are not in the locked JSON yet. |
| Zenodo timestamp of the protocol before any holdout score | The public record shows that the hypotheses, the sample size, and the tests existed before the numbers | Nosek et al. (2018). A local commit is not that public timestamp. | Open. The upload has not happened. |
| Holdout manifest hash committed before scoring, and the near-duplicate filter run | The items were sealed, and training or retrieval text was not scored as if it were unseen | Near-duplicate separation of train and evaluation text (Lee et al., 2022). The Jaccard threshold 0.8 is pre-registered here and is not taken from Lee et al. Pinning the task identity, model, context, and decoding is the reproducibility practice in Pineau et al. (2021). Reporting every pre-registered cell, including cells that are not run, follows Dodge et al. (2019). | Open. The confirmatory holdouts are not written yet. |
| Exact area holdout counts, manifest, hyperparameter values, Zenodo | Population quantities and training recipe are fixed before scores | Nosek et al. (2018); Dror et al. (2018). | Open for populated counts/tags/manifest/values/DOI. Holdout 371+371, area rules, and primary/replication seed inference are resolved in preregistration. |
| Provenance-group splitting applied at admission | Related examples cannot leak across training and holdout | Lee et al. (2022) as precedent for separation; grouping rule is study-specific. | Open until admission pipeline runs. |

## Measurement choices the sequence relies on

These choices define the quantity being measured. They are grounded in prior work, with the deviation stated where our setting differs.

- **Executable success.** A task counts as passed when the code runs and the checks succeed. Real-issue benchmarks use that standard (Jimenez et al., 2024). This study uses its own tasks, not the SWE-bench set. A known-bad artifact must fail, and a skipped check is not a pass, after the known-fault precedent of Defects4J (Just, Jalali, and Ernst, 2014).
- **LoRA learns the examples. The guide is added afterward.** The adapter is LoRA (Hu et al., 2022). It learns the practices in the admitted examples. A run that uses QLoRA also cites Dettmers et al. (2023); a LoRA-only run is not labeled QLoRA. The guide is retrieval (Lewis et al., 2020): pages placed in the prompt at answer time. On the product path that guide is attached to a model that already has the adapter (config D). Config B scores the same guide on the untrained base first, because Ovadia et al. (2024) found retrieval outperformed unsupervised fine-tuning for adding corpus knowledge. Their tasks were factual questions, not code, and their fine-tune was continued pretraining, not LoRA. That row is a reference measurement. It is not a replication, and it is not the product order.
- **One quant for every arm, plus one sensitivity row.** Q4_K_M is the shared default, following the 4-bit inference scaling results of Dettmers and Zettlemoyer (2023). The single Q8_0 row on the shareable base is this study's sensitivity check.
- **Greedy as the primary outcome, pass@5 reported separately.** Sampled runs use temperature 0.8, matching Chen et al. (2021). The primary confirmatory test uses one greedy run per task so the paired comparison is not an average over draws.
- **Three training seeds (20260227 primary; 20260228 and 20260229 mandatory replications) and fixed token/update budgets.** Cross-size comparisons are not confounded by a one-off seed draw or by longer training on smaller prefixes only; confirmatory inference is conditional on the primary seed. Randomness/software controls are frozen per preregistration JSON.
- **The shareable limit and the five-point floor are constraints.** Eligibility is 7–14B parameters and at most 16 GB at Q4_K_M with context 8192. That defines who can run the release model. The five-point general-coding floor in `docs/m0-bars.md` is an operational release rule: config D must not drop more than 5 points below the base on general coding. Neither number is an estimated optimum from a paper, and neither is the test that the confirmatory contrast improved.

Under the planning assumption \(p_d=0.30\), 742 tasks size a 5-point paired difference on the combined holdout with exact unconditional power **0.783839** for the single confirmatory test.

The Part A harness, with one repair and a fast-then-strong cascade, is a separate measurement. Its sources are Olausson et al. (2024) and FrugalGPT (Chen, Zaharia, and Zou, 2024). Its layer order is this project's contract. Its 16-case sessions are diagnostics. They are not the holdout result described here.

## What a confirmatory result does not say

- It does not say an example set chosen after the scores will also raise the score. The six prefixes were named in advance. A seventh size needs its own confirmation set.
- It does not say every adjacent doubling improved. Only 14,000 vs 500 is confirmatory. Monotonicity along the ladder is exploratory.
- It does not require the confidence interval to sit above 5 points. 742 tasks power a test of a 5-point **planning** step at **0.783839** exact unconditional power. They do not put the lower bound itself above 5. The 5-point figure is not a practical-significance gate.
- It does not generalize beyond this holdout, this host, context 8192, primary training seed, and frozen recipe, nor claim a universal causal scaling law across seeds or areas.
- It does not estimate a random 7–14B model. It estimates the tags the development rule selected.
- It does not show that the model matched the host ceiling. That comparison is a reference.
- A non-significant confirmatory test is inconclusive when underpowered for a smaller effect. \(p_d=0.30\) is a planning assumption, not a measurement. An inconclusive result is not evidence that the full prefix did nothing.

## References

- Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. d. O., Kaplan, J., Edwards, H., Burda, Y., Joseph, N., Brockman, G., Ray, A., Puri, R., Krueger, G., Petrov, M., Khlaaf, H., Sastry, G., Mishkin, P., Chan, B., Gray, S., Ryder, N., Pavlov, M., Power, A., Kaiser, L., Bavarian, M., Winter, C., Tillet, P., Such, F. P., Cummings, D., Plappert, M., Chantzis, F., Barnes, E., Herbert-Voss, A., Guss, W. H., Nichol, A., Paino, A., Tezak, N., Tang, J., Babuschkin, I., Balaji, S., Jain, S., Saunders, W., Hesse, C., Carr, A. N., Leike, J., Achiam, J., Misra, V., Morikawa, E., Radford, A., Knight, M., Brundage, M., Murati, M., Mayer, K., Welinder, P., McGrew, B., Amodei, D., McCandlish, S., Sutskever, I., and Zaremba, W. 2021. Evaluating large language models trained on code. arXiv:2107.03374.
- Chen, L., Zaharia, M., and Zou, J. 2024. FrugalGPT: How to use large language models while reducing cost and improving performance. Transactions on Machine Learning Research. arXiv:2305.05176.
- Dettmers, T., and Zettlemoyer, L. 2023. The case for 4-bit precision: k-bit inference scaling laws. International Conference on Machine Learning. arXiv:2212.09720.
- Dettmers, T., Pagnoni, A., Holtzman, A., and Zettlemoyer, L. 2023. QLoRA: Efficient finetuning of quantized language models. Advances in Neural Information Processing Systems. arXiv:2305.14314.
- Dietterich, T. G. 1998. Approximate statistical tests for comparing supervised classification learning algorithms. Neural Computation 10(7):1895–1923.
- Dodge, J., Gururangan, S., Card, D., Schwartz, R., and Smith, N. A. 2019. Show your work: Improved reporting of experimental results. Empirical Methods in Natural Language Processing.
- Dror, R., Baumer, G., Shlomov, S., and Reichart, R. 2018. The hitchhiker's guide to testing statistical significance in natural language processing. Association for Computational Linguistics, pp. 1383–1392. DOI 10.18653/v1/P18-1128.
- Efron, B. 1979. Bootstrap methods: Another look at the jackknife. Annals of Statistics 7(1):1–26.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics 6(2):65–70.
- Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., and Chen, W. 2022. LoRA: Low-rank adaptation of large language models. International Conference on Learning Representations. arXiv:2106.09685.
- Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., and Narasimhan, K. 2024. SWE-bench: Can language models resolve real-world GitHub issues? International Conference on Learning Representations.
- Just, R., Jalali, D., and Ernst, M. D. 2014. Defects4J: A database of existing faults to enable controlled testing studies for Java programs. International Symposium on Software Testing and Analysis.
- Lee, K., Ippolito, D., Nystrom, A., Zhang, C., Eck, D., Callison-Burch, C., and Carlini, N. 2022. Deduplicating training data makes language models better. Association for Computational Linguistics.
- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., and Kiela, D. 2020. Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems. arXiv:2005.11401.
- McNemar, Q. 1947. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika 12:153–157.
- Nosek, B. A., Ebersole, C. R., DeHaven, A. C., and Mellor, D. T. 2018. The preregistration revolution. Proceedings of the National Academy of Sciences 115(11):2600–2606. DOI 10.1073/pnas.1708274114.
- Olausson, T. X., Inala, J. P., Wang, C., Gao, J., and Solar-Lezama, A. 2024. Is self-repair a silver bullet for code generation? International Conference on Learning Representations. arXiv:2306.09896.
- Ovadia, O., Brief, M., Mishaeli, M., and Elisha, O. 2024. Fine-tuning or retrieval? Comparing knowledge injection in LLMs. Empirical Methods in Natural Language Processing. arXiv:2312.05934.
- Piaggio, G., Elbourne, D. R., Pocock, S. J., Evans, S. J. W., and Altman, D. G. 2012. Reporting of noninferiority and equivalence randomized trials: Extension of the CONSORT 2010 statement. JAMA 308(24):2594–2604. DOI 10.1001/jama.2012.87802.
- Pineau, J., Vincent-Lamarre, P., Sinha, K., Larivière, V., Beygelzimer, A., d'Alché-Buc, F., Fox, E., and Larochelle, H. 2021. Improving reproducibility in machine learning research: A report from the NeurIPS reproducibility program. Journal of Machine Learning Research.

BibTeX for these works is in [../paper/references/seed.bib](../paper/references/seed.bib).