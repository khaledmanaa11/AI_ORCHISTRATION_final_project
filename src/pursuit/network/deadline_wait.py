"""NET-06 bounded waits: the ONE place `asyncio.wait_for` is called (QUAL-02).

Split out of `deadline.py` at the 150-code-line gate (Segal Table 5) when 05-10's status clause
took that file over -- the same relocate-and-re-export move `deadline_errors.py` and
`deadline_status.py` already made out of it. The seam those three files now describe between
them: this module owns the BOUNDED WAIT primitive, `deadline_errors.py`/`deadline_status.py`
own WHICH FAILURES ARE RETRYABLE, and `deadline.py` keeps the D-13/D-17 POLICY built on top of
both (ladder, backoff, technical win). `deadline.py` re-exports `wait_for_opponent` in its
`__all__`, so every existing importer -- `turn_buffer`, `turn_commit_wait`, `agent_teardown`,
`tests/unit/test_deadline.py` -- resolves through it unchanged.

`bounded` is the QUAL-02 contract itself and the reason this file is worth having: `asyncio` is
awaited in exactly one function in the whole NET-06 surface, so the conversion from
`asyncio.TimeoutError` into this project's own `DeadlineExpired` cannot be forgotten at a second
call site. Callers couple to a domain exception, never to asyncio.
"""

import asyncio
from collections.abc import Awaitable

from pursuit.network.deadline_errors import DeadlineExpired

__all__ = ("bounded", "wait_for_opponent")


async def bounded(awaitable: Awaitable[object], timeout: float) -> object:
    """Await *awaitable*, bounded by *timeout*; raise DeadlineExpired on expiry.

    The single place asyncio.wait_for is called (QUAL-02) -- reused by both wait_for_opponent
    and every `deadline.call_with_retry` attempt.
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
    return await bounded(queue.get(), timeout)
