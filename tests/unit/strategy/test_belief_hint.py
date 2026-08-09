"""Tests for the D-40 hint likelihood (Task 3): the mixing formula itself,
confidence handling, and the region/cells/heading translation.

The end-to-end Sec4.4 reproduction (verification item 4 -- scent + a hint
stream over several turns, reliability moving, the fused posterior) lives in
test_belief_fusion_e2e.py, split out at the 150-code-line ceiling.
"""

import pathlib

import pytest

from pursuit.shared.belief_config import load_belief_config
from pursuit.shared.config import load_game_params
from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import NO_EVIDENCE, Inference, Region
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.belief_hint import _implied_distribution, _tilt, hint_likelihood
from pursuit.strategy.reliability import Reliability

_CONFIG_DIR = pathlib.Path(__file__).parents[3] / "config"
POLICE_BELIEF = _CONFIG_DIR / "police" / "belief.json"
POLICE_GAME = _CONFIG_DIR / "police" / "game_params.json"


@pytest.fixture
def belief_cfg():
    return load_belief_config(POLICE_BELIEF)


@pytest.fixture(scope="module")
def params():
    return load_game_params(POLICE_GAME)


def test_no_evidence_leaves_the_posterior_exactly_unchanged(belief_cfg, params):
    belief = BeliefMap(params.board_size, "thief")
    belief.observe_exact((3, 3))
    before = belief.posterior()
    grid = hint_likelihood(NO_EVIDENCE, Reliability(belief_cfg.reliability), params.board_size, belief_cfg)
    belief.update(grid)
    assert belief.posterior() == before


def test_a_confident_hint_shifts_the_argmax_but_zeroes_no_cell(belief_cfg, params):
    belief = BeliefMap(params.board_size, "thief")
    inference = Inference(region=Region.NORTHWEST, confidence=1.0)
    grid = hint_likelihood(inference, Reliability(belief_cfg.reliability), params.board_size, belief_cfg)
    belief.update(grid)
    posterior = belief.posterior()
    assert belief.argmax() == (0, 0)
    assert all(value > 0.0 for row in posterior for value in row)


def test_lowering_reliability_shrinks_the_shift(belief_cfg, params):
    inference = Inference(region=Region.NORTHWEST, confidence=1.0)

    trusting = Reliability(belief_cfg.reliability)
    wary = Reliability(belief_cfg.reliability)
    for _ in range(50):
        wary.observe(1.0)
    assert wary.value < trusting.value

    trusting_grid = hint_likelihood(inference, trusting, params.board_size, belief_cfg)
    wary_grid = hint_likelihood(inference, wary, params.board_size, belief_cfg)
    # The claimed cell's own likelihood value shrinks as reliability drops.
    assert wary_grid[0][0] < trusting_grid[0][0]


def test_confidence_zero_returns_an_all_zero_grid(belief_cfg, params):
    inference = Inference(region=Region.NORTH, confidence=0.0)
    grid = hint_likelihood(inference, Reliability(belief_cfg.reliability), params.board_size, belief_cfg)
    assert all(value == 0.0 for row in grid for value in row)


def test_a_bare_heading_with_no_region_or_cells_produces_no_shift(belief_cfg, params):
    """A positive-confidence, region-less, cells-less heading is a shape the
    real decoder never emits (Inference.is_evidence), but hint_likelihood
    must still degrade safely -- falling through to the flat uniform mix."""
    inference = Inference(direction=DirectionWord.NORTH, confidence=0.5)
    grid = hint_likelihood(inference, Reliability(belief_cfg.reliability), params.board_size, belief_cfg)
    values = {round(v, 12) for row in grid for v in row}
    assert len(values) == 1


@pytest.mark.parametrize(
    ("direction", "favoured", "disfavoured"),
    [
        (DirectionWord.NORTH, (0, 3), (2, 3)),
        (DirectionWord.SOUTH, (2, 3), (0, 3)),
        (DirectionWord.EAST, (0, 4), (0, 3)),
        (DirectionWord.WEST, (0, 3), (0, 4)),
    ],
)
def test_a_heading_alongside_a_region_tilts_within_it_without_zeroing_any_cell(
    direction, favoured, disfavoured, params
):
    """A heading riding alongside a region claim biases the implied
    distribution toward the named direction, but every cell in the claimed
    region keeps positive mass -- both `favoured` and `disfavoured` are
    inside Region.NORTH on the 7x7 board."""
    inference = Inference(region=Region.NORTH, direction=direction, confidence=0.9)
    implied = _implied_distribution(inference, params.board_size)
    assert implied[favoured] > implied[disfavoured] > 0.0
    assert sum(implied.values()) == pytest.approx(1.0)


def test_a_stay_heading_alongside_a_region_produces_no_tilt(params):
    inference = Inference(region=Region.NORTH, direction=DirectionWord.STAY, confidence=0.9)
    implied = _implied_distribution(inference, params.board_size)
    assert len({round(v, 12) for v in implied.values()}) == 1


@pytest.mark.parametrize(
    ("direction", "near_cell", "far_cell"),
    [
        (DirectionWord.NORTH, (0, 0), (6, 0)),
        (DirectionWord.SOUTH, (6, 0), (0, 0)),
        (DirectionWord.EAST, (0, 6), (0, 0)),
        (DirectionWord.WEST, (0, 0), (0, 6)),
    ],
)
def test_tilt_ranks_cells_monotonically_along_the_claimed_axis(direction, near_cell, far_cell):
    assert _tilt(near_cell, direction) > _tilt(far_cell, direction)


def test_explicit_cells_are_used_over_region(belief_cfg, params):
    inference = Inference(region=Region.SOUTHEAST, cells=((0, 0),), confidence=1.0)
    grid = hint_likelihood(inference, Reliability(belief_cfg.reliability), params.board_size, belief_cfg)
    belief = BeliefMap(params.board_size, "thief")
    belief.update(grid)
    assert belief.argmax() == (0, 0)
