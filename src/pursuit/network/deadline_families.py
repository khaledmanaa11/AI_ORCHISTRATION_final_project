"""NET-06 exception families: the named tuples that decide retry vs raise.

Split out of `deadline_errors.py` at the 150-code-line gate when the
2026-08-19 crash added family 4 -- the same relocate-and-re-export move that
module itself made out of `deadline.py` at 05-09. `deadline_errors.py` keeps
the PREDICATES (`unwraps_to_retryable`, `error_evidence`) and re-exports
these names, so every existing importer resolves unchanged.

THE RULE: a TRANSPORT failure is retried, an APPLICATION answer is raised,
a fault that is OURS AND DETERMINISTIC is raised. No catch-all anywhere --
widening happens by naming a class here, never by a bare except clause.

FAMILY 1 -- ``McpError`` (RESEARCH Pitfall 4, fastmcp 3.4.5 spelling):
transport/protocol failure and client-side timeout. Retryable.

FAMILY 2 -- ``DeadlineExpired``: our own missed-per-attempt-deadline signal,
raised instead of leaking ``asyncio.TimeoutError``. Retryable.

FAMILY 3 -- ``httpx.TransportError`` (05-09): the same failure class by a
different library's tree; before 05-09 it escaped the ladder and killed the
process (the 2026-08-13 artifact). Every member earns its place --
``RemoteProtocolError`` ("server disconnected without response") IS that
artifact's shape; ``PoolTimeout`` is transient pool exhaustion. Retryable.

FAMILY 4 -- ``anyio.BrokenResourceError`` / ``anyio.ClosedResourceError``
(2026-08-19; devlog `2026-08-19-remote-rehearsal-replay-board-final-
rejections.md`). When the peer's tunnel endpoint dies MID-CALL, fastmcp's
background ``post_writer`` absorbs the httpx fault and tears the session's
memory stream down; the pending ``send_request`` then raises
``anyio.BrokenResourceError`` -- ``raise ... from None``, so it carries NO
``__cause__`` and ``unwraps_to_retryable`` can never see it: it must be
matched by CLASS. Before this family it matched no clause, escaped the
ladder, and killed the agent mid-game (machine A, seat-swap attempt,
16:23). Retrying IS the session rebuild: every production attempt opens a
fresh ``async with ctx.runtime.client()`` (turn_commit_send), so the
poisoned session dies with the attempt that owned it, and a peer that stays
down exhausts into the measured ``OPPONENT_UNRESPONSIVE`` verdict instead
of a traceback. ``ClosedResourceError`` is the sibling shape (our own side
of the stream already closed) -- same session-death fact, same answer. A
peer's genuine rejection arrives as ``ToolError`` and stays raise-first.

RAISED, NEVER RETRIED -- ``RAISE_UNRETRIED_ERRORS``: ``ToolError`` is an
application-level RESULT (retrying it, or letting it reach the
technical-win path, would be a false declaration, rules 16/22);
``httpx.LocalProtocolError`` (we sent a malformed request) and
``httpx.UnsupportedProtocol`` (a scheme-less opponent URL -- an ordinary
league-day slip, measured) are deterministic faults of OUR OWN: all four
attempts would fail identically, burn 3 x backoff, and end in a false
``TechnicalWin`` against a peer that never received a valid request. Both
are SUBTRACTED here rather than by narrowing the retryable tuple, so any
future httpx addition under ``TransportError`` stays retryable by default.
"""

import anyio
import httpx
from fastmcp.exceptions import ToolError
from mcp import McpError

__all__ = (
    "RAISE_UNRETRIED_ERRORS",
    "RETRYABLE_TRANSPORT_ERRORS",
    "DeadlineExpired",
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
    anyio.BrokenResourceError,
    anyio.ClosedResourceError,
)
"""The four retryable transport/deadline families -- the module docstring argues each member.
``ToolError`` is deliberately ABSENT and must never be added; the two local-fault httpx
classes are subtracted by ``RAISE_UNRETRIED_ERRORS``, never by narrowing this tuple.

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
