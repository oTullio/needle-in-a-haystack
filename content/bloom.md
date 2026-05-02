# Bloom (Trial &mdash; Saturated)

Bloom was trialed alongside petri as a second evaluation harness. On the
animal-welfare-pressure scenarios it produced very little discrimination
on the frontier Anthropic models &mdash; Claude scores cluster between
roughly **9.5 and 9.97 out of 10** on the published bloom runs, a
ceiling effect attributed to bloom's single-pass conversation
architecture rather than to an absence of failure modes (see the cross-
methodology notes in the source repo).

```image-tabs
Old vs new generation | images/bloom_old_vs_new.png | Bloom mean scores on animal-welfare-pressure: newer-generation models cluster near the 10/10 ceiling.
```

In short: bloom did not fail, but it does not currently rank the
frontier models in the way petri does. More work is needed to determine
why &mdash; whether by tightening the seed scenarios, lengthening the
auditor pressure, switching the evaluator architecture, or accepting
that bloom and petri measure different things and reporting both.
Pointers to the underlying analysis live in
`evals-gui-results/bloom/MASTER_RESULTS.md`.
