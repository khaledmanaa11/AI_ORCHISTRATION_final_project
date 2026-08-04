"""Canonical Q-table state-key encoding (STRAT-01, D-04, D-05, D-06-superseded).

Implements docs/PRD_rl_strategy.md Sec2 -- the PRD is authoritative; any conflict with
this module is a bug here, not a choice to make. The key is five fields joined by "|",
a separator that cannot appear inside any field (every field is digits or a "," pair):

    own_row,own_col|target_row,target_col|blocked_mask|barriers_used|turns_remaining

Field 5 is EXACT `turns_remaining = move_ceiling - turn_index`, clamped at 0 -- not a
bucketed phase. Two independent citations argued this replacement: Puterman 1994 ch.4
(finite-horizon optimal policies are non-stationary in exact time-to-go) and Pardo et
al., "Time Limits in RL", ICML 2018 (a deadline task is non-Markov unless
turns_remaining is in the state). The old bucket was a deterministic function of the
turn index, so keeping both would only alias the exact field against a coarsened copy
of itself -- turns_remaining REPLACES the bucket, it does not join it (D-06 superseded).

The full 7x7 barrier bitmap is DELIBERATELY excluded (D-05): 2^49 possible bitmaps per
positional pair would make almost every key visited at most once, the canonical
state-space-explosion failure. blocked_mask captures the only barrier information that
changes which of the 5 actions are legal or attractive FROM THIS CELL, at a fixed cost
of 16 values.

blocked_mask bit order is agent-relative and FROZEN to Action's own order
(constants.Action, STAY excluded): bit 0 = NORTH, bit 1 = SOUTH, bit 2 =
EAST, bit 3 = WEST. A silently reordered mask would make an entire trained
table meaningless while still loading successfully -- the worst possible
failure shape -- so this order is pinned by test, not left to inference.
"""

from __future__ import annotations

import dataclasses

from pursuit.constants import Action, cell_for
from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy.base import Observation
from pursuit.strategy.pathfind import Coord

_FIELD_SEP = "|"
_COORD_SEP = ","
_KEY_FIELD_COUNT = 5
_ORTHOGONAL_ACTIONS = (Action.NORTH, Action.SOUTH, Action.EAST, Action.WEST)


def encode_state(obs: Observation, params: StrategyParams, game_params: GameParams) -> str:
    """Return the canonical string key for `obs` (PRD Sec2 worked example, adapted).

    `params` is accepted but not read here -- kept only so this signature still
    matches every existing call site (`training/harness.py`, `qlearning.py`, both
    03-14's this same wave; narrowing the signature is out of this plan's scope).
    """
    own_row, own_col = obs.own_cell
    target_row, target_col = obs.target_cell
    remaining = turns_remaining(obs.turn_index, game_params)
    return _FIELD_SEP.join(
        [
            f"{own_row}{_COORD_SEP}{own_col}",
            f"{target_row}{_COORD_SEP}{target_col}",
            str(obs.blocked_mask),
            str(obs.barriers_used),
            str(remaining),
        ]
    )


def decode_state(key: str) -> dict:
    """Reverse `encode_state`; raises ValueError on any unparseable key.

    Reconstructs every field the key carries: own_cell, target_cell,
    blocked_mask, barriers_used, turns_remaining. The raw turn_index itself is
    not recoverable -- only the clamped remaining count was ever kept.
    """
    parts = key.split(_FIELD_SEP)
    if len(parts) != _KEY_FIELD_COUNT:
        raise ValueError(f"malformed state key (expected {_KEY_FIELD_COUNT} fields): {key!r}")
    own_part, target_part, blocked_part, barriers_part, remaining_part = parts
    try:
        return {
            "own_cell": _parse_coord(own_part),
            "target_cell": _parse_coord(target_part),
            "blocked_mask": int(blocked_part),
            "barriers_used": int(barriers_part),
            "turns_remaining": int(remaining_part),
        }
    except ValueError as exc:
        raise ValueError(f"malformed state key {key!r}: {exc}") from exc


def _parse_coord(part: str) -> Coord:
    pieces = part.split(_COORD_SEP)
    if len(pieces) != 2:
        raise ValueError(f"malformed coordinate segment {part!r}")
    return (int(pieces[0]), int(pieces[1]))


def turns_remaining(turn_index: int, game_params: GameParams) -> int:
    """Exact turns left before `move_ceiling`, clamped at 0 (D-06 superseded).

    The clamp is load-bearing, not defensive: 03-16's f9 feature is
    `turns_remaining / move_ceiling` and must stay in [0, 1], and a negative
    field would widen the key space with unreachable keys. No literal ceiling
    appears here (QUAL-11) -- it always derives from `game_params.move_ceiling`.
    """
    return max(0, game_params.move_ceiling - turn_index)


def blocked_mask(state: GameState, cell: Coord, agent: str, game_params: GameParams) -> int:
    """Agent-relative bitmask of the 4 orthogonal directions blocked from `cell`.

    Blocked-ness comes from `pursuit.shared.board.get_legal_moves` on a probe
    state with `agent` hypothetically at `cell` -- never a local barrier
    check (QUAL-02), so board-edge and barrier blocking are handled
    identically and for free. STAY is never a bit -- it is always legal.
    """
    probe = (
        dataclasses.replace(state, cop=cell)
        if agent == "cop"
        else dataclasses.replace(state, thief=cell)
    )
    legal = set(get_legal_moves(probe, agent, game_params))
    mask = 0
    for action in _ORTHOGONAL_ACTIONS:
        if cell_for(action, cell) not in legal:
            mask |= 1 << action.value
    return mask
