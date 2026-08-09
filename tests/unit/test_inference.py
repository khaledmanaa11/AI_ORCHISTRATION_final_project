"""shared/inference.py: the decoder's output type and its one invariant."""

import pytest

from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import (
    NO_EVIDENCE,
    REGION_NAMES,
    Inference,
    Region,
    no_evidence_for,
)


def test_no_evidence_implicates_nothing_at_zero_confidence():
    assert NO_EVIDENCE.confidence == 0.0
    assert NO_EVIDENCE.region is None
    assert NO_EVIDENCE.cells == ()
    assert NO_EVIDENCE.direction is None
    assert NO_EVIDENCE.is_evidence is False


def test_inference_is_frozen():
    with pytest.raises(Exception):  # noqa: B017 -- dataclasses raises FrozenInstanceError
        NO_EVIDENCE.confidence = 1.0


@pytest.mark.parametrize("bad", [-0.01, 1.01, 2.0, -1.0])
def test_constructor_rejects_out_of_range_confidence(bad):
    with pytest.raises(ValueError, match="confidence must be in"):
        Inference(region=Region.NORTH, confidence=bad)


@pytest.mark.parametrize("good", [0.0, 0.5, 1.0])
def test_constructor_accepts_the_closed_unit_interval(good):
    assert Inference(region=Region.NORTH, confidence=good).confidence == good


def test_a_region_with_confidence_is_evidence():
    assert Inference(region=Region.SOUTHWEST, confidence=0.4).is_evidence is True


def test_cells_alone_are_evidence():
    assert Inference(cells=((1, 2),), confidence=0.4).is_evidence is True


def test_a_region_at_zero_confidence_is_not_evidence():
    """Zero confidence must leave the posterior untouched even when the
    sentence named somewhere -- otherwise the belief map multiplies by a
    likelihood the decoder itself does not stand behind."""
    assert Inference(region=Region.NORTH, confidence=0.0).is_evidence is False


def test_a_bare_heading_is_not_positional_evidence():
    """A heading is carried for 04-09's motion model but implicates no cell
    by itself, so it must not act as a positional likelihood."""
    carried = Inference(direction=DirectionWord.NORTH, confidence=0.0)
    assert carried.direction is DirectionWord.NORTH
    assert carried.is_evidence is False


def test_no_evidence_for_preserves_the_sentence():
    """04-14 has to tell 'we failed to read it' apart from 'it said nothing'."""
    carried = no_evidence_for("שלום")
    assert carried.raw_text == "שלום"
    assert carried.is_evidence is False
    assert carried.confidence == 0.0


def test_region_names_cover_every_member_in_declaration_order():
    assert tuple(region.value for region in Region) == REGION_NAMES
    assert len(REGION_NAMES) == len(set(REGION_NAMES))


def test_regions_are_lowercase_single_words():
    """The schema enum, the prompt and 04-08's claims all share these strings."""
    for name in REGION_NAMES:
        assert name == name.lower()
        assert " " not in name
