"""Stub tests for plan 02-09 (turn orchestrator). NET-01/NET-04.../NET-07 (D-01, D-11, D-14)."""

import pytest


def test_turn_loop_alternates_my_turn_and_wait_opponent():
    """The turn loop alternates between MY_TURN and WAIT_OPPONENT states."""
    pytest.skip("stub — implemented in plan 02-09")


def test_move_pushed_to_opponent():
    """Each move is pushed to the opponent via the network layer."""
    pytest.skip("stub — implemented in plan 02-09")


def test_event_appended_every_turn():
    """An event is appended to the JSONL log on every turn."""
    pytest.skip("stub — implemented in plan 02-09")


def test_watchdog_touched_every_turn():
    """The watchdog is touched on every turn to prevent a false freeze."""
    pytest.skip("stub — implemented in plan 02-09")


def test_game_logic_delegated_to_sdk_engine():
    """Move/capture/scoring logic is delegated to the Phase-1 SDK engine, not reimplemented."""
    pytest.skip("stub — implemented in plan 02-09")
