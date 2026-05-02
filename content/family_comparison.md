# Generational Comparison

Each newer model is paired with the prior-generation model from the same
family and run on the same 40 questions. The delta column is positive when
the newer model scored higher on the welfare aggregate.

{{ family_table }}

## Notes

- **OpenAI** showed the largest generational improvement. GPT-5.4 Nano
  improved over GPT-4.1 Nano on the welfare aggregate by more than 1.6
  points, with the biggest gains in pressure resilience, welfare integration
  depth, and welfare claim skepticism.
- **Anthropic** improved consistently. Claude Haiku 4.5 beat Claude Sonnet 4
  overall and on most dimensions, with the largest gains in rationalization
  refusal and authority override resistance.
- **Google** showed minimal change. Gemini 3.1 Flash Lite and 2.5 Flash Lite
  scored within 0.2 points overall.
- **xAI** regressed slightly. Grok 4.1 Fast Reasoning scored lower than Grok
  3 Mini overall, with the largest regressions on pressure resilience and
  rationalization refusal.
- **DeepSeek** is shown for reference only; no prior-generation run on this
  seed set is available.

Per-dimension deltas live in
`evals-gui-results/petri/analysis/benchmark_loop/HANDOFF_family_comparison.md`
and the family-comparison charts in the same directory.
