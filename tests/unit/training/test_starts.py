"""Randomised start-state distribution -- the fix run 1 most needed (module doc).

Run 1 trained from one board and was measured somewhere it had never been.
sample_start must genuinely mix the negotiated book opening with sampled
mid-game positions, and every position it produces must be a legal state.
"""

from __future__ import annotations

import random

from training.starts import MIN_SEPARATION, distinct_start_count, sample_start


def test_sample_start_sometimes_returns_the_book_opening_and_sometimes_does_not(default_params):
    rng = random.Random(0)
    opening = (default_params.cop_start, default_params.thief_start)
    seen_opening = seen_other = False
    for _ in range(200):
        state = sample_start(default_params, rng)
        if (state.cop, state.thief) == opening and state.turn == 0 and not state.barriers:
            seen_opening = True
        else:
            seen_other = True
    assert seen_opening
    assert seen_other


def test_every_sampled_state_is_legal(default_params):
    rng = random.Random(1)
    size = default_params.board_size
    for _ in range(200):
        state = sample_start(default_params, rng)
        assert state.cop != state.thief
        assert state.cop not in state.barriers
        assert state.thief not in state.barriers
        assert 0 <= state.cop[0] < size and 0 <= state.cop[1] < size
        assert 0 <= state.thief[0] < size and 0 <= state.thief[1] < size
        assert state.turn < default_params.survival_threshold
        assert state.barriers_placed == len(state.barriers)


def test_sampled_positions_respect_minimum_separation(default_params):
    rng = random.Random(2)
    for _ in range(200):
        state = sample_start(default_params, rng)
        gap = abs(state.cop[0] - state.thief[0]) + abs(state.cop[1] - state.thief[1])
        assert gap >= MIN_SEPARATION


def test_distinct_start_count_counts_distinct_states(default_params):
    rng = random.Random(3)
    states = [sample_start(default_params, rng) for _ in range(50)]
    doubled = states + states
    assert distinct_start_count(doubled) == distinct_start_count(states)
    assert distinct_start_count(states) >= 2
