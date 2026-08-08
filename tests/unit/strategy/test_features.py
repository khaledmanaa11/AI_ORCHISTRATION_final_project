"""phi(): shape, scaling, sign conventions, and the kill-range tactical feature.

Every component must stay in roughly [-1, 1] and every sign must mean "positive is
good for the cop" -- the whole zero-sum architecture rests on one vector serving
both seats by negation, and a single inverted sign silently trains the thief to
play the cop's game.
"""

import pytest

from pursuit.shared.state import GameState
from pursuit.strategy import graphcache
from pursuit.strategy.features import FEATURE_COUNT, FEATURE_NAMES, phi, value


def _state(cop, thief, barriers=frozenset(), placed=0, turn=0):
    """Build a GameState with only the fields a test cares about."""
    return GameState(
        cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=turn
    )


@pytest.fixture(autouse=True)
def _cold_caches():
    """Memoisation must never change an answer, only its cost."""
    graphcache.clear_caches()


def test_vector_length_matches_the_declared_count(default_params):
    """A mismatch here silently misaligns every weight against its feature."""
    assert len(phi(_state((0, 0), (3, 3)), default_params)) == FEATURE_COUNT
    assert len(FEATURE_NAMES) == FEATURE_COUNT


def test_every_component_is_bounded(default_params):
    """Scaling divisors come from GameParams; nothing may exceed [-1, 1]."""
    states = [
        _state((0, 0), (6, 6)),
        _state((3, 3), (3, 4), placed=13, turn=34),
        _state((0, 0), (0, 2), barriers=frozenset({(0, 1), (1, 1), (1, 0)}), placed=3),
    ]
    for state in states:
        for name, component in zip(FEATURE_NAMES, phi(state, default_params), strict=True):
            assert -1.0 <= component <= 1.0, f"{name} out of range: {component}"


def test_closing_distance_raises_the_cop_value(default_params):
    """Positive is good for the cop, so approaching must not lower the value."""
    far = phi(_state((0, 0), (6, 6)), default_params)
    near = phi(_state((3, 2), (3, 4)), default_params)
    index = FEATURE_NAMES.index("neg_distance")
    assert near[index] > far[index]


def test_unreachable_thief_is_the_worst_state_for_the_cop(default_params):
    """A thief the cop cannot reach at all is a guaranteed survival."""
    walls = frozenset({(0, 1), (1, 1), (1, 0)})
    sealed = _state((0, 0), (6, 6), barriers=walls, placed=3)
    index = FEATURE_NAMES.index("thief_unreachable")
    assert phi(sealed, default_params)[index] == -1.0
    assert phi(_state((0, 0), (6, 6)), default_params)[index] == 0.0


def test_kill_range_fires_only_at_distance_one_with_quota(default_params):
    """Rule 46 seals the cell the thief is LEAVING, so distance 1 is forced loss.

    The gate on remaining quota matters: with the quota spent there is no seal to
    place, and the same geometry is merely close rather than lost.
    """
    index = FEATURE_NAMES.index("thief_in_kill_range")
    assert phi(_state((3, 3), (3, 4)), default_params)[index] == 1.0
    assert phi(_state((3, 3), (3, 5)), default_params)[index] == 0.0
    spent = _state((3, 3), (3, 4), placed=default_params.barrier_quota)
    assert phi(spent, default_params)[index] == 0.0


def test_forest_and_cycle_rank_agree(default_params):
    """A region with no cycles is a forest; the two features must not contradict."""
    open_board = phi(_state((0, 0), (3, 3)), default_params)
    forest_index = FEATURE_NAMES.index("thief_region_is_forest")
    loops_index = FEATURE_NAMES.index("neg_cycle_rank")
    assert open_board[forest_index] == 0.0
    assert open_board[loops_index] < 0.0

    corridor = frozenset({(0, 1), (1, 1), (1, 0)})
    trapped = phi(_state((6, 6), (0, 0), barriers=corridor, placed=3), default_params)
    assert trapped[forest_index] == 1.0
    assert trapped[loops_index] == 0.0


def test_memoisation_does_not_change_the_answer(default_params):
    """Cold and warm caches must produce byte-identical vectors."""
    state = _state((2, 2), (4, 5), barriers=frozenset({(3, 3), (1, 1)}), placed=2)
    graphcache.clear_caches()
    cold = phi(state, default_params)
    warm = phi(state, default_params)
    assert cold == warm


def test_value_is_the_dot_product(default_params):
    """value() must be exactly w . phi -- the search depends on nothing else."""
    state = _state((0, 0), (3, 3))
    vector = phi(state, default_params)
    weights = tuple(0.1 * index for index in range(FEATURE_COUNT))
    expected = sum(w * x for w, x in zip(weights, vector, strict=True))
    assert value(weights, state, default_params) == pytest.approx(expected)


def test_value_rejects_a_wrong_length_weight_vector(default_params):
    """strict=True zip: a stale artefact must fail loud, never silently truncate."""
    with pytest.raises(ValueError, match="argument"):
        value((1.0, 2.0), _state((0, 0), (3, 3)), default_params)
