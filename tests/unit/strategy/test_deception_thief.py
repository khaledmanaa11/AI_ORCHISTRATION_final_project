"""strategy/deception_thief.py: D-37's danger-adaptive lying.

The thief lies when it matters, tells enough truth to stay believed, and does
not contradict its own scent trail.
"""

import pathlib
import random

import pytest

from pursuit.shared.deception_config import load_deception_config
from pursuit.shared.deception_types import ClaimKind, Intent
from pursuit.shared.inference import Region
from pursuit.shared.scent_config import load_scent_model
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.deception_thief import (
    expected_opponent_distance,
    lie_probability,
    plan_thief_claim,
)
from pursuit.strategy.regions import region_of
from pursuit.strategy.scentfield import ScentField

_CONFIG = pathlib.Path(__file__).parents[3] / "config" / "police"
DRAWS = 400


@pytest.fixture
def config():
    return load_deception_config(_CONFIG / "deception.json")


def belief_on(board_size: int, cells) -> BeliefMap:
    """A belief carrying equal mass on `cells` and none elsewhere."""
    belief = BeliefMap(board_size=board_size, role="cop")
    belief.update(
        [[1.0 if (r, c) in cells else 0.0 for c in range(board_size)] for r in range(board_size)]
    )
    return belief


def lie_rate(state, params, belief, config, seed=0, scent=None) -> float:
    """Empirical lie frequency over many seeded draws."""
    rng = random.Random(seed)
    lies = sum(
        plan_thief_claim(state, params, belief, rng, config, scent=scent).is_lie
        for _ in range(DRAWS)
    )
    return lies / DRAWS


def test_lie_probability_never_reaches_certainty(config):
    """D-37's truth floor: an always-lying agent is as readable as an
    always-truthful one, and the opponent's reliability coefficient collapses
    either way."""
    assert lie_probability(0.0, config) == config.max_lie_probability
    assert lie_probability(0.0, config) < 1.0


def test_lie_probability_never_reaches_zero_at_long_range(config):
    """A configured non-zero floor keeps the long-range claims unreadable."""
    assert lie_probability(999.0, config) == config.min_lie_probability
    assert lie_probability(999.0, config) > 0.0


def test_lie_probability_falls_monotonically_with_distance(config):
    sweep = [lie_probability(d / 2, config) for d in range(0, 40)]
    assert all(a >= b for a, b in zip(sweep, sweep[1:], strict=False))


def test_lie_probability_strictly_falls_inside_the_ramp(config):
    """Between the two thresholds the response must actually respond."""
    low = config.danger_distance + (config.safe_distance - config.danger_distance) / 4
    high = config.danger_distance + 3 * (config.safe_distance - config.danger_distance) / 4
    assert lie_probability(low, config) > lie_probability(high, config)


def test_expected_distance_uses_the_whole_posterior_not_the_argmax(default_params):
    """A bimodal belief with one close mode is exactly where the argmax
    misleads -- it reports the likeliest cell and ignores the rest of the mass."""
    size = default_params.board_size
    near, far = (0, 1), (size - 1, size - 1)
    belief = belief_on(size, {near, far})
    own = (0, 0)

    argmax_distance = abs(belief.argmax()[0] - own[0]) + abs(belief.argmax()[1] - own[1])
    expected = expected_opponent_distance(belief, own, size)
    assert expected > argmax_distance
    assert expected == pytest.approx((1 + (size - 1) * 2) / 2)


def test_the_thief_lies_more_when_the_cop_is_believed_close(start_state, default_params, config):
    size = default_params.board_size
    thief = start_state.thief
    close = belief_on(size, {(thief[0], min(thief[1] + 1, size - 1))})
    far = belief_on(size, {(0, 0) if thief != (0, 0) else (size - 1, size - 1)})

    assert lie_rate(start_state, default_params, close, config) > lie_rate(
        start_state, default_params, far, config
    )


def test_truths_are_still_sprinkled_at_maximum_danger(start_state, default_params, config):
    """The floor is a measured property of the policy, not just of the curve."""
    size = default_params.board_size
    adjacent = belief_on(size, {start_state.thief})
    rate = lie_rate(start_state, default_params, adjacent, config)
    assert rate < 1.0
    assert rate == pytest.approx(config.max_lie_probability, abs=0.1)


def test_lies_still_occur_at_maximum_safety(start_state, default_params, config):
    size = default_params.board_size
    far_corner = belief_on(size, {(0, 0) if start_state.thief != (0, 0) else (size - 1, size - 1)})
    assert lie_rate(start_state, default_params, far_corner, config) > 0.0


def test_a_truthful_claim_states_the_true_sector(start_state, default_params, config):
    size = default_params.board_size
    belief = belief_on(size, {(0, 0)})
    rng = random.Random(1)
    for _ in range(DRAWS):
        plan = plan_thief_claim(start_state, default_params, belief, rng, config)
        assert plan.kind is ClaimKind.LOCATION
        assert plan.true_region is region_of(start_state.thief, size)
        if plan.intent is Intent.TRUTH:
            assert plan.claimed_region is plan.true_region


def test_a_lie_never_claims_the_true_sector(start_state, default_params, config):
    size = default_params.board_size
    belief = belief_on(size, {start_state.thief})
    rng = random.Random(2)
    for _ in range(DRAWS):
        plan = plan_thief_claim(start_state, default_params, belief, rng, config)
        if plan.is_lie:
            assert plan.claimed_region is not plan.true_region


def test_a_lie_does_not_claim_the_sector_its_own_trail_betrays(
    start_state, default_params, config
):
    """Book Sec4.4's contradiction test, run on ourselves before committing:
    a claim landing on our freshest trail is a confession, not a lie."""
    size = default_params.board_size
    model = load_scent_model(_CONFIG / "scent.json")
    scent = ScentField(model=model, board_size=size)
    trail_cell = (0, 0)
    scent.emit_own(trail_cell)
    betrayed = region_of(trail_cell, size)

    belief = belief_on(size, {start_state.thief})
    rng = random.Random(3)
    lied = False
    for _ in range(DRAWS):
        plan = plan_thief_claim(start_state, default_params, belief, rng, config, scent=scent)
        if plan.is_lie:
            lied = True
            assert plan.claimed_region is not betrayed
    assert lied, "the setup must actually produce lies for this to prove anything"


def test_an_empty_scent_field_degrades_instead_of_failing(start_state, default_params, config):
    """Turn zero: no trail yet. The turn must still carry a hint (LANG-01)."""
    size = default_params.board_size
    scent = ScentField(model=load_scent_model(_CONFIG / "scent.json"), board_size=size)
    plan = plan_thief_claim(
        start_state, default_params, belief_on(size, {(0, 0)}), random.Random(4), config, scent=scent
    )
    assert plan is not None
    assert plan.claimed_region in set(Region)


def test_identical_seeds_reproduce_identical_sequences(start_state, default_params, config):
    size = default_params.board_size
    belief = belief_on(size, {start_state.thief})

    def run(seed):
        rng = random.Random(seed)
        return [
            plan_thief_claim(start_state, default_params, belief, rng, config)
            for _ in range(DRAWS)
        ]

    assert run(7) == run(7)
    assert run(7) != run(8)
