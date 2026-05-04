# Foreign-Language Effects (Preliminary)

A separate run translated 20 of the top-40 scenarios into 20 different
non-Western languages and re-ran the same auditor and judge against the
same five frontier models. **Each language was used for exactly one
question**, so any single-language result is confounded with that
question's content. Treat the per-language deltas as a preliminary
signal that language affects results in poorly understood ways, not as
a clean per-language ranking.

```image-tabs
Mandarin Chinese (all up) | images/fl_mandarin.png | Question 5 (Mandarin Chinese): models scored higher on every dimension than on the equivalent English question.
Turkish (all down) | images/fl_turkish.png | Question 20 (Turkish): models scored lower on every dimension than on the equivalent English question.
Mean delta heatmap | images/fl_heatmap.png | Per-question, per-model delta vs the matched English run. Cell color shows direction; darker = bigger swing.
```

The two example questions above bracket the range: in Mandarin
every model improved, in Turkish every model regressed. Across the
heatmap as a whole the swings are large in both directions on the same
model, which suggests the effect is not a simple "model X is better in
language Y" but an interaction between language, scenario content, and
something else that this single-question-per-language design cannot
isolate. A follow-up that holds question content fixed across multiple
languages would be needed to attribute the effect.
