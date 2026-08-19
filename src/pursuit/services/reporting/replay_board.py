"""Reconstruct one board colour frame per turn from a sealed `log_` artifact.

FULL-BOARD RECONSTRUCTION IS A POST-GAME OPERATION. Rule 9 forbids the
objective board in the LIVE interface; the replay viewer opens only a sealed
artifact of a finished game (`replay_source.py` refuses live files by name),
and the book's own audit reconstructs exactly this view once reveals are
public. The artifact still never records the opponent's absolute cells --
local truth survives into the file -- so the opponent's track is INTEGRATED
from their negotiated start cell plus their per-turn revealed moves, which is
why the byte-identical shared `game_params.json` (rule 11) must be supplied.

MALFORMED INPUT DEGRADES, NEVER RAISES -- the same boundary discipline as
`replay_verify`: a record that is not a dict, a missing reveal, an unknown
direction each freeze the affected track for that step and reconstruction
continues. A tampered artifact must still produce frames for the verifier's
verdict to sit beside; a renderer that dies shows nothing at all.

`gui/` reaches this module ONLY through its re-export in `replay_verify`
(`scripts/check_local_truth.py` allows that single import path), and every
value it hands over is ready to paint: `widgets.GridPanel` receives colour
matrices and computes nothing (`test_gui_structural.py`).
"""

from __future__ import annotations

from pathlib import Path

from pursuit.services.reporting.log_artifact_fields import LogArtifactField
from pursuit.services.reporting.log_turn_fields import TurnField, WireSide
from pursuit.shared.config import load_game_params

#: Presentation only -- which colour a reconstructed cell paints. Named per
#: the hardcoded-value rule; no game parameter is expressible as a colour.
EMPTY_COLOUR = "#ffffff"
BARRIER_COLOUR = "#1f2937"
COP_COLOUR = "#2563eb"
THIEF_COLOUR = "#dc2626"
CAPTURE_COLOUR = "#f59e0b"

#: Inner-record keys of the sealed turn shape (state_record.py writes them);
#: TurnField/WireSide cover only the top level, so the leaves are named here.
_POSITION = "position"
_ROW = "row"
_COL = "col"
_MOVE = "move"
_BARRIER = "barrier"
_DIRECTION = "direction"
_OUTCOME = "outcome"
_CAPTURE = "capture"
_POLICE = "police"

#: Orthogonal move deltas, row 0 at the top-left origin (Table 13). An
#: unknown or absent direction moves nothing rather than guessing.
_DELTAS = {
    "north": (-1, 0),
    "south": (1, 0),
    "east": (0, 1),
    "west": (0, -1),
    "stay": (0, 0),
}


def board_colour_frames(artifact: dict, game_params_path: Path | str) -> tuple:
    """One paintable colour matrix per turn record, in artifact order.

    The frame for index `i` shows the PRE-turn positions of turn record `i`,
    so the trailing outcome record (every field null) naturally renders the
    final configuration; a capture outcome overlays the thief's cell there.
    """
    params = load_game_params(game_params_path)
    turns = artifact.get(LogArtifactField.TURNS)
    if not isinstance(turns, list):
        return ()
    role = artifact.get(LogArtifactField.ROLE)
    own, opponent = _starts(role, params)
    captured = _is_capture(artifact)
    barriers: set = set()
    frames = []
    for index, record in enumerate(turns):
        own = _recorded_position(record) or own
        overlay = captured and index == len(turns) - 1
        frames.append(_frame(params.board_size, own, opponent, barriers, role, overlay))
        own, opponent = _advance(record, own, opponent, barriers, params.board_size)
    return tuple(frames)


def _starts(role: object, params) -> tuple:
    """Own and opponent start cells for the artifact's seat."""
    if role == _POLICE:
        return params.cop_start, params.thief_start
    return params.thief_start, params.cop_start


def _is_capture(artifact: dict) -> bool:
    outcome = artifact.get(LogArtifactField.OUTCOME)
    return isinstance(outcome, dict) and outcome.get(_OUTCOME) == _CAPTURE


def _recorded_position(record: object) -> tuple | None:
    """The turn's own pre-move cell, when the record carries a usable one."""
    if not isinstance(record, dict):
        return None
    state = record.get(TurnField.STATE)
    position = state.get(_POSITION) if isinstance(state, dict) else None
    if not isinstance(position, dict):
        return None
    row, col = position.get(_ROW), position.get(_COL)
    if isinstance(row, int) and isinstance(col, int):
        return row, col
    return None


def _advance(record: object, own: tuple, opponent: tuple, barriers: set, size: int) -> tuple:
    """Apply one turn's own and revealed actions; unusable halves freeze."""
    if not isinstance(record, dict):
        return own, opponent
    revealed = record.get(TurnField.REVEALED_MOVE)
    received = revealed.get(WireSide.RECEIVED) if isinstance(revealed, dict) else None
    return (
        _apply(own, record.get(TurnField.MOVE), barriers, size),
        _apply(opponent, received, barriers, size),
    )


def _apply(cell: tuple, action: object, barriers: set, size: int) -> tuple:
    """One actor's action: a barrier lands beside its pre-move cell (rule 46's
    geometry), then the move half relocates the actor."""
    if not isinstance(action, dict):
        return cell
    barrier = action.get(_BARRIER)
    if isinstance(barrier, dict):
        barriers.add(_shift(cell, barrier.get(_DIRECTION), size))
    move = action.get(_MOVE)
    if isinstance(move, dict):
        return _shift(cell, move.get(_DIRECTION), size)
    return cell


def _shift(cell: tuple, direction: object, size: int) -> tuple:
    """Move one step, clamped to the board -- a sealed log holds only legal
    moves, so the clamp is containment for tampered input, not game logic."""
    delta = _DELTAS.get(direction, (0, 0))
    row = min(max(cell[0] + delta[0], 0), size - 1)
    col = min(max(cell[1] + delta[1], 0), size - 1)
    return row, col


def _frame(
    size: int, own: tuple, opponent: tuple, barriers: set, role: object, overlay: bool
) -> tuple:
    """One colour matrix: barriers under agents, capture overlay on top."""
    own_colour = COP_COLOUR if role == _POLICE else THIEF_COLOUR
    opponent_colour = THIEF_COLOUR if role == _POLICE else COP_COLOUR
    thief_cell = opponent if role == _POLICE else own
    grid = [[EMPTY_COLOUR] * size for _ in range(size)]
    for row, col in barriers:
        grid[row][col] = BARRIER_COLOUR
    grid[opponent[0]][opponent[1]] = opponent_colour
    grid[own[0]][own[1]] = own_colour
    if overlay:
        grid[thief_cell[0]][thief_cell[1]] = CAPTURE_COLOUR
    return tuple(tuple(row) for row in grid)
