"""The one-shot inbound gate that makes `late_peer_harness`'s teardown
sequence a fact of PROGRAM ORDER instead of a coin flip (deferred-items.md
#4). Test-only; no production source is touched, and no number moves.

Not a `test_*.py` file on purpose -- pytest never collects it (the
`tests/unit/_fakes_agent.py` precedent). It is a sibling of
`late_peer_harness.py` rather than three more lines inside it because that
file measures 131/150 code lines under `scripts/check_line_limit.sh`, whose
awk rule skips blanks and `#` comments but COUNTS docstring lines. Split,
never compress.

WHY A GATE IS THE ONLY SEAM. `run_final_audit` is push-THEN-receive
(`agent_audit_wiring.py`), and the receive leg is
`receive_final_reveal` -> `next_protocol_message` -> `wait_for_opponent` ->
`bounded(queue.get(), ...)` (`deadline_wait.py:46`). The ONLY producer for
that queue is this same process's own tool handler,
`tools._accept`'s `await queue.put(envelope)` (`tools.py:87`), which runs
DURING the peer's `client.call_tool`. So A cannot finish its audit until B
has already pushed: `_LATE_SECONDS` is absorbed whole by A blocking on B,
and B is never "late" in any sense the non-vacuity control needs. What was
left racing was a sub-tick TAIL on ONE event loop -- `tools._accept` acks at
ENQUEUE time (`tools.py:87-88`), so A's audit unblocks BEFORE the 200 is
flushed, and A's post-dequeue work then races B's client reading that 200.
Nothing sequenced them. Widening any timeout cannot reach that race (and
would move a Table-19 number, CLAUDE.md rule 1); only holding the handler
open can.

THE TWO EDGES IT BUYS, both strict program order:

1. ARRIVAL. `arrived` is set inside A's own tool handler, after the
   envelope is queued and before the handler returns. That handler sits on
   the request path of B's `client.call_tool`, so `arrived` cannot be set
   unless B's push has already reached A. Awaiting it therefore returns
   only in a state where B is demonstrably mid-request. The old harness
   merely HOPED for this; the gate makes it true by construction.
2. CUT-OFF. The handler is parked on `await released.wait()`, so it cannot
   emit its 200. `stop_runtime` enters `PeerRuntime.stop()` and reaches
   `task.cancel()` with no intervening suspension point -- only the
   following `await task` yields -- so the cancel is committed before the
   loop can ever resume a parked handler. `released.set()` in the harness's
   `finally` is then a no-op for the outcome and exists only so no path
   leaves a handler parked forever.

`put_nowait`, never `queue.put`: rebinding the instance attribute and then
calling `queue.put` from inside the replacement would recurse. The queue is
unbounded (`asyncio.Queue()`, maxsize 0), so `put_nowait` cannot raise
`QueueFull`. `tools._accept` resolves `queue.put` at CALL time, so the
instance attribute wins over the class method without patching production.
"""

from __future__ import annotations

import asyncio

from pursuit.network.envelope import MessageType


def hold_peer_final_reveal_open(ctx) -> tuple[asyncio.Event, asyncio.Event]:
    """Gate `ctx.runtime.queue` so the NEXT inbound FINAL_REVEAL is queued
    and then HELD un-acked until the caller releases it.

    Returns `(arrived, released)`. `arrived` is set once the peer's
    FINAL_REVEAL has been enqueued -- i.e. the peer is provably inside its
    own `call_tool` -- and the handler then blocks on `released`, so the
    peer cannot receive its 200 until the caller says so. Every other
    message type passes straight through, so the game phase, the handshake
    and `linger_for_peer`'s drain are all byte-unaffected.
    """
    queue = ctx.runtime.queue
    arrived, released = asyncio.Event(), asyncio.Event()
    put_nowait = queue.put_nowait

    async def _gated_put(item) -> None:
        put_nowait(item)
        if item.type is MessageType.FINAL_REVEAL:
            arrived.set()
            await released.wait()

    queue.put = _gated_put
    return arrived, released
