"""Tests for BeliefMap: the invariants, both regimes (Task 1, D-48)."""

import random

import pytest

from pursuit.sdk.actions import thief_actions
from pursuit.shared.state import GameState
from pursuit.strategy.belief import BeliefMap, _clip_barriers, _renormalize, _uniform


def _state(params, cop=(0, 0), thief=(3, 3), barriers=frozenset(), placed=0):
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=0)


def _sum(posterior):
    return sum(sum(row) for row in posterior)


def test_invalid_role_raises():
    with pytest.raises(ValueError, match="role"):
        BeliefMap(7, "referee")


def test_constructor_seeds_a_uniform_prior(default_params):
    belief = BeliefMap(default_params.board_size, "cop")
    posterior = belief.posterior()
    assert _sum(posterior) == pytest.approx(1.0)
    values = {v for row in posterior for v in row}
    assert len(values) == 1


def test_observe_exact_collapses_to_a_delta(default_params):
    belief = BeliefMap(default_params.board_size, "cop")
    belief.observe_exact((0, 0))
    posterior = belief.posterior()
    assert posterior[0][0] == 1.0
    assert _sum(posterior) == pytest.approx(1.0)


def test_observe_exact_out_of_bounds_raises(default_params):
    belief = BeliefMap(default_params.board_size, "cop")
    with pytest.raises(ValueError, match="outside"):
        belief.observe_exact((-1, 0))


def test_update_multiplies_pointwise_and_renormalises(default_params):
    n = default_params.board_size
    belief = BeliefMap(n, "cop")
    likelihood = [[2.0 if (r, c) == (0, 0) else 1.0 for c in range(n)] for r in range(n)]
    belief.update(likelihood)
    posterior = belief.posterior()
    assert posterior[0][0] > posterior[0][1]
    assert _sum(posterior) == pytest.approx(1.0)


def test_all_zero_likelihood_leaves_the_prior_exactly_unchanged(default_params):
    belief = BeliefMap(default_params.board_size, "cop")
    belief.observe_exact((2, 2))
    before = belief.posterior()
    zero = [[0.0] * default_params.board_size for _ in range(default_params.board_size)]
    belief.update(zero)
    assert belief.posterior() == before


def test_predict_conserves_total_mass(default_params):
    belief = BeliefMap(default_params.board_size, "thief")
    belief.observe_exact((3, 3))
    belief.predict(_state(default_params, thief=(3, 3)), default_params)
    assert _sum(belief.posterior()) == pytest.approx(1.0)


def test_predict_clips_a_newly_barriered_cells_mass_to_zero(default_params):
    belief = BeliefMap(default_params.board_size, "thief")
    belief.observe_exact((3, 3))
    state = _state(default_params, thief=(3, 3), barriers=frozenset({(3, 3)}), placed=1)
    belief.predict(state, default_params)
    posterior = belief.posterior()
    assert posterior[3][3] == 0.0
    assert _sum(posterior) == pytest.approx(1.0)


def test_argmax_returns_the_unique_peak(default_params):
    belief = BeliefMap(default_params.board_size, "cop")
    belief.observe_exact((4, 5))
    assert belief.argmax() == (4, 5)


def test_argmax_breaks_ties_in_row_major_order(default_params):
    belief = BeliefMap(default_params.board_size, "cop")  # uniform -> every cell tied
    assert belief.argmax() == (0, 0)


def test_sample_reproducible_with_a_fixed_seed(default_params):
    belief = BeliefMap(default_params.board_size, "cop")
    belief.observe_exact((2, 2))
    assert belief.sample(random.Random(42)) == belief.sample(random.Random(42)) == (2, 2)


def test_sample_empirical_frequency_matches_the_posterior(default_params):
    n = default_params.board_size
    belief = BeliefMap(n, "thief")
    belief.observe_exact((1, 1))
    belief.predict(_state(default_params, thief=(1, 1)), default_params)
    posterior = belief.posterior()
    rng = random.Random(3)
    draws = 4000
    counts: dict = {}
    for _ in range(draws):
        cell = belief.sample(rng)
        counts[cell] = counts.get(cell, 0) + 1
    for cell, count in counts.items():
        assert count / draws == pytest.approx(posterior[cell[0]][cell[1]], abs=0.03)


def test_normalisation_holds_after_a_random_predict_update_sequence(default_params):
    n = default_params.board_size
    rng = random.Random(7)
    belief = BeliefMap(n, "thief")
    state = _state(default_params, thief=(3, 3))
    for _ in range(8):
        if rng.random() < 0.5:
            belief.predict(state, default_params)
        else:
            likelihood = [[rng.random() + 0.1 for _ in range(n)] for _ in range(n)]
            belief.update(likelihood)
        posterior = belief.posterior()
        assert _sum(posterior) == pytest.approx(1.0)
        assert all(v >= 0.0 for row in posterior for v in row)


def test_renormalize_of_an_all_zero_grid_falls_back_to_uniform():
    """Defensive-only branch: no live call path can hand `_renormalize` an
    all-zero grid (spread()'s output is always positive given any positive
    input, since STAY is always a legal destination), but the fallback is
    tested directly so a future caller cannot divide by zero silently."""
    zero = [[0.0] * 7 for _ in range(7)]
    assert _renormalize(zero, 7) == _uniform(7)


def test_clip_barriers_with_every_cell_barriered_falls_back_to_uniform():
    """Equally unreachable through real gameplay (barrier_quota is far below
    board_size**2), defended the same way."""
    all_barriers = frozenset((r, c) for r in range(7) for c in range(7))
    grid = _uniform(7)
    result = _clip_barriers(grid, all_barriers, 7)
    assert result == _uniform(7)


def test_regime_a_observe_then_predict_matches_the_legal_successor_set(default_params):
    n = default_params.board_size
    belief = BeliefMap(n, "thief")
    belief.observe_exact((3, 3))
    state = _state(default_params, thief=(3, 3))
    belief.predict(state, default_params)
    posterior = belief.posterior()
    legal = set(thief_actions(state, default_params))
    nonzero = {(r, c) for r in range(n) for c in range(n) if posterior[r][c] > 0.0}
    assert nonzero == legal
