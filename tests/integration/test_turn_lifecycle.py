"""Stub tests for plan 02-10, Section 10.4 gate criteria 2 and 3 (turn lifecycle)."""

import pytest


def test_two_runtimes_share_no_runtime_state():
    """Two PeerRuntime instances (cop and thief) share no runtime state object."""
    pytest.skip("stub — implemented in plan 02-10")


def test_full_lifecycle_init_to_game_over():
    """A full game lifecycle runs from INIT through to GAME_OVER."""
    pytest.skip("stub — implemented in plan 02-10")


def test_illegal_transition_reported_with_severity():
    """An illegal transition during a live game is reported with its severity."""
    pytest.skip("stub — implemented in plan 02-10")


def test_silent_opponent_yields_technical_win():
    """A silent (non-responding) opponent yields a technical win for the other side."""
    pytest.skip("stub — implemented in plan 02-10")


def test_freeze_writes_incident_before_exit():
    """A watchdog freeze writes an incident record before the process exits."""
    pytest.skip("stub — implemented in plan 02-10")
