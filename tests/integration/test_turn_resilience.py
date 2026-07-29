"""§10.4 gate criterion 3, resilience half: "watchdog + deadline tracker
prevent hangs."

These tests use the injected `sleep` / `clock` / exit seams 02-07 and 02-04
already provide, so DURATIONS never elapse while counts and thresholds stay
config-sourced. No test here waits on the real 30 s response deadline or the
real 60 s watchdog threshold -- a gate test that slept on either would be
unrunnable in CI. Split out of test_turn_lifecycle.py at the 150-code-line
gate (QUAL-08, split never compress).
"""

from __future__ import annotations

from mcp import McpError
from mcp.types import ErrorData

from pursuit.network import turn_events
from pursuit.network.agent_wiring import make_freeze_handler
from pursuit.network.deadline import call_with_retry
from pursuit.network.event_log import append_event
from pursuit.network.watchdog import Watchdog
from tests.integration.conftest import read_events, recording_sleep, stepping_clock


async def test_silent_opponent_yields_technical_win(network_params, agent_log_paths):
    """GATE-3, NET-06, D-13, D-17 -- retry -> backoff -> technical win,
    cleanly logged, never a hang. Does NOT re-test the ToolError-is-not-a-
    technical-win distinction (tests/unit/test_deadline.py already covers
    that, QUAL-02)."""
    log_a, _log_b = agent_log_paths
    sleep, durations = recording_sleep()

    async def _silent_send() -> object:
        raise McpError(ErrorData(code=-1, message="simulated silent opponent"))

    call_outcome = await call_with_retry(
        _silent_send,
        timeout=network_params.response_timeout,
        retries=network_params.retry_count,
        backoff=network_params.backoff_seconds,
        sleep=sleep,
    )

    # 1. A TechnicalWin verdict carries the evidence the event log needs (D-13).
    assert not call_outcome.succeeded
    assert call_outcome.value is None  # agent ended cleanly -- no hang, no exception escaped
    verdict = call_outcome.verdict
    assert verdict.reason.value

    # 2. The retry budget came from CONFIG, not the test (D-17): recorded sleeps
    #    equal exactly [backoff_seconds] * retry_count, zero wall-clock elapsed.
    assert durations == [network_params.backoff_seconds] * network_params.retry_count

    # 3. The technical win reaches the log via the real D-11 builder + append_event.
    record = turn_events.technical_win_record(
        game_uid="resilience", turn=0, sender="police",
        retries_attempted=verdict.attempts, timeout_seconds=verdict.timeout_seconds,
        reason=verdict.reason.value,
    )
    append_event(log_a, record)
    events = read_events(log_a)
    assert len(events) == 1
    assert events[0]["event"] == "technical_win"
    assert events[0]["retries_attempted"] == network_params.retry_count + 1


def test_freeze_writes_incident_before_exit(network_params, agent_log_paths):
    """GATE-3, NET-07, D-14, D-18 -- the ordering proof: the incident record
    is durable BEFORE the injected exit call fires, driven through
    `Watchdog.check_once` with a stepping clock (never the daemon thread),
    using the real `make_freeze_handler` writer (not a stand-in)."""
    log_a, _log_b = agent_log_paths
    clock = stepping_clock()
    captured: dict[str, list[dict]] = {}

    def _fake_exit() -> None:
        captured["at_exit"] = read_events(log_a)

    on_freeze = make_freeze_handler(
        log_a, game_uid="resilience", role="police",
        threshold_seconds=network_params.watchdog_threshold,
    )
    watchdog = Watchdog(
        threshold_seconds=network_params.watchdog_threshold,
        poll_seconds=network_params.watchdog_poll_seconds,
        on_freeze=on_freeze,
        exit_action=_fake_exit,
        clock=clock,
    )

    watchdog.touch()

    # Control case: clock not advanced past the threshold -- nothing fires.
    assert watchdog.check_once() is False
    assert read_events(log_a) == []
    assert "at_exit" not in captured

    clock.advance(network_params.watchdog_threshold + network_params.watchdog_poll_seconds)
    assert watchdog.check_once() is True

    # 1 & 2. The fake exit fired exactly once, and by the TIME it ran, the
    # incident it read from disk was ALREADY there -- the before-exit proof.
    assert "at_exit" in captured
    assert len(captured["at_exit"]) == 1
    assert captured["at_exit"][0]["event"] == "watchdog_incident"

    # 3. The durable record on disk now matches exactly what check_once wrote.
    assert read_events(log_a) == captured["at_exit"]
