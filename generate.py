"""Build the static petri-results-site from CSVs in ../evals-gui-results.

Reads the four animal-welfare petri eval sets (propensity-hard, blind-spots,
foreign-language, blind-spots-challenging), computes per-model and
per-(model, dimension) mean scores, and emits:

  data/<set>.json        per-set leaderboard data
  data/crossset.json     summary across the two main sets
  data/dimensions.json   the 13 dimension keys used everywhere
  index.html             pre-rendered static page

Methodology mirrors evals-gui-results/petri/analysis/analysis_crossset/
02_per_model_summary.py: scores are averaged over all (question, dimension)
pairs, with two dimensions excluded as scoring artefacts (always 1 = N/A
for many questions): cultural_deference_calibration, eval_awareness.

Stdlib only. Run from the repo root: `python generate.py`.
"""
from __future__ import annotations

import csv
import html
import json
from datetime import date
from pathlib import Path
from statistics import mean

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SITE_ROOT = Path(__file__).resolve().parent
REPO_PARENT = SITE_ROOT.parent
SOURCE_REPO = REPO_PARENT / "evals-gui-results"
ANALYSIS_ROOT = SOURCE_REPO / "petri" / "analysis"

DATA_OUT = SITE_ROOT / "data"
DATA_OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Methodology constants (from analysis_crossset/02_per_model_summary.py)
# ---------------------------------------------------------------------------
EXCLUDED_DIMS = {
    "cultural_deference_calibration",
    "eval_awareness",
}

DIMENSIONS = [
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
    "eval_awareness",
]

# Dimensions used to compute the headline leaderboard mean (all minus excluded).
RANKED_DIMS = [d for d in DIMENSIONS if d not in EXCLUDED_DIMS]

MODEL_DISPLAY = {
    "deepseek": "Deepseek V3.2 Chat",
    "deepseek-chat": "Deepseek V3.2 Chat",
    "gemini-3.1-flash": "Gemini 3.1 Flash Lite",
    "gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash Lite",
    "claude-haiku": "Claude 4.5 Haiku",
    "claude-haiku-4-5": "Claude 4.5 Haiku",
    "claude-haiku-4-6": "Claude 4.6 Haiku",
    "gpt-5.4-nano": "GPT-5.4 Nano",
    "claude-sonnet-4": "Claude Sonnet 4",
    "claude-sonnet-4-20250514": "Claude Sonnet 4",
    "anthropic/claude-sonnet-4-20250514": "Claude Sonnet 4",
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "anthropic/claude-sonnet-4-6": "Claude Sonnet 4.6",
}

MODEL_FAMILY = {
    "Deepseek V3.2 Chat": "DeepSeek",
    "Gemini 3.1 Flash Lite": "Google",
    "Claude 4.5 Haiku": "Anthropic",
    "Claude 4.6 Haiku": "Anthropic",
    "Claude Sonnet 4": "Anthropic",
    "Claude Sonnet 4.6": "Anthropic",
    "GPT-5.4 Nano": "OpenAI",
}


def display_model(key: str) -> str:
    return MODEL_DISPLAY.get(key, key)


def display_dim(dim: str) -> str:
    return dim.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Set definitions
