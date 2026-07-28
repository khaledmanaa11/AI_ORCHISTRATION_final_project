"""Tests for the watchdog daemon thread (D-14, D-18, NET-07).

Every test injects a fake clock and a fake sleeper — nothing here calls
time.sleep and nothing calls os._exit. The threshold/poll values below are
test fixtures, not game parameters; the real 60 s threshold and 1 s poll
live in config/{police,thief}/network.json and are injected by 02-09.

The daemon-thread lifecycle test lives in test_watchdog_thread.py — split
out to keep this file under the 150 code-line limit (split, never
compress); it shares this module's fixture constants and fakes via
`from tests.unit.test_watchdog import ...`.
"""

from pursuit.network.event_log import EventType, append_event, build_event
from pursuit.network.watchdog import Watchdog

_TEST_THRESHOLD = 5.0  # seconds of the FAKE clock — a test fixture, not Table 19's 60 s
_TEST_POLL = 0.01  # fake-sleeper interval — never a real sleep
_JOIN_TIMEOUT = 2.0  # test-only guard so a broken loop fails fast instead of hanging


class _FakeClock:
    """A mutable, hand-advanced stand-in for time.monotonic."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, dt):
        self.now += dt


class _Recorder:
    """A callable that records every invocation; usable as on_freeze or exit_action."""

    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1


def test_watchdog_stays_quiet_while_activity_is_fresh():
    clock = _FakeClock()
    on_freeze = _Recorder()
    exit_action = _Recorder()
    wd = Watchdog(
        threshold_seconds=_TEST_THRESHOLD,
        poll_seconds=_TEST_POLL,
        on_freeze=on_freeze,
        exit_action=exit_action,
        clock=clock,
        sleeper=lambda _dt: None,
    )
    wd.touch()
    clock.advance(_TEST_THRESHOLD / 2)

    assert wd.check_once() is False
    assert on_freeze.calls == 0
    assert exit_action.calls == 0


def test_watchdog_does_not_fire_exactly_at_threshold():
    clock = _FakeClock()
    on_freeze = _Recorder()
    exit_action = _Recorder()
    wd = Watchdog(
        threshold_seconds=_TEST_THRESHOLD,
        poll_seconds=_TEST_POLL,
        on_freeze=on_freeze,
        exit_action=exit_action,
        clock=clock,
        sleeper=lambda _dt: None,
    )
    wd.touch()
    clock.advance(_TEST_THRESHOLD)

    assert wd.check_once() is False


def test_incident_record_is_on_disk_before_exit(tmp_path):
    log = tmp_path / "log.jsonl"
    call_order = []

    def on_freeze():
        call_order.append("freeze")
        append_event(
            log,
            build_event(
                game_uid="g", turn=0, event=EventType.WATCHDOG_INCIDENT, sender="police"
            ),
        )

    def exit_action():
        call_order.append(("exit", log.read_text(encoding="utf-8")))

    clock = _FakeClock()
    wd = Watchdog(
        threshold_seconds=_TEST_THRESHOLD,
        poll_seconds=_TEST_POLL,
        on_freeze=on_freeze,
        exit_action=exit_action,
        clock=clock,
        sleeper=lambda _dt: None,
    )
    wd.touch()
    clock.advance(_TEST_THRESHOLD * 2)

    assert wd.check_once() is True
    assert call_order[0] == "freeze"
    assert call_order[1][0] == "exit"
    assert "watchdog_incident" in call_order[1][1]


def test_exit_still_fires_when_on_freeze_raises():
    def on_freeze():
        raise RuntimeError("disk error")

    exit_action = _Recorder()
    clock = _FakeClock()
    wd = Watchdog(
        threshold_seconds=_TEST_THRESHOLD,
        poll_seconds=_TEST_POLL,
        on_freeze=on_freeze,
        exit_action=exit_action,
        clock=clock,
        sleeper=lambda _dt: None,
    )
    wd.touch()
    clock.advance(_TEST_THRESHOLD * 2)

    assert wd.check_once() is True
    assert exit_action.calls == 1


def test_touch_resets_the_clock():
    clock = _FakeClock()
    on_freeze = _Recorder()
    exit_action = _Recorder()
    wd = Watchdog(
        threshold_seconds=_TEST_THRESHOLD,
        poll_seconds=_TEST_POLL,
        on_freeze=on_freeze,
        exit_action=exit_action,
        clock=clock,
        sleeper=lambda _dt: None,
    )
    wd.touch()
    clock.advance(_TEST_THRESHOLD * 2)
    wd.touch()

    assert wd.check_once() is False
    assert on_freeze.calls == 0
    assert exit_action.calls == 0
