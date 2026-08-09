"""Tests for state_record.py (D-60)."""

import pytest

from pursuit.security.state_record import StateRecordKey, build_state_record


def _build(**overrides: object) -> dict:
    base = {
        "game_id": "g1",
        "turn": 5,
        "role": "cop",
        "position": (2, 3),
        "barriers_remaining": 4,
    }
    base.update(overrides)
    return build_state_record(**base)  # type: ignore[arg-type]


def test_returns_exactly_the_five_fixed_fields() -> None:
    record = _build()
    assert set(record) == {
        StateRecordKey.GAME_ID.value,
        StateRecordKey.TURN.value,
        StateRecordKey.ROLE.value,
        StateRecordKey.POSITION.value,
        StateRecordKey.BARRIERS_REMAINING.value,
    }


def test_field_values_match_inputs() -> None:
    record = _build(game_id="g42", turn=7, role="thief", position=(1, 9), barriers_remaining=1)
    assert record["game_id"] == "g42"
    assert record["turn"] == 7
    assert record["role"] == "thief"
    assert record["position"] == {"row": 1, "col": 9}
    assert record["barriers_remaining"] == 1


def test_position_nests_as_row_col() -> None:
    record = _build(position=(0, 0))
    assert record["position"] == {"row": 0, "col": 0}


def test_turn_bool_raises() -> None:
    with pytest.raises(TypeError):
        _build(turn=True)


def test_barriers_remaining_bool_raises() -> None:
    with pytest.raises(TypeError):
        _build(barriers_remaining=True)


def test_turn_non_int_raises() -> None:
    with pytest.raises(TypeError):
        _build(turn="5")


def test_state_record_key_str_returns_the_bare_field_name() -> None:
    assert str(StateRecordKey.BARRIERS_REMAINING) == "barriers_remaining"
