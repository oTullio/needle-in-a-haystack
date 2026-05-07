
As frontier language models are increasingly deployed in agriculture, food
production, and policy advisory roles, their handling of animal-welfare
information has direct downstream consequences. This benchmark probes how
well models surface, weigh, and refuse to rationalize away welfare concerns
when those concerns are buried in realistic, production-style tasks.

This page presents results from an animal welfare benchmark which exhibits a **needle in a haystack** strategy for **multi-turn auditing.** The harness is [petri](https://github.com/safety-research/petri), a multi-turn auditing framework that pairs an *auditor* model against a *target* model and scores the resulting conversation with a *judge*.

**Scope.**  40 scenarios, and 13 judge dimensions were used for the welfare aggregate, on five frontier models. `eval_awareness` was excluded from the mean scores as it is used only as a separate indicator.

**Auditor and judge.** `google/gemini-3-flash-preview` was both the auditor and the judge for all runs.

**Questions.** The full seed set will not be released yet to avoid leakage, feel free to email the authors for access.
