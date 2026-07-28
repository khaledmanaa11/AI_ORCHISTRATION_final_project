"""Full BASE-02 test suite — barrier placement and quota enforcement."""

from pursuit.shared.barrier import place_barrier

from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState


def test_valid_placement(default_params: GameParams, start_state: GameState) -> None:
    """Accepted placement returns a NEW GameState with the cell in barriers."""
    new_state = place_barrier(start_state, (1, 1), default_params)
    assert (1, 1) in new_state.barriers
    assert new_state.barriers_placed == start_state.barriers_placed + 1
    assert new_state is not start_state
    assert start_state.barriers == frozenset()


def test_valid_placement_does_not_mutate_original(
    default_params: GameParams, start_state: GameState
) -> None:
    """Original GameState is untouched after an accepted placement."""
    place_barrier(start_state, (2, 2), default_params)
    assert start_state.barriers_placed == 0
    assert (2, 2) not in start_state.barriers


def test_quota_exceeded(default_params: GameParams) -> None:
    """Over-quota placement returns the original state unchanged."""
    state = GameState(
        cop=(0, 0),
        thief=(3, 3),
        barriers=frozenset(),
        barriers_placed=default_params.barrier_quota,
        turn=0,
    )
    result = place_barrier(state, (0, 1), default_params)
    assert result is state
    assert result.barriers_placed == default_params.barrier_quota
    assert (0, 1) not in result.barriers


def test_rejected_no_quota_cost(
    default_params: GameParams, start_state: GameState
) -> None:
    """A rejected placement (cop's own cell) does NOT consume quota."""
    state_near_quota = GameState(
        cop=start_state.cop,
        thief=start_state.thief,
        barriers=frozenset(),
        barriers_placed=default_params.barrier_quota - 1,
        turn=0,
    )
    result = place_barrier(state_near_quota, state_near_quota.cop, default_params)
    assert result.barriers_placed == default_params.barrier_quota - 1
    assert result is state_near_quota


def test_on_own_cell_rejected(
    default_params: GameParams, start_state: GameState
) -> None:
    """Placing a barrier on the cop's own cell is rejected with no quota cost."""
    result = place_barrier(start_state, start_state.cop, default_params)
    assert result is start_state
    assert result.barriers_placed == 0


def test_on_already_barriered_cell_rejected(default_params: GameParams) -> None:
    """Placing on an already-barriered cell is rejected."""
    state = GameState(
        cop=(0, 0),
        thief=(3, 3),
        barriers=frozenset({(2, 2)}),
        barriers_placed=1,
        turn=0,
    )
    result = place_barrier(state, (2, 2), default_params)
    assert result is state
    assert result.barriers_placed == 1


def test_out_of_bounds_rejected(
    default_params: GameParams, start_state: GameState
) -> None:
    """Out-of-bounds placements are rejected with no quota cost."""
    result = place_barrier(start_state, (-1, 0), default_params)
    assert result is start_state
    assert result.barriers_placed == 0
    result2 = place_barrier(start_state, (default_params.board_size, 0), default_params)
    assert result2 is start_state


def test_on_thief_cell_is_valid_placement(
    default_params: GameParams, start_state: GameState
) -> None:
    """Placing on the thief's cell IS accepted — capture detection is 01-03's job."""
    new_state = place_barrier(start_state, start_state.thief, default_params)
    assert start_state.thief in new_state.barriers
    assert new_state.barriers_placed == start_state.barriers_placed + 1
    assert new_state is not start_state
