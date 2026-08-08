"""Gatekeeper retry/backoff/timeout suite -- the other half of test_gatekeeper.py.

Split at the 150-code-line gate, not by test meaning (see that module's
docstring). Shared fakes (FakeSleep, _params) are defined once there
(QUAL-02) and imported here. Only test_timeout_is_treated_as_retryable
uses a real (tiny) wall-clock wait, because asyncio.wait_for's own
deadline is not an injectable seam -- the same pattern
tests/unit/test_deadline.py uses via _TEST_DEADLINE_SECONDS.
"""

import asyncio
from pathlib import Path

import pytest

from pursuit.services.llm import CallResult, Gatekeeper
from tests.unit.services.test_bucket import FakeClock
from tests.unit.services.test_gatekeeper import FakeSleep, _params

_REAL_TIMEOUT_SECONDS = 0.05  # test scaffolding only; NOT a PARAMETERS.md value


async def test_transient_failure_retries_then_surfaces_after_exhausting_retries() -> None:
    params = _params(retries_before_failure=2, wait_after_error_seconds=7)
    sleeper = FakeSleep()
    gk = Gatekeeper(params=params, clock=FakeClock(), sleep=sleeper)
    attempts = 0

    async def always_fails() -> CallResult:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await gk.submit(always_fails, estimated_tokens=0)
    assert attempts == 3  # retries_before_failure + 1 initial attempt
    assert sleeper.calls == [7, 7]  # backoff between attempts, none after the last


async def test_transient_failure_then_success_recovers_without_exhausting() -> None:
    params = _params(retries_before_failure=3, wait_after_error_seconds=1)
    gk = Gatekeeper(params=params, clock=FakeClock(), sleep=FakeSleep())
    attempts = 0

    async def fails_once() -> CallResult:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("transient")
        return CallResult(value="recovered", input_tokens=1, output_tokens=1)

    assert await gk.submit(fails_once, estimated_tokens=1) == "recovered"
    assert attempts == 2


async def test_timeout_is_treated_as_retryable() -> None:
    params = _params(
        retries_before_failure=1,
        response_timeout_seconds=_REAL_TIMEOUT_SECONDS,
        wait_after_error_seconds=0,
    )
    gk = Gatekeeper(params=params, clock=FakeClock(), sleep=FakeSleep())
    attempts = 0

    async def hangs() -> CallResult:
        nonlocal attempts
        attempts += 1
        await asyncio.Event().wait()  # never set -> asyncio.wait_for times out

    with pytest.raises(TimeoutError):
        await gk.submit(hangs, estimated_tokens=0)
    assert attempts == 2  # retries_before_failure(1) + 1 initial attempt


async def test_no_settlement_on_a_failure_that_exhausts_every_retry() -> None:
    params = _params(retries_before_failure=1, wait_after_error_seconds=0)
    gk = Gatekeeper(params=params, clock=FakeClock(), sleep=FakeSleep())

    async def always_fails() -> CallResult:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await gk.submit(always_fails, estimated_tokens=5)
    assert gk.budget.report()["calls"] == 0


async def test_default_clock_and_sleep_are_real_asyncio_primitives() -> None:
    """No injected seams -- confirms the defaults wire up a working instance."""
    gk = Gatekeeper(params=_params(wait_after_error_seconds=0))

    async def fn() -> CallResult:
        return CallResult(value="ok", input_tokens=0, output_tokens=0)

    assert await gk.submit(fn, estimated_tokens=0) == "ok"


def test_no_anthropic_or_openai_import_in_gatekeeper_module() -> None:
    import pursuit.services.llm.gatekeeper as gatekeeper_module

    source = Path(gatekeeper_module.__file__).read_text(encoding="utf-8").lower()
    assert "anthropic" not in source
    assert "openai" not in source
