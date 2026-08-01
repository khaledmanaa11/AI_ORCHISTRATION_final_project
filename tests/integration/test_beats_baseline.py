"""GATE-4 (STRAT-01/06, PRD §10.4 criterion d) -- the shipped `QLearningBrain`
beats `HeuristicBrain` per role, on held-out seeds, at the configured margin.

CI only runs the smoke subset (`eval_games_ci`) plus the disjointness and
grid-consistency assertions -- the full 200-game statistical gate is a
checkpoint-PROMOTION step
(`uv run python training/evaluate.py --full --assert-gate`), not a
per-commit test (AI-SPEC Sec5's CI/CD split).

No trained Q-table exists anywhere in this repo yet -- Task 4 of this plan
is the overnight run that produces one. `test_beats_baseline_smoke_subset`
SKIPS with a stated reason until both `artifacts/qtable_police.json` and
`artifacts/qtable_thief.json` exist: a green GATE-4 that never loaded a
table is the worst possible outcome for this phase, so it never passes
vacuously.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from training import eval_arms
from training.eval_report import run_evaluation
from training.eval_scenarios import DEFAULT_SCENARIOS_PATH, assert_seeds_held_out, load_scenarios


def _qtable_missing() -> bool:
    cop_params = eval_arms.strategy_params("cop")
    thief_params = eval_arms.strategy_params("thief")
    return not Path(cop_params.qtable_path).exists() or not Path(thief_params.qtable_path).exists()


def test_eval_scenario_seeds_are_held_out_from_training() -> None:
    """D-23, executable: a property of the committed scenario file and
    config alone, provable independently of whether training has run."""
    cop_params = eval_arms.strategy_params("cop")
    scenarios = load_scenarios(DEFAULT_SCENARIOS_PATH)
    assert_seeds_held_out(scenarios, cop_params)  # raises AssertionError if violated


def test_eval_scenario_grid_matches_configured_game_count() -> None:
    cop_params = eval_arms.strategy_params("cop")
    scenarios = load_scenarios(DEFAULT_SCENARIOS_PATH)
    assert len(scenarios) == cop_params.eval_scenarios
    assert cop_params.eval_scenarios * cop_params.repeats_per_scenario == cop_params.eval_games


def test_smoke_evaluation_machinery_runs_and_reports_baseline_numbers() -> None:
    """The evaluation machinery -- scenario loading, the baseline arm,
    disjointness -- works end to end even before any table is trained; both
    per-role baseline win rates are real, measured numbers, never fabricated."""
    report = run_evaluation(full=False)
    assert report.n_scenarios == 20
    assert set(report.baseline_win_rates) == {"cop", "thief"}
    for rate in report.baseline_win_rates.values():
        assert 0.0 <= rate <= 1.0


@pytest.mark.skipif(
    _qtable_missing(),
    reason=(
        "no trained Q-table at artifacts/qtable_police.json / "
        "artifacts/qtable_thief.json yet -- Task 4 of 03-10-PLAN.md (the "
        "overnight training run) has not executed"
    ),
)
def test_beats_baseline_smoke_subset() -> None:
    """GATE-4 itself, smoke subset: passes only once a real table is loaded
    for BOTH roles independently (D-25) -- never a shared pass flag lets a
    strong cop mask a thief that never learned, or vice versa."""
    report = run_evaluation(full=False)
    assert not report.errors, f"unexpected missing table(s): {report.errors}"
    for role, verdict in report.verdicts.items():
        assert verdict.passed, f"GATE-4 not met for role={role}: {verdict}"
