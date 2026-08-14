"""NET-06 exception taxonomy: which failures are retried, which are raised.

Split out of `deadline.py` at the 150-code-line gate (Segal Table 5) when 05-09 added the
httpx family and its reasoning -- the same relocate-and-re-export move `agent_audit_verdict.py`,
`game_identity.py`, `secret_wiring.py` and `turn_hint_buffer.py` already made. `deadline.py`
keeps the D-13/D-17 POLICY (bounded wait, ladder, technical win) and re-exports both names
below, so every existing importer is unaffected. The taxonomy is the load-bearing part of
NET-06 and now has one owner.

THE RULE THIS MODULE ENCODES: a TRANSPORT failure is retried, an APPLICATION answer is raised,
and a fault that is OURS AND DETERMINISTIC is raised. There is no catch-all anywhere in either
module -- widening happens by naming a class, never by a bare catch-all clause.

FAMILY 1 -- ``McpError`` (RESEARCH Pitfall 4, verified against the installed fastmcp 3.4.5 /
mcp source): transport/protocol failure and client-side timeout, spelled mixed-case in this
version (`from mcp import McpError`, not `MCPError`). Retryable.

FAMILY 2 -- ``DeadlineExpired``: this module's own missed-per-attempt-deadline signal, raised
instead of leaking `asyncio.TimeoutError` so callers couple to a domain exception, never to
asyncio. Same failure class as family 1. Retryable.

FAMILY 3 -- ``httpx.TransportError`` (added 05-09): the connection/read failure family, i.e.
the SAME failure class family 1 covers, arriving by a different library's exception tree
because fastmcp's client raises httpx's own errors directly on the connect path. Before 05-09
it matched neither clause, so it escaped `call_with_retry` entirely, propagated out of
`run_agent` through `main.py` and KILLED the process -- making US the side that published no
nonces (rule 36) with no verdict at all in our own log. Measured 4/4 runs while 05-04
established its own baseline; it is the exact artifact machine B produced on 2026-08-13. And
it was never teardown-only: `call_with_retry` is the ladder for EVERY outgoing envelope, so a
transient drop mid-game over a real tunnel forfeited the game.

Every remaining member of family 3 stays retryable, and each earns it:
``ConnectError``/``ReadError``/``WriteError``/``CloseError`` and the four ``TimeoutException``
members (``ConnectTimeout``/``ReadTimeout``/``WriteTimeout``/``PoolTimeout``) are transient by
definition -- ``PoolTimeout`` is our own pool exhaustion rather than the peer's fault, but it
is still transient and a backoff is exactly the right answer (and it is near-unreachable here:
every call site opens a fresh `async with ctx.runtime.client()`). ``RemoteProtocolError`` most
commonly means "server disconnected without sending a complete response", which IS the
2026-08-13 shape itself; a genuine application-level rejection arrives as ``ToolError``
instead, and is handled below.

RAISED, NEVER RETRIED -- ``RAISE_UNRETRIED_ERRORS``:

- ``fastmcp.exceptions.ToolError``: the opponent's tool body itself rejected the call. An
  application-level RESULT, not a transport failure. Retrying it, or letting it fall into the
  technical-win path, would be a false declaration (rules 16/22). Its clause is placed BEFORE
  the retryable one in `call_with_retry` and burns no backoff; 06-06 reviewed and affirmed
  that contract, and 05-09 did not disturb it -- it only widened the tuple that sits after it.
- ``httpx.LocalProtocolError`` (we sent a malformed request) and ``httpx.UnsupportedProtocol``
  (a scheme-less or bad-scheme URL). Both are members of family 3 by inheritance, and both are
  SUBTRACTED here rather than by narrowing ``RETRYABLE_TRANSPORT_ERRORS`` -- so any FUTURE
  httpx addition under ``TransportError`` stays retryable by default, which is the right
  default for a transport family. They are raised because the fault is OURS and is
  DETERMINISTIC: all four attempts fail identically, burn 3 x backoff_seconds, and end in a
  durable ``TechnicalWin(OPPONENT_UNRESPONSIVE)`` against a peer that never received a valid
  request. ``UnsupportedProtocol`` is reachable in practice, not theoretical:
  REMOTE-ROUND-RUNBOOK.md has the operator set ``PURSUIT_OPPONENT_URL`` by hand on league day
  (the D-16 env override), and omitting the ``https://`` prefix is an ordinary slip -- measured
  to raise ``UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol.``
  Raising these is NOT a reintroduction of the crash 05-09 exists to fix: a bad opponent URL is
  a configuration error that fires at the handshake, before any game exists, and failing loudly
  on bad config is this codebase's house style (`load_network_config` already raises) --
  strictly better than ~135 s of futile retries ending in a false accusation.

WRAPPED, NOT RE-CLASSIFIED -- ``unwraps_to_retryable``. Family 3 arrives in TWO shapes, and
05-09 measured both before believing either. When the failure lands on an ALREADY-OPEN session
(`client.call_tool`) it is the raw httpx exception, which the tuple above matches. When it
lands on the CONNECT path (`async with ctx.runtime.client()`), fastmcp 3.4.5 catches it at
`client/client.py:616-624` and re-raises ``RuntimeError(f"Client failed to connect: {exc}")
from exc`` -- preserving only ``httpx.HTTPStatusError`` and ``McpError`` unwrapped. Measured
against a real closed loopback port through the exact `PeerRuntime.client()` construction:
``RuntimeError: Client failed to connect: All connection attempts failed`` with
``__cause__`` = ``httpx.ConnectError``. The connect shape is the COMMON one -- it is what the
`late_peer_round(linger=False)` harness reproduces -- so a widened tuple ALONE still let the
2026-08-13 artifact through, which is why this predicate exists.

It is deliberately NOT "retry RuntimeError". ``RuntimeError`` is one of the broadest classes in
the language and our own bugs (a closed event loop, an exhausted generator) raise it; treating
it as transient would be the catch-all this module forbids in all but name. The predicate
therefore decides on the DIRECT CAUSE and on the same two named tuples as everything else: a
wrapper whose cause is retryable is retried, and EVERYTHING ELSE -- no cause, an unrelated
cause, or a cause in ``RAISE_UNRETRIED_ERRORS`` (so a scheme-less URL still fails loudly at the
handshake even when fastmcp wraps it) -- is re-raised untouched.

DELIBERATELY NOT USED -- ``httpx.HTTPError``. ``HTTPStatusError`` is a SIBLING under it (its
MRO goes straight to ``HTTPError``, never through ``TransportError``), and a 403 from 05-02's
``SharedSecretMiddleware`` is an application-level answer about OUR OWN credentials -- never a
transport failure, and exactly as unretried and unaccused as ``ToolError``. That is empirically
anchored, not an MRO argument:
``tests/integration/test_secret_channel.py::test_wrong_secret_fails_every_call`` drives the
real fastmcp client over a real socket and asserts
``pytest.raises(httpx.HTTPStatusError, match="403")``, so using ``HTTPError`` here would
demonstrably have swept the production 403 into the retry ladder and turned our own wrong
secret into an accusation against the peer.
"""

