"""Tests for training/arena.py -- held-out matchup measurement with intervals.

Every rate this module reports must carry its Wilson interval (module doc):
a bare fraction at n=20 cannot tell "badly broken" from "nearly there". This
file checks the interval math directly, then a single small real matchup end
to end so run_match's own bookkeeping (wins/points) is proven, not just
wilson() in isolation.
"""

from __future__ import annotations

from pursuit.shared.resolution import PREFERRED
from pursuit.strategy.naive import ChaserCop, GreedyEvader
from training.arena import MatchResult, compare, run_match, wilson

_GAMES = 6


def test_wilson_of_zero_games_returns_the_full_interval() -> None:
    assert wilson(0, 0) == (0.0, 1.0)


def test_wilson_interval_contains_the_observed_rate() -> None:
    low, high = wilson(15, 20)
    assert low <= 15 / 20 <= high


def test_wilson_interval_stays_within_unit_bounds() -> None:
    low, high = wilson(20, 20)
    assert 0.0 <= low <= high <= 1.0


def test_wilson_interval_widens_with_fewer_games() -> None:
    narrow = wilson(50, 100)
    wide = wilson(5, 10)
    assert (narrow[1] - narrow[0]) < (wide[1] - wide[0])


def test_match_result_rate_and_interval_and_line() -> None:
    result = MatchResult(label="demo", seat="cop", wins=8, games=10, points=7.5)
    assert result.rate == 0.8
    low, high = result.interval
    assert low <= 0.8 <= high
    assert "demo" in result.line()
    assert "cop" in result.line()


def test_compare_reports_significant_for_non_overlapping_intervals() -> None:
    baseline = MatchResult(label="base", seat="cop", wins=0, games=100, points=0.0)
    candidate = MatchResult(label="cand", seat="cop", wins=100, games=100, points=20.0)
    verdict = compare(baseline, candidate)
    assert "SIGNIFICANT" in verdict
    assert "not separable" not in verdict


def test_compare_reports_not_separable_for_overlapping_intervals() -> None:
    baseline = MatchResult(label="base", seat="cop", wins=5, games=10, points=2.5)
    candidate = MatchResult(label="cand", seat="cop", wins=6, games=10, points=3.0)
    verdict = compare(baseline, candidate)
    assert "not separable" in verdict


def test_run_match_scores_cop_seat_against_greedy_evader(default_params) -> None:
    def make_cop(index: int) -> ChaserCop:
        return ChaserCop("cop", game_params=default_params, use_barriers=True)

    def make_thief(index: int) -> GreedyEvader:
        return GreedyEvader("thief", game_params=default_params)

    result = run_match(
        "chaser vs evader", "cop", make_cop, make_thief, _GAMES,
        default_params, PREFERRED, seed=0,
    )
    assert result.games == _GAMES
    assert 0 <= result.wins <= _GAMES
    assert result.rate == result.wins / _GAMES


def test_run_match_with_zero_games_reports_zero_points(default_params) -> None:
    def make_cop(index: int) -> ChaserCop:
        return ChaserCop("cop", game_params=default_params)

    def make_thief(index: int) -> GreedyEvader:
        return GreedyEvader("thief", game_params=default_params)

    result = run_match(
        "empty", "thief", make_cop, make_thief, 0, default_params, PREFERRED, seed=0,
    )
    assert result.games == 0
    assert result.points == 0.0
    assert result.rate == 0.0
