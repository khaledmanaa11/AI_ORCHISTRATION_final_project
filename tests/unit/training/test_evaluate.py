"""Tests for training/evaluate.py's CLI (D-16-style direct-path bootstrap,
matching training/plot_curves.py's own 03-09 precedent). The evaluation
MATH itself is tested in test_eval_stats.py/test_eval_report.py -- this
file covers argument parsing, exit codes, and the printed report only."""

from __future__ import annotations

import pathlib
import subprocess
import sys

from training import evaluate
from training.eval_report import EvaluationReport
from training.eval_stats import GateVerdict

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent.parent


def test_main_smoke_mode_runs_and_prints_baseline_numbers(capsys) -> None:
    exit_code = evaluate.main(["--smoke"])

    printed = capsys.readouterr().out
    assert exit_code == 0  # no --assert-gate: a missing table is not a failure by itself
    assert "20 scenarios" in printed
    assert "role=cop" in printed
    assert "role=thief" in printed


def test_main_full_mode_uses_repeats_per_scenario(capsys) -> None:
    evaluate.main(["--full"])
    printed = capsys.readouterr().out
    assert "x 10 repeats = 200 games per arm" in printed


def test_print_report_shows_effective_n_and_degenerate_warning(capsys) -> None:
    verdict = GateVerdict(
        role="cop", n_games=200, n_effective=20,
        learner_win_rate=0.65, baseline_win_rate=0.50, margin=0.15,
        mcnemar_p=0.25, z_score=0.96, z_p_one_sided=0.17,
        meets_margin=True, meets_absolute_floor=True, is_significant=False, passed=False,
    )
    report = EvaluationReport(
        repeats=10, n_scenarios=20, verdicts={"cop": verdict}, errors={},
        baseline_win_rates={}, replays_degenerate=True,
    )
    evaluate._print_report(report)

    printed = capsys.readouterr().out
    assert "repeats are deterministic replays" in printed
    assert "role=cop n=200 n_effective=20" in printed


def test_main_assert_gate_exits_nonzero_when_a_table_is_missing() -> None:
    exit_code = evaluate.main(["--smoke", "--assert-gate"])
    assert exit_code == 1


def test_main_rejects_smoke_and_full_together() -> None:
    try:
        evaluate.main(["--smoke", "--full"])
    except SystemExit as exc:
        assert exc.code != 0
    else:  # pragma: no cover -- argparse always raises SystemExit on this conflict
        raise AssertionError("expected argparse to reject --smoke and --full together")


def test_cli_runs_by_direct_path_uv_style() -> None:
    """Proves the plan's literal `uv run python training/evaluate.py --smoke`
    form actually works -- direct-path execution needs its own sys.path
    bootstrap since it does not get `-m`'s or pytest's rootdir insertion."""
    result = subprocess.run(
        [sys.executable, "training/evaluate.py", "--smoke"],
        cwd=_REPO_ROOT, capture_output=True, text=True, check=True,
    )
    assert "20 scenarios" in result.stdout
