# Repo build notes

## index.html is generated — do not edit directly

`index.html` is built by `generate.py` from:

- `content/<section>.md` for prose (intro, leaderboard, family_comparison, foreign_language, bloom, transcripts, methodology)
- The HTML page shell baked into `PAGE_TMPL` inside `generate.py`
- Auto-generated tables (`{{ leaderboard }}`, `{{ family_table }}`) computed from `../evals-gui-results/`

Running `python generate.py` overwrites `index.html` and `data/*.json`. Any direct edit to `index.html` will be lost on the next build.

### Where to make changes

| Change                                | Edit                                       |
| ------------------------------------- | ------------------------------------------ |
| Section prose / ordering within section | `content/<section>.md`                     |
| Section ordering on page              | `PAGE_TMPL` in `generate.py`               |
| Transcript excerpt + metadata         | ` ```transcript ``` ` block in `content/transcripts.md` |
| Full transcript body                  | `content/transcripts/<slug>.md` (rendered to `<slug>.html` at build) |
| Image-tabs widget                     | ` ```image-tabs ``` ` block in the relevant `.md` |
| Card / button HTML emitted per transcript | `_render_transcript` in `generate.py`      |
| Page shell (header, footer, hero, script tags) | `PAGE_TMPL` in `generate.py`               |
| Tab widget emitted HTML               | `_render_image_tabs` in `generate.py`      |

### Custom fenced blocks in markdown

- ` ```image-tabs ``` ` — one tab per non-empty line, fields pipe-separated: `Label | path | optional caption`. Paths use `images/foo.png` and get rewritten to `content/images/foo.png` at build.
- ` ```transcript slug=... title="..." source="..." ``` ` — body is the markdown excerpt rendered into the card. `slug` must match a file at `content/transcripts/<slug>.md`, which is rendered to `content/transcripts/<slug>.html` and fetched lazily by `script.js` on click.

### Verifying changes

```
python generate.py
```

prints summaries of what it wrote and overwrites `index.html`. Diff-check the result before committing.
