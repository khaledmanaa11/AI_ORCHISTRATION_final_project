"""D-53 direction-token move/barrier payload codec.

Phase 2 sent {"x": int, "y": int} -- an absolute board coordinate, forbidden
by rule 27 once a real opponent is on the wire (LANG-02). This module
replaces it: a move or barrier target is named by a DIRECTION WORD relative
to the mover's own pre-turn cell (north/south/east/west/stay), covering both
the thief/cop MOVE action and the cop's BARRIER placement with one small
vocabulary (RULES-RESOLUTION.md Sec2 -- a barrier names the cop's own cell
or one orthogonal neighbour).

`decode()` also accepts the legacy {"x","y"} shape so a Phase-2 peer is
still understood (D-53) -- both branches resolve through the SAME
word->cell step, so exactly one validation path exists. Nothing here ever
raises out to the caller for attacker-controlled input: an illegal or
unparseable payload comes back as a ResolvedAction with ok=False, which the
caller (turn_actions.py) turns into a technical loss for the SENDER (rules
13/14), never a crash and never a silent STAY.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pursuit.sdk.actions import barrier_cells, cop_actions, thief_actions
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

Coord = tuple[int, int]


class Origin(str, Enum):
    """Axis-origin corners named by PARAMETERS.md Table 13 row 3. Which
    corner is cell (0,0) decides which delta the word "north" resolves to;
    "top-left" is game_params.json's negotiated default (config/*/game_params.json)."""

    TOP_LEFT = "top-left"
    BOTTOM_LEFT = "bottom-left"
    TOP_RIGHT = "top-right"
    BOTTOM_RIGHT = "bottom-right"


DEFAULT_ORIGIN = Origin.TOP_LEFT.value


class DirectionWord(str, Enum):
    """The wire vocabulary (D-53): a move, or a barrier target, named
    relative to the mover's own pre-turn cell. No integer ever names a
    cell (rule 27)."""

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    STAY = "stay"


class ActionKind(str, Enum):
    """What a direction word names: a move, or a cop barrier target
    relative to the cop (RULES-RESOLUTION.md Sec2)."""

    MOVE = "move"
    BARRIER = "barrier"


class MovePayloadKey(str, Enum):
    """Wire key names for the direction-token payload shape."""

    KIND = "kind"
    DIRECTION = "direction"


_BASE_VECTOR: dict[DirectionWord, Coord] = {
    DirectionWord.NORTH: (-1, 0),
    DirectionWord.SOUTH: (1, 0),
    DirectionWord.EAST: (0, 1),
    DirectionWord.WEST: (0, -1),
    DirectionWord.STAY: (0, 0),
}


def _axis_signs(origin: str) -> Coord:
    """row_sign, col_sign for `origin`: negate the row axis for a bottom-*
    corner, negate the column axis for a *-right corner. "top-left"
    reproduces pursuit.constants.Direction's own convention exactly."""
    row_sign = -1 if origin.startswith("bottom") else 1
    col_sign = -1 if origin.endswith("right") else 1
    return row_sign, col_sign


def _vector_for(word: DirectionWord, origin: str) -> Coord:
    """(row_delta, col_delta) for `word`, DERIVED from the loaded `origin`
    -- never a hardcoded top-left assumption."""
    row_sign, col_sign = _axis_signs(origin)
    dr, dc = _BASE_VECTOR[word]
    return dr * row_sign, dc * col_sign


def _word_for_vector(vector: Coord, origin: str) -> DirectionWord | None:
    """Inverse of `_vector_for`: the word matching `vector` under `origin`,
    or None when `vector` is not one of the five (a diagonal, a 2-cell
    jump, ...)."""
    for word in DirectionWord:
        if _vector_for(word, origin) == vector:
            return word
    return None


@dataclass(frozen=True)
class ResolvedAction:
    """decode()'s result. Never an exception -- `ok=False` carries a
    human-readable `reason` the caller logs and turns into a technical loss
    for the sender; `ok=True` carries the resolved `cell` and `kind`."""

    ok: bool
    cell: Coord | None = None
    kind: ActionKind | None = None
    reason: str | None = None


