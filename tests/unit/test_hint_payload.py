"""Tests for the D-47 hint payload shape (hint_payload.py)."""

import pytest

from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.hint_payload import (
    HintKey,
    Intent,
    assert_no_coordinates,
    build_hint,
    validate_hint_payload,
)


@pytest.mark.parametrize(
    "text",
    ["I am at 3,4", "(3, 4)", "row 3 column 4", "Row 3 Col 4"],
)
def test_assert_no_coordinates_rejects_coordinate_shapes(text):
    with pytest.raises(ValueError):
        assert_no_coordinates(text)


def test_assert_no_coordinates_accepts_plain_language():
    assert_no_coordinates("heading uptown past the park")  # must not raise


def test_validate_hint_payload_missing_intent_is_rejected():
    payload = {HintKey.TEXT.value: "hello", HintKey.TURN.value: 1}
    with pytest.raises(KeyError):
        validate_hint_payload(payload)


def test_validate_hint_payload_missing_text_is_rejected():
    payload = {HintKey.INTENT.value: Intent.TRUTH.value, HintKey.TURN.value: 1}
    with pytest.raises(KeyError):
        validate_hint_payload(payload)


def test_validate_hint_payload_bad_intent_value_is_rejected():
    payload = {HintKey.TEXT.value: "hello", HintKey.INTENT.value: "maybe", HintKey.TURN.value: 1}
    with pytest.raises(ValueError):
        validate_hint_payload(payload)


def test_validate_hint_payload_accepts_a_well_formed_payload():
    payload = {
        HintKey.TEXT.value: "heading uptown",
        HintKey.INTENT.value: Intent.LIE.value,
        HintKey.TURN.value: 3,
    }
    validate_hint_payload(payload)  # must not raise


def test_build_hint_round_trips_through_the_envelope():
    envelope = build_hint("heading uptown past the park", Intent.TRUTH, 5, "police")
    assert envelope.type is MessageType.HINT
    assert envelope.turn == 5
    assert envelope.sender == "police"
    wire = envelope.to_dict()
    restored = Envelope.from_dict(wire)
    assert restored == envelope
    assert restored.payload[HintKey.INTENT.value] == "truth"


def test_build_hint_rejects_a_coordinate_bearing_text():
    with pytest.raises(ValueError):
        build_hint("I am at 3,4", Intent.LIE, 1, "thief")


def test_build_hint_requires_an_explicit_intent_argument():
    with pytest.raises(TypeError):
        build_hint("heading uptown", turn=1, sender="police")
