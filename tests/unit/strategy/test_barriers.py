"""Tests for the cop barrier sub-policy (STRAT-05, D-09, D-12, AI-SPEC E9)."""

from __future__ import annotations

from pursuit.shared.barrier import place_barrier
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.barriers import choose_barrier
from pursuit.strategy.pathfind import Coord

_CHOKEPOINT_COP = (0, 0)
_CHOKEPOINT_THIEF = (5, 5)
_CHOKEPOINT_EXISTING_BARRIER = frozenset({(5, 6)})
_CHOKEPOINT_EXPECTED_SEAL = (6, 5)  # the corner's one remaining open entry


def _state(
    cop: Coord, thief: Coord, barriers: frozenset = frozenset(), barriers_placed: int | None = None
) -> GameState:
    return GameState(
        cop=cop,
        thief=thief,
        barriers=barriers,
        barriers_placed=len(barriers) if barriers_placed is None else barriers_placed,
        turn=0,
    )


def test_quota_exhausted_returns_none_immediately(default_params: GameParams) -> None:
    state = _state(
        cop=_CHOKEPOINT_COP,
        thief=_CHOKEPOINT_THIEF,
        barriers=_CHOKEPOINT_EXISTING_BARRIER,
        barriers_placed=default_params.barrier_quota,
    )
    assert choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1) is None


def test_open_board_has_no_candidate_above_threshold(default_params: GameParams) -> None:
    """No single barrier lengthens an already-wide-open shortest path on a bare
    board -- the sub-policy must not spend a barrier for zero measurable gain.
    Regression coverage: before the anchor cell was excluded from candidates,
    this exact scenario returned the anchor corner itself (a trivial, thief-
    position-independent 'win') instead of None."""
    state = _state(cop=(0, 0), thief=(3, 3))
    assert choose_barrier(state, default_params, (3, 3), 1) is None


def test_chokepoint_placement_that_lengthens_escape_is_chosen(default_params: GameParams) -> None:
    """One existing barrier leaves a single open approach to the far corner
    from the cop's cell; the sub-policy must find and seal the other one,
    severing the corner from the believed thief cell entirely (STRAT-05)."""
    state = _state(
        cop=_CHOKEPOINT_COP, thief=_CHOKEPOINT_THIEF, barriers=_CHOKEPOINT_EXISTING_BARRIER
    )
    chosen = choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1)
    assert chosen == _CHOKEPOINT_EXPECTED_SEAL
    assert chosen != state.cop
    assert chosen != _CHOKEPOINT_THIEF


def test_returned_cell_is_always_engine_legal(default_params: GameParams) -> None:
    """Legality is never re-derived (QUAL-02) -- the returned cell must be one
    `place_barrier` itself actually accepts."""
    state = _state(
        cop=_CHOKEPOINT_COP, thief=_CHOKEPOINT_THIEF, barriers=_CHOKEPOINT_EXISTING_BARRIER
    )
    chosen = choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1)
    assert chosen is not None
    after = place_barrier(state, chosen, default_params)
    assert after is not state
    assert chosen in after.barriers
    assert after.barriers_placed == state.barriers_placed + 1


def test_already_unreachable_anchor_yields_no_further_gain(default_params: GameParams) -> None:
    """Both of the corner's entries are already sealed -- baseline distance to
    the anchor is already UNREACHABLE, so no further candidate can register a
    gain and the sub-policy must not spend a barrier chasing zero."""
    state = _state(
        cop=_CHOKEPOINT_COP,
        thief=_CHOKEPOINT_THIEF,
        barriers=_CHOKEPOINT_EXISTING_BARRIER | frozenset({_CHOKEPOINT_EXPECTED_SEAL}),
    )
    assert choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1) is None


def test_deterministic_repeated_calls(default_params: GameParams) -> None:
    """Pure function of its inputs (D-03) -- identical inputs, identical output."""
    state = _state(
        cop=_CHOKEPOINT_COP, thief=_CHOKEPOINT_THIEF, barriers=_CHOKEPOINT_EXISTING_BARRIER
    )
    first = choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1)
    second = choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1)
    assert first == second == _CHOKEPOINT_EXPECTED_SEAL