import httpx
from fastmcp.exceptions import ToolError
from mcp import McpError

__all__ = (
    "RAISE_UNRETRIED_ERRORS",
    "RETRYABLE_TRANSPORT_ERRORS",
    "DeadlineExpired",
    "error_evidence",
    "unwraps_to_retryable",
)


class DeadlineExpired(Exception):  # noqa: N818 -- name fixed by the 02-07 interface contract
    """The opponent did not answer inside the allowed response deadline.

    Raised instead of leaking asyncio.TimeoutError, so callers couple to this module's own
    domain exception, never to asyncio (NET-06).
    """


RETRYABLE_TRANSPORT_ERRORS: tuple[type[Exception], ...] = (
    McpError,
    DeadlineExpired,
    httpx.TransportError,
)
"""The three retryable transport/deadline families -- see this module's docstring for why each
is here and why ``httpx.HTTPError`` is not. ``ToolError`` is deliberately ABSENT and must never
be added; the two local-fault httpx classes are subtracted by ``RAISE_UNRETRIED_ERRORS``, never
by narrowing this tuple.

An immutable tuple, not a list, so it is not module-level mutable state (NET-02)."""


RAISE_UNRETRIED_ERRORS: tuple[type[Exception], ...] = (
    ToolError,
    httpx.LocalProtocolError,
    httpx.UnsupportedProtocol,
)
"""Caught FIRST by ``call_with_retry`` and re-raised untouched, burning no backoff: an
application-level rejection (``ToolError``) or a deterministic fault of our own
(``LocalProtocolError``/``UnsupportedProtocol``). Naming them here keeps the subtraction
greppable and testable; the except clause spells them out again at the point it fires."""


def unwraps_to_retryable(exc: BaseException) -> bool:
    """True when *exc* is a WRAPPER around a retryable transport failure.

    The decision is made by the two named tuples above and by the DIRECT cause only -- see this
    module's docstring for why "retry RuntimeError" would have been a catch-all in all but name.
    No cause, an unrelated cause, or a cause that is itself raise-first: False, so the caller
    re-raises the wrapper untouched.
    """
    cause = exc.__cause__
    if cause is None or isinstance(cause, RAISE_UNRETRIED_ERRORS):
        return False
    return isinstance(cause, RETRYABLE_TRANSPORT_ERRORS)


def error_evidence(exc: BaseException) -> str:
    """The `last_error` text a TechnicalWin carries -- the ONE definition, used by both of
    `call_with_retry`'s retryable clauses.

    A grader reading the artifact sees the real fault ("ConnectError: All connection attempts
    failed"), never a bare accusation. A wrapped failure additionally names its cause, so the
    evidence distinguishes "the session dropped mid-call" from "we never connected at all".
    """
    text = f"{type(exc).__name__}: {exc}"
    cause = exc.__cause__
    if cause is not None and isinstance(cause, RETRYABLE_TRANSPORT_ERRORS):
        text += f" (cause: {type(cause).__name__}: {cause})"
    return text
