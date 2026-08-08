"""strategy/deception_cop.py: D-38's herding lies.

The cop's claims are chosen for the movement they CAUSE, not for the
concealment they buy, and they fall back to the truth when they buy nothing.
"""

import pathlib
import random

import pytest

from pursuit.shared.config import load_game_params
from pursuit.shared.deception_config import load_deception_config
from pursuit.shared.deception_types import ClaimKind, Intent
from pursuit.shared.inference import Region
from pursuit.shared.state import GameState
from pursuit.strategy.deception_cop import _believing_step, _herded_value, plan_cop_claim
from pursuit.strategy.features import FEATURE_COUNT, _degree
from pursuit.strategy.graphcache import passable
from pursuit.strategy.regions import region_center, region_of
from pursuit.strategy.weights import PRIOR

_CONFIG = pathlib.Path(__file__).parents[3] / "config" / "police"
FLAT_WEIGHTS = (0.0,) * FEATURE_COUNT


@pytest.fixture
def config():
    return load_deception_config(_CONFIG / "deception.json")


@pytest.fixture
def params():
    return load_game_params(_CONFIG / "game_params.json")


def open_board(params, cop=(3, 0), thief=(3, 3)) -> GameState:
    return GameState(cop=cop, thief=thief, barriers=frozenset(), barriers_placed=0, turn=5)


def herding_board(params) -> GameState:
    """A position found by search, then frozen, where the lever measurably
    bites: the truthful claim sends a believing thief to a degree-4 cell and
    the chosen lie sends it to a degree-3 one."""
    walls = frozenset(
        {(0, 3), (0, 5), (1, 5), (2, 3), (2, 6), (3, 4), (5, 2), (6, 0)}
    )
    return GameState(
        cop=(1, 4), thief=(2, 0), barriers=walls, barriers_placed=len(walls), turn=5
    )


def gains(state, params) -> dict:
    """Herding gain over the truthful claim, per candidate sector."""
    truth = region_of(state.cop, params.board_size)
    baseline = _herded_value(truth, state, params, PRIOR)
    return {
        region: _herded_value(region, state, params, PRIOR) - baseline
        for region in Region
        if region is not truth
    }


def test_the_believing_thief_responds_to_the_believed_position(params):
    """If the claim did not change the step, the whole channel is inert."""
    state = open_board(params)
    steps = {
        _believing_step(state, params, region_center(region, params.board_size), PRIOR)
        for region in Region
    }
    assert len(steps) > 1


def test_the_believing_thief_only_ever_picks_a_legal_destination(params):
    from pursuit.sdk.actions import thief_actions

    state = herding_board(params)
    legal = set(thief_actions(state, params))
    for region in Region:
        step = _believing_step(state, params, region_center(region, params.board_size), PRIOR)
        assert step in legal


def test_the_chosen_lie_is_the_best_scoring_claim(params, config):
    state = open_board(params)
    plan = plan_cop_claim(state, params, None, random.Random(0), config)
    assert plan.is_lie, "this board must produce a lie for the assertion to mean anything"
    scored = gains(state, params)
    assert scored[plan.claimed_region] == max(scored.values())


def test_it_only_lies_when_the_gain_clears_the_threshold(params, config):
    state = open_board(params)
    plan = plan_cop_claim(state, params, None, random.Random(0), config)
    assert gains(state, params)[plan.claimed_region] > config.min_herding_gain


def test_when_no_claim_improves_on_the_truth_it_tells_the_truth(params, config):
    """A flat evaluation makes every claim worth exactly the same. A lie that
    buys nothing still spends the credibility the next lie needs."""
    state = open_board(params)
    plan = plan_cop_claim(state, params, None, random.Random(0), config, weights=FLAT_WEIGHTS)
    assert plan.intent is Intent.TRUTH
    assert plan.claimed_region is plan.true_region is region_of(state.cop, params.board_size)


def test_a_prohibitive_threshold_forces_the_truth(params, config):
    """The gain threshold is the knob, and it must actually be honoured."""
    import dataclasses

    strict = dataclasses.replace(config, min_herding_gain=1e6)
    plan = plan_cop_claim(open_board(params), params, None, random.Random(0), strict)
    assert plan.intent is Intent.TRUTH


def test_the_lie_drives_the_thief_somewhere_less_connected(params, config):
    """The plan's own criterion, at the one-step lookahead it commits to: a
    believing thief ends up on a cell with fewer ways out than the truthful
    claim would have given it."""
    state = herding_board(params)
    plan = plan_cop_claim(state, params, None, random.Random(0), config)
    assert plan.is_lie

    free = passable(state.barriers, params.board_size)
    board = params.board_size
    truth_step = _believing_step(
        state, params, region_center(region_of(state.cop, board), board), PRIOR
    )
    lie_step = _believing_step(state, params, region_center(plan.claimed_region, board), PRIOR)
    assert lie_step != truth_step
    assert _degree(free, lie_step) < _degree(free, truth_step)


def test_the_cop_never_proposes_a_barrier_or_capture_claim(params, config):
    """Task 1's constructor gate is not the only defence: this policy does not
    generate the always-true kinds at all."""
    for cop in [(0, 0), (3, 3), (6, 6), (1, 4)]:
        state = open_board(params, cop=cop, thief=(2, 2) if cop != (2, 2) else (5, 5))
        plan = plan_cop_claim(state, params, None, random.Random(0), config)
        assert plan.kind is ClaimKind.LOCATION


def test_a_lie_never_claims_the_true_sector(params, config):
    state = open_board(params)
    plan = plan_cop_claim(state, params, None, random.Random(0), config)
    assert plan.true_region is region_of(state.cop, params.board_size)
    if plan.is_lie:
        assert plan.claimed_region is not plan.true_region


@pytest.mark.parametrize("seed", [0, 1, 99, 12345])
def test_the_choice_is_deterministic_regardless_of_the_draw(params, config, seed):
    """The cop's policy takes an RNG for interface symmetry only; the same
    board must give the same claim however the RNG is seeded."""
    state = herding_board(params)
    reference = plan_cop_claim(state, params, None, random.Random(0), config)
    assert plan_cop_claim(state, params, None, random.Random(seed), config) == reference


def test_trained_weights_are_used_when_supplied(params, config):
    """The policy must score with the agent's actual evaluation, not silently
    with the prior -- otherwise a trained cop herds on someone else's opinion."""
    state = open_board(params)
    with_prior = plan_cop_claim(state, params, None, random.Random(0), config, weights=PRIOR)
    with_flat = plan_cop_claim(state, params, None, random.Random(0), config, weights=FLAT_WEIGHTS)
    assert with_prior != with_flat
