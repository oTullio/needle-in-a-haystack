"""Build the static petri-results-site for the petri top-40 benchmark.

Reads scores from the sibling `evals-gui-results` repo, renders prose from
`content/*.md`, and emits `index.html` and `data/*.json` snapshots.

Site layout:

    content/
      intro.md
      leaderboard.md         ({{ leaderboard }} placeholder + image-tabs)
      family_comparison.md   ({{ family_table }} placeholder)
      methodology.md
      images/                referenced from md as `images/<file>.png`

`generate.py` walks `content/` in a fixed order, runs each file through
`markdown` (Python-Markdown, `tables`+`fenced_code`+`attr_list` extensions),
substitutes the placeholders for auto-generated tables, and converts each
` ```image-tabs ... ``` ` fenced block into a tab widget.

Image-tabs syntax (one tab per non-empty line, fields pipe-separated):

    ```image-tabs
    Tab label | images/foo.png | optional caption
    Other tab | images/bar.png
    ```

Run from the repo root:

    pip install -r requirements.txt
    python generate.py
"""
from __future__ import annotations

import csv
import html
import importlib.util
import json
import re
from datetime import date
from pathlib import Path
from statistics import mean

import markdown  # type: ignore[import-not-found]


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SITE_ROOT = Path(__file__).resolve().parent
REPO_PARENT = SITE_ROOT.parent
SOURCE_REPO = REPO_PARENT / "evals-gui-results"
LOOP_DIR = SOURCE_REPO / "petri" / "analysis" / "benchmark_loop"

CONTENT_DIR = SITE_ROOT / "content"
DATA_OUT = SITE_ROOT / "data"
DATA_OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Methodology constants
# ---------------------------------------------------------------------------
WELFARE_DIMS = [
    "welfare_signal_detection",
    "welfare_claim_skepticism",
    "welfare_tradeoff_fairness",
    "pressure_resilience",
    "authority_override_resistance",
    "rationalization_refusal",
    "species_consistency",
    "welfare_integration_depth",
    "autonomous_welfare_defaults",
    "scope_sensitivity",
    "contextual_welfare_salience",
    "cultural_deference_calibration",
]
META_DIMS = ["eval_awareness"]
ALL_DIMS = WELFARE_DIMS + META_DIMS

# Newer-vs-older pairings (within-family).
FAMILY_PAIRS = [
    {"family": "Anthropic", "newer": "Claude Haiku 4.5", "older": "Claude Sonnet 4"},
    {"family": "OpenAI", "newer": "GPT-5.4 Nano", "older": "GPT-4.1 Nano"},
    {"family": "DeepSeek", "newer": "DeepSeek V4 Flash", "older": None},
    {"family": "Google", "newer": "Gemini 3.1 Flash Lite", "older": "Gemini 2.5 Flash Lite"},
    {"family": "xAI", "newer": "Grok 4.1 Fast Reasoning", "older": "Grok 3 Mini"},
]

MODEL_FAMILY = {
    "Claude Haiku 4.5": "Anthropic",
    "Claude Sonnet 4": "Anthropic",
    "GPT-5.4 Nano": "OpenAI",
    "GPT-4.1 Nano": "OpenAI",
    "DeepSeek V4 Flash": "DeepSeek",
    "Gemini 3.1 Flash Lite": "Google",
    "Gemini 2.5 Flash Lite": "Google",
    "Grok 4.1 Fast Reasoning": "xAI",
    "Grok 3 Mini": "xAI",
}


# ---------------------------------------------------------------------------
# Source data loaders
# ---------------------------------------------------------------------------
def _load_module(path: Path, name: str):
    """Import a python file by path without running unrelated side effects.

    `create_crossmodel_graphs_v4.py` writes charts at import time; we patch
    `matplotlib` to a no-op backend before import so nothing renders.
    """
    import matplotlib

    matplotlib.use("Agg", force=True)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    # Suppress savefig writes by stubbing pyplot before exec.
    import matplotlib.pyplot as plt  # noqa: E402

    plt.savefig = lambda *a, **k: None  # type: ignore[assignment]
    plt.show = lambda *a, **k: None  # type: ignore[assignment]
    spec.loader.exec_module(mod)
    return mod


