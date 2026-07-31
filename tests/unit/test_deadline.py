"""Tests for the NET-06 deadline tracker: wait_for_opponent + call_with_retry.

Task 1 STEP 0 exception-surface finding: the installed fastmcp 3.4.5 / mcp
packages spell the transport error class ``McpError`` (mixed case), not the
``MCPError`` spelling used in 02-RESEARCH.md's cited snippet -- verified
against ``mcp.shared.exceptions.McpError`` and the ``Raises:`` docstrings in
``fastmcp/client/mixins/tools.py``. ``from mcp import McpError`` is the
corrected import used throughout this suite. ``issubclass(ToolError,
McpError)`` is False, so Pitfall 4's two-clause except-split design holds
without dilution.

Shared fakes (FakeSleep/FakeClock/FakeSend/mcp_error) are defined once here
(QUAL-02) and imported by tests/unit/test_deadline_retry.py, which holds the
other half of the NET-06 suite -- split at the 150-code-line gate, not by
test meaning.
"""

import asyncio

import pytest
from mcp import McpError
from mcp.types import ErrorData

from pursuit.network.deadline import DeadlineExpired, call_with_retry, wait_for_opponent

_TEST_DEADLINE_SECONDS = 0.01  # test scaffolding only; NOT a PARAMETERS.md value
_FAKE_RPC_ERROR_CODE = -1  # test scaffolding only; any JSON-RPC error code works


def mcp_error(message: str) -> McpError:
    """Build a McpError the way the real MCP client raises one."""
    return McpError(ErrorData(code=_FAKE_RPC_ERROR_CODE, message=message))


class FakeSleep:
    """Records what the retry ladder asked to wait, in order."""

    def __init__(self):
        self.calls = []

    async def __call__(self, seconds):
        self.calls.append(seconds)


class FakeClock:
    """Scripted monotonic readings; deterministic elapsed time."""

    def __init__(self, readings):
        self._readings = list(readings)

    def __call__(self):
        if len(self._readings) > 1:
            return self._readings.pop(0)
        return self._readings[0]


class FakeSend:
    """The opponent, faked -- never a socket, never a server.

    `script` is a list of either exception instances (raised) or values
    (returned); exhausting it repeats the last entry, so an always-failing
    peer is one script entry.
    """

    def __init__(self, script):
        self.script = list(script)
        self._tail = self.script[-1] if self.script else None
        self.calls = 0

    async def __call__(self):
        self.calls += 1
        item = self.script.pop(0) if self.script else self._tail
        if isinstance(item, Exception):
            raise item
        return item


async def test_wait_for_opponent_returns_queued_envelope(network_params):
    """NET-06 happy path: an already-queued envelope returns instantly."""
    queue = asyncio.Queue()
    envelope = {"type": "move", "turn": 1, "sender": "police", "payload": {"x": 1, "y": 2}}
    queue.put_nowait(envelope)
    result = await wait_for_opponent(queue, timeout=network_params.response_timeout)
    assert result == envelope


async def test_wait_for_opponent_raises_deadline_expired():
    """An empty queue past the deadline raises this module's own exception."""
    queue = asyncio.Queue()
    with pytest.raises(DeadlineExpired):
        await wait_for_opponent(queue, timeout=_TEST_DEADLINE_SECONDS)
    assert DeadlineExpired is not asyncio.TimeoutError
    assert not issubclass(DeadlineExpired, asyncio.TimeoutError)


async def test_first_attempt_success_makes_no_retry_and_no_backoff(network_params):
    """A same-attempt success never retries or sleeps."""
    send = FakeSend(["ack"])
    sleeper = FakeSleep()
    outcome = await call_with_retry(
        send,
        timeout=network_params.response_timeout,
        retries=network_params.retry_count,
        backoff=network_params.backoff_seconds,
        sleep=sleeper,
        clock=FakeClock([0.0, 0.0]),
    )
    assert outcome.succeeded is True
    assert outcome.value == "ack"
    assert outcome.verdict is None
    assert outcome.attempts == 1
    assert send.calls == 1
    assert sleeper.calls == []


async def test_transient_failure_then_success_records_the_retry(network_params):
    """A transient failure recovers on the next attempt without escalating."""
    send = FakeSend([mcp_error("connection reset"), "ack"])
    sleeper = FakeSleep()
    outcome = await call_with_retry(
        send,
        timeout=network_params.response_timeout,
        retries=network_params.retry_count,
        backoff=network_params.backoff_seconds,
        sleep=sleeper,
        clock=FakeClock([0.0, 0.0]),
    )
    assert outcome.succeeded is True
    assert outcome.value == "ack"
    assert outcome.verdict is None
    assert outcome.attempts == 2
    assert send.calls == 2
    assert sleeper.calls == [network_params.backoff_seconds]
