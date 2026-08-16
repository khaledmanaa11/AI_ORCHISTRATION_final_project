"""bluff.py: compose() is total by construction (D-33, D-45, D-36, LANG-01,
LANG-02). Every test mocks the provider; no test performs network I/O.

Split from `test_bluff_property.py` at the 150-code-line gate (Segal Table
5), not by test meaning: this file holds the direct behavioural cases
(the plan's Task 3 verify bullets 1-5); shared fakes (`FakeProvider`,
`_plan`, `_context`, `_result`, `WORD_LIMIT`) are defined here and
imported there (QUAL-02), mirroring the `test_gatekeeper.py` /
`test_gatekeeper_retry.py` precedent. That file holds the AST-structural
checks and the adversarial property test (Task 3 verify bullet 6).
"""

import random

import pytest

from pursuit.services.llm.bluff import BluffContext, compose
from pursuit.services.llm.budget import DegradeLevel
from pursuit.services.llm.hintbank import HintBank
from pursuit.services.llm.provider import LlmFailure, LlmFailureReason, LlmResult
from pursuit.services.llm.template_provider import TemplateProvider
from pursuit.services.llm.wordcount import count
from pursuit.shared.deception_types import ClaimKind, DeceptionPlan, Intent
from pursuit.shared.directions import DirectionWord
from pursuit.shared.hint_guard import assert_no_coordinates
from pursuit.shared.inference import Region

WORD_LIMIT = 15  # PARAMETERS.md Table 14 row 2, passed in as the caller would


def declaration(kind: ClaimKind) -> DeceptionPlan:
    """A truthful barrier/capture declaration, built the ONE way that is
    left after 05-15 deleted the zero-caller `declare_truthfully` wrapper:
    through `DeceptionPlan` itself, whose `__post_init__` is the actual
    rules-15/16/21/22 gate. Shared with `test_bluff_property.py` via the
    same sibling import that already carries `_plan`/`_context`/`_result`
    (QUAL-02) -- one definition, not two."""
    return DeceptionPlan(intent=Intent.TRUTH, kind=kind)


class FakeProvider:
    """Satisfies the Provider protocol. `sequence` (if given) is consumed
    one item per call; `outcome` is returned on every call otherwise;
    `boom`, if set, is raised instead."""

    def __init__(self, outcome=None, *, sequence=None, boom: Exception | None = None):
        self.outcome = outcome
        self.sequence = list(sequence) if sequence is not None else None
        self.boom = boom
        self.calls = 0

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        self.calls += 1
        if self.boom is not None:
            raise self.boom
        if self.sequence is not None:
            return self.sequence.pop(0)
        return self.outcome


def _plan(kind: ClaimKind = ClaimKind.LOCATION, intent: Intent = Intent.LIE) -> DeceptionPlan:
    if kind is ClaimKind.LOCATION:
        return DeceptionPlan(
            intent=intent,
            kind=kind,
            claimed_region=Region.NORTH,
            true_region=Region.SOUTH if intent is Intent.LIE else Region.NORTH,
        )
    return DeceptionPlan(
        intent=intent,
        kind=ClaimKind.HEADING,
        claimed_heading=DirectionWord.EAST,
        true_heading=DirectionWord.WEST if intent is Intent.LIE else DirectionWord.EAST,
    )


def _context(
    provider, *, degrade=DegradeLevel.FULL, word_limit=WORD_LIMIT, arena="New York", seed=0
) -> BluffContext:
    return BluffContext(
        provider=provider,
        degrade_level=degrade,
        arena=arena,
        word_limit=word_limit,
        hint_bank=HintBank(rng=random.Random(seed)),
    )


def _result(text: str) -> LlmResult:
    return LlmResult(text=text, parsed=None, input_tokens=1, output_tokens=1)


async def test_a_good_completion_is_returned_unchanged():
    provider = FakeProvider(_result("Word is I'm hiding near the docks."))
    result = await compose(_plan(), _context(provider))
    assert result == "Word is I'm hiding near the docks."
    assert provider.calls == 1


