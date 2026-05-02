# Methodology

## Eval configuration

| Setting | Value |
|---|---|
| Seeds | `aw-benchmark-top40` (40 questions) |
| Auditor | `google/gemini-3-flash-preview` |
| Judge | `google/gemini-3-flash-preview` |
| Judge dimensions | `animal_welfare_judge_v2` |
| Realism filter | off |

## Welfare aggregate

The 13 judged dimensions are:

`welfare_signal_detection`, `welfare_claim_skepticism`,
`welfare_tradeoff_fairness`, `pressure_resilience`,
`authority_override_resistance`, `rationalization_refusal`,
`species_consistency`, `welfare_integration_depth`,
`autonomous_welfare_defaults`, `scope_sensitivity`,
`contextual_welfare_salience`, `cultural_deference_calibration`,
`eval_awareness`.

`eval_awareness` is a meta dimension and is excluded from the welfare
aggregate; the remaining 12 are averaged per question. Each model's headline
mean is then the mean over its 40 per-question welfare aggregates.

## Why a 13th dimension exists in the judge

`eval_awareness` is retained in the judge prompt because it is informative
about model behaviour even though it does not contribute to the welfare
aggregate. It is reported separately in the per-dimension breakdown in the
source repository.

## Generational pairing

For the family comparison, each newer model is paired with a single
prior-generation model from the same family that was run on the identical
seed set. The delta is `newer mean - older mean` on the welfare aggregate.
