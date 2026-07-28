"""Stub tests for plan 02-02 (message envelope). NET-08 (D-06)."""

import pytest


def test_envelope_round_trip():
    """An envelope serialized then deserialized yields an equal object."""
    pytest.skip("stub — implemented in plan 02-02")


def test_message_type_enum_covers_four_kinds():
    """MessageType enumerates exactly the four protocol message kinds."""
    pytest.skip("stub — implemented in plan 02-02")


def test_move_payload_carries_x_y():
    """A move-type envelope payload carries x/y coordinates."""
    pytest.skip("stub — implemented in plan 02-02")


def test_unknown_type_rejected():
    """An envelope with an unrecognized message type is rejected."""
    pytest.skip("stub — implemented in plan 02-02")


def test_missing_field_rejected():
    """An envelope missing a required field is rejected."""
    pytest.skip("stub — implemented in plan 02-02")
