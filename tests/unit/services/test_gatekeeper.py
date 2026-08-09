"""Tests for Gatekeeper -- D-34's one door, D-35's budget, QUAL-05's queue.

Happy path, budget reflection and the FIFO queue/parallel-cap/overflow
suite. Split from test_gatekeeper_retry.py at the 150-code-line gate
(Segal Table 5), not by test meaning -- mirrors the
test_deadline.py/test_deadline_retry.py precedent (QUAL-02: shared fakes
defined once here and imported there).

FakeClock is imported from test_bucket.py (QUAL-02: no duplicated fake).
"""

import asyncio

import pytest

from pursuit.services.llm import CallResult, Gatekeeper, GatekeeperOverflow
from pursuit.shared.language_config import LanguageParams
from tests.unit.services.test_bucket import FakeClock


class FakeSleep:
    """Records what was asked to wait, in order; never actually waits."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def _params(**overrides: object) -> LanguageParams:
    """Test-only LanguageParams. Unoverridden fields keep Table-19-sourced
    magnitudes (config/police/language.json); queue_depth/parallel_requests/
    timeouts are shrunk per-test for speed, labelled at each call site --
    same pattern as tests/unit/test_deadline.py's _TEST_DEADLINE_SECONDS.
    """
    defaults: dict[str, object] = {
        "version": "1.00",
        "requests_per_minute": 30,
        "parallel_requests": 2,
        "wait_after_error_seconds": 0,
        "retries_before_failure": 3,
        "queue_depth": 100,
        "response_timeout_seconds": 5,
        "watchdog_threshold_seconds": 60,
        "token_budget_per_series": 200_000,
        "short_prompt_threshold_tokens": 140_000,
        "template_only_threshold_tokens": 180_000,
        "model": {},
    }
    defaults.update(overrides)
    return LanguageParams(**defaults)


async def test_successful_call_returns_fns_value() -> None:
    gk = Gatekeeper(params=_params(), clock=FakeClock(), sleep=FakeSleep())

    async def fn() -> CallResult:
        return CallResult(value="ack", input_tokens=1, output_tokens=1)

    assert await gk.submit(fn, estimated_tokens=2) == "ack"


async def test_budget_reflects_every_settled_call() -> None:
    gk = Gatekeeper(params=_params(), clock=FakeClock(), sleep=FakeSleep())

    async def fn() -> CallResult:
        return CallResult(value="ok", input_tokens=10, output_tokens=5)

    for _ in range(3):
        await gk.submit(fn, estimated_tokens=15)
    report = gk.budget.report()
    assert report["calls"] == 3
    assert report["input_tokens"] == 30
    assert report["output_tokens"] == 15


async def test_exhausted_bucket_awaits_the_injected_sleep_before_the_next_call() -> None:
    """Step 4 of submit()'s order: an empty bucket is awaited, not busy-polled."""
    sleeper = FakeSleep()
    params = _params(requests_per_minute=2, wait_after_error_seconds=0)
    gk = Gatekeeper(params=params, clock=FakeClock(), sleep=sleeper)

    async def fn() -> CallResult:
        return CallResult(value="ok", input_tokens=0, output_tokens=0)

    for _ in range(3):  # capacity 2 -> the 3rd call finds the bucket empty
        await gk.submit(fn, estimated_tokens=0)
    assert any(wait > 0 for wait in sleeper.calls)


async def test_calls_beyond_parallel_cap_queue_and_run_in_submission_order() -> None:
    params = _params(parallel_requests=1, queue_depth=5)
    gk = Gatekeeper(params=params, clock=FakeClock(), sleep=FakeSleep())
    started: list[int] = []
    first_started = asyncio.Event()
    release = asyncio.Event()

    def make_fn(i: int):
        async def fn() -> CallResult:
            started.append(i)
            if i == 0:
                first_started.set()
            await release.wait()
            return CallResult(value=i, input_tokens=0, output_tokens=0)

        return fn

    tasks = [asyncio.create_task(gk.submit(make_fn(i), estimated_tokens=0)) for i in range(3)]
    await asyncio.wait_for(first_started.wait(), timeout=1.0)
    # Semaphore capacity 1 structurally prevents 1/2 from having entered fn
    # yet -- this is not a timing race, it is enforced by the lock itself.
    assert started == [0]
    release.set()
    results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=1.0)
    assert started == [0, 1, 2]
    assert results == [0, 1, 2]


async def test_full_queue_raises_overflow_and_leaves_queued_work_intact() -> None:
    params = _params(parallel_requests=1, queue_depth=1)
    gk = Gatekeeper(params=params, clock=FakeClock(), sleep=FakeSleep())
    holding = asyncio.Event()
    release = asyncio.Event()

    async def holder() -> CallResult:
        holding.set()
        await release.wait()
        return CallResult(value="held", input_tokens=0, output_tokens=0)

    async def queued() -> CallResult:
        return CallResult(value="queued", input_tokens=0, output_tokens=0)

    hold_task = asyncio.create_task(gk.submit(holder, estimated_tokens=0))
    await asyncio.wait_for(holding.wait(), timeout=1.0)
    queued_task = asyncio.create_task(gk.submit(queued, estimated_tokens=0))
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    with pytest.raises(GatekeeperOverflow, match="queue depth"):
        await gk.submit(queued, estimated_tokens=0)

    release.set()
    assert await asyncio.wait_for(hold_task, timeout=1.0) == "held"
    assert await asyncio.wait_for(queued_task, timeout=1.0) == "queued"
