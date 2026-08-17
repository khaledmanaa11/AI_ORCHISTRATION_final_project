"""Render the RUN-2 learning curves rule 42 / Sec9.4.2 item 4 ask for (08-06).

    uv run python scripts/plot_run2_curves.py

WHY THIS FILE EXISTS. `artifacts/curves/*.png` are RUN 1's figures -- the
tabular Q-learning run Phase 3 withdrew (`docs/PRD_rl_strategy.md` carries a
SUPERSEDED banner). The script that drew them, `training/plot_curves.py`, was
DELETED with the rest of the run-1 stack in `f3d9847`, so the command the old
README documented names a file this repository does not ship. Presenting run 1's
figures as "the learning curves" would illustrate the academic report with the
training history of a mechanism that is not in the product.

What ships is fitted here instead: `artifacts/run2/` (outcome regression, the
vector in `config/*/weights.json`) and `artifacts/run2_es/` ((1+lambda)-ES, kept
as a documented negative result -- `docs/phases/phase-3/ENGINEERING-LOG.md`
Act 5). Both curve files are TRACKED, so the figures are reproducible from a
clean checkout with no training run and no API key.

Lives in `scripts/` rather than `training/` deliberately: it reads finished
artefacts and draws, it is not part of the learner.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SELFPLAY_CURVE = REPO_ROOT / "artifacts" / "run2" / "curve.json"
EVOLUTION_CURVE = REPO_ROOT / "artifacts" / "run2_es" / "curve.json"
OUT_DIR = REPO_ROOT / "artifacts" / "curves"

SELFPLAY_PNG = "run2_selfplay.png"
EVOLUTION_PNG = "run2_evolution.png"

#: A curve with fewer rows than this is not a curve; refuse rather than draw a
#: near-empty axis that still looks like evidence.
MIN_ROWS = 5

#: (json key, legend label) per figure. Named tables, not inline literals.
SELFPLAY_SERIES = (
    ("cop_capture_rate", "cop capture rate (vs fixed anchors)"),
    ("thief_survival_rate", "thief survival rate (vs fixed anchors)"),
    ("loss", "regression loss"),
)
EVOLUTION_SERIES = (
    ("best_fitness", "best-so-far fitness (league points)"),
    ("batch_best", "best of generation"),
)


def load_curve(path: Path) -> list[dict]:
    """One tracked `curve.json`, refusing anything too short to plot."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or len(rows) < MIN_ROWS:
        raise ValueError(f"{path} holds {len(rows)} row(s); need at least {MIN_ROWS}")
    return rows


def series(rows: list[dict], key: str) -> tuple[list[int], list[float]]:
    """`generation` against `key`, over the rows that actually carry the key."""
    present = [row for row in rows if key in row]
    if not present:
        raise KeyError(f"no curve row carries '{key}'")
    return [int(row["generation"]) for row in present], [float(row[key]) for row in present]


def _draw(rows: list[dict], spec: tuple, title: str, ylabel: str, out: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(8, 4.5))
    for key, label in spec:
        generations, values = series(rows, key)
        axis.plot(generations, values, marker="o", markersize=3, label=label)
    axis.set_xlabel("generation")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True, alpha=0.3)
    axis.legend(loc="best", fontsize=8)
    figure.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out, dpi=120)
    plt.close(figure)
    return out


def render_selfplay(rows: list[dict], out_dir: Path) -> Path:
    """Outcome regression -- the optimiser whose vector ships."""
    return _draw(
        rows, SELFPLAY_SERIES,
        "Run 2 - outcome regression (the shipped 15-weight vector)",
        "rate / loss", out_dir / SELFPLAY_PNG,
    )


def render_evolution(rows: list[dict], out_dir: Path) -> Path:
    """(1+lambda)-ES -- the optimiser kept as a negative result."""
    return _draw(
        rows, EVOLUTION_SERIES,
        "Run 2 - (1+lambda)-ES on league points (not shipped)",
        "league points", out_dir / EVOLUTION_PNG,
    )


def _display(path: Path) -> str:
    """Repo-relative when it can be -- `--out-dir` may point anywhere."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--selfplay-curve", type=Path, default=SELFPLAY_CURVE)
    parser.add_argument("--evolution-curve", type=Path, default=EVOLUTION_CURVE)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    written = [
        render_selfplay(load_curve(args.selfplay_curve), args.out_dir),
        render_evolution(load_curve(args.evolution_curve), args.out_dir),
    ]
    for path in written:
        print(f"wrote {_display(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
