"""The bounded post-audit grace window (05-UAT.md G1) -- a sibling module,
the established tunnel_wiring/secret_wiring/agent_entrypoint split
precedent, so `agent_entrypoint.py` stays a thin caller.

Why it exists: `peer_runtime.stop()` is `task.cancel()` plus
`listen_socket.close()`, documented there as deliberately bypassing
uvicorn's own `Server.shutdown()`. On 2026-08-13 that fired within
milliseconds of a matched audit while the opponent was still mid-exchange,
cancelling its live authenticated ASGI session -- so the peer's own push
appeared to fail and it declared us unresponsive. This window is the fix;
a gentler stop is NOT (do not soften `peer_runtime.stop`).

Parameter provenance. Both bounds are EXISTING `NetworkParams` fields
(docs/PARAMETERS.md Table 19). This module contains zero numeric literals
and adds zero keys to any `config/*/network.json` (CLAUDE.md rule 1):

- **total cap = `NetworkParams.response_timeout`** (Table 19 row 6,
  "Deadline on any network request", negotiable, 30 s). The thing being
  waited out IS one inbound network request -- the peer's own FINAL_REVEAL
  push. A peer still inside its own request deadline is by definition still
  inside this window.
- **quiet interval = `NetworkParams.backoff_seconds`** (Table 19 row 3,
  "Backoff before a retry", minimum, 5 s). If the peer were going to retry,
  it would have retried inside one backoff. This is the same row
  `deadline.py` already reuses for the same meaning (D-17).
- `watchdog_threshold` (row 7) is DELIBERATELY not used as a bound: it
  answers "has this process stopped making progress", a different question,
  and borrowing it would double the teardown wait for no negotiated reason.

Draining is not answering: the receiving tool handler already returned 200
by enqueuing the envelope. This loop only keeps the queue bounded and
supplies the quiet signal, so do not "optimise" the drain away -- without
it the window cannot tell a still-retrying peer from a silent one.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from pursuit.network.agent_context import AgentContext
from pursuit.network.deadline import DeadlineExpired, wait_for_opponent


async def linger_for_peer(
    ctx: AgentContext, *, clock: Callable[[], float] = time.monotonic,
) -> None:
    """Keep this process's server task alive, draining `ctx.runtime.queue`,
    until EITHER the queue has been quiet for one full `backoff_seconds`
    window OR `response_timeout` has elapsed in total.

    Pulls through `deadline.wait_for_opponent`, so `deadline._bounded`
    remains the ONE place this codebase calls `asyncio.wait_for` (QUAL-02).
    A `DeadlineExpired` here is the SUCCESS signal, not a fault: nothing
    more is arriving. This function never raises and never ends the game.

    `clock` is an injected seam (default `time.monotonic`, matching
    `Watchdog`/`call_with_retry`'s own DI style) so a test can drive the
    total cap deterministically.

    Cancellation is deliberately NOT swallowed. `asyncio.wait_for` is a
    cancellation point and `CancelledError` is a `BaseException`, so
    `run_agent` wraps this call in a `try/finally` -- that, not this
    function, is what guarantees `ctx.runtime.stop()` still runs.
    """
    deadline_at = clock() + ctx.net.response_timeout
    while True:
        remaining = deadline_at - clock()
        if remaining <= 0:
            return
        try:
            await wait_for_opponent(
                ctx.runtime.queue, timeout=min(ctx.net.backoff_seconds, remaining),
            )
        except DeadlineExpired:
            return
