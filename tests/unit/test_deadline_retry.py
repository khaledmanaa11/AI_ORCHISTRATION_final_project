"""NET-06 retry-ladder tests: technical win, ToolError, hung opponent, evidence.

The other half of the NET-06 suite -- split from tests/unit/test_deadline.py
at the 150-code-line gate (QUAL-02: the shared fakes live there and are
imported here, not duplicated). See test_deadline.py's module docstring for
the Task 1 STEP 0 exception-surface finding (``McpError``, not ``MCPError``).
"""

import asyncio
import json

import pytest
from fastmcp.exceptions import ToolError

from pursuit.network.deadline import (
    RETRYABLE_TRANSPORT_ERRORS,
    TechnicalWinReason,
    call_with_retry,
)
from tests.unit.test_deadline import (
    _TEST_DEADLINE_SECONDS,
    FakeClock,
    FakeSend,
    FakeSleep,
    mcp_error,
)


async def test_exhausted_retries_declare_technical_win_with_evidence(network_params):
    """Every attempt failing declares a technical win with measured evidence."""
    send = FakeSend([mcp_error("opponent unreachable")])
    sleeper = FakeSleep()
    clock = FakeClock([0.0, 12.5])
    outcome = await call_with_retry(
        send,
        timeout=network_params.response_timeout,
        retries=network_params.retry_count,
        backoff=network_params.backoff_seconds,
        sleep=sleeper,
        clock=clock,
    )
    assert outcome.succeeded is False
    assert outcome.value is None
    assert outcome.attempts == network_params.retry_count + 1
    assert send.calls == outcome.attempts
    assert sleeper.calls == [network_params.backoff_seconds] * network_params.retry_count
    verdict = outcome.verdict
    assert verdict is not None
    assert verdict.reason is TechnicalWinReason.OPPONENT_UNRESPONSIVE
    assert verdict.attempts == outcome.attempts
    assert verdict.timeout_seconds == network_params.response_timeout
    assert verdict.backoff_seconds == network_params.backoff_seconds
    assert verdict.elapsed_seconds == 12.5
    assert "McpError" in verdict.last_error
    assert "opponent unreachable" in verdict.last_error


async def test_tool_error_is_not_a_technical_win(network_params):
    """A ToolError is an application rejection, never a technical win (Pitfall 4)."""
    send = FakeSend([ToolError("illegal move")])
    sleeper = FakeSleep()
    with pytest.raises(ToolError):
        await call_with_retry(
            send,
            timeout=network_params.response_timeout,
            retries=network_params.retry_count,
            backoff=network_params.backoff_seconds,
            sleep=sleeper,
            clock=FakeClock([0.0, 0.0]),
        )
    assert send.calls == 1
    assert sleeper.calls == []
    assert ToolError not in RETRYABLE_TRANSPORT_ERRORS
    assert not issubclass(ToolError, tuple(RETRYABLE_TRANSPORT_ERRORS))


async def test_hung_opponent_becomes_deadline_expired_then_technical_win(network_params):
    """The per-attempt deadline is enforced by the retry ladder, not just recorded."""

    async def hanging_send():
        await asyncio.Event().wait()

    outcome = await call_with_retry(
        hanging_send,
        timeout=_TEST_DEADLINE_SECONDS,
        retries=network_params.retry_count,
        backoff=network_params.backoff_seconds,
        sleep=FakeSleep(),
        clock=FakeClock([0.0, 1.0]),
    )
    assert outcome.succeeded is False
    assert outcome.verdict.reason is TechnicalWinReason.OPPONENT_UNRESPONSIVE
    assert "DeadlineExpired" in outcome.verdict.last_error


async def test_technical_win_evidence_is_json_serializable(network_params):
    """TechnicalWin.as_evidence() is a plain, json.dumps-serializable dict."""
    send = FakeSend([mcp_error("opponent unreachable")])
    outcome = await call_with_retry(
        send,
        timeout=network_params.response_timeout,
        retries=network_params.retry_count,
        backoff=network_params.backoff_seconds,
        sleep=FakeSleep(),
        clock=FakeClock([0.0, 12.5]),
    )
    evidence = outcome.verdict.as_evidence()
    assert isinstance(evidence, dict)
    json.dumps(evidence)
    assert evidence["reason"] == TechnicalWinReason.OPPONENT_UNRESPONSIVE.value
    for key in (
        "reason",
        "attempts",
        "timeout_seconds",
        "backoff_seconds",
        "elapsed_seconds",
        "last_error",
    ):
        assert key in evidence
