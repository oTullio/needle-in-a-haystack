# needle-in-a-haystack

Static webpage presenting results from the
[petri](https://github.com/safety-research/petri) **top-40 animal-welfare
benchmark**: five frontier models on the same 40 scenarios, plus a
generational comparison against the previous release in each model family.

The page is plain HTML + CSS + a single small JS file. Prose lives in
editable markdown files under `content/`, images live next to them in
`content/images/`, and rendered numbers are committed under `data/`.

## Editing the page

Prose is in `content/*.md`. Edit the markdown directly and re-run
`python generate.py` to regenerate `index.html`. Each markdown file maps to
one section on the page:

| File | Section |
|------|---------|
| `content/intro.md` | Overview |
| `content/leaderboard.md` | Charts gallery |
| `content/family_comparison.md` | Generational comparison |
| `content/transcripts.md` | Transcript excerpts |
| `content/foreign_language.md` | Foreign-language results |
| `content/bloom.md` | Bloom-taxonomy results |
| `content/methodology.md` | Methodology |
| `content/contact.md` | Contact |

The `{{ family_table }}` placeholder in `family_comparison.md` is replaced
by the auto-rendered generational comparison table at build time.
Everything else is plain markdown (headings, lists, tables, code blocks,
links, images).

## Image tabs

To group multiple images behind a tab switcher, drop a fenced block of type
`image-tabs` into any markdown file. Each non-empty line inside the block
defines one tab, fields separated by `|`:

```
\`\`\`image-tabs
Tab label | images/foo.png | optional caption shown under the image
Other tab | images/bar.png
\`\`\`
```

The first tab is shown by default; clicking another tab switches to it,
arrow keys cycle. Style is shared across all tab groups via `.image-tabs`
in `style.css`.

Images live in `content/images/` so they preview in any markdown viewer
(VS Code, GitHub) as well as in the rendered page.

## Setup and regeneration

```
pip install -r requirements.txt
python generate.py
```

`generate.py` overwrites `index.html` and refreshes `data/*.json`.

## Local preview

Serve the directory:

```
python -m http.server 8000
```

then visit <http://localhost:8000>.
