"""Tests for the Bayes motion-model PREDICTION step (D-10, D-11)."""

from __future__ import annotations

import pytest

from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.pathfind import Coord
from pursuit.strategy.prior import argmax_cell, spread, uniform


def _state(cop: Coord, thief: Coord, barriers: frozenset = frozenset()) -> GameState:
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=len(barriers), turn=0)


def test_uniform_sums_to_one() -> None:
    cells = [(0, 0), (0, 1), (1, 0)]
    prior = uniform(cells)
    assert sum(prior.values()) == pytest.approx(1.0)
    assert set(prior) == set(cells)


def test_uniform_rejects_empty() -> None:
    with pytest.raises(ValueError):
        uniform([])


def test_spread_preserves_total_mass(default_params: GameParams) -> None:
    state = _state(cop=(0, 0), thief=(3, 3))
    prior = uniform([(3, 3)])
    spread_prior = spread(prior, state, "thief", default_params)
    assert sum(spread_prior.values()) == pytest.approx(1.0)


def test_spread_never_enters_barrier_or_off_board(default_params: GameParams) -> None:
    size = default_params.board_size
    barrier = (0, 1)
    state = _state(cop=(size - 1, size - 1), thief=(0, 0), barriers=frozenset({barrier}))
    prior = uniform([(0, 0)])
    spread_prior = spread(prior, state, "thief", default_params)
    assert barrier not in spread_prior
    for cell in spread_prior:
        assert 0 <= cell[0] < size
        assert 0 <= cell[1] < size
    assert sum(spread_prior.values()) == pytest.approx(1.0)


def test_spread_concentrated_prior_matches_legal_moves(default_params: GameParams) -> None:
    state = _state(cop=(0, 0), thief=(3, 3))
    prior = uniform([(3, 3)])
    spread_prior = spread(prior, state, "thief", default_params)
    expected = set(get_legal_moves(state, "thief", default_params))
    assert set(spread_prior) == expected
    for mass in spread_prior.values():
        assert mass == pytest.approx(1.0 / len(expected))


def test_spread_skips_zero_mass_cells(default_params: GameParams) -> None:
    """A cell carrying exactly zero mass contributes no spread share -- the
    loop's early-continue branch, exercised here rather than left dead."""
    state = _state(cop=(0, 0), thief=(3, 3))
    prior = {(3, 3): 1.0, (6, 6): 0.0}
    spread_prior = spread(prior, state, "thief", default_params)
    assert sum(spread_prior.values()) == pytest.approx(1.0)
    assert (6, 6) not in spread_prior


def test_spread_rejects_unnormalized_input(default_params: GameParams) -> None:
    state = _state(cop=(0, 0), thief=(3, 3))
    with pytest.raises(ValueError):
        spread({(3, 3): 0.4}, state, "thief", default_params)


def test_argmax_cell_picks_highest_mass() -> None:
    prior = {(0, 0): 0.2, (1, 1): 0.7, (2, 2): 0.1}
    assert argmax_cell(prior) == (1, 1)


def test_argmax_cell_breaks_ties_deterministically() -> None:
    prior = {(2, 2): 0.5, (0, 0): 0.5}
    assert argmax_cell(prior) == (0, 0)


def test_argmax_cell_rejects_empty() -> None:
    with pytest.raises(ValueError):
        argmax_cell({})
