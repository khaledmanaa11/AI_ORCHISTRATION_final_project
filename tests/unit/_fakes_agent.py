"""Shared network-layer test doubles + the AgentContext assembly helper
(QUAL-02 applies to tests too -- one copy, imported everywhere it's needed).

Not a `test_*.py` file on purpose: pytest's default collection pattern never
imports this module as a test module, so it can hold plain helper code
without tripping "no test functions found" collection warnings.

These fakes stand in for SIBLING modules only (02-04's Watchdog, 02-06's
PeerRuntime/Client) -- they are the injection seams `AgentContext` exists to
provide, never mocks of the orchestrator/agent_lifecycle modules under test.
"""

import asyncio
import dataclasses

from mcp import McpError
from mcp.types import ErrorData

from pursuit.network import orchestrator
from pursuit.network.state_machine import State, TurnStateMachine
from pursuit.sdk import engine

_FAST_TIMEOUT = 0.05  # test scaffolding only; NOT a PARAMETERS.md value


class FakeReporter:
    """Records every illegal-transition report (NET-05), never touches disk."""

    def __init__(self):
        self.calls = []

    def __call__(self, *, current, target, severity, reason):
        self.calls.append(
            {"current": current, "target": target, "severity": severity, "reason": reason}
        )


class FakeWatchdog:
    """Stands in for 02-04's Watchdog. No real thread, no real clock."""

    def __init__(self):
        self.touches = 0
        self.started = False
        self.stopped = False

    def touch(self):
        self.touches += 1

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


class FakeClient:
    """Stands in for 02-06's fastmcp.Client -- an async context manager,
    never a socket. Records every call_tool invocation in order."""

    def __init__(self, *, fail=False):
        self.calls = []
        self.fail = fail
        self.entered = 0

    async def __aenter__(self):
        self.entered += 1
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def call_tool(self, name, args, **kwargs):
        self.calls.append((name, args))
        if self.fail:
            raise McpError(ErrorData(code=-1, message="simulated silent opponent"))
        return {"status": "ack"}


class FakeRuntime:
    """Stands in for 02-06's PeerRuntime. Owns a real asyncio.Queue -- nothing
    else here is real; no socket is ever opened."""

    def __init__(self, *, client=None):
        self.queue: asyncio.Queue = asyncio.Queue()
        self._client = client or FakeClient()
        self.stops = 0

    def client(self):
        return self._client

    async def stop(self):
        self.stops += 1


def make_ctx(
    tmp_path,
    default_params,
    network_params,
    *,
    role="police",
    label="ctx",
    initial_state=State.HANDSHAKE,
    client=None,
    net_overrides=None,
):
    """Assemble a fully-independent AgentContext from fakes plus a REAL
    TurnStateMachine (02-03) and a REAL engine.make_state (Phase 1). Nothing
    here is a module-level global (NET-02).

    `response_timeout` defaults to `_FAST_TIMEOUT`, not 0: a literal-0
    deadline cancels `asyncio.wait_for`'s wrapped task before it gets a
    single scheduling turn, which also kills a same-loop FakeClient push
    that would otherwise succeed instantly. `_FAST_TIMEOUT` lets an
    already-resolved fake resolve well within budget, while a genuinely
    empty queue still times out fast (test scaffolding only -- mirrors
    test_deadline.py's own `_TEST_DEADLINE_SECONDS` precedent, NOT a
    PARAMETERS.md value)."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter, initial=initial_state)
    watchdog = FakeWatchdog()
    runtime = FakeRuntime(client=client)
    net = dataclasses.replace(
        network_params,
        response_timeout=_FAST_TIMEOUT,
        retry_count=1,
        backoff_seconds=0,
        watchdog_threshold=0,
        watchdog_poll_seconds=0,
        **(net_overrides or {}),
    )
    return orchestrator.AgentContext(
        role=role,
        params=default_params,
        net=net,
        machine=machine,
        runtime=runtime,
        watchdog=watchdog,
        reporter=reporter,
        log_path=tmp_path / f"{label}.jsonl",
        game_uid=f"test-{label}",
        state=engine.make_state(default_params),
        choose_move=None,
    )