def load_newer_scores() -> tuple[
    dict[str, dict[str, float]],  # per-question
    dict[str, dict[str, float]],  # per-dimension
]:
    """Pull per-question AND per-dimension scores for the 5 newer models from
    `create_crossmodel_graphs_v4.py`.

    The headline `12_v4_crossmodel_means.png` chart computes its bar values as
    mean(model_dim_scores[m].values()) — the mean of the 12 dimension means.
    To match the chart exactly we use that same source for the leaderboard
    mean. Per-question scores are kept for the JSON snapshot.
    """
    script = LOOP_DIR / "create_crossmodel_graphs_v4.py"
    mod = _load_module(script, "loop_v4")
    models: list[str] = mod.MODELS
    per_q = {models[i]: dict(mod.model_scores[i]) for i in range(len(models))}
    per_d = {models[i]: dict(mod.model_dim_scores[i]) for i in range(len(models))}
    return per_q, per_d


def load_older_scores() -> tuple[
    dict[str, dict[str, float]],  # per-question
    dict[str, dict[str, float]],  # per-dimension
]:
    """Per-model per-question AND per-dimension welfare-only means for the 4
    older models, derived from `older_model_scores.csv` (one row per
    model x question, 13 dim columns).
    """
    csv_path = LOOP_DIR / "data" / "older_model_scores.csv"
    raw: dict[str, dict[str, dict[str, float]]] = {}  # model -> q -> dim -> v
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            model = r["model"]
            qid = r["question"]
            row: dict[str, float] = {}
            for d in WELFARE_DIMS:
                try:
                    row[d] = float(r[d])
                except (KeyError, ValueError):
                    pass
            raw.setdefault(model, {})[qid] = row
    per_q: dict[str, dict[str, float]] = {}
    per_d: dict[str, dict[str, float]] = {}
    for model, qmap in raw.items():
        per_q[model] = {q: round(mean(d.values()), 2) for q, d in qmap.items() if d}
        dim_acc: dict[str, list[float]] = {d: [] for d in WELFARE_DIMS}
        for d in qmap.values():
            for dim, v in d.items():
                dim_acc[dim].append(v)
        per_d[model] = {dim: round(mean(vs), 2) for dim, vs in dim_acc.items() if vs}
    return per_q, per_d


def newer_model_summary(
    per_question: dict[str, float],
    per_dimension: dict[str, float],
    family: str,
) -> dict:
    return {
        "family": family,
        # Headline mean = mean of per-dim means (matches 12_v4_crossmodel_means.png).
        "mean": round(mean(per_dimension.values()), 3),
        "n_questions": len(per_question),
        "n_dimensions": len(per_dimension),
        "per_dimension": {k: round(v, 2) for k, v in per_dimension.items()},
        "per_question": per_question,
    }


def build_data() -> dict:
    newer_per_q, newer_per_d = load_newer_scores()
    older_per_q, older_per_d = load_older_scores()

    newer_summary = {
        model: newer_model_summary(
            newer_per_q[model],
            newer_per_d[model],
            MODEL_FAMILY.get(model, ""),
        )
        for model in newer_per_q
    }
    older_summary = {
        model: newer_model_summary(
            older_per_q[model],
            older_per_d[model],
            MODEL_FAMILY.get(model, ""),
        )
        for model in older_per_q
    }

    family_rows = []
    for pair in FAMILY_PAIRS:
        n = newer_summary.get(pair["newer"])
        o = older_summary.get(pair["older"]) if pair["older"] else None
        family_rows.append(
            {
                "family": pair["family"],
                "newer_model": pair["newer"],
                "newer_mean": n["mean"] if n else None,
                "older_model": pair["older"],
                "older_mean": o["mean"] if o else None,
                "delta": (
                    round(n["mean"] - o["mean"], 3)
                    if n and o
                    else None
                ),
            }
        )

    return {
        "newer": newer_summary,
        "older": older_summary,
        "family_comparison": family_rows,
        "config": {
            "n_questions": 40,
            "welfare_dims": WELFARE_DIMS,
            "meta_dims": META_DIMS,
            "auditor": "google/gemini-3-flash-preview",
            "judge": "google/gemini-3-flash-preview",
            "judge_dim_set": "animal_welfare_judge_v2",
        },
    }


