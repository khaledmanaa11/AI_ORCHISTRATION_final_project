"""Tests for encoding.py -- canonical state key, D-05/D-06/D-18 (STRAT-01)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pursuit.constants import Action
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams, load_strategy_config
from pursuit.strategy.base import Observation
from pursuit.strategy.encoding import blocked_mask, decode_state, encode_state, turn_bucket

_POLICE_STRATEGY = Path(__file__).parent.parent.parent.parent / "config" / "police" / "strategy.json"


def _strategy_params() -> StrategyParams:
    """Real config/police/strategy.json -- turn_bucket_fractions=[0.34, 0.69]."""
    return load_strategy_config(_POLICE_STRATEGY)


def _state(cop: tuple, thief: tuple, barriers: frozenset = frozenset()) -> GameState:
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=len(barriers), turn=0)


def _obs(own, target, mask, barriers_used, turn_index) -> Observation:
    return Observation(
        own_cell=own, target_cell=target, blocked_mask=mask,
        barriers_used=barriers_used, turn_index=turn_index,
    )


def test_worked_example_key_matches_prd_verbatim(default_params: GameParams) -> None:
    """docs/PRD_rl_strategy.md Sec2's own worked example -- (2,3)/(5,5)/9/6/turn14."""
    obs = _obs(own=(2, 3), target=(5, 5), mask=9, barriers_used=6, turn_index=14)
    key = encode_state(obs, _strategy_params(), default_params)
    assert key == "2,3|5,5|9|6|1"


def test_round_trip_decode_reconstructs_every_keyed_field(default_params: GameParams) -> None:
    params = _strategy_params()
    obs = _obs(own=(1, 2), target=(6, 6), mask=5, barriers_used=3, turn_index=30)
    key = encode_state(obs, params, default_params)
    decoded = decode_state(key)
    assert decoded == {
        "own_cell": (1, 2),
        "target_cell": (6, 6),
        "blocked_mask": 5,
        "barriers_used": 3,
        "turn_bucket": turn_bucket(30, params, default_params),
    }


def test_distant_barrier_does_not_change_key(default_params: GameParams) -> None:
    """D-05: two states differing only in a barrier FAR from own_cell encode identically."""
    own = (3, 3)
    state_a = _state(cop=own, thief=(0, 6), barriers=frozenset({(0, 0)}))
    state_b = _state(cop=own, thief=(0, 6), barriers=frozenset({(6, 6)}))

    mask_a = blocked_mask(state_a, own, "cop", default_params)
    mask_b = blocked_mask(state_b, own, "cop", default_params)
    assert mask_a == mask_b == 0

    obs_a = _obs(own=own, target=(6, 6), mask=mask_a, barriers_used=1, turn_index=5)
    obs_b = _obs(own=own, target=(6, 6), mask=mask_b, barriers_used=1, turn_index=5)
    params = _strategy_params()
    assert encode_state(obs_a, params, default_params) == encode_state(obs_b, params, default_params)


def test_adjacent_barrier_changes_key(default_params: GameParams) -> None:
    """A barrier directly adjacent to own_cell DOES change blocked_mask, hence the key."""
    own = (3, 3)
    blocked_state = _state(cop=own, thief=(0, 6), barriers=frozenset({(3, 4)}))
    open_state = _state(cop=own, thief=(0, 6), barriers=frozenset())

    mask_blocked = blocked_mask(blocked_state, own, "cop", default_params)
    mask_open = blocked_mask(open_state, own, "cop", default_params)
    assert mask_blocked != mask_open

    params = _strategy_params()
    obs_blocked = _obs(own=own, target=(6, 6), mask=mask_blocked, barriers_used=1, turn_index=5)
    obs_open = _obs(own=own, target=(6, 6), mask=mask_open, barriers_used=0, turn_index=5)
    assert encode_state(obs_blocked, params, default_params) != encode_state(
        obs_open, params, default_params
    )


def test_blocked_mask_bit_order_pinned_to_action_order(default_params: GameParams) -> None:
    """Bit i = Action(i).value for the 4 orthogonal directions (STAY excluded);
    board edges give pure single/double-direction cases with no barriers needed."""
    size = default_params.board_size
    mid = size // 2
    state = _state(cop=(mid, mid), thief=(0, 0))

    assert blocked_mask(state, (0, mid), "cop", default_params) == 1 << Action.NORTH.value
    assert blocked_mask(state, (size - 1, mid), "cop", default_params) == 1 << Action.SOUTH.value
    assert blocked_mask(state, (mid, size - 1), "cop", default_params) == 1 << Action.EAST.value
    assert blocked_mask(state, (mid, 0), "cop", default_params) == 1 << Action.WEST.value
    # Corner: NORTH + WEST blocked -> bit0 + bit3 = 1 + 8 = 9 (PRD's own worked example value).
    assert blocked_mask(state, (0, 0), "cop", default_params) == 9


def test_turn_bucket_boundaries_pinned(default_params: GameParams) -> None:
    """fractions=[0.34, 0.69] * move_ceiling=35 -> boundaries at 11.9 / 24.15."""
    params = _strategy_params()
    assert params.turn_bucket_fractions == [0.34, 0.69]
    assert turn_bucket(11, params, default_params) == 0
    assert turn_bucket(12, params, default_params) == 1
    assert turn_bucket(24, params, default_params) == 1
    assert turn_bucket(25, params, default_params) == 2


def test_decode_state_wrong_field_count_raises() -> None:
    with pytest.raises(ValueError, match="5 fields"):
        decode_state("1,2|3,4|9|6")


def test_decode_state_non_integer_field_raises() -> None:
    with pytest.raises(ValueError):
        decode_state("1,2|3,4|nine|6|1")


def test_decode_state_malformed_coordinate_raises() -> None:
    with pytest.raises(ValueError):
        decode_state("1,2,9|3,4|9|6|1")
