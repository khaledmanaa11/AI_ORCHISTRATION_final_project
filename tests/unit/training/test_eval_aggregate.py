"""Tests for training/eval_aggregate.py -- scenario-level GATE-4 evidence.

The evaluation grid can contain deterministic repeats, but D-23 scenarios
remain the independent units for AI-SPEC Sec5 E5 significance. These tests
pin that aggregation before eval_report turns it into D-25 per-role verdicts.
"""

from __future__ import annotations

import pytest

from pursuit.constants import Outcome
from training.eval_aggregate import (
    discordant_scenarios,
    replays_are_degenerate,
    scenario_win_fractions,
)
from training.eval_arms import GameResult


def _result(scenario_id: str, outcome: Outcome | None, seed: int = 1) -> GameResult:
    return GameResult(scenario_id=scenario_id, seed=seed, outcome=outcome)


def test_scenario_win_fractions_groups_replays_by_scenario() -> None:
    results = [
        _result("a", Outcome.CAPTURE),
        _result("a", Outcome.SURVIVAL, seed=2),
        _result("b", Outcome.SURVIVAL),
    ]
    assert scenario_win_fractions(results, "cop") == {"a": 0.5, "b": 0.0}
    assert scenario_win_fractions(results, "thief") == {"a": 0.5, "b": 1.0}


def test_scenario_win_fractions_rejects_unknown_role() -> None:
    with pytest.raises(ValueError, match="unknown role"):
        scenario_win_fractions([_result("a", Outcome.CAPTURE)], "referee")


def test_discordant_scenarios_compares_fractional_scenario_pairs() -> None:
    learner = {"a": 1.0, "b": 0.5, "c": 0.0}
    baseline = {"a": 0.0, "b": 0.5, "c": 1.0}
    assert discordant_scenarios(learner, baseline) == (1, 1)


def test_discordant_scenarios_rejects_unpaired_inputs() -> None:
    with pytest.raises(ValueError, match="scenario ids"):
        discordant_scenarios({"a": 1.0}, {"b": 0.0})


def test_replays_are_degenerate_when_each_scenario_repeats_one_outcome() -> None:
    results = [
        _result("a", Outcome.CAPTURE),
        _result("a", Outcome.CAPTURE, seed=2),
        _result("b", Outcome.SURVIVAL),
    ]
    assert replays_are_degenerate(results) is True


def test_replays_are_degenerate_detects_varying_replay_outcomes() -> None:
    results = [_result("a", Outcome.CAPTURE), _result("a", Outcome.SURVIVAL, seed=2)]
    assert replays_are_degenerate(results) is False