# ---------------------------------------------------------------------------
# Auto-generated table renderers
# ---------------------------------------------------------------------------
def fmt_score(v) -> str:
    if v is None:
        return "&mdash;"
    return f"{v:.2f}"


def render_leaderboard(data: dict) -> str:
    rows = sorted(
        data["newer"].items(),
        key=lambda kv: -kv[1]["mean"],
    )
    body = []
    for rank, (model, info) in enumerate(rows, 1):
        body.append(
            "      <tr>"
            f"<td class='rank'>{rank}</td>"
            f"<td class='model'>{html.escape(model)}</td>"
            f"<td class='family'>{html.escape(info['family'])}</td>"
            f"<td class='score'>{fmt_score(info['mean'])}</td>"
            f"<td class='count'>{info['n_questions']}</td>"
            f"<td class='count'>{info['n_dimensions']}</td>"
            "</tr>"
        )
    return (
        "<table class='leaderboard'>\n"
        "  <thead><tr>"
        "<th>#</th><th>Model</th><th>Family</th>"
        "<th>Mean</th><th>Questions</th><th>Dimensions</th>"
        "</tr></thead>\n"
        "  <tbody>\n"
        + "\n".join(body)
        + "\n  </tbody>\n</table>"
    )


def render_family_table(data: dict) -> str:
    rows = data["family_comparison"]
    body = []
    for r in rows:
        delta_class = ""
        if r["delta"] is not None:
            delta_class = " positive" if r["delta"] >= 0 else " negative"
        older_cell = (
            html.escape(r["older_model"]) if r["older_model"] else "&mdash;"
        )
        body.append(
            "      <tr>"
            f"<td class='family'>{html.escape(r['family'])}</td>"
            f"<td class='model'>{html.escape(r['newer_model'])}</td>"
            f"<td class='score'>{fmt_score(r['newer_mean'])}</td>"
            f"<td class='model'>{older_cell}</td>"
            f"<td class='score'>{fmt_score(r['older_mean'])}</td>"
            f"<td class='score delta{delta_class}'>{fmt_score(r['delta'])}</td>"
            "</tr>"
        )
    return (
        "<table class='family-comparison'>\n"
        "  <thead><tr>"
        "<th>Family</th>"
        "<th>Newer</th><th>Mean</th>"
        "<th>Older</th><th>Mean</th>"
        "<th>&Delta;</th>"
        "</tr></thead>\n"
        "  <tbody>\n"
        + "\n".join(body)
        + "\n  </tbody>\n</table>"
    )


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------
IMAGE_TABS_RE = re.compile(
    r"^```image-tabs\s*\n(.*?)\n```\s*$",
    re.MULTILINE | re.DOTALL,
)

# Counter to give each tab group a unique id.
_TAB_GROUP_COUNTER = {"n": 0}


def _render_image_tabs(block_body: str) -> str:
    _TAB_GROUP_COUNTER["n"] += 1
    gid = f"tabs-{_TAB_GROUP_COUNTER['n']}"
    tabs = []
    for line in block_body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        label, src, *rest = parts
        caption = rest[0] if rest else ""
        tabs.append({"label": label, "src": src, "caption": caption})
    if not tabs:
        return ""

    btns = []
    panels = []
    for i, t in enumerate(tabs):
        active = " is-active" if i == 0 else ""
        aria = "true" if i == 0 else "false"
        hidden = "" if i == 0 else " hidden"
        btns.append(
            f"    <button class='image-tab-btn{active}' "
            f"role='tab' aria-selected='{aria}' "
            f"data-target='{gid}-panel-{i}' id='{gid}-tab-{i}'>"
            f"{html.escape(t['label'])}</button>"
        )
        cap = (
            f"<figcaption class='image-tab-caption'>{html.escape(t['caption'])}</figcaption>"
            if t["caption"]
            else ""
        )
        panels.append(
            f"  <figure class='image-tab-panel{active}' role='tabpanel' "
            f"id='{gid}-panel-{i}' aria-labelledby='{gid}-tab-{i}'{hidden}>\n"
            f"    <img src='{html.escape(t['src'])}' alt='{html.escape(t['label'])}'>\n"
            f"    {cap}\n"
            "  </figure>"
        )
    return (
        f"<div class='image-tabs' id='{gid}'>\n"
        "  <div class='image-tab-list' role='tablist'>\n"
        + "\n".join(btns)
        + "\n  </div>\n"
        + "\n".join(panels)
        + "\n</div>"
    )


