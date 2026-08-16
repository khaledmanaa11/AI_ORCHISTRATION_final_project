"""An INJECTED-clock harness for the REAL `Watchdog` (05-13, 05-UAT.md G6).

Not a `test_*.py` file on purpose -- pytest never collects it as a test
module (the `_fakes_agent.py` precedent).

WHY IT EXISTS, stated as a measurement of what was missing. No suite could
express the window that hid G6: `_fakes_agent.make_ctx` installs a
`FakeWatchdog` that counts touches and checks nothing, and forces
`watchdog_threshold=0`; `tests/integration/late_peer_harness.py` says in
its own module docstring that the watchdog is DELIBERATELY not started,
because a real one's default exit action is `os._exit(1)` and would kill
the pytest process. So a REAL freeze threshold had never once been armed
across a REAL retry ladder, and the audit path's total absence of
`touch()` calls was invisible to every green test.

WHAT THIS GIVES INSTEAD. The real `Watchdog` class -- its real
`check_once` arithmetic -- with its clock, its `on_freeze` and its
`exit_action` all injected, driven by a clock the test advances by hand.
Zero real sleeps, zero 60-second tests, and `os._exit` is never reachable.
The daemon thread is never started either: `check_once()` is driven
directly, so a freeze verdict is a deterministic function of the clock the
test set (the shape `test_agent_teardown.py`'s own non-vacuity control
already uses).
"""

from __future__ import annotations

import asyncio

from pursuit.network.deadline import DeadlineExpired
from pursuit.network.watchdog import Watchdog
from tests.unit._fakes_agent import FakeClient


class ManualClock:
    """A monotonic clock that moves only when a test moves it."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> float:
        self.now += seconds
        return self.now


class ArmedWatchdog:
    """A live `Watchdog` wearing the `ctx.watchdog` surface.

    Passed to `make_ctx(watchdog=...)`, so production code touches the REAL
    watchdog while the test keeps the clock, the incident log and a touch
    count. `start()`/`stop()` delegate but no test needs them: starting the
    daemon thread would reintroduce a real `time.sleep` poll loop.
    """

    def __init__(self, *, threshold_seconds: float, poll_seconds: float) -> None:
        self.clock = ManualClock()
        self.fired: list[str] = []
        self.checks: list[bool] = []
        self.touches = 0
        self.watchdog = Watchdog(
            threshold_seconds=threshold_seconds, poll_seconds=poll_seconds,
            on_freeze=lambda: self.fired.append("freeze"),
            exit_action=lambda: self.fired.append("exit"),
            clock=self.clock,
        )

    def touch(self) -> None:
        self.touches += 1
        self.watchdog.touch()

    def start(self) -> None:
        self.watchdog.start()

    def stop(self) -> None:
        self.watchdog.stop()

    def check(self) -> bool:
        """One poll, recorded. True iff this poll called the freeze action."""
        detected = self.watchdog.check_once()
        self.checks.append(detected)
        return detected


class StalledClient(FakeClient):
    """A peer whose socket accepts TCP and never answers -- a stalled tunnel
    edge, the drop 05-11 exists for and the failure class G6 is about.

    Each `call_tool` is ONE bounded attempt that burned its whole
    `response_timeout` and then its `backoff_seconds`, charged to the
    INJECTED clock only: the real event loop never sleeps, and
    `DeadlineExpired` is the exact class `deadline_wait.bounded` raises when
    an attempt hits its deadline (and a member of
    `RETRYABLE_TRANSPORT_ERRORS`, so the ladder retries it as it would in
    production). The freeze poll runs INSIDE the attempt, after the clock
    moves -- the moment the real daemon thread would have run it.
    """

    def __init__(self, armed: ArmedWatchdog, *, step: float) -> None:
        super().__init__()
        self._armed = armed
        self._step = step

    async def call_tool(self, name, args, **kwargs):
        self.calls.append((name, args))
        self._armed.clock.advance(self._step)
        self._armed.check()
        raise DeadlineExpired("stalled tunnel edge: no answer within the deadline")


class StalledQueue(asyncio.Queue):
    """The RECEIVE-leg mirror of `StalledClient`: our own inbound queue stays
    empty for the whole ladder, each pull costing a full attempt on the
    injected clock. Assigned onto `ctx.runtime.queue` after `make_ctx`."""

    def __init__(self, armed: ArmedWatchdog, *, step: float) -> None:
        super().__init__()
        self._armed = armed
        self._step = step
        self.pulls = 0

    async def get(self) -> object:
        self.pulls += 1
        self._armed.clock.advance(self._step)
        self._armed.check()
        raise DeadlineExpired("no FINAL_REVEAL within the deadline")
