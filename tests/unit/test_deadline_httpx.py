"""NET-06, the httpx third of the exception taxonomy (05-09).

The third file of the NET-06 suite -- split from `test_deadline.py` (104 code lines) and
`test_deadline_retry.py` (105) at the 150-code-line gate, not by test meaning; the shared fakes
still live in `test_deadline.py` and are imported, never duplicated (QUAL-02).

What it pins. `httpx.ConnectError` used to match neither `except` clause in `call_with_retry`,
so it escaped the ladder, propagated out of `run_agent` and killed the process -- making US the
side that published no nonces (rule 36) with no verdict at all in our own log. Measured 4/4 runs
by 05-04 (deferred-items.md #1); it is the 2026-08-13 artifact. It is now a retryable transport
failure. The three controls pin the two SUBTRACTIONS that keep the widening honest: a 403
`HTTPStatusError` is an answer about our own credentials, and the two local-fault classes are
our own deterministic mistakes -- none of the three may become an accusation against the peer.
"""

import httpx
import pytest

from pursuit.network.deadline import (
    RAISE_UNRETRIED_ERRORS,
    RETRYABLE_TRANSPORT_ERRORS,
    TechnicalWinReason,
    call_with_retry,
)
from tests.unit.test_deadline import FakeClock, FakeSend, FakeSleep

_CONNECT_ERROR_TEXT = "All connection attempts failed"


def _forbidden() -> httpx.HTTPStatusError:
    """The 403 shape `SharedSecretMiddleware` really produces -- the same class
    tests/integration/test_secret_channel.py::test_wrong_secret_fails_every_call catches off a
    real socket through the real fastmcp client."""
    request = httpx.Request("POST", "http://127.0.0.1:9/mcp")
    return httpx.HTTPStatusError(
        "Client error '403 Forbidden'", request=request, response=httpx.Response(403, request=request),
    )


async def _ladder(send, network_params, sleeper, *, clock=(0.0, 12.5)):
    return await call_with_retry(
        send,
        timeout=network_params.response_timeout,
        retries=network_params.retry_count,
        backoff=network_params.backoff_seconds,
        sleep=sleeper,
        clock=FakeClock(list(clock)),
    )


async def test_a_dropped_connection_is_retried_and_becomes_a_measured_technical_win(
    network_params,
):
    """THE FIX. A peer unreachable for the WHOLE ladder genuinely is unresponsive, so the
    accusation is correct here -- and it is a returned verdict, never an escaping exception."""
    send = FakeSend([httpx.ConnectError(_CONNECT_ERROR_TEXT)])
    sleeper = FakeSleep()

    outcome = await _ladder(send, network_params, sleeper)

    assert outcome.succeeded is False
    assert outcome.attempts == network_params.retry_count + 1
    assert send.calls == outcome.attempts
    assert sleeper.calls == [network_params.backoff_seconds] * network_params.retry_count
    assert outcome.verdict.reason is TechnicalWinReason.OPPONENT_UNRESPONSIVE
    assert outcome.verdict.elapsed_seconds == 12.5
    # The evidence a grader reads names the real fault, not a bare accusation.
    assert outcome.verdict.last_error == f"ConnectError: {_CONNECT_ERROR_TEXT}"
    assert httpx.ConnectError in RETRYABLE_TRANSPORT_ERRORS or issubclass(
        httpx.ConnectError, tuple(RETRYABLE_TRANSPORT_ERRORS)
    )


async def test_a_transient_drop_recovers_on_the_next_attempt(network_params):
    """The point of retrying at all: a mid-game drop over a real tunnel costs one backoff, not
    the game. `call_with_retry` carries every outgoing envelope -- moves, commit/ack/reveal,
    hints, the inbound pull and the final-reveal push."""
    send = FakeSend([httpx.ReadError("connection reset by peer"), "ack"])
    sleeper = FakeSleep()

    outcome = await _ladder(send, network_params, sleeper, clock=(0.0, 0.0))

    assert outcome.succeeded is True
    assert outcome.value == "ack"
    assert outcome.verdict is None
    assert outcome.attempts == 2
    assert sleeper.calls == [network_params.backoff_seconds]


async def test_a_403_is_not_swept_into_the_retry_ladder(network_params):
    """CONTROL, and the reason the retryable class is `TransportError` and NOT `HTTPError`.

    A 403 from 05-02's `SharedSecretMiddleware` is an application-level answer about OUR OWN
    shared secret -- never a transport failure, and never grounds to accuse the peer. Its
    discrimination is against the DESIGN ALTERNATIVE, not against old code: written with
    `httpx.HTTPError` in place of `httpx.TransportError` this test FAILS, because
    `HTTPStatusError` is a sibling under `HTTPError`."""
    send = FakeSend([_forbidden()])
    sleeper = FakeSleep()

    with pytest.raises(httpx.HTTPStatusError, match="403"):
        await _ladder(send, network_params, sleeper)

    assert send.calls == 1, "our own wrong secret burned the peer's retry budget"
    assert sleeper.calls == []
    assert not issubclass(httpx.HTTPStatusError, tuple(RETRYABLE_TRANSPORT_ERRORS))


@pytest.mark.parametrize(
    ("exc", "why"),
    [
        (httpx.LocalProtocolError("malformed request"), "we sent a malformed request"),
        (
            httpx.UnsupportedProtocol(
                "Request URL is missing an 'http://' or 'https://' protocol."
            ),
            "a scheme-less PURSUIT_OPPONENT_URL, pasted by hand on league day",
        ),
    ],
)
async def test_our_own_deterministic_fault_is_raised_not_retried(exc, why, network_params):
    """CONTROL. Both classes ARE `httpx.TransportError` subclasses, so the widened tuple alone
    would retry them: four identical failures, 3 x backoff_seconds burned, and a DURABLE
    TechnicalWin(OPPONENT_UNRESPONSIVE) against a peer that never received a valid request --
    a false declaration (rules 16/22). Written against the tuple-only version of 05-09, this
    test FAILS. Failing loudly at the handshake instead is the house style for bad config."""
    assert issubclass(type(exc), httpx.TransportError), why
    send = FakeSend([exc])
    sleeper = FakeSleep()

    with pytest.raises(type(exc)):
        await _ladder(send, network_params, sleeper)

    assert send.calls == 1
    assert sleeper.calls == []
    assert type(exc) in RAISE_UNRETRIED_ERRORS
