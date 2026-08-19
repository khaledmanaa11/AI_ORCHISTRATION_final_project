"""Family 4: a broken client session is retried on a fresh attempt (2026-08-19).

The remote-round crash artifact (docs/devlog/2026-08-19-remote-rehearsal-
replay-board-final-rejections.md, Side-notes): the peer's tunnel endpoint
died mid-call, fastmcp's background post_writer broke the session, and the
pending send raised ``anyio.BrokenResourceError`` -- ``raise ... from None``
at ``anyio/streams/memory.py``, so it carries NO ``__cause__`` and the
``unwraps_to_retryable`` predicate can never see it: it must be matched by
CLASS. It matched no clause, escaped ``call_with_retry`` entirely, and
killed the agent mid-game instead of feeding the OPPONENT_UNRESPONSIVE
ladder.

Retrying is CORRECT for this family because every production attempt opens
a fresh ``async with ctx.runtime.client()`` (turn_commit_send) -- the broken
session is disposed with the attempt that owned it, so the retry is the
session rebuild. The silent-peer control below is the pattern the
envelope-boundary defect class demands: a peer that STAYS broken must end
in the measured deadline verdict, never a traceback.
"""

import anyio
import pytest
from fastmcp.exceptions import ToolError

from pursuit.network.deadline import TechnicalWinReason, call_with_retry
from pursuit.network.deadline_errors import RETRYABLE_TRANSPORT_ERRORS
from tests.unit.test_deadline import FakeClock, FakeSend, FakeSleep

_TIMEOUT = 0.01  # test scaffolding only; NOT a PARAMETERS.md value
_BACKOFF = 5.0
_RETRIES = 3


async def _run(send, sleep):
    return await call_with_retry(
        send, timeout=_TIMEOUT, retries=_RETRIES, backoff=_BACKOFF,
        sleep=sleep, clock=FakeClock([0.0, 1.0]),
    )


async def test_a_broken_session_is_retried_and_a_fresh_attempt_recovers():
    """One mid-call session break, then a healthy fresh session: recovered."""
    send = FakeSend([anyio.BrokenResourceError(), "answer"])
    sleep = FakeSleep()
    outcome = await _run(send, sleep)
    assert outcome.succeeded
    assert outcome.value == "answer"
    assert outcome.attempts == 2
    assert sleep.calls == [_BACKOFF]


async def test_a_closed_stream_is_the_same_family():
    """``ClosedResourceError`` is the sibling shape (our side of the stream
    torn down); same session-death fact, same retry answer."""
    send = FakeSend([anyio.ClosedResourceError(), "answer"])
    outcome = await _run(send, FakeSleep())
    assert outcome.succeeded
    assert outcome.attempts == 2


async def test_a_peer_whose_session_stays_broken_yields_the_deadline_verdict():
    """THE SILENT-PEER CONTROL: a session that breaks on every attempt burns
    the whole measured budget and ends in OPPONENT_UNRESPONSIVE with the real
    exception named -- never a raise."""
    send = FakeSend([anyio.BrokenResourceError("stream is broken")])
    sleep = FakeSleep()
    outcome = await _run(send, sleep)
    assert not outcome.succeeded
    assert outcome.verdict is not None
    assert outcome.verdict.reason is TechnicalWinReason.OPPONENT_UNRESPONSIVE
    assert outcome.attempts == _RETRIES + 1
    assert send.calls == _RETRIES + 1
    assert "BrokenResourceError" in outcome.verdict.last_error
    assert sleep.calls == [_BACKOFF] * _RETRIES


async def test_the_raise_first_contract_is_untouched_by_the_widening():
    """The control for the control: ``ToolError`` still propagates unretried
    and burns no backoff -- widening the retryable family must not have
    disturbed the clause order rules 16/22 depend on."""
    send = FakeSend([ToolError("the peer's tool body rejected the call")])
    sleep = FakeSleep()
    with pytest.raises(ToolError):
        await _run(send, sleep)
    assert send.calls == 1
    assert sleep.calls == []


def test_the_tuple_names_the_two_anyio_members():
    """Greppable pin: the family-4 members sit in the ONE owned tuple, so the
    class test and this suite can never drift apart."""
    assert anyio.BrokenResourceError in RETRYABLE_TRANSPORT_ERRORS
    assert anyio.ClosedResourceError in RETRYABLE_TRANSPORT_ERRORS
