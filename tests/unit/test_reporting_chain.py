"""ReportingChain -- the Figure-13 composition (D-69, rules 28-29).

The load-bearing claim is a NEGATIVE one: no refusal path raises out of the
caller. A negative claim is the easiest kind to pass vacuously, so every
"nothing raised" assertion here is paired with something that CAN fail --
either a checked outcome value, or the BaseException control at the foot of
the file proving `send()` is not a blanket swallow.

Every gatekeeper is built with an injected FakeClock and FakeSleep; no test
waits, and no test transmits -- the sink is a local coroutine.
"""

from pathlib import Path

import pytest

from pursuit.services.llm import Gatekeeper
from pursuit.services.reporting import DosDetector, QuotaManager, Refusal, ReportingChain
from tests.unit.services.test_bucket import FakeClock
from tests.unit.services.test_gatekeeper import FakeSleep
from tests.unit.test_gatekeeper_params import MailShapedParams
from tests.unit.test_reporting_quota import FakeWallClock

#: Test scaffolding, not docs/ values. The shipped ceiling and queue depth are
#: 500 and 100, asserted against the real files in test_reporting_config.py.
_TEST_CEILING = 2
_TEST_QUEUE_DEPTH = 2
_TEST_RETRIES = 3

_REPORT = {"game_id": "g-1", "outcome": "capture"}


class RecordingSink:
    """A sink that records what it was handed, and can be made to fail."""

    def __init__(self, *, fail: bool = False) -> None:
        self.sent: list[dict] = []
        self.fail = fail

    async def __call__(self, report: dict) -> str:
        if self.fail:
            raise RuntimeError("sink down")
        self.sent.append(report)
        return "receipt"


def _chain(tmp_path: Path, sink: RecordingSink, **kwargs: object) -> ReportingChain:
    return ReportingChain(
        gatekeeper=Gatekeeper(
            params=MailShapedParams(retries_before_failure=_TEST_RETRIES),
            clock=FakeClock(),
            sleep=FakeSleep(),
        ),
        quota=QuotaManager(
            ceiling_per_hour=kwargs.pop("ceiling", _TEST_CEILING),
            path=tmp_path / "quota.json",
            clock=FakeWallClock(),
        ),
        dos=kwargs.pop("dos", DosDetector(retries_before_failure=_TEST_RETRIES)),
        sink=sink,
        queue_depth=kwargs.pop("queue_depth", _TEST_QUEUE_DEPTH),
    )


async def test_a_healthy_send_reaches_the_sink(tmp_path: Path) -> None:
    sink = RecordingSink()
    outcome = await _chain(tmp_path, sink).send(_REPORT)
    assert outcome.sent is True
    assert outcome.refusal is None
    assert sink.sent == [_REPORT]


async def test_quota_exhaustion_refuses_and_queues_without_raising(tmp_path: Path) -> None:
    sink = RecordingSink()
    chain = _chain(tmp_path, sink)
    for _ in range(_TEST_CEILING):
        await chain.send(_REPORT)
    outcome = await chain.send(_REPORT)
    assert outcome.sent is False
    assert outcome.refusal is Refusal.QUOTA_EXHAUSTED
    assert outcome.queued is True
    assert chain.pending == 1
    assert len(sink.sent) == _TEST_CEILING


async def test_a_latched_lock_refuses_and_never_reaches_the_sink(tmp_path: Path) -> None:
    dos = DosDetector(retries_before_failure=_TEST_RETRIES)
    for _ in range(_TEST_RETRIES + 1):
        dos.observe(bucket_ready=False)
    sink = RecordingSink()
    chain = _chain(tmp_path, sink, dos=dos)
    outcome = await chain.send(_REPORT)
    assert outcome.refusal is Refusal.DOS_LOCKED
    assert outcome.queued is True
    assert sink.sent == []


async def test_a_latched_lock_is_gated_before_the_quota_is_spent(tmp_path: Path) -> None:
    """D-69's order, asserted where it is observable: a locked interface must
    not burn a send out of the hourly ceiling on the way to refusing."""
    dos = DosDetector(retries_before_failure=_TEST_RETRIES)
    for _ in range(_TEST_RETRIES + 1):
        dos.observe(bucket_ready=False)
    quota_path = tmp_path / "quota.json"
    await _chain(tmp_path, RecordingSink(), dos=dos).send(_REPORT)
    assert not quota_path.exists()


async def test_a_permanently_failing_sink_queues_instead_of_raising(tmp_path: Path) -> None:
    sink = RecordingSink(fail=True)
    chain = _chain(tmp_path, sink)
    outcome = await chain.send(_REPORT)
    assert outcome.sent is False
    assert outcome.refusal is Refusal.SEND_FAILED
    assert chain.pending == 1


async def test_a_full_queue_alerts_and_still_returns_an_outcome(tmp_path: Path) -> None:
    """SEGAL §4: overflow is a backpressure alert, never a rejection and never
    a crash. The newest report is dropped so the FIFO keeps its oldest."""
    sink = RecordingSink(fail=True)
    chain = _chain(tmp_path, sink, ceiling=10)
    for _ in range(_TEST_QUEUE_DEPTH):
        await chain.send(_REPORT)
    assert chain.pending == _TEST_QUEUE_DEPTH
    outcome = await chain.send(_REPORT)
    assert outcome.refusal is Refusal.QUEUE_FULL
    assert outcome.queued is False
    assert chain.pending == _TEST_QUEUE_DEPTH


async def test_drain_resends_what_was_queued_once_the_sink_recovers(tmp_path: Path) -> None:
    sink = RecordingSink(fail=True)
    chain = _chain(tmp_path, sink, ceiling=10)
    await chain.send(_REPORT)
    assert chain.pending == 1
    sink.fail = False
    outcomes = await chain.drain()
    assert [o.sent for o in outcomes] == [True]
    assert chain.pending == 0
    assert sink.sent == [_REPORT]


async def test_drain_attempts_each_queued_report_exactly_once(tmp_path: Path) -> None:
    """No background thread and no retry loop inside drain(): a report that
    fails again is owed to the NEXT drain, not retried forever in this one."""
    sink = RecordingSink(fail=True)
    chain = _chain(tmp_path, sink, ceiling=10)
    await chain.send(_REPORT)
    outcomes = await chain.drain()
    assert [o.refusal for o in outcomes] == [Refusal.SEND_FAILED]
    assert chain.pending == 1


class OperatorAbort(BaseException):
    """A BaseException that is NOT an Exception, standing in for a task
    cancellation or an operator interrupt. Its own class rather than
    KeyboardInterrupt, which pytest intercepts to abort the whole session --
    the property under test is `except Exception` vs `except BaseException`,
    not pytest's signal handling."""


async def test_control_the_chain_does_not_swallow_a_baseexception(tmp_path: Path) -> None:
    """The vacuity control for every "never raises" assertion above. send()
    catches Exception, NOT BaseException, so a cancellation still propagates.
    Without this, "nothing raised" would be trivially true of a blanket
    try/except and would prove nothing at all."""

    class Interrupting(RecordingSink):
        async def __call__(self, report: dict) -> str:
            raise OperatorAbort("the run was cancelled")

    with pytest.raises(OperatorAbort):
        await _chain(tmp_path, Interrupting()).send(_REPORT)
