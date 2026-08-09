"""Tests for the Sec4.4 contradiction test (Task 1, D-51)."""

import pathlib

import pytest

from pursuit.shared.belief_config import load_belief_config
from pursuit.shared.inference import NO_EVIDENCE, Inference, Region
from pursuit.shared.scent_config import load_scent_model
from pursuit.strategy.regions import region_of
from pursuit.strategy.scent import expected_strength_after
from pursuit.strategy.scent_check import contradicts
from pursuit.strategy.scentfield import ScentField

_CONFIG_DIR = pathlib.Path(__file__).parents[3] / "config"
POLICE_BELIEF = _CONFIG_DIR / "police" / "belief.json"
POLICE_SCENT = _CONFIG_DIR / "police" / "scent.json"
_BOARD_SIZE = 7


@pytest.fixture(scope="module")
def model():
    return load_scent_model(POLICE_SCENT)


@pytest.fixture
def belief_cfg():
    return load_belief_config(POLICE_BELIEF)


def _field_with_peak_at(model, cell) -> ScentField:
    """A field carrying exactly the book's worked-example strength (0.81,
    one decay step past a fresh deposit) at `cell` and nothing else."""
    field = ScentField(model=model, board_size=_BOARD_SIZE)
    field.opponent = {cell: expected_strength_after(model, 1)}
    return field


def test_book_worked_example_a_claim_away_from_the_trail_scores_near_the_maximum(
    model, belief_cfg
):
    """Sec4.4, p.30 (PDF 46): thief's trail betrays the south-east corner;
    claiming "north" is the book's own maximum-confidence lie detection."""
    field = _field_with_peak_at(model, (6, 6))
    assert region_of((6, 6), _BOARD_SIZE) is Region.SOUTHEAST
    claim = Inference(region=Region.NORTH, confidence=0.9)
    assert contradicts(claim, field, model, belief_cfg) == pytest.approx(1.0)


def test_a_claim_matching_the_trail_scores_zero(model, belief_cfg):
    field = _field_with_peak_at(model, (6, 6))
    claim = Inference(region=Region.SOUTHEAST, confidence=0.9)
    assert contradicts(claim, field, model, belief_cfg) == 0.0


def test_an_all_zero_field_scores_zero_for_every_claim(model, belief_cfg):
    empty = ScentField(model=model, board_size=_BOARD_SIZE)
    for region in (Region.NORTH, Region.SOUTHEAST, Region.CENTER):
        claim = Inference(region=region, confidence=0.9)
        assert contradicts(claim, empty, model, belief_cfg) == 0.0


def test_a_region_less_inference_scores_zero(model, belief_cfg):
    field = _field_with_peak_at(model, (6, 6))
    heading_only = Inference(confidence=0.0)
    assert contradicts(heading_only, field, model, belief_cfg) == 0.0


def test_no_evidence_singleton_scores_zero(model, belief_cfg):
    field = _field_with_peak_at(model, (6, 6))
    assert contradicts(NO_EVIDENCE, field, model, belief_cfg) == 0.0


def test_a_sub_epsilon_peak_is_treated_as_no_information(model, belief_cfg):
    field = ScentField(model=model, board_size=_BOARD_SIZE)
    field.emit_opponent((0, 0))
    for _ in range(30):
        field.advance()
    peak = field.freshest("opponent")
    assert peak is not None
    assert 0.0 < field.strength("opponent", peak) < belief_cfg.epsilon
    claim = Inference(region=Region.NORTH, confidence=0.9)
    assert contradicts(claim, field, model, belief_cfg) == 0.0


def test_explicit_cells_are_used_over_region_when_both_present(model, belief_cfg):
    field = _field_with_peak_at(model, (6, 6))
    claim = Inference(region=Region.SOUTHEAST, cells=((0, 0),), confidence=0.9)
    # `cells` names (0, 0), far from the trail -- even though `region` names
    # the correct sector, the explicit cell list is what gets checked.
    assert contradicts(claim, field, model, belief_cfg) == pytest.approx(1.0)


def test_score_is_always_bounded_in_the_unit_interval(model, belief_cfg):
    field = _field_with_peak_at(model, (3, 3))
    for region in Region:
        claim = Inference(region=region, confidence=0.9)
        score = contradicts(claim, field, model, belief_cfg)
        assert 0.0 <= score <= 1.0
