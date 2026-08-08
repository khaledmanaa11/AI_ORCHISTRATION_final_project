"""Tests for the D-42 scent-likelihood inversion (Task 3).

belief.json loader tests live in tests/unit/test_belief_config.py (a
150-code-line split, see that file's docstring and this plan's SUMMARY.md).
"""

import pathlib

import pytest

from pursuit.shared.belief_config import load_belief_config
from pursuit.shared.config import GameParams
from pursuit.shared.scent_config import load_scent_model
from pursuit.shared.state import GameState
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.belief_scent import inverted_age, scent_likelihood
from pursuit.strategy.scent import decay
from pursuit.strategy.scentfield import ScentField

_CONFIG_DIR = pathlib.Path(__file__).parents[3] / "config"
POLICE_BELIEF = _CONFIG_DIR / "police" / "belief.json"
POLICE_SCENT = _CONFIG_DIR / "police" / "scent.json"


@pytest.fixture(scope="module")
def model():
    return load_scent_model(POLICE_SCENT)


@pytest.fixture
def belief_cfg():
    return load_belief_config(POLICE_BELIEF)


@pytest.fixture
def params(default_params) -> GameParams:
    return default_params


def _state():
    return GameState(cop=(0, 0), thief=(3, 3), barriers=frozenset(), barriers_placed=0, turn=0)


def test_inverted_age_zero_at_source_strength(model, belief_cfg):
    assert inverted_age(model.source, model, belief_cfg.age_cap) == 0


@pytest.mark.parametrize("k", [1, 3, 5])
def test_inverted_age_matches_k_decays(model, belief_cfg, k):
    field = {(0, 0): model.source}
    for _ in range(k):
        field = decay(field, model)
    assert inverted_age(field[(0, 0)], model, belief_cfg.age_cap) == k


def test_inverted_age_is_capped_at_the_configured_maximum(model, belief_cfg):
    assert inverted_age(0.0, model, belief_cfg.age_cap) <= belief_cfg.age_cap


def test_trail_below_epsilon_everywhere_leaves_the_prior_unchanged(model, belief_cfg, params):
    """A neutral (all-1.0) likelihood still round-trips through renormalise
    -- unlike a literal all-zero likelihood, this is not the early-return
    path, so the comparison must tolerate float rounding, not require
    bit-for-bit equality."""
    field = ScentField(model=model, board_size=params.board_size)
    likelihood = scent_likelihood(field, "thief", _state(), params, model, belief_cfg)
    assert all(v == 1.0 for row in likelihood for v in row)
    belief = BeliefMap(params.board_size, "thief")
    before = belief.posterior()
    belief.update(likelihood)
    after = belief.posterior()
    for before_row, after_row in zip(before, after, strict=True):
        for expected, actual in zip(before_row, after_row, strict=True):
            assert actual == pytest.approx(expected)


def test_a_residual_but_sub_epsilon_peak_is_also_neutral(model, belief_cfg, params):
    """scent.py's own prune floor (1e-6) is far below belief.json's epsilon
    (0.05): a trail can still hold a nonzero, non-pruned `freshest()` peak
    that is nonetheless too faint to trust -- that peak must be neutral
    too, not just a fully-empty field (the branch the test above covers)."""
    field = ScentField(model=model, board_size=params.board_size)
    field.emit_opponent((0, 0))
    for _ in range(28):
        field.advance()
    peak_strength = field.strength("opponent", field.freshest("opponent"))
    assert 0.0 < peak_strength < belief_cfg.epsilon
    likelihood = scent_likelihood(field, "thief", _state(), params, model, belief_cfg)
    assert all(v == 1.0 for row in likelihood for v in row)


def test_fresh_trail_concentrates_exactly_at_its_source(model, belief_cfg, params):
    field = ScentField(model=model, board_size=params.board_size)
    field.emit_opponent((3, 3))
    likelihood = scent_likelihood(field, "thief", _state(), params, model, belief_cfg)
    belief = BeliefMap(params.board_size, "thief")
    belief.update(likelihood)
    assert belief.argmax() == (3, 3)