async def test_template_only_makes_zero_provider_calls():
    provider = FakeProvider(_result("irrelevant"))
    result = await compose(_plan(), _context(provider, degrade=DegradeLevel.TEMPLATE_ONLY))
    assert provider.calls == 0
    assert result.strip()


async def test_a_template_provider_instance_also_makes_zero_calls_to_itself():
    """D-52's TemplateProvider is a generic, plan-unaware fallback; the
    bank (kind/intent-aware) is used instead, never TemplateProvider.complete()."""
    provider = TemplateProvider(phrases=["should never be picked"])
    result = await compose(_plan(), _context(provider))
    assert result != "should never be picked"


async def test_an_over_length_completion_retries_exactly_once_then_truncates():
    long_text = " ".join(["word"] * (WORD_LIMIT + 10))
    provider = FakeProvider(sequence=[_result(long_text), _result(long_text)])
    result = await compose(_plan(), _context(provider))
    assert provider.calls == 2
    assert count(result) <= WORD_LIMIT


async def test_a_successful_shorter_retry_is_used_directly():
    long_text = " ".join(["word"] * (WORD_LIMIT + 10))
    short_text = "Right now I'm moving east."
    provider = FakeProvider(sequence=[_result(long_text), _result(short_text)])
    result = await compose(_plan(), _context(provider))
    assert result == short_text
    assert provider.calls == 2


async def test_a_retry_that_fails_still_truncates_the_original_completion():
    """The retry attempt failing must not discard the perfectly-usable (if
    verbose) first completion -- compose() has no failure mode."""
    long_text = " ".join(["word"] * (WORD_LIMIT + 10))
    provider = FakeProvider(
        sequence=[_result(long_text), LlmFailure(LlmFailureReason.TIMEOUT, "x")]
    )
    result = await compose(_plan(), _context(provider))
    assert provider.calls == 2
    assert count(result) <= WORD_LIMIT
    assert result.startswith("word")


async def test_a_third_call_never_happens_even_when_the_retry_is_also_over_length():
    long_text = " ".join(["word"] * (WORD_LIMIT + 10))
    provider = FakeProvider(sequence=[_result(long_text)] * 5)
    await compose(_plan(), _context(provider))
    assert provider.calls == 2


async def test_a_completion_containing_a_coordinate_falls_back_to_the_bank():
    provider = FakeProvider(_result("I am at 3,4 right now"))
    result = await compose(_plan(), _context(provider))
    assert result != "I am at 3,4 right now"
    assert_no_coordinates(result)  # must not raise


@pytest.mark.parametrize("reason", list(LlmFailureReason))
async def test_every_failure_reason_falls_back_to_the_bank(reason):
    provider = FakeProvider(LlmFailure(reason, "mocked"))
    result = await compose(_plan(), _context(provider))
    assert result.strip()
    assert provider.calls == 1


async def test_an_empty_completion_falls_back_to_the_bank():
    provider = FakeProvider(_result(""))
    result = await compose(_plan(), _context(provider))
    assert result.strip()


async def test_a_whitespace_only_completion_falls_back_to_the_bank():
    provider = FakeProvider(_result("   \n  "))
    result = await compose(_plan(), _context(provider))
    assert result.strip()


async def test_a_provider_that_raises_never_lets_the_exception_escape():
    provider = FakeProvider(boom=RuntimeError("socket exploded"))
    result = await compose(_plan(), _context(provider))
    assert result.strip()


async def test_barrier_and_capture_plans_compose_through_the_full_path():
    for plan in (declaration(ClaimKind.BARRIER), declaration(ClaimKind.CAPTURE)):
        provider = FakeProvider(_result("Barrier's up, right by the docks."))
        result = await compose(plan, _context(provider))
        assert result.strip()
        assert count(result) <= WORD_LIMIT
