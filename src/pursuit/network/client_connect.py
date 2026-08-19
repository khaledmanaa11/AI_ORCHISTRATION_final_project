"""Bounded client connect for the handshake (the 2026-08-19 startup crash).

``_play`` used to open its handshake client with a bare
``async with ctx.runtime.client()`` -- the ONE outgoing network act in the
whole agent that stood outside the D-13 ladder. fastmcp 3.4.5 raises the
connect fault as ``RuntimeError("Client failed to connect: ...") from
httpx.ConnectError`` at ``__aenter__``, so a peer that was merely LATE (the
seat-swap attempt, 16:23: B's tunnel repointed but its agent not yet up)
killed this process with a traceback before any game existed.

This helper gives the enter the SAME measured budget every other call gets
-- ``response_timeout`` / ``retry_count`` / ``backoff_seconds`` from
NetworkParams, never widened (the envelope-boundary discipline) -- and a
FRESH client per attempt, since ``PeerRuntime.client()`` never reuses one.

ON EXHAUSTION THE CALLER ENDS WITH NO GAME, NOT A TECHNICAL WIN. The
mid-game ladder converts exhaustion into ``OPPONENT_UNRESPONSIVE`` because
a negotiated game exists to score; here NOTHING has been agreed -- no
handshake, no game_id, no Step-0 exchange -- and declaring a verdict
against a peer with whom no game was ever negotiated would be a false
declaration (rules 16/22). The caller logs the evidence and returns None,
exactly its existing not-agreed shape.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AsyncExitStack

from pursuit.network.deadline import call_with_retry
from pursuit.network.verdict import CallOutcome

#: The operator-facing evidence line, printed by the caller on exhaustion --
#: stdout is retained round evidence (REMOTE-ROUND-RUNBOOK.md), the same
#: channel tunnel_wiring uses for its own state lines.
NEVER_CONNECTED_LINE = (
    "=== PURSUIT PEER NEVER CONNECTED -- handshake abandoned after the full "
    "retry budget; no game was negotiated and no verdict is declared ==="
)


async def enter_client_with_retry(
    stack: AsyncExitStack, make_client: Callable[[], object], net: object
) -> CallOutcome:
    """Enter a fresh client through the D-13 ladder; *stack* owns its exit.

    Each attempt calls ``make_client()`` anew (``PeerRuntime.client`` builds
    a fresh ``fastmcp.Client``), so a failed enter leaves nothing behind and
    the retry IS the rebuild. On success ``outcome.value`` is the entered
    client, registered on *stack* so the caller's scope closes it; on
    exhaustion ``outcome.verdict`` carries the measured evidence and the
    stack holds nothing.
    """

    async def _connect() -> object:
        return await stack.enter_async_context(make_client())

    return await call_with_retry(
        _connect,
        timeout=net.response_timeout,
        retries=net.retry_count,
        backoff=net.backoff_seconds,
    )