@pytest.mark.parametrize("origin", [(3, 3), (1, 1), (0, 0), (5, 5)])
def test_decisive_a_stale_trail_never_argmaxes_at_its_source(model, belief_cfg, params, origin):
    """D-42's whole point: a trail deposited at `origin` and decayed for
    several turns, with no re-emission (the opponent walked away), must not
    leave the posterior pointing back at `origin` -- for a corner, an edge,
    AND the board's most symmetric interior point alike."""
    field = ScentField(model=model, board_size=params.board_size)
    field.emit_opponent(origin)
    for _ in range(3):
        field.advance()
    likelihood = scent_likelihood(field, "thief", _state(), params, model, belief_cfg)
    belief = BeliefMap(params.board_size, "thief")
    belief.update(likelihood)
    assert belief.argmax() != origin


def test_regime_b_stays_a_valid_distribution_for_ten_turns_scent_only(model, belief_cfg, params):
    """Sec1's Regime B: no observe_exact ever -- the SAME predict/update loop
    stays a valid distribution for 10 joint turns fed by scent alone."""
    n = params.board_size
    belief = BeliefMap(n, "thief")
    field = ScentField(model=model, board_size=n)
    state = _state()
    field.emit_opponent((3, 3))
    for _ in range(10):
        likelihood = scent_likelihood(field, "thief", state, params, model, belief_cfg)
        belief.update(likelihood)
        belief.predict(state, params)
        field.advance()
        posterior = belief.posterior()
        assert sum(sum(row) for row in posterior) == pytest.approx(1.0)
        assert all(v >= 0.0 for row in posterior for v in row)


def test_regime_b_diffuses_without_evidence_then_reconcentrates(model, belief_cfg, params):
    """No further evidence -> pure predict()-driven diffusion lowers the
    peak; a fresh trail on a cell the thief can actually occupy raises it again.

    The trail must land on a cell carrying prior mass. A fresh (age 0) reading
    boosts only its own deposit cell (scent_likelihood leaves every other cell
    at _NEUTRAL), so a deposit on a zero-probability cell multiplies the whole
    support by the same constant and renormalises back to an identical
    distribution -- the peak then moves only by float noise, in whichever
    direction the rounding falls. (0, 0) is exactly such a cell here: it is the
    cop's square, which the legal-motion model correctly holds at probability 0
    for the thief. Asserting a strict rise there passed on one machine and
    failed on CI at 1e-17. The non-vacuity assertion below pins this down."""
    n = params.board_size
    belief = BeliefMap(n, "thief")
    belief.observe_exact((3, 3))
    empty_field = ScentField(model=model, board_size=n)
    state = _state()
    neutral = scent_likelihood(empty_field, "thief", state, params, model, belief_cfg)

    peak_before = max(max(row) for row in belief.posterior())
    for _ in range(5):
        belief.update(neutral)
        belief.predict(state, params)
    peak_diffused = max(max(row) for row in belief.posterior())
    assert peak_diffused < peak_before

    fresh_field = ScentField(model=model, board_size=n)
    fresh_field.emit_opponent(state.thief)
    fresh_likelihood = scent_likelihood(fresh_field, "thief", state, params, model, belief_cfg)

    # Non-vacuity: the evidence must actually discriminate across the support,
    # or the update below is a no-op and the peak assertion tests only rounding.
    support = [
        fresh_likelihood[r][c]
        for r, row in enumerate(belief.posterior())
        for c, mass in enumerate(row)
        if mass > 0.0
    ]
    assert len(set(support)) > 1

    belief.update(fresh_likelihood)
    peak_reconcentrated = max(max(row) for row in belief.posterior())
    assert peak_reconcentrated > peak_diffused
