"""NET-06 retryability predicates, over the families `deadline_families.py` owns.

Split history, each at the 150-code-line gate: 05-09 moved the taxonomy out
of `deadline.py` into this module; 05-10 moved the status decision to
`deadline_status.py`; the 2026-08-19 family-4 addition moved the tuples and
their member-by-member argument to `deadline_families.py`. This module keeps
the two PREDICATES and re-exports every historical name, so `deadline.py`
and every other importer resolve unchanged.

WRAPPED, NOT RE-CLASSIFIED -- ``unwraps_to_retryable``. Family 3 arrives in
TWO shapes, and 05-09 measured both before believing either. On an
ALREADY-OPEN session (`client.call_tool`) the raw httpx exception matches
the tuple directly. On the CONNECT path (`async with ctx.runtime.client()`),
fastmcp 3.4.5 catches it and re-raises ``RuntimeError(f"Client failed to
connect: {exc}") from exc`` -- measured against a real closed loopback port:
``RuntimeError: Client failed to connect: All connection attempts failed``
with ``__cause__ = httpx.ConnectError``. The connect shape is the COMMON
one, so a widened tuple ALONE still let the 2026-08-13 artifact through --
which is why this predicate exists.

It is deliberately NOT "retry RuntimeError": our own bugs (a closed event
loop, an exhausted generator) raise it too, and treating it as transient
would be the catch-all this design forbids in all but name. The decision is
made on the DIRECT CAUSE and on the same named tuples as everything else --
no cause, an unrelated cause, or a cause that is itself raise-first, and the
wrapper is re-raised untouched. Family 4's ``BrokenResourceError`` is raised
``from None`` and therefore never reaches this predicate at all; it is
matched by CLASS in the tuple (see `deadline_families.py`).

DECIDED BY STATUS, NOT BY CLASS -- ``retryable_status`` (05-10):
``HTTPStatusError`` is the one class whose type cannot answer the question
(a 502 from the peer's tunnel is transient, a 403 about our own shared
secret is not); `deadline_status.py` owns that whole argument.
"""

from pursuit.network.deadline_families import (
    RAISE_UNRETRIED_ERRORS,
    RETRYABLE_TRANSPORT_ERRORS,
    DeadlineExpired,
)
from pursuit.network.deadline_status import retryable_status

__all__ = (
    "RAISE_UNRETRIED_ERRORS",
    "RETRYABLE_TRANSPORT_ERRORS",
    "DeadlineExpired",
    "error_evidence",
    "retryable_status",
    "unwraps_to_retryable",
)


# THE one retryability question, asked in exactly one place so the class test and the status
# test can never drift apart. `retryable_status` is a PREDICATE, not a class, so a wrapped 502
# would go unrecognised if the two were wired separately -- 05-10 joins them here rather than
# leaving a second, silently narrower copy in `error_evidence`.
def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, RETRYABLE_TRANSPORT_ERRORS) or retryable_status(exc)


def unwraps_to_retryable(exc: BaseException) -> bool:
    """True when *exc* is a WRAPPER around a retryable transport failure.

    The decision is made by the two named tuples, by `retryable_status`, and by the DIRECT
    cause only -- see this module's docstring for why "retry RuntimeError" would have been a
    catch-all in all but name. No cause, an unrelated cause, or a cause that is itself
    raise-first: False, so the caller re-raises the wrapper untouched.
    """
    cause = exc.__cause__
    if cause is None or isinstance(cause, RAISE_UNRETRIED_ERRORS):
        return False
    return _is_retryable(cause)


def error_evidence(exc: BaseException) -> str:
    """The `last_error` text a TechnicalWin carries -- the ONE definition, used by every one of
    `call_with_retry`'s retryable clauses.

    A grader reading the artifact sees the real fault ("ConnectError: All connection attempts
    failed"), never a bare accusation. A wrapped failure additionally names its cause, so the
    evidence distinguishes "the session dropped mid-call" from "we never connected at all".
    """
    text = f"{type(exc).__name__}: {exc}"
    cause = exc.__cause__
    if cause is not None and _is_retryable(cause):
        text += f" (cause: {type(cause).__name__}: {cause})"
    return text
