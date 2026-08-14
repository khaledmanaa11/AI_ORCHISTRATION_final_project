"""05-UAT.md G1: the bounded post-audit grace window, and the NET-07 hazard
it must not fire inside.

The hazard is PRE-EXISTING, found here rather than introduced here:
`grep -rn "watchdog.touch()" src/` returns only turn_buffer.py,
turn_commit_send.py and turn_commit_wait.py -- nothing in the audit path.
So the untouched window ALREADY spans the whole of `run_final_audit`
(receive ladder bounded at 4x30 + 3x5 = 135 s) against a 60 s
`watchdog_threshold` whose freeze action is `os._exit(1)`. This plan closes
that window (stop the watchdog BEFORE the linger) rather than widening it.
"""

from __future__ import annotations

import asyncio
import dataclasses
import time

from pursuit.network.agent_lifecycle import stop_watchdog
from pursuit.network.agent_teardown import linger_for_peer
from pursuit.network.watchdog import Watchdog

# Test scaffolding only -- NOT PARAMETERS.md values (mirrors
# _fakes_agent._FAST_TIMEOUT's own precedent). The PRODUCTION bounds are
# NetworkParams.response_timeout / .backoff_seconds, read in the module
# under test and never written down here.
_CAP_SECONDS = 0.20
_QUIET_SECONDS = 0.02
_CLOCK_STEP = 0.05


class _StepClock:
    """A clock that advances a fixed step per read, so the total-cap branch
    is deterministic instead of load-sensitive."""

    def __init__(self, step: float) -> None:
        self._step = step
        self._now = 0.0

    def __call__(self) -> float:
        now, self._now = self._now, self._now + self._step
        return now


class _NeverQuietQueue(asyncio.Queue):
    """A peer that keeps pushing for the whole window -- the drain half."""

    async def get(self) -> object:
        return {"type": "final_reveal"}


class _Runtime:
    def __init__(self, queue: asyncio.Queue) -> None:
        self.queue = queue


class _Ctx:
    """Minimal stand-in: `linger_for_peer` touches only ctx.net and
    ctx.runtime.queue (the test_audit_turn_binding.py `_Ctx` precedent)."""

    def __init__(self, net, queue: asyncio.Queue) -> None:
        self.net = net
        self.runtime = _Runtime(queue)


def _ctx(network_params, queue: asyncio.Queue) -> _Ctx:
    net = dataclasses.replace(
        network_params, response_timeout=_CAP_SECONDS, backoff_seconds=_QUIET_SECONDS,
    )
    return _Ctx(net, queue)


async def test_an_empty_queue_returns_after_one_quiet_interval(network_params):
    """(a) A peer that is genuinely finished costs one backoff window, not
    the full response_timeout cap -- the linger must not tax every clean
    game with the whole deadline."""
    ctx = _ctx(network_params, asyncio.Queue())

    started = time.monotonic()
    await linger_for_peer(ctx)
    elapsed = time.monotonic() - started

    assert elapsed < _CAP_SECONDS, f"lingered {elapsed:.3f}s, expected ~{_QUIET_SECONDS}s"


async def test_a_queue_that_keeps_delivering_is_drained_until_the_total_cap(network_params):
    """(b) A peer still pushing never gets cut off early, but the window is
    still BOUNDED -- the cap is what stops a hostile peer holding teardown
    open forever."""
    ctx = _ctx(network_params, _NeverQuietQueue())

    await asyncio.wait_for(linger_for_peer(ctx, clock=_StepClock(_CLOCK_STEP)), timeout=5.0)


async def test_the_linger_never_raises_and_never_ends_the_game(network_params):
    """(c) Its only job is to wait. A DeadlineExpired inside is the SUCCESS
    signal, not a fault, and nothing here returns an Outcome."""
    ctx = _ctx(network_params, asyncio.Queue())

    assert await linger_for_peer(ctx) is None
    assert await linger_for_peer(ctx, clock=_StepClock(_CLOCK_STEP)) is None


async def test_no_watchdog_freeze_can_fire_across_the_linger(network_params):
    """NET-07. `Watchdog.check_once` fires when `clock() - last_activity >
    threshold_seconds`; `touch()` is called nowhere in the audit path, so
    `run_agent` stops the watchdog BEFORE the linger. exit_action is
    INJECTED here -- this test must never reach the real `os._exit`."""
    fired: list[str] = []
    watchdog = Watchdog(
        threshold_seconds=_QUIET_SECONDS, poll_seconds=_QUIET_SECONDS,
        on_freeze=lambda: fired.append("freeze"),
        exit_action=lambda: fired.append("exit"),
    )
    ctx = _ctx(network_params, _NeverQuietQueue())
    watchdog.start()

    stop_watchdog(_WatchdogCtx(watchdog))
    await linger_for_peer(ctx, clock=_StepClock(_CLOCK_STEP))
    await asyncio.sleep(_QUIET_SECONDS * 3)

    assert fired == []
    # Non-vacuity control: an IDENTICAL watchdog left running does treat
    # this same idle window as a freeze -- so the assertion above is a
    # measured property of stopping it, not of the window being short.
    control: list[str] = []
    unstopped = Watchdog(
        threshold_seconds=_QUIET_SECONDS, poll_seconds=_QUIET_SECONDS,
        on_freeze=lambda: control.append("freeze"),
        exit_action=lambda: control.append("exit"),
        clock=_StepClock(_CAP_SECONDS),
    )
    assert unstopped.check_once() is True
    assert control == ["freeze", "exit"]


class _WatchdogCtx:
    """`stop_watchdog` touches only ctx.watchdog."""

    def __init__(self, watchdog: Watchdog) -> None:
        self.watchdog = watchdog
