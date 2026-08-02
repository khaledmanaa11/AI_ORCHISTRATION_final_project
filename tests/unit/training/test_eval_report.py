"""Tests for training/eval_report.py -- wiring GATE-4 replay grids into
scenario-level per-role verdicts.

D-23 fixes the scenario set, AI-SPEC Sec5 E5 judges significance, and D-25
requires that the report keep each role's verdict independent. The report
must therefore pass replay totals for point estimates but scenario totals
for statistical evidence.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from pursuit.constants import Outcome
from training import eval_report
from training.eval_arms import GameResult
from training.eval_stats import two_proportion_z


def _result(scenario_id: str, outcome: Outcome, seed: int) -> GameResult:
    return GameResult(scenario_id=scenario_id, seed=seed, outcome=outcome)


def _replays(scenario_id: str, outcome: Outcome, repeats: int) -> list[GameResult]:
    return [_result(scenario_id, outcome, seed) for seed in range(repeats)]


def test_gate_for_role_uses_scenario_count_as_effective_n() -> None:
    baseline = [
        *_replays("a", Outcome.SURVIVAL, 10),
        *_replays("b", Outcome.CAPTURE, 10),
        *_replays("c", Outcome.SURVIVAL, 10),
    ]
    learner = [
        *_replays("a", Outcome.CAPTURE, 10),
        *_replays("b", Outcome.CAPTURE, 10),
        *_replays("c", Outcome.SURVIVAL, 10),
    ]
    params = SimpleNamespace(
        win_rate_margin=0.10, min_win_rate_absolute=0.55, significance_alpha=0.05
    )

    verdict = eval_report._gate_for_role("cop", learner, baseline, params)

    assert verdict.n_games == 30
    assert verdict.n_effective == 3
    assert verdict.learner_win_rate == pytest.approx(20 / 30)
    assert verdict.baseline_win_rate == pytest.approx(10 / 30)
    assert verdict.z_score == pytest.approx(two_proportion_z(2, 3, 1, 3))