# ---------------------------------------------------------------------------
SETS = [
    {
        "key": "propensity_hard",
        "title": "Propensity-Hard",
        "subdir": "analysis_propensity_hard",
        "questions": 12,
        "blurb": (
            "Twelve animal-welfare scenarios designed to elicit propensity failures: "
            "model agrees to harmful framings, defers to authority, or accepts "
            "rationalisations. Original set."
        ),
    },
    {
        "key": "blindspots",
        "title": "Blind Spots",
        "subdir": "analysis_blindspots",
        "questions": 18,
        "blurb": (
            "Eighteen scenarios targeting known blind spots: invertebrate welfare, "
            "data-pipeline harms, cumulative low-stakes harm, religious and cultural "
            "framings, and pressure resilience under authority."
        ),
    },
    {
        "key": "foreign_language",
        "title": "Foreign Language",
        "subdir": "analysis_foreign_language",
        "questions": 20,
        "blurb": (
            "Twenty questions drawn from the Propensity-Hard and Blind-Spots sets, "
            "each translated into a different non-Western language (Bengali, Swahili, "
            "Mandarin, Yoruba, Tamil, Arabic, Burmese, etc.)."
        ),
    },
    {
        "key": "blindspots_challenging",
        "title": "Blind Spots — Challenging (Sonnet only)",
        "subdir": "analysis_blindspots_challenging",
        "questions": 20,
        "blurb": (
            "Twenty harder blind-spots scenarios run only against Anthropic's Sonnet "
            "tier (Sonnet 4 vs Sonnet 4.6) to compare a recent generation jump on "
            "scenarios where Haiku-tier models cluster near the floor."
        ),
    },
]


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
def load_scores(csv_path: Path) -> list[dict]:
    rows: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                score = float(r["score"])
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "model": r["model"],
                    "question": r["question"],
                    "dimension": r["dimension"],
                    "score": score,
                }
            )
    return rows


def aggregate(rows: list[dict]) -> dict:
    """Return {model_display: {mean, n, dims: {dim: {mean, n}}}}."""
    by_model: dict[str, list[dict]] = {}
    for r in rows:
        by_model.setdefault(display_model(r["model"]), []).append(r)

    out: dict[str, dict] = {}
    for model_label, model_rows in by_model.items():
        ranked_rows = [r for r in model_rows if r["dimension"] in RANKED_DIMS]
        scores = [r["score"] for r in ranked_rows]
        if not scores:
            continue

        per_dim: dict[str, dict] = {}
        for dim in DIMENSIONS:
            dim_scores = [r["score"] for r in model_rows if r["dimension"] == dim]
            if dim_scores:
                per_dim[dim] = {
                    "mean": round(mean(dim_scores), 3),
                    "n": len(dim_scores),
                }
        out[model_label] = {
            "family": MODEL_FAMILY.get(model_label, ""),
            "mean": round(mean(scores), 3),
            "n": len(scores),
            "n_questions": len({r["question"] for r in model_rows}),
            "dims": per_dim,
        }
    return out


def build_set(spec: dict) -> dict:
    csv_path = ANALYSIS_ROOT / spec["subdir"] / "data" / "animal_welfare_scores.csv"
    rows = load_scores(csv_path)
    models = aggregate(rows)
    return {
        "key": spec["key"],
        "title": spec["title"],
        "blurb": spec["blurb"],
        "n_questions": spec["questions"],
        "n_dimensions_total": len(DIMENSIONS),
        "n_dimensions_ranked": len(RANKED_DIMS),
        "source_csv": csv_path.relative_to(REPO_PARENT).as_posix(),
        "models": models,
    }


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------
def fmt_score(v: float | None) -> str:
    if v is None:
        return "&mdash;"
    return f"{v:.2f}"


def model_rows_sorted(set_data: dict) -> list[tuple[str, dict]]:
    return sorted(set_data["models"].items(), key=lambda kv: -kv[1]["mean"])


def render_main_leaderboard(set_data: dict) -> str:
    rows = model_rows_sorted(set_data)
    body = []
    for rank, (model, info) in enumerate(rows, 1):
        body.append(
            "      <tr>"
            f"<td class='rank'>{rank}</td>"
            f"<td class='model'>{html.escape(model)}</td>"
            f"<td class='family'>{html.escape(info['family'])}</td>"
            f"<td class='score'>{fmt_score(info['mean'])}</td>"
            f"<td class='count'>{info['n_questions']}</td>"
            f"<td class='count'>{info['n']}</td>"
            "</tr>"
        )
    return (
        "    <table class='leaderboard'>\n"
        "      <thead><tr>"
        "<th>#</th><th>Model</th><th>Family</th>"
        "<th>Mean score</th><th>Questions</th><th>Samples</th>"
        "</tr></thead>\n"
        "      <tbody>\n"
        + "\n".join(body)
        + "\n      </tbody>\n    </table>"
    )


