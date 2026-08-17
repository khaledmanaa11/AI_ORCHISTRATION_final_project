"""`scripts/plot_run2_curves.py` -- the run-2 figures the README embeds (08-06).

Loaded BY PATH, the `submission_gate_helpers` idiom, so the suite exercises the
same file a reader runs. `scripts/` is outside the coverage `source` list, so
without this module the figure generator would be unmeasured.

The point of each test is that a figure cannot be produced from nothing: an
empty or truncated curve must RAISE rather than draw a blank axis that still
looks like evidence in a graded README.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCRIPT = REPO_ROOT / "scripts" / "plot_run2_curves.py"

#: Enough rows to clear MIN_ROWS with room to spare.
_ROWS = 6


def _load():
    spec = importlib.util.spec_from_file_location("plot_run2_curves", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["plot_run2_curves"] = module
    spec.loader.exec_module(module)
    return module


plot = _load()


def _synthetic(count: int = _ROWS) -> list[dict]:
    return [
        {"generation": index, "cop_capture_rate": 0.5 + index / 100,
         "thief_survival_rate": 0.3, "loss": 1.0 - index / 100,
         "best_fitness": 30.0 + index, "batch_best": 29.0 + index}
        for index in range(count)
    ]


def test_series_pairs_generation_with_the_requested_key():
    generations, values = plot.series(_synthetic(3), "loss")
    assert generations == [0, 1, 2]
    assert values == [1.0, 0.99, 0.98]


def test_series_refuses_a_key_no_row_carries():
    with pytest.raises(KeyError):
        plot.series(_synthetic(), "not_a_recorded_quantity")


def test_load_curve_refuses_a_truncated_curve(tmp_path):
    short = tmp_path / "curve.json"
    short.write_text(json.dumps(_synthetic(plot.MIN_ROWS - 1)), encoding="utf-8")
    with pytest.raises(ValueError, match="need at least"):
        plot.load_curve(short)


def test_load_curve_refuses_an_empty_list(tmp_path):
    empty = tmp_path / "curve.json"
    empty.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        plot.load_curve(empty)


def test_both_tracked_curves_are_long_enough_to_plot():
    """The figures in the README are drawn from THESE files, not from fixtures."""
    for path in (plot.SELFPLAY_CURVE, plot.EVOLUTION_CURVE):
        assert len(plot.load_curve(path)) >= plot.MIN_ROWS

    for key, _label in plot.SELFPLAY_SERIES:
        assert plot.series(plot.load_curve(plot.SELFPLAY_CURVE), key)[1]
    for key, _label in plot.EVOLUTION_SERIES:
        assert plot.series(plot.load_curve(plot.EVOLUTION_CURVE), key)[1]


def test_main_writes_both_figures_and_neither_is_empty(tmp_path):
    exit_code = plot.main(["--out-dir", str(tmp_path)])
    assert exit_code == 0
    produced = sorted(path.name for path in tmp_path.glob("*.png"))
    assert produced == [plot.EVOLUTION_PNG, plot.SELFPLAY_PNG]
    for path in tmp_path.glob("*.png"):
        assert path.stat().st_size > 1000, f"{path.name} is too small to be a figure"


def test_the_committed_figures_exist_and_are_not_gitignored():
    """A README image link that resolves to nothing renders as a broken icon.

    Existence alone is not enough: a figure sitting under an ignored path is
    present on the author's disk and absent from the grader's clone.
    """
    for name in (plot.SELFPLAY_PNG, plot.EVOLUTION_PNG):
        path = plot.OUT_DIR / name
        assert path.is_file(), f"artifacts/curves/{name} is missing"
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", str(path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT, capture_output=True, check=False,
        )
        assert ignored.returncode != 0, f"artifacts/curves/{name} is gitignored"
