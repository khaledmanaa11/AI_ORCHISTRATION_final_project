"""Stub tests for plan 02-08 (handshake). NET-09 (D-08, D-15)."""

import pytest


def test_handshake_transitions_init_to_handshake():
    """Initiating a handshake transitions the state machine from INIT to HANDSHAKE."""
    pytest.skip("stub — implemented in plan 02-08")


def test_matching_digest_allows_play():
    """A matching config digest from both sides allows the game to proceed."""
    pytest.skip("stub — implemented in plan 02-08")


def test_mismatched_digest_aborts_before_move_one():
    """A mismatched config digest aborts the game before move one."""
    pytest.skip("stub — implemented in plan 02-08")


def test_unreachable_opponent_is_reported():
    """An unreachable opponent during handshake is reported, not silently dropped."""
    pytest.skip("stub — implemented in plan 02-08")
