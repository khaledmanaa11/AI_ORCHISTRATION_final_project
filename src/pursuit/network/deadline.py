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
at the transport level, plus DeadlineExpired for a missed per-attempt deadline).
``fastmcp.exceptions.ToolError`` means the opponent's tool body itself rejected the call -- an
application-level result, not a transport failure -- and must propagate untouched: retrying it, or
letting it fall into the technical-win path, would be a false declaration (rules 16/22). The
raise-first clause is therefore placed BEFORE ``except RETRYABLE_TRANSPORT_ERRORS`` and this
module contains no bare catch-all except clause of any kind.

05-09 added a THIRD retryable family, ``httpx.TransportError``, and TWO more raise-first classes,
``httpx.LocalProtocolError`` and ``httpx.UnsupportedProtocol``. Summary: fastmcp's client raises
httpx's own errors on the connect path, so a dropped connection used to match neither clause,
escape this ladder, and kill the process (rule 36 against us -- the 2026-08-13 artifact); the two
subtracted classes are OUR OWN deterministic faults, which would otherwise burn the full ladder
and end in a false ``TechnicalWin`` against a peer that never received a valid request; and
``httpx.HTTPError`` is deliberately NOT the class used, because ``HTTPStatusError`` sits under it
and a 403 from ``SharedSecretMiddleware`` is an answer about our own credentials. A widened tuple
alone was measured INSUFFICIENT: on the CONNECT path fastmcp re-raises the httpx fault as
``RuntimeError(...) from exc``, so the ladder also asks ``unwraps_to_retryable`` about a
RuntimeError's direct CAUSE -- never about the RuntimeError class itself. The FULL argument,
member by member and shape by shape, lives with the two tuples in the sibling
``deadline_errors.py`` (split at the 150-code-line gate); read it before changing either tuple.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable

import httpx
from fastmcp.exceptions import ToolError

from pursuit.network.deadline_errors import (
    RAISE_UNRETRIED_ERRORS,
    RETRYABLE_TRANSPORT_ERRORS,
    DeadlineExpired,
    error_evidence,
    unwraps_to_retryable,
)
from pursuit.network.verdict import CallOutcome, TechnicalWin, TechnicalWinReason

# __all__ is an immutable tuple, not a list, so it is not module-level mutable state (NET-02).
# DeadlineExpired / RETRYABLE_TRANSPORT_ERRORS / RAISE_UNRETRIED_ERRORS are RE-EXPORTED from
# deadline_errors.py, so every pre-05-09 importer of this module resolves unchanged.
__all__ = (
    "CallOutcome",
    "RAISE_UNRETRIED_ERRORS",
    "RETRYABLE_TRANSPORT_ERRORS",
    "DeadlineExpired",
    "TechnicalWin",
    "TechnicalWinReason",
    "call_with_retry",
    "wait_for_opponent",
)


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
    carrying measured evidence whose `last_error` is the real exception text
    (`f"{type(exc).__name__}: {exc}"`), so the artifact a grader reads says
    `ConnectError: All connection attempts failed` rather than a bare accusation.

    Raises `RAISE_UNRETRIED_ERRORS` unchanged and never retried, burning no backoff: a
    ToolError is an application-level rejection rather than a transport failure (RESEARCH
    Pitfall 4), and the two httpx members are deterministic faults of our own. An
    `httpx.HTTPStatusError` (e.g. the 403 from a wrong shared secret) matches no clause here
    and propagates for the same reason -- it is an answer, not a transport failure.

    D-13 policy: missed deadline -> retry `retries` times with `backoff` between attempts ->
    technical win with measured evidence -> returned cleanly; this function never ends the
    game, scores, or logs.
    """
    started = clock()
    attempts = 0
    last_error = ""
    total_attempts = retries + 1
    for attempt in range(total_attempts):
        attempts = attempt + 1
        try:
            result = await _bounded(send(), timeout)
        # Spelled out rather than `except RAISE_UNRETRIED_ERRORS` so the three classes are
        # visible at the point the clause fires; deadline_errors.py names the same three and
        # carries the argument for each. MUST stay before the retryable clause: the two httpx
        # members are TransportError subclasses and would otherwise be retried.
        except (ToolError, httpx.LocalProtocolError, httpx.UnsupportedProtocol):
            raise
        except RETRYABLE_TRANSPORT_ERRORS as exc:
            last_error = error_evidence(exc)
        # The SAME failure, wrapped: fastmcp re-raises a connect-path fault as
        # `RuntimeError(f"Client failed to connect: {exc}") from exc`. Narrow by CAUSE, never
        # by class -- `unwraps_to_retryable` re-raises anything whose cause is absent,
        # unrelated, or itself raise-first, so this is not "retry RuntimeError".
        except RuntimeError as exc:
            if not unwraps_to_retryable(exc):
                raise
            last_error = error_evidence(exc)
        else:
            return CallOutcome(value=result, verdict=None, attempts=attempts)
        if attempts < total_attempts:
            await sleep(backoff)

    verdict = TechnicalWin(
        reason=TechnicalWinReason.OPPONENT_UNRESPONSIVE,
        attempts=attempts,
        timeout_seconds=timeout,
        backoff_seconds=backoff,
        elapsed_seconds=clock() - started,
        last_error=last_error,
    )
    return CallOutcome(value=None, verdict=verdict, attempts=attempts)
