"""Tests for the legal-motion model (Task 2, D-48 Sec1)."""

import pytest

from pursuit.shared.state import GameState
from pursuit.strategy.belief_motion import spread


def _state(params, cop=(0, 0), thief=(3, 3), barriers=frozenset(), placed=0):
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=0)


def _delta(size, cell):
    grid = [[0.0] * size for _ in range(size)]
    grid[cell[0]][cell[1]] = 1.0
    return grid


def _total(grid):
    return sum(sum(row) for row in grid)


def test_invalid_role_raises(default_params):
    with pytest.raises(ValueError, match="role"):
        spread(_delta(default_params.board_size, (0, 0)), "referee", _state(default_params), default_params)


def test_interior_thief_spreads_to_five_cells_with_equal_mass(default_params):
    state = _state(default_params, thief=(3, 3))
    result = spread(_delta(default_params.board_size, (3, 3)), "thief", state, default_params)
    nonzero = [v for row in result for v in row if v > 0.0]
    assert len(nonzero) == 5
    assert all(v == pytest.approx(0.2) for v in nonzero)


def test_corner_thief_spreads_only_to_the_legal_remainder(default_params):
    state = _state(default_params, thief=(0, 0))
    result = spread(_delta(default_params.board_size, (0, 0)), "thief", state, default_params)
    nonzero_cells = {(r, c) for r in range(7) for c in range(7) if result[r][c] > 0.0}
    assert nonzero_cells == {(0, 0), (0, 1), (1, 0)}


def test_mass_conserved_for_an_interior_multi_cell_prior(default_params):
    state = _state(default_params, thief=(3, 3))
    prior = _delta(default_params.board_size, (3, 3))
    prior[1][1] = 1.0
    result = spread(prior, "thief", state, default_params)
    assert _total(result) == pytest.approx(_total(prior))


def test_thief_spread_never_exceeds_five_destination_cells(default_params):
    state = _state(default_params, thief=(2, 2))
    result = spread(_delta(default_params.board_size, (2, 2)), "thief", state, default_params)
    nonzero = sum(1 for row in result for v in row if v > 0.0)
    assert nonzero <= 5


def test_cop_spread_never_exceeds_five_destination_cells(default_params):
    state = _state(default_params, cop=(3, 3))
    result = spread(_delta(default_params.board_size, (3, 3)), "cop", state, default_params)
    nonzero = sum(1 for row in result for v in row if v > 0.0)
    assert nonzero <= 5
    assert _total(result) == pytest.approx(1.0)


def test_cop_barrier_actions_collapse_onto_the_stay_branch(default_params):
    """5 moves (incl. move-to-self) + 5 barrier placements = 10 actions; the
    barrier placements ALL land on the cop's own cell via .destination(), so
    it gets 6/10 while each of the 4 other moves gets 1/10 (Task 2 note)."""
    state = _state(default_params, cop=(3, 3))
    result = spread(_delta(default_params.board_size, (3, 3)), "cop", state, default_params)
    assert result[3][3] == pytest.approx(0.6)
    assert result[2][3] == pytest.approx(0.1)


def test_cop_with_exhausted_quota_matches_the_thief_pattern(default_params):
    """No barrier actions left -> cop_actions degenerates to plain moves,
    same 5-way equal split as the thief."""
    state = _state(default_params, cop=(3, 3), placed=default_params.barrier_quota)
    result = spread(_delta(default_params.board_size, (3, 3)), "cop", state, default_params)
    nonzero = [v for row in result for v in row if v > 0.0]
    assert len(nonzero) == 5
    assert all(v == pytest.approx(0.2) for v in nonzero)


def test_zero_mass_cells_do_not_contribute(default_params):
    state = _state(default_params, thief=(3, 3))
    prior = _delta(default_params.board_size, (3, 3))
    result_with_zeros = spread(prior, "thief", state, default_params)
    result_plain = spread(_delta(default_params.board_size, (3, 3)), "thief", state, default_params)
    assert result_with_zeros == result_plain


def test_action_weights_seam_overrides_the_uniform_split(default_params):
    state = _state(default_params, thief=(3, 3))

    def all_to_first(destinations, mass):
        return [mass] + [0.0] * (len(destinations) - 1)

    result = spread(
        _delta(default_params.board_size, (3, 3)),
        "thief",
        state,
        default_params,
        action_weights=all_to_first,
    )
    assert _total(result) == pytest.approx(1.0)
    assert sum(1 for row in result for v in row if v > 0.0) == 1
