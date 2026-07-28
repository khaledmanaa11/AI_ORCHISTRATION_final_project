"""Watchdog daemon-thread lifecycle test (D-14, NET-07).

Split out of test_watchdog.py to keep that file under the 150 code-line
limit (split, never compress) — same module under test, same fixture
constants and fakes, imported from the sibling test module rather than
duplicated.
"""

import threading

from pursuit.network.watchdog import Watchdog
from tests.unit.test_watchdog import (
    _JOIN_TIMEOUT,
    _TEST_POLL,
    _TEST_THRESHOLD,
    _FakeClock,
    _Recorder,
)


def test_thread_lifecycle_is_daemon_and_stops_cleanly():
    # A fake sleeper with zero real work can race ahead of the main thread
    # and finish before is_alive() is checked, so this test synchronizes
    # with a blocking Event (not a timed sleep) rather than fake-clock
    # advancement — the worker parks on release.wait() until the main
    # thread has observed it alive, then it proceeds to stop() cleanly.
    clock = _FakeClock()
    on_freeze = _Recorder()
    exit_action = _Recorder()
    wd = Watchdog(
        threshold_seconds=_TEST_THRESHOLD,
        poll_seconds=_TEST_POLL,
        on_freeze=on_freeze,
        exit_action=exit_action,
        clock=clock,
    )
    started = threading.Event()
    release = threading.Event()
    sleep_calls = []

    def fake_sleeper(dt):
        sleep_calls.append(dt)
        if len(sleep_calls) == 1:
            started.set()
            release.wait(timeout=_JOIN_TIMEOUT)
        else:
            wd.stop()

    wd._sleeper = fake_sleeper

    wd.start()
    assert started.wait(timeout=_JOIN_TIMEOUT)
    assert wd._thread.is_alive()
    assert wd._thread.daemon is True
    release.set()

    wd._thread.join(timeout=_JOIN_TIMEOUT)
    assert not wd._thread.is_alive()
    assert on_freeze.calls == 0
    assert exit_action.calls == 0


def test_run_returns_after_detecting_a_freeze():
    # Exercises _run()'s freeze-triggered return branch synchronously (no
    # real thread, no real sleeping) — the fake sleeper advances the fake
    # clock past the threshold on its first call.
    clock = _FakeClock()
    on_freeze = _Recorder()
    exit_action = _Recorder()
    wd = Watchdog(
        threshold_seconds=_TEST_THRESHOLD,
        poll_seconds=_TEST_POLL,
        on_freeze=on_freeze,
        exit_action=exit_action,
        clock=clock,
        sleeper=lambda _dt: clock.advance(_TEST_THRESHOLD * 2),
    )
    wd.touch()

    wd._run()

    assert on_freeze.calls == 1
    assert exit_action.calls == 1