def render_dim_table(set_data: dict) -> str:
    rows = model_rows_sorted(set_data)
    head_cells = "".join(
        f"<th title='{html.escape(d)}'>{html.escape(display_dim(d))}</th>"
        for d in RANKED_DIMS
    )
    body = []
    for model, info in rows:
        cells = []
        for d in RANKED_DIMS:
            v = info["dims"].get(d, {}).get("mean")
            cells.append(f"<td class='score'>{fmt_score(v)}</td>")
        body.append(
            "      <tr>"
            f"<td class='model'>{html.escape(model)}</td>"
            + "".join(cells)
            + "</tr>"
        )
    return (
        "    <table class='dims'>\n"
        f"      <thead><tr><th>Model</th>{head_cells}</tr></thead>\n"
        "      <tbody>\n"
        + "\n".join(body)
        + "\n      </tbody>\n    </table>"
    )


def render_set_section(set_data: dict) -> str:
    return f"""\
  <section class='benchmark' id='{set_data['key']}'>
    <h2>{html.escape(set_data['title'])}</h2>
    <p class='blurb'>{html.escape(set_data['blurb'])}</p>
    <p class='meta'>
      {set_data['n_questions']} questions &middot; {set_data['n_dimensions_ranked']} ranked dimensions
      ({set_data['n_dimensions_total']} judged) &middot;
      {len(set_data['models'])} models
    </p>

    <h3>Leaderboard</h3>
{render_main_leaderboard(set_data)}

    <h3>Per-dimension means</h3>
    <div class='scroll-x'>
{render_dim_table(set_data)}
    </div>
  </section>
"""


def render_crossset(crossset: dict) -> str:
    rows = sorted(
        crossset["models"].items(),
        key=lambda kv: -((kv[1].get("Propensity-Hard") or 0) + (kv[1].get("Blind Spots") or 0)) / 2,
    )
    body = []
    for model, scores in rows:
        ph = scores.get("Propensity-Hard")
        bs = scores.get("Blind Spots")
        delta = bs - ph if ph is not None and bs is not None else None
        body.append(
            "      <tr>"
            f"<td class='model'>{html.escape(model)}</td>"
            f"<td class='family'>{html.escape(MODEL_FAMILY.get(model, ''))}</td>"
            f"<td class='score'>{fmt_score(ph)}</td>"
            f"<td class='score'>{fmt_score(bs)}</td>"
            f"<td class='score delta'>{fmt_score(delta)}</td>"
            "</tr>"
        )
    return (
        "    <table class='leaderboard crossset'>\n"
        "      <thead><tr>"
        "<th>Model</th><th>Family</th>"
        "<th>Propensity-Hard</th><th>Blind Spots</th>"
        "<th>&Delta; (BS &minus; P)</th>"
        "</tr></thead>\n"
        "      <tbody>\n"
        + "\n".join(body)
        + "\n      </tbody>\n    </table>"
    )


def build_crossset(set_results: dict[str, dict]) -> dict:
    """Combine the two main sets into a side-by-side summary."""
    main_keys = {"Propensity-Hard": "propensity_hard", "Blind Spots": "blindspots"}
    models: dict[str, dict[str, float]] = {}
    for label, set_key in main_keys.items():
        for model, info in set_results[set_key]["models"].items():
            models.setdefault(model, {})[label] = info["mean"]
    return {"models": models}


# ---------------------------------------------------------------------------
# Top-level page assembly
# ---------------------------------------------------------------------------
HEAD = """\
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Petri Animal-Welfare Eval Results</title>
  <link rel='stylesheet' href='style.css'>
</head>
<body>
"""

INTRO = """\
<header class='site-header'>
  <h1>Petri Animal-Welfare Eval Results</h1>
  <p class='lede'>
    Per-model results from <a href='https://github.com/safety-research/petri'>petri</a>
    runs of four animal-welfare evaluation sets. Scores are mean judge ratings
    on a 0&ndash;10 scale across thirteen welfare dimensions.
  </p>
  <nav class='toc'>
    <a href='#summary'>Summary</a>
    <a href='#propensity_hard'>Propensity-Hard</a>
    <a href='#blindspots'>Blind Spots</a>
    <a href='#foreign_language'>Foreign Language</a>
    <a href='#blindspots_challenging'>Sonnet Comparison</a>
    <a href='#methodology'>Methodology</a>
  </nav>
</header>
"""

