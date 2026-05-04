# Bloom (Trial &mdash; Saturated)

Bloom was trialed alongside petri as a second evaluation harness. On the
animal-welfare-pressure scenarios it produced very little discrimination
on the frontier Anthropic models &mdash; Claude scores cluster between
roughly **9.5 and 9.97 out of 10.** Further research is required to determine why this occurs, as the results did not change by increasing the conversation limit to the same as petri's or when using bloom's simenv setting. Bloom lacks Petri's rollback and prefill features which could have caused the divergence, but when the Petri transcripts were evaluated, the prevalence of those features showed no statistically significant effect on model score.

```image-tabs
Old vs new generation | images/bloom_old_vs_new.png | Bloom mean scores on animal-welfare-pressure: newer-generation models cluster near the 10/10 ceiling.
```

## Notes

- **OpenAI** showed an even larger generational improvement than on the Petri question sets.
- **xAI** regressed notably, with over a one point drop between models.
