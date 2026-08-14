"""NET-06, the FOURTH decision: which HTTP STATUS answers are transient.

Split out of `deadline_errors.py` at the 150-code-line gate (Segal Table 5) --
the relocate-and-re-export move this codebase makes instead of compressing.
`deadline_errors.py` decides retryability by EXCEPTION CLASS; this module
decides it, for the one class where the class alone cannot say, by the status
code the peer's server actually answered with. It also inherits that module's
`httpx.HTTPError` paragraph verbatim below, because 05-10 narrows exactly that
argument rather than overturning it.

WHY ``httpx.HTTPError`` IS STILL NOT THE RETRYABLE CLASS (05-09, unchanged).
``HTTPStatusError`` is a SIBLING under it -- its MRO goes straight to
``HTTPError``, never through ``TransportError`` -- and a 403 from 05-02's
``SharedSecretMiddleware`` is an application-level answer about OUR OWN
credentials, never a transport failure, and exactly as unretried and unaccused
as ``ToolError``. That is empirically anchored, not an MRO argument:
``tests/integration/test_secret_channel.py::test_wrong_secret_fails_every_call``
drives the real fastmcp client over a real socket and asserts
``pytest.raises(httpx.HTTPStatusError, match="403")``, so treating the whole
class as transient would demonstrably sweep the production 403 into the retry
ladder and turn our own wrong secret into an accusation against the peer.

WHAT 05-10 ADDS. `mcp/client/streamable_http.py` calls `raise_for_status()` at
four sites (re-counted against the installed mcp), so ANY non-2xx becomes
``httpx.HTTPStatusError``; and fastmcp 3.4.5's connect path PRESERVES that class
unwrapped -- re-verified against the installed source, `client/client.py:620`
reads ``if isinstance(exception, httpx.HTTPStatusError | McpError): raise
exception``. So unlike ``ConnectError`` it needs no `__cause__` handling here.
Before this module it matched no clause in `call_with_retry`, was not caught by
`agent_entrypoint`'s `except ToolError`, and propagated out of `run_agent` and
killed the process -- the rule-36 artifact 05-09 closed for connection failures,
arriving through a different door. On league day this is the likeliest real
failure of all: **ngrok answers 502 whenever the peer's local server is briefly
unavailable**, and 429 when a free-tier rate limit trips. Both are answers about
the SERVER's availability rather than about our credentials -- the same
transient class as ``ConnectError``, and exactly what a backoff exists for.

THE SET IS ENUMERATED, NEVER "5xx or 429". A `5xx` RANGE would sweep in **501
Not Implemented** and **505 HTTP Version Not Supported**: deterministic refusals
that fail identically on all four attempts, burn `3 x backoff_seconds`, and end
in a durable ``TechnicalWin(OPPONENT_UNRESPONSIVE)`` against a peer that
answered us honestly (rules 16/22). That is the mirror image of the
``LocalProtocolError``/``UnsupportedProtocol`` shape 05-09 already SUBTRACTED
for the same reason, and `deadline_errors.py`'s own docstring states the
principle: a fault that is deterministic is raised, never laddered.

The five members are STRUCTURAL protocol constants (RFC 9110 section 15.5.1,
15.6.1-15.6.5), the same category as `WatchdogExit.FREEZE` or `MessageType`'s
wire tokens -- they are not game parameters, no PARAMETERS.md row governs them,
and no team may negotiate them. 429 is the one non-5xx member and it earns its
place: it is transient BY DEFINITION and conventionally carries `Retry-After`.
Its residual -- an EXHAUSTED 429 ladder accuses the peer for a rate limit our
own request volume may have tripped -- is appended to deferred item #5, whose
ours-versus-theirs ambiguity it is identical in kind to.
"""

import httpx

# An immutable frozenset, not a set, so it is not module-level mutable state
# (NET-02) -- the same reasoning the two tuples in deadline_errors.py carry.
__all__ = ("RETRYABLE_STATUS_CODES", "retryable_status")

RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})
"""Too Many Requests, Internal Server Error, Bad Gateway, Service Unavailable,
Gateway Timeout. Enumerated one by one rather than as a range -- see this
module's docstring for why 501 and 505 are deliberately absent, and why every
4xx other than 429 must keep propagating unretried."""


def retryable_status(exc: BaseException) -> bool:
    """True only for an ``httpx.HTTPStatusError`` whose status is in the set above.

    A PREDICATE rather than a class tuple, because retryability here is decided
    by a value on the response and not by the exception's type -- which is why
    `deadline_errors.unwraps_to_retryable` has to ask this by name as well as
    asking `isinstance` about its own tuples. False for every other exception,
    including a 403 (our own wrong secret), a 404 and a 501.
    """
    return (
        isinstance(exc, httpx.HTTPStatusError)
        and exc.response.status_code in RETRYABLE_STATUS_CODES
    )
