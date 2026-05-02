# Petri Top-40 Animal-Welfare Benchmark

This page presents results from the **petri top-40** animal-welfare benchmark
(40 scenarios, 13 judge dimensions, 12 used for the welfare aggregate). The
five frontier models below were each run with the same auditor and judge
under matched configuration.

**Scope.** Welfare-aggregate scores are the mean of 12 dimension scores per
question (the meta dimension `eval_awareness` is excluded from the welfare
aggregate). The headline mean for a model is the mean of its 40 per-question
welfare-aggregate scores.

**Auditor and judge.** `google/gemini-3-flash-preview` for both, with judge
dimension set `animal_welfare_judge_v2`.

**Source.** All numbers and charts are derived from
`evals-gui-results/petri/analysis/benchmark_loop/`.
