"""Tests for run_agent (agent_entrypoint.py) -- CLOUD-01, NET-04, D-01.

Every collaborator is monkeypatched to a fake AT THE agent_entrypoint
MODULE's own namespace (the real functions are bound there by `from ...
import`, so patching agent_lifecycle/handshake/etc. directly would not
reach these call sites) -- zero real sockets, zero real handshake, matching
this codebase's DI-with-fakes house style.

The fakes and the `_patch_common` driver moved to
`_agent_entrypoint_fixtures.py` (07-00) when this file reached 148/150 code
lines and a second consumer appeared. Split, never compressed: nothing in
the four cases below was edited, and `_FakeTunnel`/`_patch_common` are
imported back so they read exactly as they did.
"""

import asyncio

import pytest

from pursuit.network import agent_entrypoint
from tests.unit._agent_entrypoint_fixtures import _FakeTunnel, _patch_common


async def test_run_agent_happy_path_returns_the_turn_loop_outcome(monkeypatch) -> None:
    order: list[str] = []
    _patch_common(monkeypatch, agreed=True, order=order)

    result = await agent_entrypoint.run_agent("config/police")

    assert result == "OUTCOME"
    assert order == [
        "declare_step0", "default_context", "start_server", "perform_handshake",
        "adopt_negotiated_game_id", "write_declaration", "run_turn_loop",
        "record_completed_game",
        "stop_watchdog", "linger_for_peer", "stop_runtime",
    ]


async def test_run_agent_returns_none_when_handshake_does_not_agree(monkeypatch) -> None:
    """Error case: a disagreed handshake ends the game before the turn
    loop, but the FULL teardown always still runs (finally). Asserted as an
    exact list (05-04, a strengthening of the old "not in"/"[-1]" pair):
    the old final element is no longer the last thing that runs.

    07-00 (rules 37/38): the exact list is ALSO what proves a handshake
    that never became a game is never counted as one -- "record_completed_game"
    is absent, and an exact list is the only assertion shape that can say so."""
    order: list[str] = []
    _patch_common(monkeypatch, agreed=False, order=order)

    result = await agent_entrypoint.run_agent("config/police")

    assert result is None
    assert order == [
        "declare_step0", "default_context", "start_server", "perform_handshake",
        "stop_watchdog", "linger_for_peer", "stop_runtime",
    ]


async def test_run_agent_wraps_the_whole_play_in_the_tunnel(monkeypatch) -> None:
    """End-to-end through the real run_with_tunnel composition (not just
    the wiring helper in isolation): tunnel start precedes default_context,
    and tunnel stop follows the WHOLE teardown -- so the tunnel is still up
    across the linger, which is the only way a late peer can reach us
    through it (confirmed here, not assumed)."""
    order: list[str] = []
    tunnel = _FakeTunnel(order)
    _patch_common(monkeypatch, agreed=True, order=order, tunnel=tunnel)

    result = await agent_entrypoint.run_agent("config/police")

    assert result == "OUTCOME"
    assert order == [
        "tunnel_start", "declare_step0", "default_context", "start_server", "perform_handshake",
        "adopt_negotiated_game_id", "write_declaration", "run_turn_loop",
        "record_completed_game",
        "stop_watchdog", "linger_for_peer", "stop_runtime", "tunnel_stop",
    ]


async def test_the_runtime_is_stopped_even_when_the_linger_is_cancelled(monkeypatch) -> None:
    """The `try/finally` around the linger is load-bearing, not decoration.
    `linger_for_peer` awaits `asyncio.wait_for`, a cancellation point, and
    `CancelledError` is a `BaseException` -- so three bare statements in the
    finally would skip `stop_runtime` entirely on a Ctrl-C during the grace
    window, leaking the server task and leaving the port bound. A version
    without the inner finally fails this test."""
    order: list[str] = []
    _patch_common(monkeypatch, agreed=True, order=order)

    async def _blocking_linger(ctx):
        order.append("linger_for_peer")
        await asyncio.Event().wait()

    monkeypatch.setattr(agent_entrypoint, "linger_for_peer", _blocking_linger)

    task = asyncio.create_task(agent_entrypoint.run_agent("config/police"))
    while "linger_for_peer" not in order:
        await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert order[-1] == "stop_runtime"