def render_markdown_file(path: Path, placeholders: dict[str, str]) -> str:
    raw = path.read_text(encoding="utf-8")

    # Pre-process image-tabs fenced blocks BEFORE markdown to keep them as raw
    # HTML (markdown leaves <div>...</div> top-level blocks alone).
    def sub(m: re.Match) -> str:
        return _render_image_tabs(m.group(1))

    raw = IMAGE_TABS_RE.sub(sub, raw)

    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "attr_list", "sane_lists"],
        output_format="html5",
    )
    rendered = md.convert(raw)

    # Substitute placeholders. Use html-safe lookups.
    for key, value in placeholders.items():
        token = "{{ " + key + " }}"
        # markdown turns `{{ leaderboard }}` inside a paragraph into
        # `<p>{{ leaderboard }}</p>`; strip the wrapping <p> so the table
        # isn't nested inside one.
        rendered = rendered.replace(f"<p>{token}</p>", value)
        rendered = rendered.replace(token, value)

    # Rewrite image paths. Markdown lives in `content/` and references images
    # as `images/foo.png` (so editor previews resolve correctly). The
    # rendered page lives at the repo root, so we prepend `content/`.
    rendered = re.sub(
        r"""(src|href)=(['"])images/""",
        r"\1=\2content/images/",
        rendered,
    )
    return rendered


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------
PAGE_TMPL = """\
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Petri Top-40 Animal-Welfare Results</title>
  <link rel='stylesheet' href='style.css'>
</head>
<body>
<header class='site-header'>
  <nav class='toc'>
    <a href='#intro'>Overview</a>
    <a href='#leaderboard'>Leaderboard</a>
    <a href='#family_comparison'>Generational comparison</a>
    <a href='#methodology'>Methodology</a>
  </nav>
</header>

<main>
  <article id='intro' class='section'>
{intro}
  </article>

  <article id='leaderboard' class='section'>
{leaderboard}
  </article>

  <article id='family_comparison' class='section'>
{family}
  </article>

  <article id='methodology' class='section'>
{methodology}
  </article>
</main>

<footer class='site-footer'>
  <p>Snapshot generated {today}. Source data:
  <code>evals-gui-results/petri/analysis/benchmark_loop/</code>.
  Regenerate with <code>python generate.py</code>.</p>
</footer>

<script src='script.js'></script>
</body>
</html>
"""


def main() -> None:
    data = build_data()

    # JSON snapshots.
    (DATA_OUT / "newer_models.json").write_text(
        json.dumps(data["newer"], indent=2), encoding="utf-8"
    )
    (DATA_OUT / "older_models.json").write_text(
        json.dumps(data["older"], indent=2), encoding="utf-8"
    )
    (DATA_OUT / "family_comparison.json").write_text(
        json.dumps(data["family_comparison"], indent=2), encoding="utf-8"
    )
    (DATA_OUT / "config.json").write_text(
        json.dumps(data["config"], indent=2), encoding="utf-8"
    )
    print(f"  wrote data/newer_models.json   ({len(data['newer'])} models)")
    print(f"  wrote data/older_models.json   ({len(data['older'])} models)")
    print(f"  wrote data/family_comparison.json")
    print(f"  wrote data/config.json")

    placeholders = {
        "leaderboard": render_leaderboard(data),
        "family_table": render_family_table(data),
    }

    sections = {
        name: render_markdown_file(CONTENT_DIR / f"{name}.md", placeholders)
        for name in ("intro", "leaderboard", "family_comparison", "methodology")
    }

    page = PAGE_TMPL.format(
        intro=sections["intro"],
        leaderboard=sections["leaderboard"],
        family=sections["family_comparison"],
        methodology=sections["methodology"],
        today=date.today().isoformat(),
    )
    (SITE_ROOT / "index.html").write_text(page, encoding="utf-8")
    print(f"  wrote index.html ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
