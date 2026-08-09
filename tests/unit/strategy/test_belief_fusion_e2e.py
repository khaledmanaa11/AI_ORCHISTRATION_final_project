"""End-to-end belief-fusion tests closing the whole D-40/D-42/D-51 loop
(verification item 4): scent and a hint stream feeding the SAME BeliefMap,
reliability moving from scent_check.contradicts(), Sec4.4 reproduced.

Split out of test_belief_hint.py at the 150-code-line ceiling.
"""

import pathlib

import pytest

from pursuit.shared.belief_config import load_belief_config
from pursuit.shared.config import load_game_params
from pursuit.shared.inference import NO_EVIDENCE, Inference, Region
from pursuit.shared.scent_config import load_scent_model
from pursuit.shared.state import GameState
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.belief_hint import hint_likelihood
from pursuit.strategy.belief_scent import scent_likelihood
from pursuit.strategy.regions import region_of
from pursuit.strategy.reliability import Reliability
from pursuit.strategy.scent_check import contradicts
from pursuit.strategy.scentfield import ScentField

_CONFIG_DIR = pathlib.Path(__file__).parents[3] / "config"
POLICE_BELIEF = _CONFIG_DIR / "police" / "belief.json"
POLICE_SCENT = _CONFIG_DIR / "police" / "scent.json"
POLICE_GAME = _CONFIG_DIR / "police" / "game_params.json"


@pytest.fixture(scope="module")
def model():
    return load_scent_model(POLICE_SCENT)


@pytest.fixture
def belief_cfg():
    return load_belief_config(POLICE_BELIEF)


@pytest.fixture(scope="module")
def params():
    return load_game_params(POLICE_GAME)


def _state(params, thief=(6, 6)):
    return GameState(cop=(0, 0), thief=thief, barriers=frozenset(), barriers_placed=0, turn=0)


def test_posterior_stays_valid_after_every_combination_of_the_two_likelihoods(
    model, belief_cfg, params
):
    field = ScentField(model=model, board_size=params.board_size)
    belief = BeliefMap(params.board_size, "thief")
    reliability = Reliability(belief_cfg.reliability)
    state = _state(params)
    for region in (Region.NORTH, Region.SOUTHEAST, None):
        field.emit_opponent((6, 6))
        scent_grid = scent_likelihood(field, "thief", state, params, model, belief_cfg)
        inference = (
            Inference(region=region, confidence=0.8) if region is not None else NO_EVIDENCE
        )
        hint_grid = hint_likelihood(inference, reliability, params.board_size, belief_cfg)
        belief.update(scent_grid)
        belief.update(hint_grid)
        posterior = belief.posterior()
        assert sum(sum(row) for row in posterior) == pytest.approx(1.0)
        assert all(v >= 0.0 for row in posterior for v in row)
        belief.predict(state, params)
        field.advance()


def test_contradictory_scent_and_hint_land_nearer_the_scent_reading(model, belief_cfg, params):
    """D-40's asymmetry, asserted numerically: scent claims south-east
    (where the trail actually is), the hint claims north-west (a lie) --
    the fused posterior favours the scent reading, not the claim."""
    state = _state(params)
    field = ScentField(model=model, board_size=params.board_size)
    field.emit_opponent((6, 6))
    assert region_of((6, 6), params.board_size) is Region.SOUTHEAST

    scent_grid = scent_likelihood(field, "thief", state, params, model, belief_cfg)
    hint = Inference(region=Region.NORTHWEST, confidence=1.0)
    hint_grid = hint_likelihood(hint, Reliability(belief_cfg.reliability), params.board_size, belief_cfg)

    belief = BeliefMap(params.board_size, "thief")
    belief.update(scent_grid)
    belief.update(hint_grid)
    assert belief.argmax() == (6, 6)


def _run_ten_turns(model, belief_cfg, params, claimed_region):
    """Ten joint turns: the opponent truly sits at (6, 6) (south-east) the
    whole time, and sends a hint claiming `claimed_region` every turn. Scent
    and the hint both feed the SAME BeliefMap; reliability is updated from
    scent_check.contradicts() each turn. Returns the reliability trajectory
    (prior first, one value per turn after) and the final argmax."""
    true_cell = (6, 6)
    state = _state(params, thief=true_cell)
    field = ScentField(model=model, board_size=params.board_size)
    belief = BeliefMap(params.board_size, "thief")
    reliability = Reliability(belief_cfg.reliability)
    trajectory = [reliability.value]
    for _ in range(10):
        field.emit_opponent(true_cell)
        scent_grid = scent_likelihood(field, "thief", state, params, model, belief_cfg)
        hint = Inference(region=claimed_region, confidence=0.9)
        score = contradicts(hint, field, model, belief_cfg)
        hint_grid = hint_likelihood(hint, reliability, params.board_size, belief_cfg)
        belief.update(scent_grid)
        belief.update(hint_grid)
        reliability.observe(score)
        trajectory.append(reliability.value)
        belief.predict(state, params)
        field.advance()
    return trajectory, belief.argmax()


def test_a_consistent_hint_stream_keeps_reliability_at_the_prior(model, belief_cfg, params):
    trajectory, argmax = _run_ten_turns(model, belief_cfg, params, Region.SOUTHEAST)
    assert all(value == belief_cfg.reliability.prior for value in trajectory)
    assert argmax == (6, 6)


def test_a_contradictory_hint_stream_drives_reliability_to_r_min_and_argmax_follows_scent(
    model, belief_cfg, params
):
    trajectory, argmax = _run_ten_turns(model, belief_cfg, params, Region.NORTHWEST)
    assert trajectory[0] == belief_cfg.reliability.prior
    assert trajectory[-1] == belief_cfg.reliability.r_min
    # Monotonically non-increasing: every lie only ever pulls trust down here.
    assert all(a >= b for a, b in zip(trajectory[:-1], trajectory[1:], strict=True))
    # Sec4.4's whole point: even under a sustained lie, the posterior tracks
    # the trail, not the claim.
    assert argmax == (6, 6)
