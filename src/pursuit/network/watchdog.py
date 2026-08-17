"""Freeze-detecting daemon thread — the other half of D-14 (NET-07).

A background daemon thread polls a last-activity timestamp against a
config-driven threshold. On freeze it writes a final incident record and
THEN exits — never the reverse, because RESEARCH Pitfall 6 is explicit
that a buffered-but-unflushed incident record never reaches disk once
os._exit() runs.

Two hard design rules follow directly from that pitfall:
1. The incident write is the caller's injected `on_freeze` callable
   (typically a real, flushed-and-fsynced append_event call), invoked and
   allowed to complete BEFORE `exit_action` runs — never in a finally
   block, an atexit hook, or anything depending on interpreter shutdown.
2. `exit_action` is itself injected, so the test suite can assert that
   ordering without ever calling os._exit() and killing the pytest
   process.

No POSIX interrupt-based timer facility is used anywhere here — Windows
does not support that mechanism reliably, and the daemon-thread +
timestamp-polling design sidesteps the whole problem by construction.

Import rules: stdlib only. This module never imports the sibling event
log module — the incident write arrives as the injected `on_freeze`
callable, and wiring the two together is 02-09's job.
"""

from __future__ import annotations

import contextlib
import os
import threading
import time
from collections.abc import Callable
from enum import IntEnum


class WatchdogExit(IntEnum):
    """Process exit code used by the default hard-exit action.

    A conventional non-zero POSIX/Windows failure code, expressed as an
    Enum per CLAUDE.md's hardcoded-value rule — NOT a game parameter and
    never traced to PARAMETERS.md.
    """

    FREEZE = 1


def _default_exit() -> None:
    """Terminate the process immediately.

    Deliberately os._exit() rather than the standard library's
    thread-scoped process-termination call, which only raises SystemExit
    in the calling thread and does not terminate a process whose main
    thread is frozen in the asyncio loop — exactly the scenario this
    watchdog exists to escape.
    """
    os._exit(WatchdogExit.FREEZE)


class Watchdog:
    """Background daemon thread watching a last-activity timestamp.

    threshold_seconds and poll_seconds are keyword-only and REQUIRED —
    no default in source — so the config-driven values (60 s threshold
    from PARAMETERS.md Table 19 row 7; 1 s poll from D-18, an engineering
    default) must arrive from NetworkParams via 02-09 and can never be
    silently hardcoded here.
    """

    def __init__(
        self,
        *,
        threshold_seconds: float,
        poll_seconds: float,
        on_freeze: Callable[[], None],
        exit_action: Callable[[], None] = _default_exit,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._threshold_seconds = threshold_seconds
        self._poll_seconds = poll_seconds
        self._on_freeze = on_freeze
        self._exit_action = exit_action
        self._clock = clock
        self._sleeper = sleeper
        self._last_activity = self._clock()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="pursuit-watchdog"
        )

    def touch(self) -> None:
        """Record activity now. 02-09 calls this every turn."""
        self._last_activity = self._clock()

    @property
    def idle_seconds(self) -> float:
        """Seconds since the last `touch()` -- READ-ONLY, and the exact
        quantity `check_once` compares against the threshold.

        Added by 07-06 for the live view's freeze timer. 07-03 recorded that
        `LocalView.idle_seconds` had to be supplied by the caller "because
        `Watchdog` exposes no public idle reading and this plan does not edit
        `network/`"; this is that reading. It takes no lock and mutates
        nothing, so it cannot perturb the poll loop -- a float read against a
        float write is atomic under the GIL, and a value one poll stale is
        exactly what a display wants anyway.
        """
        return self._clock() - self._last_activity

    def start(self) -> None:
        """Start the background poll loop."""
        self._thread.start()

    def stop(self) -> None:
        """Signal the poll loop to exit at its next wake-up (clean
        GAME_OVER shutdown, not a freeze)."""
        self._stop.set()

    def check_once(self) -> bool:
        """Run one poll. Returns True iff a freeze was detected and
        handled — on_freeze then exit_action, in that literal order."""
        if self._clock() - self._last_activity <= self._threshold_seconds:
            return False
        # A failed incident write must not become a permanent hang.
        with contextlib.suppress(Exception):
            self._on_freeze()
        self._exit_action()
        return True

    def _run(self) -> None:
        while not self._stop.is_set():
            self._sleeper(self._poll_seconds)
            if self._stop.is_set():
                return
            if self.check_once():
                return
