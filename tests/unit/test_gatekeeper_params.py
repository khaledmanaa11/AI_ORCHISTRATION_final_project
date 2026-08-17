"""D-68: ONE gatekeeper class, two shapes of caller -- and Phase 4 cannot
tell the difference.

Two halves. The first pins the new structural contract
(``shared/gatekeeper_params.py``) and the mail-shaped caller: a params object
with no token concept yields ``budget is None`` and a zero-token call runs
end to end without touching a ``TokenBudget``. The second is the CONTROL for
that claim -- an injected budget double that fails on any method call proves
the "touches no budget" assertion is capable of failing.

The reserve/settle ORDER that D-35 depends on is pinned separately, in
``tests/unit/test_gatekeeper_order.py`` (split at the 150-code-line gate).
"""

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

from pursuit.services.llm import CallResult, Gatekeeper, TokenBudget
from pursuit.services.llm.budget import budget_for_params
from pursuit.shared.gatekeeper_params import BudgetParams, GatekeeperParams
from pursuit.shared.language_config import load_language_config
from tests.unit.services.test_bucket import FakeClock
from tests.unit.services.test_gatekeeper import FakeSleep

_SHIPPED_CONFIG = Path(__file__).resolve().parents[2] / "config"

#: Test scaffolding only -- a burst of 3 is small enough to exhaust in a test
#: and is NOT a docs/PARAMETERS.md value (the shipped file ships Table 19's
#: minimum of 30, asserted from the real config in
#: tests/unit/test_gatekeeper_llm_unchanged.py).
_TEST_RPM = 3


@dataclass(frozen=True)
class MailShapedParams:
    """A caller with Table 19's seven rows and no token concept at all --
    the shape ``ReportingParams`` will have (07-01 Task 3). Deliberately NOT
    ``ReportingParams`` itself: this half of D-68 must hold for any params
    object lacking the three budget rows, not only for the one the reporting
    loader happens to build."""

    requests_per_minute: int = _TEST_RPM
    parallel_requests: int = 2
    wait_after_error_seconds: int = 0
    retries_before_failure: int = 3
    queue_depth: int = 100
    response_timeout_seconds: int = 5
    watchdog_threshold_seconds: int = 60


class BudgetTouchedError(AssertionError):
    """Raised by ``TrapBudget`` -- its own class so it can never be mistaken
    for an ordinary failed assertion elsewhere in the run."""


class TrapBudget:
    """A ``TokenBudget``-shaped double that fails the test on ANY call.

    This is the counter-control: injected into a gatekeeper it turns "the
    mail path touches no budget" into a claim that demonstrably CAN fail.
    """

    def reserve(self, estimated_tokens: int) -> None:
        raise BudgetTouchedError(f"reserve({estimated_tokens}) reached the budget")

    def settle(self, **kwargs: int) -> None:
        raise BudgetTouchedError(f"settle({kwargs}) reached the budget")


async def _ok() -> CallResult:
    """A mail-shaped call: no token concept, so 0 for both (CallResult docs)."""
    return CallResult(value="sent", input_tokens=0, output_tokens=0)


def _mail_gatekeeper(**kwargs: object) -> Gatekeeper:
    return Gatekeeper(
        params=MailShapedParams(), clock=FakeClock(), sleep=FakeSleep(), **kwargs
    )


@pytest.mark.parametrize("role", ["police", "thief"])
def test_shipped_language_params_satisfy_both_protocols(role: str) -> None:
    """The extraction is only real if the SHIPPED LLM params satisfy it."""
    params = load_language_config(_SHIPPED_CONFIG / role / "language.json")
    assert isinstance(params, GatekeeperParams)
    assert isinstance(params, BudgetParams)


def test_mail_shaped_params_satisfy_the_gatekeeper_contract_but_not_the_budget_one() -> None:
    """The distinction D-68 turns on, asserted in both directions."""
    params = MailShapedParams()
    assert isinstance(params, GatekeeperParams)
    assert not isinstance(params, BudgetParams)


def test_gatekeeper_params_module_holds_no_numeric_literal() -> None:
    """Floors stay in language_config.py's GATEKEEPER_MINIMA; this module is
    structure only. Parsed, not grepped -- the docstring cites measured line
    counts, and a grep would have flagged those and proved nothing."""
    source = (
        Path(__file__).resolve().parents[2]
        / "src" / "pursuit" / "shared" / "gatekeeper_params.py"
    ).read_text(encoding="utf-8")
    numbers = [
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        and not isinstance(node.value, bool)
    ]
    assert numbers == []


def test_a_params_object_without_the_budget_rows_yields_no_budget() -> None:
    assert budget_for_params(MailShapedParams()) is None
    assert _mail_gatekeeper().budget is None


@pytest.mark.parametrize("role", ["police", "thief"])
def test_language_params_still_yield_a_real_budget(role: str) -> None:
    params = load_language_config(_SHIPPED_CONFIG / role / "language.json")
    derived = budget_for_params(params)
    assert isinstance(derived, TokenBudget)
    assert derived.report()["budget"] == params.token_budget_per_series


async def test_mail_shaped_call_completes_without_touching_any_budget() -> None:
    """Success criterion 1: zero tokens, no budget, still a completed call."""
    gk = _mail_gatekeeper()
    assert gk.budget is None
    assert await gk.submit(_ok, estimated_tokens=0) == "sent"
    assert gk.budget is None


async def test_control_an_injected_budget_double_does_get_touched() -> None:
    """The vacuity control for the test above: with a budget present, the very
    same call reaches it. Without this, "touches no budget" would pass just as
    happily against a submit() that had stopped calling the budget at all."""
    gk = _mail_gatekeeper(budget=TrapBudget())
    with pytest.raises(BudgetTouchedError, match="reserve"):
        await gk.submit(_ok, estimated_tokens=0)


async def test_bucket_ready_seam_tracks_the_private_bucket() -> None:
    """D-69/OQ-2's read-only seam: True while the bucket can admit, False once
    ``_TEST_RPM`` immediate sends have drained it."""
    gk = _mail_gatekeeper()
    assert gk.bucket_ready is True
    for _ in range(_TEST_RPM):
        await gk.submit(_ok, estimated_tokens=0)
    assert gk.bucket_ready is False


async def test_reading_the_seam_never_consumes_a_token() -> None:
    """Observing must not steal the token the next real send needs -- the seam
    reads time_until_available(), never try_acquire()."""
    gk = _mail_gatekeeper()
    for _ in range(_TEST_RPM * 2):
        assert gk.bucket_ready is True
    for _ in range(_TEST_RPM):
        await gk.submit(_ok, estimated_tokens=0)
    assert gk.bucket_ready is False
