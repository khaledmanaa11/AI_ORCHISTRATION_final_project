"""Tests for training/generation.py -- one batch-synchronous self-play batch.

Weights are FROZEN for the whole generation (module doc): every sample in a
batch is drawn against the same opponent the update is later fitted to.
This file checks the batch bookkeeping (seat alternation, record count) and
the epsilon decay schedule, using a small game count so real ValueSearchBrain
search stays fast.
"""

from __future__ import annotations

import random

import pytest

from pursuit.shared.resolution import PREFERRED
from pursuit.strategy.weights import PRIOR
from training.generation import epsilon_for, play_generation

_GAMES = 6


def test_play_generation_produces_one_record_per_game(default_params) -> None:
    result = play_generation(
        PRIOR, [], _GAMES, epsilon=0.0, params=default_params, rules=PREFERRED,
        rng=random.Random(0),
    )
    assert len(result.records) == _GAMES
    assert len(result.starts) == _GAMES


def test_play_generation_alternates_seats_strictly(default_params) -> None:
    result = play_generation(
        PRIOR, [], _GAMES, epsilon=0.0, params=default_params, rules=PREFERRED,
        rng=random.Random(1),
    )
    assert result.cop_games + result.thief_games == _GAMES
    assert result.cop_games == _GAMES // 2
    assert result.thief_games == _GAMES // 2


def test_rates_are_bounded_fractions(default_params) -> None:
    result = play_generation(
        PRIOR, [], _GAMES, epsilon=0.1, params=default_params, rules=PREFERRED,
        rng=random.Random(2),
    )
    assert 0.0 <= result.cop_rate <= 1.0
    assert 0.0 <= result.thief_rate <= 1.0
    assert result.cop_captures <= result.cop_games
    assert result.thief_survivals <= result.thief_games


def test_rate_is_zero_when_the_learner_never_held_that_seat(default_params) -> None:
    result = play_generation(
        PRIOR, [], 0, epsilon=0.0, params=default_params, rules=PREFERRED,
        rng=random.Random(3),
    )
    assert result.cop_rate == 0.0
    assert result.thief_rate == 0.0


def test_epsilon_for_starts_at_start_value() -> None:
    assert epsilon_for(0, total=10, start=0.5, floor=0.05) == 0.5


def test_epsilon_for_ends_at_floor_value() -> None:
    assert epsilon_for(9, total=10, start=0.5, floor=0.05) == pytest.approx(0.05)


def test_epsilon_for_decays_linearly_at_the_midpoint() -> None:
    midpoint = epsilon_for(5, total=11, start=1.0, floor=0.0)
    assert midpoint == 0.5


def test_epsilon_for_returns_floor_when_total_is_not_more_than_one() -> None:
    assert epsilon_for(0, total=1, start=0.9, floor=0.1) == 0.1
    assert epsilon_for(0, total=0, start=0.9, floor=0.1) == 0.1
