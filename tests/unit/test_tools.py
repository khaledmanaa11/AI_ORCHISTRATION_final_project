"""Stub tests for plan 02-06 (FastMCP tool surface). NET-03/NET-08 (D-05, D-07)."""

import pytest


def test_four_tools_registered():
    """Exactly four @mcp.tool handlers are registered on the server."""
    pytest.skip("stub — implemented in plan 02-06")


def test_every_handler_is_coroutine_function():
    """Every registered tool handler is an async coroutine function."""
    pytest.skip("stub — implemented in plan 02-06")


def test_receive_move_acks_immediately():
    """receive_move acknowledges immediately without blocking on processing."""
    pytest.skip("stub — implemented in plan 02-06")


def test_receive_move_enqueues_envelope():
    """receive_move enqueues the incoming envelope for later processing."""
    pytest.skip("stub — implemented in plan 02-06")


def test_handshake_returns_digest_and_role():
    """The handshake tool returns both a config digest and the caller's role."""
    pytest.skip("stub — implemented in plan 02-06")
