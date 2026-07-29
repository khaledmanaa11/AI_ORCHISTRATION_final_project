"""NET-06 deadline tracker: bounded waits, narrow retry ladder, technical win.

RULES.md rule 6 makes a deadline tracker mandatory ("system paralysis, loss on timeout" is the
sanction for its absence). D-13 fixes the policy implemented here: a missed response deadline is
retried N times with backoff, then declared a technical win with logged evidence, ending cleanly.
The verdict is RETURNED to the caller -- this module never ends the game, scores, logs, or touches
game state; the 02-09 orchestrator acts on it and 02-04's JSONL writer persists it.

D-17 parameter provenance (docs/PARAMETERS.md Table 19, "Gatekeeper: rate limiting and
protection"): response timeout 30s -> row 6 (negotiable); retries 3 -> row 4 (minimum); backoff 5s
-> row 3 (minimum). Rows 3-4 are titled for the Phase-7 mail Gatekeeper, not network transport, but
02-CONTEXT.md delegates NET-06's exact retry/backoff to implementation discretion, and this module
DELIBERATELY REUSES those rows -- the only project-wide precedent for "how many retries, how long a
wait" -- rather than inventing a second, unsourced pair. Both rows are MINIMUM values, so meeting
them exactly is compliant (rule 12: minimums may be raised by agreement, never lowered). All three
numbers arrive only as arguments read from NetworkParams; none is a literal in this file.

RESEARCH Pitfall 4 (verified against the installed fastmcp 3.4.5 / mcp source): the transport
exception is spelled ``McpError`` (mixed case) in this version, not the ``MCPError`` spelling an
earlier research citation used -- ``from mcp import McpError`` is the corrected import (see
tests/unit/test_deadline.py's STEP 0 note). ``McpError`` is retryable (TimeoutError | JSONRPCError
at the transport level, plus this module's own DeadlineExpired for a missed per-attempt deadline).
``fastmcp.exceptions.ToolError`` means the opponent's tool body itself rejected the call -- an
application-level result, not a transport failure -- and must propagate untouched: retrying it, or
letting it fall into the technical-win path, would be a false declaration (rules 16/22). The
``except ToolError: raise`` clause is therefore placed BEFORE ``except RETRYABLE_TRANSPORT_ERRORS``
and this module contains no bare catch-all except clause of any kind.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable

from fastmcp.exceptions import ToolError
from mcp import McpError

from pursuit.network.verdict import CallOutcome, TechnicalWin, TechnicalWinReason

# __all__ is an immutable tuple, not a list, so it is not module-level mutable state (NET-02) --
# consistent with RETRYABLE_TRANSPORT_ERRORS below being the only other module-level datum.
__all__ = (
    "CallOutcome",
    "DeadlineExpired",
    "RETRYABLE_TRANSPORT_ERRORS",
    "TechnicalWin",
    "TechnicalWinReason",
    "call_with_retry",
    "wait_for_opponent",
)


class DeadlineExpired(Exception):  # noqa: N818 -- name fixed by the 02-07 interface contract
    """The opponent did not answer inside the allowed response deadline.

    Raised instead of leaking asyncio.TimeoutError, so callers couple to this module's own
    domain exception, never to asyncio (NET-06).
    """


RETRYABLE_TRANSPORT_ERRORS: tuple[type[Exception], ...] = (McpError, DeadlineExpired)
"""Exactly the two transport/deadline failure types (RESEARCH Pitfall 4).

McpError covers transport/protocol failure and client-side timeout; DeadlineExpired is this
module's own missed-deadline signal for the same failure class. fastmcp.exceptions.ToolError is
deliberately ABSENT and must never be added here -- see the module docstring.
"""


async def _bounded(awaitable: Awaitable[object], timeout: float) -> object:
    """Await awaitable, bounded by timeout; raise DeadlineExpired on expiry.

    The single place asyncio.wait_for is called (QUAL-02) -- reused by both wait_for_opponent
    and every call_with_retry attempt.
    """
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout)
    except TimeoutError as exc:
        raise DeadlineExpired(f"No response within {timeout} second deadline") from exc


async def wait_for_opponent(queue: asyncio.Queue, *, timeout: float) -> object:
    """Bound the WAIT_OPPONENT state on a single queued envelope.

    `queue` is the per-process asyncio.Queue that receiving MCP tools enqueue onto. `timeout`
    is the per-attempt deadline in seconds, keyword-only with no default (QUAL-11) -- callers
    supply NetworkParams.response_timeout (Table 19 row 6). Returns the queued envelope; raises
    DeadlineExpired if the deadline passes with the queue still empty.
    """
    return await _bounded(queue.get(), timeout)


async def call_with_retry(
    send: Callable[[], Awaitable[object]],
    *,
    timeout: float,
    retries: int,
    backoff: float,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> CallOutcome:
    """Call send through a bounded, narrow retry ladder (D-13, RESEARCH Pitfall 4).

    `send` is a zero-argument async callable performing one outgoing attempt; it is opaque to
    this module -- the caller (02-09) closes over the opponent client and envelope, keeping this
    module free of any FastMCP dependency and unit-testable with a plain fake. `timeout`
    (NetworkParams.response_timeout, Table 19 row 6), `retries` (retry_count, row 4) and
    `backoff` (backoff_seconds, row 3, both reused per D-17 and both minimum values) are
    keyword-only with no default (QUAL-11). `sleep`/`clock` are injected seams (default
    asyncio.sleep / time.monotonic) so tests never wait on a real backoff and elapsed_seconds is
    deterministic.

    Returns a CallOutcome: on success, value set and verdict None, attempts measured (equal to
    the number of send invocations); on exhaustion, value None and verdict a TechnicalWin
    carrying measured evidence. Raises ToolError unchanged and never retried -- an
    application-level rejection is not a transport failure and burns no backoff (RESEARCH
    Pitfall 4). D-13 policy: missed deadline -> retry `retries` times with `backoff` between
    attempts -> technical win with measured evidence -> returned cleanly; this function never
    ends the game, scores, or logs.
    """
    started = clock()
    attempts = 0
    last_error = ""
    total_attempts = retries + 1
    for attempt in range(total_attempts):
        attempts = attempt + 1
        try:
            result = await _bounded(send(), timeout)
        except ToolError:
            raise
        except RETRYABLE_TRANSPORT_ERRORS as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempts < total_attempts:
                await sleep(backoff)
            continue
        return CallOutcome(value=result, verdict=None, attempts=attempts)

    verdict = TechnicalWin(
        reason=TechnicalWinReason.OPPONENT_UNRESPONSIVE,
        attempts=attempts,
        timeout_seconds=timeout,
        backoff_seconds=backoff,
        elapsed_seconds=clock() - started,
        last_error=last_error,
    )
    return CallOutcome(value=None, verdict=verdict, attempts=attempts)
