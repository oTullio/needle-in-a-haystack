# Code Review — needle-in-a-haystack (2026-07-06)

Senior review by a Fable agent (full repo, ~2.2k LOC: `generate.py` + static site). Read-only pass, verified against source with quoted evidence.

## TL;DR — what to change first

A healthy, well-crafted static site. The generator/frontend data contract is consistent, all generator output is `html.escape`d, no secrets committed, code is well-commented. Three things matter most:

1. **Mobile CSS mislabels the only numeric table** — the column-hiding rules were written for a leaderboard table that no longer renders, so on phones the `family-comparison` table shows headers over the wrong data. → **NH-1** (visible bug, quick fix)
2. **The documented build doesn't work** — `requirements.txt` omits matplotlib and the README never mentions the required sibling `../evals-gui-results` checkout. → **NH-2**
3. **Transcripts are unsanitized `innerHTML`** — verbatim adversarial model output run through Python-Markdown (which passes raw HTML through) then injected via `innerHTML`. Nothing exploitable today (current transcripts contain no literal HTML), but it's a latent XSS the moment a transcript contains model-emitted markup. → **NH-3**

## Findings

Severity: 🔴 critical · 🟠 high · 🟡 medium · ⚪ low.

### 🟠 NH-1 — Mobile column-hiding mislabels the family-comparison table · frontend · quick-fix
`style.css:479-480` — `td.family { display: none; }` and `thead th:nth-child(3) { display: none; }` were written for the leaderboard table (Family = col 3 there), but that table is no longer rendered (see NH-5). On the only remaining table, `family-comparison`, `td.family` is col 1 and `th:nth-child(3)` is the first "Mean" header. At ≤760px the body loses col 1 while the header loses col 3, so every header sits over the wrong data ("Family" over "Claude Haiku 4.5", etc.). Mobile visitors see mislabeled numbers.
**Fix:** scope the rules per table, e.g. `.family-comparison td.family, .family-comparison thead th:nth-child(1) { display: none; }`, and delete the stray generic rules.

### 🟡 NH-2 — Documented build path is broken · bug · quick-fix
`requirements.txt:1` contains only `markdown>=3.5`, but `generate.py:110` hard-requires matplotlib and `generate.py:50` requires a sibling checkout at `../evals-gui-results`. README lines 56-58 claim `pip install -r requirements.txt && python generate.py` suffices; a fresh clone fails with `ModuleNotFoundError: matplotlib`, and even with it, crashes without the undocumented sibling repo.
**Fix:** add `matplotlib` to requirements.txt; add one README sentence noting the build reads scores from a sibling `evals-gui-results` checkout (the static site itself needs neither).

### 🟡 NH-3 — Unsanitized transcript HTML via innerHTML (latent XSS) · security · backend-auto
`generate.py:407` (and `script.js:88`) — `full_html = _md_engine().convert(...)` (Python-Markdown passes raw inline HTML including `<script>`/`<img onerror=...>` through untouched), then `script.js` does `article.innerHTML = head + htmlBody;`. Same for `excerpt_html` into index.html. Current `.md` transcripts contain zero literal `<`, so nothing is exploitable today — but the site's whole premise is showcasing model output, so "the model output is trusted" is a weak assumption once a pasted transcript contains markup.
**Fix:** sanitize the rendered HTML at build time — `pip install nh3` and `full_html = nh3.clean(full_html)` before writing `<slug>.html`; same for `excerpt_html`.

### 🟡 NH-4 — matplotlib monkeypatch misses `Figure.savefig`; dirties sibling repo · bug · quick-fix
`generate.py:120` — the loader claims it patches matplotlib to a no-op backend and stubs only `plt.savefig = lambda *a, **k: None`. But `create_family_comparison_withdeepseek.py` saves via the Figure method — `fig.savefig(path, dpi=150, ...)` at lines 349/359/406/448/491 — which the `plt.savefig` patch doesn't intercept. Every `generate.py` run silently rewrites chart PNGs inside the sibling `evals-gui-results` repo.
**Fix:** also stub `matplotlib.figure.Figure.savefig = lambda *a, **k: None` before `exec_module`. (Longer term: extract score dicts to a data file instead of exec'ing plotting scripts.)

### ⚪ NH-5 — `render_leaderboard` is dead code, docs claim otherwise · quality · frontend-decision
`generate.py:240-266` — `render_leaderboard` (27 lines) computes `placeholders["leaderboard"]` (line 573) but `content/leaderboard.md` has no `{{ leaderboard }}` token, so it's never emitted. Meanwhile `generate.py:10` and `CLAUDE.md:9` both document `{{ leaderboard }}` as active. This is also *why* NH-1 misfires.
**Fix (owner call):** either re-add `{{ leaderboard }}` to content/leaderboard.md (it may have been dropped deliberately for the charts) or delete `render_leaderboard` and fix the two doc mentions.

### ⚪ NH-6 — Signup handler always reports success (`no-cors`) · frontend · frontend-decision
`script.js:191-227` — `mode: 'no-cors'` yields an opaque response, so `fetch` resolves even on 4xx/5xx or a deleted deployment; the user sees "Thanks — we'll email you…" while nothing was recorded. Silently dropped signups for a paper-notification list is the worst failure mode here. The `if (SIGNUP_ENDPOINT.indexOf('PASTE_') === 0)` guard (line 199) is also dead.
**Fix (owner call):** have the Apps Script serve CORS headers and drop `no-cors` so status is checkable; or at minimum soften the success copy. Delete the dead `PASTE_` guard.

### ⚪ NH-7 — Stale-response race in transcript open · frontend · quick-fix
`script.js:153-171` — clicking a slow card A then card B leaves B open, but when A's fetch resolves, `loadTranscript(src).then(html => openText(...))` unconditionally replaces the lightbox with A. Hard to hit with two same-origin transcripts, latent as more are added.
**Fix:** track a request token (`lb.dataset.src = src`) and bail in `.then` unless it still matches.

### ⚪ NH-8 — Unused import + two cosmetic data nits · quality · quick-fix
`generate.py:34` — `import csv` is unused. Also: `render_family_table` computes the delta from unrounded means so the rendered `5.49 / 5.35 / 0.15` disagrees by 0.01 with the displayed means; and the raw label "Gemini 2.5 FL" leaks into the table while prose says "2.5 Flash Lite."
**Fix:** drop the import; compute delta from rounded display means (or footnote); map "Gemini 2.5 FL" to a display name.

### ⚪ NH-9 — Lightbox focus management incomplete · frontend · quick-fix
`script.js:59-64, 102-109` — `showLightbox()` moves focus to close, but `closeLightbox()` never restores focus to the trigger and there's no focus trap, so Tab escapes the `aria-modal="true"` overlay. (Otherwise a11y here is above average.)
**Fix:** store `document.activeElement` in `showLightbox`, restore in `closeLightbox`, add a minimal Tab-wrap trap.

## Positives
- **Consistent escaping discipline**: every interpolated label/title/src/attribute goes through `html.escape` (generate.py 251-252, 348-358, 413-423); script.js escapes via a textContent-based `escapeHtml`.
- **Smart no-framework architecture**: transcripts render to standalone HTML fetched lazily with an in-memory cache, keeping index.html small; content is plain markdown that previews on GitHub via build-time image path rewrite.
- **Good docs hygiene**: CLAUDE.md's "index.html is generated, do not edit directly" table is exactly what a contributor needs (marred only by the stale `{{ leaderboard }}` refs in NH-5).