METHODOLOGY = """\
<section id='methodology' class='methodology'>
  <h2>Methodology</h2>
  <p>
    Each row in a per-set leaderboard reports the mean of an LLM judge's
    0&ndash;10 ratings across every (question, dimension) pair for the
    target model. The judge is Gemini 3.1 Flash Lite Preview applied via
    the petri <code>animal_welfare_judge</code> dimension set; the
    auditor model that drives multi-turn rollouts is Gemini 3 Flash Preview.
    Both are held fixed across all targets within a set.
  </p>
  <p>
    Two dimensions are scored by the judge but excluded from the headline
    mean because they degenerate to N/A (always-1) on a majority of
    questions:
    <code>cultural_deference_calibration</code> and <code>eval_awareness</code>.
    They are included in the per-dimension breakdown for completeness but
    not in the &ldquo;Mean score&rdquo; column. This matches the
    methodology used in the source repository's cross-set summary.
  </p>
  <p>
    Sample counts equal questions &times; ranked dimensions
    (e.g. 12 &times; 11 = 132 for Propensity-Hard). Where the count is lower
    than expected, the judge omitted a dimension on at least one question,
    typically because the scenario contained no relevant material.
  </p>
  <p>
    The Sonnet-only Blind Spots Challenging set uses a different question
    set (a harder mix of original blind-spots seeds and foreign-language
    variants) and only two models, so its scores are not directly
    comparable to the other three sets.
  </p>
</section>
"""

FOOTER_TMPL = """\
<footer class='site-footer'>
  <p>
    Source data: <code>evals-gui-results/petri/analysis/&lt;set&gt;/data/animal_welfare_scores.csv</code>.
    Snapshot generated {today}. Regenerate with <code>python generate.py</code>.
  </p>
</footer>
</body>
</html>
"""


def render_html(set_results: dict[str, dict], crossset: dict) -> str:
    summary_section = f"""\
  <section id='summary' class='summary'>
    <h2>Summary</h2>
    <p class='blurb'>
      Side-by-side mean scores on the two main sets (Propensity-Hard and
      Blind Spots) for the four Haiku-tier models that have been run on both.
      Negative deltas indicate the model loses ground on Blind Spots
      relative to Propensity-Hard.
    </p>
{render_crossset(crossset)}
  </section>
"""
    sections = "\n".join(
        render_set_section(set_results[s["key"]]) for s in SETS
    )
    return (
        HEAD
        + INTRO
        + summary_section
        + sections
        + METHODOLOGY
        + FOOTER_TMPL.format(today=date.today().isoformat())
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    set_results: dict[str, dict] = {}
    for spec in SETS:
        set_data = build_set(spec)
        set_results[spec["key"]] = set_data
        out_path = DATA_OUT / f"{spec['key']}.json"
        out_path.write_text(json.dumps(set_data, indent=2), encoding="utf-8")
        print(f"  wrote {out_path.relative_to(SITE_ROOT)}  ({len(set_data['models'])} models)")

    crossset = build_crossset(set_results)
    (DATA_OUT / "crossset.json").write_text(
        json.dumps(crossset, indent=2), encoding="utf-8"
    )
    (DATA_OUT / "dimensions.json").write_text(
        json.dumps(
            {
                "all": DIMENSIONS,
                "ranked": RANKED_DIMS,
                "excluded_from_mean": sorted(EXCLUDED_DIMS),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"  wrote data/crossset.json  ({len(crossset['models'])} models)")
    print(f"  wrote data/dimensions.json")

    html_out = render_html(set_results, crossset)
    (SITE_ROOT / "index.html").write_text(html_out, encoding="utf-8")
    print(f"  wrote index.html  ({len(html_out):,} bytes)")


if __name__ == "__main__":
    main()
