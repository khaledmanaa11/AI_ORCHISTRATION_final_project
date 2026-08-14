"""NET-06: the WRAPPED shape of a transport failure (05-09, deviation 3).

Family 3 reaches `call_with_retry` two different ways, and 05-09 measured both. On an
ALREADY-OPEN session the raw `httpx` exception arrives and the widened tuple matches it. On the
CONNECT path -- `async with ctx.runtime.client()`, which is how EVERY outgoing envelope in this
codebase starts -- fastmcp 3.4.5 catches the fault at `client/client.py:616-624` and re-raises
`RuntimeError(f"Client failed to connect: {exc}") from exc`, preserving only
`httpx.HTTPStatusError` and `McpError` unwrapped.

That makes the connect shape the COMMON one, and a widened tuple ALONE still let it escape: the
`late_peer_round(linger=False)` harness was re-measured after the tuple landed and the late peer
STILL ended on `game_over` with nothing after it -- the 2026-08-13 artifact, unfixed. These cases
pin the predicate that closes it, and the two controls pin that it did NOT become "retry
RuntimeError". The real-socket anchor for the wrapper's existence is
tests/integration/test_connect_failure_containment.py.

Split from `test_deadline_httpx.py` (109 code lines) at the 150-code-line gate; the shared fakes
still live in `test_deadline.py` and are imported, never duplicated (QUAL-02).
"""

import httpx
import pytest

from pursuit.network.deadline import TechnicalWinReason, call_with_retry
from pursuit.network.deadline_errors import unwraps_to_retryable
from tests.unit.test_deadline import FakeClock, FakeSend, FakeSleep

_FASTMCP_WRAPPER_TEXT = "Client failed to connect: All connection attempts failed"


def _wrapped(cause: BaseException) -> RuntimeError:
    """Rebuild fastmcp's own wrapper: `raise RuntimeError(...) from exc`."""
    wrapper = RuntimeError(f"Client failed to connect: {cause}")
    wrapper.__cause__ = cause
    return wrapper


async def _ladder(send, network_params, sleeper):
    return await call_with_retry(
        send,
        timeout=network_params.response_timeout,
        retries=network_params.retry_count,
        backoff=network_params.backoff_seconds,
        sleep=sleeper,
        clock=FakeClock([0.0, 9.0]),
    )


async def test_a_wrapped_connect_failure_is_retried_and_becomes_a_verdict(network_params):
    """THE DEVIATION FIX. The shape production actually produces is contained, and its evidence
    names BOTH the wrapper and the real cause -- so the artifact a grader reads distinguishes
    "the session dropped mid-call" from "we never connected at all"."""
    send = FakeSend([_wrapped(httpx.ConnectError("All connection attempts failed"))])
    sleeper = FakeSleep()

    outcome = await _ladder(send, network_params, sleeper)

    assert outcome.succeeded is False
    assert outcome.attempts == network_params.retry_count + 1
    assert sleeper.calls == [network_params.backoff_seconds] * network_params.retry_count
    assert outcome.verdict.reason is TechnicalWinReason.OPPONENT_UNRESPONSIVE
    assert outcome.verdict.last_error == (
        f"RuntimeError: {_FASTMCP_WRAPPER_TEXT} (cause: ConnectError: All connection attempts failed)"
    )


async def test_a_runtime_error_that_is_not_a_wrapped_transport_failure_is_raised(network_params):
    """CONTROL, and the whole reason this is a predicate rather than `except RuntimeError`.
    `RuntimeError` is one of the broadest classes in the language and OUR OWN bugs raise it; a
    bare one has no cause at all and must never be mistaken for a transient peer failure and
    silently retried three times before being reported as the peer's fault."""
    send = FakeSend([RuntimeError("Event loop is closed")])
    sleeper = FakeSleep()

    with pytest.raises(RuntimeError, match="Event loop is closed"):
        await _ladder(send, network_params, sleeper)

    assert send.calls == 1
    assert sleeper.calls == []
    assert unwraps_to_retryable(RuntimeError("no cause")) is False
    assert unwraps_to_retryable(_wrapped(ValueError("unrelated"))) is False


async def test_a_wrapped_scheme_less_url_still_fails_loudly(network_params):
    """CONTROL. The subtraction survives the wrapper: `UnsupportedProtocol` is a fault of OUR
    own and deterministic, so wrapping it must not smuggle it back into the ladder and turn a
    mistyped `PURSUIT_OPPONENT_URL` into ~135 s of futile retries and a false accusation."""
    cause = httpx.UnsupportedProtocol("Request URL is missing an 'http://' or 'https://' protocol.")
    send = FakeSend([_wrapped(cause)])
    sleeper = FakeSleep()

    with pytest.raises(RuntimeError):
        await _ladder(send, network_params, sleeper)

    assert send.calls == 1
    assert sleeper.calls == []
    assert unwraps_to_retryable(_wrapped(cause)) is False
