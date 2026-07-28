"""Stub tests for plan 02-03 (protocol state machine). NET-04/NET-05 (D-09, D-10, D-12)."""

import pytest


def test_legal_transition_applies():
    """A legal state transition is applied and returns the new state."""
    pytest.skip("stub — implemented in plan 02-03")


def test_illegal_transition_is_always_reported():
    """An illegal transition is always reported, never silently swallowed."""
    pytest.skip("stub — implemented in plan 02-03")


def test_recoverable_severity_keeps_game_running():
    """A recoverable-severity violation does not end the game."""
    pytest.skip("stub — implemented in plan 02-03")


def test_protocol_violation_escalates_to_error():
    """A protocol violation escalates to error severity."""
    pytest.skip("stub — implemented in plan 02-03")


def test_terminal_states_have_no_outgoing_transitions():
    """Terminal states permit no further transitions."""
    pytest.skip("stub — implemented in plan 02-03")