def encode(pre: Coord, post: Coord, kind: ActionKind, *, origin: str = DEFAULT_ORIGIN) -> dict:
    """Our own outgoing shape -- no integer ever names a cell (rule 27).

    `post` is the destination cell for a MOVE, or the barrier target cell
    (the cop's own cell or one neighbour) for a BARRIER. Raises ValueError
    if pre->post is not one of the five orthogonal-or-stay steps: OUR OWN
    strategy layer must only ever offer a legal step here (unlike decode(),
    which handles attacker-controlled input and must never raise)."""
    vector = (post[0] - pre[0], post[1] - pre[1])
    word = _word_for_vector(vector, origin)
    if word is None:
        raise ValueError(f"{pre} -> {post} is not an orthogonal step under origin={origin!r}")
    return {MovePayloadKey.KIND.value: kind.value, MovePayloadKey.DIRECTION.value: word.value}


def _resolve_legacy(payload: dict, pre_cell: Coord) -> tuple[int, int] | str:
    """Extract and int-validate the D-53 legacy {"x","y"} pair: the (x, y)
    tuple, or a str reason (bool fails too -- bool is an int subclass)."""
    x, y = payload["x"], payload["y"]
    for value, label in ((x, "x"), (y, "y")):
        if isinstance(value, bool) or not isinstance(value, int):
            return f"legacy payload {label!r} must be an int, got {type(value).__name__}"
    return x, y


def decode(
    payload: dict, pre_cell: Coord, params: GameParams, *, origin: str = DEFAULT_ORIGIN
) -> ResolvedAction:
    """Accept EITHER the direction shape or the legacy {"x","y"} shape
    (D-53) and resolve to a candidate cell. Never raises: a malformed or
    geometrically illegal payload comes back with ok=False and a reason
    (rules 13/14) -- it is never coerced to STAY."""
    if not isinstance(payload, dict):
        return ResolvedAction(ok=False, reason=f"payload must be a dict, got {type(payload).__name__}")
    try:
        if MovePayloadKey.DIRECTION.value in payload:
            kind = ActionKind(payload.get(MovePayloadKey.KIND.value, ActionKind.MOVE.value))
            word = DirectionWord(payload[MovePayloadKey.DIRECTION.value])
        elif "x" in payload and "y" in payload:
            kind = ActionKind.MOVE
            legacy = _resolve_legacy(payload, pre_cell)
            if isinstance(legacy, str):
                return ResolvedAction(ok=False, reason=legacy)
            vector = (legacy[0] - pre_cell[0], legacy[1] - pre_cell[1])
            word = _word_for_vector(vector, origin)
            if word is None:
                return ResolvedAction(ok=False, reason=f"{pre_cell} -> {legacy} is not an orthogonal step")
        else:
            return ResolvedAction(ok=False, reason="payload has neither direction nor x/y keys")
    except (KeyError, ValueError, TypeError) as exc:
        return ResolvedAction(ok=False, reason=str(exc))

    dr, dc = _vector_for(word, origin)
    cell = (pre_cell[0] + dr, pre_cell[1] + dc)
    if not (0 <= cell[0] < params.board_size and 0 <= cell[1] < params.board_size):
        return ResolvedAction(ok=False, reason=f"resolved cell {cell} is off-board")
    return ResolvedAction(ok=True, cell=cell, kind=kind)


def is_legal(pre: Coord, resolved: ResolvedAction, state: GameState, params: GameParams) -> bool:
    """The resolved action must be in the mover's legal set from
    sdk/actions.py -- imported, never reimplemented here."""
    if not resolved.ok or resolved.cell is None:
        return False
    if resolved.kind is ActionKind.BARRIER:
        return pre == state.cop and resolved.cell in barrier_cells(state, params)
    if pre == state.cop:
        return resolved.cell in {a.move for a in cop_actions(state, params) if not a.is_barrier}
    if pre == state.thief:
        return resolved.cell in set(thief_actions(state, params))
    return False
