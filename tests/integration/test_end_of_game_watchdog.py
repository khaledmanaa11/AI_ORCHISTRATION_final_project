"""Proof (c): the reporting ladder outlives the freeze threshold and does NOT
trip it -- and NET-07 is not traded away to get that.

ZERO REAL SLEEPS, NO 60-SECOND TESTS. The REAL `Watchdog`, its real
`check_once` arithmetic, on a clock the test advances by hand (05-13's
technique, `tests/unit/_fakes_watchdog.py`). The 210 s ladder costs 0.000 s of
wall time and `os._exit` is never reachable.

EVERY NUMBER COMES OFF `reporting.json`. The ladder is computed from
`response_timeout_seconds`, `retries_before_failure` and
`wait_after_error_seconds`; the threshold is `watchdog_threshold_seconds`.
Nothing here writes a duration down, so lowering a config leaf cannot keep
these tests green by accident -- it changes both sides of the comparison.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.services.llm import Gatekeeper
from pursuit.services.reporting.chain import ReportingChain
from pursuit.services.reporting.dos import DosDetector
from pursuit.services.reporting.end_of_game_chain import build_reporting_chain
from pursuit.services.reporting.quota import QuotaManager
from pursuit.shared.reporting_config import REPORTING_CONFIG_SOURCE, load_reporting_config
from tests.unit._fakes_watchdog import ArmedWatchdog

POLICE_CONFIG = Path("config/police")
REPORT = {"game_uid": "watchdogseries", "game_id": "watchdogseries"}


class StalledMailSink:
    """A mail endpoint that accepts the connection and never answers. Each
    `send` is ONE bounded attempt that burned its whole `response_timeout`,
    charged to the INJECTED clock; the freeze poll runs inside the attempt, at
    the moment the real daemon thread would have run it."""

    def __init__(self, armed: ArmedWatchdog, *, step: float) -> None:
        self._armed, self._step, self.attempts = armed, step, 0

    async def send(self, report: dict) -> object:
        self.attempts += 1
        self._armed.clock.advance(self._step)
        self._armed.check()
        raise TimeoutError("stalled mail endpoint: no answer within the deadline")


def _sleeper(armed: ArmedWatchdog):
    """`Gatekeeper`'s injected backoff, charged to the same injected clock."""

    async def _sleep(seconds: float) -> None:
        armed.clock.advance(seconds)
        armed.check()

    return _sleep


def _setup(network_params):
    params = load_reporting_config(POLICE_CONFIG / REPORTING_CONFIG_SOURCE)
    armed = ArmedWatchdog(
        threshold_seconds=params.watchdog_threshold_seconds,
        poll_seconds=network_params.watchdog_poll_seconds,
    )
    return params, armed, StalledMailSink(armed, step=params.response_timeout_seconds)


def _ladder(params) -> float:
    """Table 19's worst-case reporting window, from the config's own leaves."""
    return params.response_timeout_seconds * (params.retries_before_failure + 1) + (
        params.wait_after_error_seconds * params.retries_before_failure
    )


async def test_the_reporting_ladder_outlives_the_threshold_and_never_trips_it(
    tmp_path, network_params
):
    """(c). The premise is asserted first: if the ladder ever fitted under the
    threshold this test would prove nothing at all."""
    params, armed, sink = _setup(network_params)
    assert _ladder(params) > params.watchdog_threshold_seconds, "the premise"

    chain = build_reporting_chain(
        params, watchdog=armed, artifact_dir=tmp_path, quota_dir=tmp_path,
        sink=sink, sleep=_sleeper(armed),
    )
    outcome = await chain.send(dict(REPORT))

    assert sink.attempts == params.retries_before_failure + 1, "the whole ladder ran"
    assert armed.clock.now == _ladder(params)
    assert len(armed.checks) > 1, "the freeze poll really ran, more than once"
    assert True not in armed.checks
    assert armed.fired == [], "no watchdog_incident across a 210 s reporting window"
    assert outcome.queued is True, "and the report is still owed"


async def test_the_same_ladder_without_the_touch_is_killed(tmp_path, network_params):
    """THE ANTI-VACUITY CONTROL for the test above. Same clock, same ladder,
    same harness -- with `watchdog_touching` deliberately bypassed. If this
    passed too, the test above would be green because the harness cannot see a
    freeze rather than because the touch works."""
    params, armed, sink = _setup(network_params)
    chain = ReportingChain(
        gatekeeper=Gatekeeper(params=params, sleep=_sleeper(armed)),
        quota=QuotaManager(ceiling_per_hour=params.requests_per_hour, path=tmp_path / "q.json"),
        dos=DosDetector(retries_before_failure=params.retries_before_failure),
        sink=sink.send,  # NOT wrapped -- this is the bug being controlled for
        queue_depth=params.queue_depth,
    )
    await chain.send(dict(REPORT))

    assert True in armed.checks
    assert armed.fired[:2] == ["freeze", "exit"], "on_freeze runs BEFORE the exit action"


async def test_a_genuinely_frozen_agent_is_still_killed(network_params):
    """NET-07 is not traded away. Nothing touches -- which is what a frozen
    process looks like -- and the real `Watchdog`, at the real threshold, still
    fires. The advance is `response_timeout_seconds` x 3, off the config, so no
    duration is written down here either."""
    params, armed, _sink = _setup(network_params)
    armed.clock.advance(params.response_timeout_seconds * 3)
    assert armed.clock.now > params.watchdog_threshold_seconds, "the premise"

    assert armed.check() is True
    assert armed.fired[:2] == ["freeze", "exit"]

    fresh = ArmedWatchdog(
        threshold_seconds=params.watchdog_threshold_seconds,
        poll_seconds=network_params.watchdog_poll_seconds,
    )
    fresh.clock.advance(params.response_timeout_seconds * 3)
    fresh.touch()
    assert fresh.check() is False, "and one touch inside the window still saves it"
