"""shared/deception_types.py: a disqualifying lie must not be constructible.

The point of these tests is that the CONSTRUCTOR is the gate. If the check
ever moves into a helper a caller can skip, `test_replace_cannot_bypass_the_gate`
is the one that fails.
"""

import dataclasses

import pytest

from pursuit.shared.deception_types import (
    ALWAYS_TRUE_KINDS,
    ClaimKind,
    DeceptionPlan,
    Intent,
)
from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import Region


def truthful_location(region=Region.NORTH) -> DeceptionPlan:
    return DeceptionPlan(
        intent=Intent.TRUTH,
        kind=ClaimKind.LOCATION,
        claimed_region=region,
        true_region=region,
    )


@pytest.mark.parametrize("kind", sorted(ALWAYS_TRUE_KINDS, key=lambda k: k.value))
def test_an_always_true_kind_cannot_be_a_lie(kind):
    with pytest.raises(ValueError, match="can never be a lie"):
        DeceptionPlan(intent=Intent.LIE, kind=kind)


def test_the_barrier_refusal_names_its_rules():
    with pytest.raises(ValueError, match="rules 15/16"):
        DeceptionPlan(intent=Intent.LIE, kind=ClaimKind.BARRIER)


def test_the_capture_refusal_names_its_rules_and_the_sanction():
    with pytest.raises(ValueError, match="rules 21/22"):
        DeceptionPlan(intent=Intent.LIE, kind=ClaimKind.CAPTURE)
    with pytest.raises(ValueError, match="no appeal"):
        DeceptionPlan(intent=Intent.LIE, kind=ClaimKind.CAPTURE)


@pytest.mark.parametrize("kind", sorted(ALWAYS_TRUE_KINDS, key=lambda k: k.value))
def test_an_always_true_kind_is_fine_as_the_truth(kind):
    assert DeceptionPlan(intent=Intent.TRUTH, kind=kind).is_lie is False


def test_replace_cannot_bypass_the_gate():
    """dataclasses.replace re-runs __post_init__, so there is no back door."""
    honest = DeceptionPlan(intent=Intent.TRUTH, kind=ClaimKind.CAPTURE)
    with pytest.raises(ValueError, match="can never be a lie"):
        dataclasses.replace(honest, intent=Intent.LIE)


def test_a_truthful_location_claim_must_state_the_truth():
    """A plan flagged `truth` that claims the wrong sector is a lie under a
    truthful flag -- the one thing an auditor can actually catch us at."""
    with pytest.raises(ValueError, match="is not the true value"):
        DeceptionPlan(
            intent=Intent.TRUTH,
            kind=ClaimKind.LOCATION,
            claimed_region=Region.NORTH,
            true_region=Region.SOUTH,
        )


def test_a_truthful_heading_claim_must_state_the_truth():
    with pytest.raises(ValueError, match="is not the true value"):
        DeceptionPlan(
            intent=Intent.TRUTH,
            kind=ClaimKind.HEADING,
            claimed_heading=DirectionWord.NORTH,
            true_heading=DirectionWord.SOUTH,
        )


def test_a_lie_may_of_course_differ_from_the_truth():
    plan = DeceptionPlan(
        intent=Intent.LIE,
        kind=ClaimKind.LOCATION,
        claimed_region=Region.NORTH,
        true_region=Region.SOUTH,
    )
    assert plan.is_lie is True
    assert plan.claimed_region is Region.NORTH
    assert plan.true_region is Region.SOUTH


def test_the_plan_records_both_the_claim_and_the_truth():
    """The event log has to prove the flag was honest about itself."""
    plan = truthful_location(Region.EAST)
    assert plan.claimed_region is Region.EAST
    assert plan.true_region is Region.EAST


def test_a_truthful_claim_with_no_recorded_truth_is_allowed():
    """Turn zero, before a true value is known, must not blow up."""
    assert DeceptionPlan(
        intent=Intent.TRUTH, kind=ClaimKind.LOCATION, claimed_region=Region.NORTH
    ).is_lie is False


def test_the_plan_is_frozen():
    with pytest.raises(Exception):  # noqa: B017 -- FrozenInstanceError
        truthful_location().intent = Intent.LIE


def test_the_plan_carries_no_text_field():
    """04-10 owns phrasing; this type owns meaning. If a text field appears
    here, the intent flag stops being decided before the text exists."""
    assert not set(vars(truthful_location())) & {"text", "hint", "phrase", "message"}


def test_intent_is_the_same_object_the_wire_serialises():
    """One definition -- network/hint_payload.py re-exports, never redeclares."""
    from pursuit.network.hint_payload import Intent as WireIntent

    assert WireIntent is Intent
