"""replay_board: full-board reconstruction from a sealed artifact.

Happy paths cover both seats, barrier accumulation and the capture overlay;
containment paths prove a malformed record freezes a track instead of
raising -- the module's stated boundary discipline. The shared config path is
the same canonical file conftest's `default_params` loads.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pursuit.services.reporting.log_artifact_fields import LogArtifactField
from pursuit.services.reporting.log_turn_fields import TurnField, WireSide
from pursuit.services.reporting.replay_board import (
    BARRIER_COLOUR,
    CAPTURE_COLOUR,
    COP_COLOUR,
    EMPTY_COLOUR,
    THIEF_COLOUR,
    board_colour_frames,
)

_PARAMS = Path(__file__).parent.parent.parent / "config" / "police" / "game_params.json"


def _action(direction: str, barrier: dict | None = None) -> dict:
    return {"barrier": barrier, "move": {"direction": direction, "kind": "move"}}


def _turn(number: int, row: int, col: int, own: dict, received: dict | None) -> dict:
    return {
        TurnField.TURN: number,
        TurnField.STATE: {"position": {"row": row, "col": col}},
        TurnField.MOVE: own,
        TurnField.REVEALED_MOVE: {WireSide.SENT: own, WireSide.RECEIVED: received},
    }


def _sentinel(number: int) -> dict:
    return {
        TurnField.TURN: number,
        TurnField.STATE: None,
        TurnField.MOVE: None,
        TurnField.REVEALED_MOVE: {WireSide.SENT: None, WireSide.RECEIVED: None},
    }


def _artifact(turns: list, outcome: dict | None = None, role: str = "police") -> dict:
    return {
        LogArtifactField.ROLE: role,
        LogArtifactField.TURNS: turns,
        LogArtifactField.OUTCOME: outcome,
    }


def test_positions_advance_and_capture_overlays_the_thief_cell():
    artifact = _artifact(
        [_turn(0, 0, 0, _action("east"), _action("north")), _sentinel(1)],
        outcome={"outcome": "capture", "turn": 1},
    )
    first, last = board_colour_frames(artifact, _PARAMS)
    assert first[0][0] == COP_COLOUR
    assert first[3][3] == THIEF_COLOUR
    assert first[2][3] == EMPTY_COLOUR
    assert last[0][1] == COP_COLOUR
    assert last[2][3] == CAPTURE_COLOUR


def test_a_barrier_lands_beside_the_pre_move_cell_and_persists():
    barrier = {"direction": "north", "kind": "barrier"}
    artifact = _artifact(
        [_turn(0, 1, 1, _action("stay", barrier), _action("stay")), _sentinel(1)]
    )
    _, last = board_colour_frames(artifact, _PARAMS)
    assert last[0][1] == BARRIER_COLOUR
    assert last[1][1] == COP_COLOUR
    assert last[3][3] == THIEF_COLOUR


def test_the_thief_seat_paints_its_own_track_red_and_the_cop_blue():
    artifact = _artifact([_turn(0, 3, 3, _action("stay"), _action("stay"))], role="thief")
    (frame,) = board_colour_frames(artifact, _PARAMS)
    assert frame[3][3] == THIEF_COLOUR
    assert frame[0][0] == COP_COLOUR


def test_a_survival_outcome_never_paints_the_capture_overlay():
    artifact = _artifact(
        [_turn(0, 0, 0, _action("stay"), _action("stay"))],
        outcome={"outcome": "survival", "turn": 0},
    )
    (frame,) = board_colour_frames(artifact, _PARAMS)
    assert all(colour != CAPTURE_COLOUR for row in frame for colour in row)


def test_a_garbage_record_freezes_both_tracks_instead_of_raising():
    artifact = _artifact(["not a turn record", _sentinel(1)])
    first, last = board_colour_frames(artifact, _PARAMS)
    assert first == last
    assert last[0][0] == COP_COLOUR
    assert last[3][3] == THIEF_COLOUR


def test_a_missing_reveal_freezes_only_the_opponent_track():
    record = _turn(0, 0, 0, _action("east"), None)
    artifact = _artifact([record, _sentinel(1)])
    _, last = board_colour_frames(artifact, _PARAMS)
    assert last[0][1] == COP_COLOUR
    assert last[3][3] == THIEF_COLOUR


def test_an_artifact_without_a_turn_list_yields_no_frames():
    assert board_colour_frames({LogArtifactField.TURNS: None}, _PARAMS) == ()


def test_a_missing_game_params_file_raises_for_the_app_boundary_to_map():
    artifact = _artifact([_sentinel(0)])
    with pytest.raises(OSError):
        board_colour_frames(artifact, "does-not-exist/game_params.json")
