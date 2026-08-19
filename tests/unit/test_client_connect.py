"""Bounded handshake connect (2026-08-19 crash, the startup shape).

Machine A died at ``_play``'s bare ``async with ctx.runtime.client()``:
fastmcp wraps the connect fault as ``RuntimeError("Client failed to
connect: ...") from httpx.ConnectError`` and no ladder stood around the
enter, so a peer that was merely LATE killed the process before any game
existed. ``enter_client_with_retry`` gives the enter the same D-13 budget
as every other outgoing call; on exhaustion the caller ends cleanly with no
game -- no agreement means no verdict, and a TechnicalWin against a peer
with whom no game was ever negotiated would be a false declaration.
"""

from contextlib import AsyncExitStack

import httpx

from pursuit.network.client_connect import enter_client_with_retry
from pursuit.network.deadline import TechnicalWinReason


class FakeNet:
    """Only the three ladder fields, mirroring NetworkParams' names."""

    response_timeout = 0.01
    retry_count = 3
    backoff_seconds = 0.0


def _wrapped_connect_fault() -> RuntimeError:
    """The measured shape: RuntimeError raised FROM httpx.ConnectError."""
    fault = RuntimeError("Client failed to connect: All connection attempts failed")
    fault.__cause__ = httpx.ConnectError("All connection attempts failed")
    return fault


class FakeClient:
    """An async-context client whose enter follows a script."""

    def __init__(self, entry):
        self.entry = entry
        self.exited = False

    async def __aenter__(self):
        if isinstance(self.entry, Exception):
            raise self.entry
        return self

    async def __aexit__(self, *exc_info):
        self.exited = True
        return False


class FakeClientFactory:
    """`runtime.client` faked: a FRESH client object per call, scripted."""

    def __init__(self, script):
        self.script = list(script)
        self.built: list[FakeClient] = []

    def __call__(self) -> FakeClient:
        entry = self.script.pop(0) if self.script else self.script
        client = FakeClient(entry)
        self.built.append(client)
        return client


async def test_a_late_peer_is_retried_and_the_second_fresh_client_connects():
    factory = FakeClientFactory([_wrapped_connect_fault(), None])
    async with AsyncExitStack() as stack:
        outcome = await enter_client_with_retry(stack, factory, FakeNet())
        assert outcome.succeeded
        assert outcome.value is factory.built[1]
        assert len(factory.built) == 2
    assert factory.built[1].exited  # the stack owns the lifetime


async def test_a_peer_that_never_comes_up_exhausts_into_the_deadline_verdict():
    """Silent-peer control: every enter fails; the outcome carries the
    measured verdict and NOTHING was left half-entered on the stack."""
    factory = FakeClientFactory([_wrapped_connect_fault()])

    def always_broken():
        client = FakeClient(_wrapped_connect_fault())
        factory.built.append(client)
        return client

    async with AsyncExitStack() as stack:
        outcome = await enter_client_with_retry(stack, always_broken, FakeNet())
    assert not outcome.succeeded
    assert outcome.verdict.reason is TechnicalWinReason.OPPONENT_UNRESPONSIVE
    assert len(factory.built) == FakeNet.retry_count + 1
    assert "ConnectError" in outcome.verdict.last_error
    assert not any(client.exited for client in factory.built)
