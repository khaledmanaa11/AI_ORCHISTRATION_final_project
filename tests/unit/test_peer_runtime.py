"""Stub tests for plan 02-06 (PeerRuntime). NET-02/NET-03."""

import pytest


def test_factory_returns_distinct_instances():
    """The PeerRuntime factory returns a distinct instance per role (no shared state)."""
    pytest.skip("stub — implemented in plan 02-06")


def test_host_and_port_not_passed_to_fastmcp_constructor():
    """host/port are supplied to run(), not to the FastMCP() constructor."""
    pytest.skip("stub — implemented in plan 02-06")


def test_server_runs_as_background_task():
    """The FastMCP server runs as a background asyncio task."""
    pytest.skip("stub — implemented in plan 02-06")


def test_client_targets_opponent_url():
    """The FastMCP client is constructed against the configured opponent_url."""
    pytest.skip("stub — implemented in plan 02-06")


def test_clean_shutdown_releases_server_task():
    """Shutting down the runtime cleanly cancels/releases the server task."""
    pytest.skip("stub — implemented in plan 02-06")
