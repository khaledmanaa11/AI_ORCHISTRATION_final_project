"""D-35's statement ORDER inside ``Gatekeeper.submit()`` -- the contract with
no test until now.

``budget.reserve()`` runs UNCONDITIONALLY and ABOVE the queue-depth check, and
``settle()`` runs only on the success path. That is deliberate: "the degrade
level reflects every QUEUED call immediately, not just completed ones"
(``budget.py`` module docstring, ``gatekeeper.py`` step 1). So an overflow and
a retry-exhausted call both leave the reservation standing.

Nothing said so. An executor tidying 07-01's ``budget is None`` guard could
have moved ``reserve()`` below the overflow check -- a one-line move that
turns the degrade ladder into a completed-call counter -- and the whole
pre-existing Phase-4 suite would still have been green. These four tests are
what makes that move impossible; the probes that prove they are not vacuous
are recorded in 07-01-SUMMARY.md with their failure counts.

Split from ``test_gatekeeper_params.py`` at the 150-code-line gate (Segal
Table 5), same precedent as test_gatekeeper.py / test_gatekeeper_retry.py.
"""

import asyncio

import pytest

from pursuit.services.llm import CallResult, DegradeLevel, Gatekeeper, GatekeeperOverflow
from pursuit.services.llm.gatekeeper import _SECONDS_PER_MINUTE
from tests.unit.services.test_bucket import FakeClock
from tests.unit.services.test_gatekeeper import FakeSleep, _params
from tests.unit.test_gatekeeper_params import MailShapedParams

#: Test scaffolding, NOT docs/PARAMETERS.md values. A three-rung ladder small
#: enough that one reservation crosses rung 1 and one settled call then
#: crosses rung 2 -- the shipped thresholds are 140_000/180_000/200_000 and
#: are asserted against the real files in test_gatekeeper_llm_unchanged.py.
_SHORT_RUNG = 100
_TEMPLATE_RUNG = 150
_SERIES_CEILING = 200

#: The estimate carried by the call that never completes. Equal to _SHORT_RUNG
#: so that reserving it, and ONLY reserving it, moves the ladder one rung.
_UNCOMPLETED_ESTIMATE = 100

#: Observed usage of the one call that DOES complete afterwards. Chosen so the
#: total only reaches _TEMPLATE_RUNG if the earlier reservation is still standing:
#: 50 alone is below rung 1, 50 + 100 is exactly rung 2.
_SETTLED_INPUT_TOKENS = 50

#: requests_per_minute for the bucket test: C = 3, r = 3/60 = 0.05 tokens/sec.
_BURST_RPM = 3


def _ladder_params(**overrides: object):
    return _params(
        token_budget_per_series=_SERIES_CEILING,
        short_prompt_threshold_tokens=_SHORT_RUNG,
        template_only_threshold_tokens=_TEMPLATE_RUNG,
        wait_after_error_seconds=0,
        **overrides,
    )


def _gatekeeper(params, **kwargs: object) -> Gatekeeper:
    return Gatekeeper(params=params, clock=FakeClock(), sleep=FakeSleep(), **kwargs)


async def _ok() -> CallResult:
    return CallResult(value="ok", input_tokens=0, output_tokens=0)


async def _spends() -> CallResult:
    return CallResult(value="ok", input_tokens=_SETTLED_INPUT_TOKENS, output_tokens=0)


async def _boom() -> CallResult:
    raise RuntimeError("boom")


async def test_an_overflowed_call_has_already_reserved_and_stays_reserved() -> None:
    """(a) GatekeeperOverflow leaves the reservation standing, and a LATER
    settled call cannot un-reserve it: 50 observed tokens on their own sit
    below rung 1, but 50 on top of the standing 100 reach rung 2 exactly."""
    gk = _gatekeeper(_ladder_params(parallel_requests=1, queue_depth=1))
    holding, release = asyncio.Event(), asyncio.Event()

    async def holder() -> CallResult:
        holding.set()
        await release.wait()
        return CallResult(value="held", input_tokens=0, output_tokens=0)

    held = asyncio.create_task(gk.submit(holder, estimated_tokens=0))
    await asyncio.wait_for(holding.wait(), timeout=1.0)
    queued = asyncio.create_task(gk.submit(_ok, estimated_tokens=0))
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    with pytest.raises(GatekeeperOverflow):
        await gk.submit(_ok, estimated_tokens=_UNCOMPLETED_ESTIMATE)
    assert gk.budget.level is DegradeLevel.SHORT_PROMPT

    release.set()
    assert await asyncio.wait_for(held, timeout=1.0) == "held"
    await asyncio.wait_for(queued, timeout=1.0)
    await gk.submit(_spends, estimated_tokens=0)
    assert gk.budget.level is DegradeLevel.TEMPLATE_ONLY
    assert gk.budget.report()["input_tokens"] == _SETTLED_INPUT_TOKENS


async def test_a_retry_exhausted_call_has_reserved_and_never_settles() -> None:
    """(b) The last exception surfaces, ``calls`` stays 0 because settle()
    never ran, and the ladder has still moved because reserve() did."""
    gk = _gatekeeper(_ladder_params(retries_before_failure=1))
    with pytest.raises(RuntimeError, match="boom"):
        await gk.submit(_boom, estimated_tokens=_UNCOMPLETED_ESTIMATE)
    assert gk.budget.report()["calls"] == 0
    assert gk.budget.level is DegradeLevel.SHORT_PROMPT


async def test_a_mail_shaped_failure_surfaces_its_own_exception_with_no_budget() -> None:
    """(c) The failure path is the one that would raise AttributeError if the
    None guard were only on the success path -- the caller must still see its
    own RuntimeError, not a crash from inside the gatekeeper."""
    gk = _gatekeeper(MailShapedParams(retries_before_failure=1))
    assert gk.budget is None
    with pytest.raises(RuntimeError, match="boom"):
        await gk.submit(_boom, estimated_tokens=0)
    assert gk.budget is None


async def test_bucket_admits_exactly_capacity_then_waits_one_over_r() -> None:
    """(d) Table 19's law, measured on the gatekeeper rather than the bucket:
    C immediate sends with ZERO waits, then a wait of exactly (1 - tokens)/r."""
    sleeper = FakeSleep()
    gk = Gatekeeper(
        params=_ladder_params(requests_per_minute=_BURST_RPM),
        clock=FakeClock(),
        sleep=sleeper,
    )
    for _ in range(_BURST_RPM):
        await gk.submit(_ok, estimated_tokens=0)
    assert sleeper.calls == []
    assert gk.bucket_ready is False

    refill_rate = _BURST_RPM / _SECONDS_PER_MINUTE
    expected_wait = (1 - gk._bucket.tokens) / refill_rate
    assert expected_wait == 20.0
    await gk.submit(_ok, estimated_tokens=0)
    assert sleeper.calls == [expected_wait]
