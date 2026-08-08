"""The matrix-game solver -- the component that makes the agent unexploitable.

Matching pennies is the anchor test: it has NO pure equilibrium, its unique
solution is (0.5, 0.5) for both players, and its value is 0. A solver that
returns a pure strategy there is exactly the deterministic policy an opponent
reads and punishes, which is the failure mode this whole module exists to remove.
"""

import pytest

from pursuit.strategy.equilibrium import pure_saddle, sample, solve

MATCHING_PENNIES = [[1.0, -1.0], [-1.0, 1.0]]
TOLERANCE = 0.05


def test_saddle_found_when_one_exists():
    """A dominant row with a clear minimum is a pure equilibrium."""
    matrix = [[3.0, 2.0], [1.0, 0.0]]
    assert pure_saddle(matrix) == (0, 1)


def test_no_saddle_for_matching_pennies():
    """max-min (-1) and min-max (+1) disagree, so no pure equilibrium exists."""
    assert pure_saddle(MATCHING_PENNIES) is None


def test_saddle_play_is_pure_and_deterministic():
    """Where a saddle exists the solver must not mix -- replays stay exact."""
    rows, columns, value = solve([[3.0, 2.0], [1.0, 0.0]], iterations=200)
    assert rows == (1.0, 0.0)
    assert columns == (0.0, 1.0)
    assert value == pytest.approx(2.0)


def test_matching_pennies_converges_to_half_half():
    """The classic mixed equilibrium, recovered by regret matching."""
    rows, columns, value = solve(MATCHING_PENNIES, iterations=2000)
    assert rows[0] == pytest.approx(0.5, abs=TOLERANCE)
    assert columns[0] == pytest.approx(0.5, abs=TOLERANCE)
    assert value == pytest.approx(0.0, abs=TOLERANCE)


def test_strategies_are_probability_vectors():
    """Both vectors must sum to one for sampling to be well defined."""
    matrix = [[0.3, -0.8, 0.1], [-0.5, 0.9, -0.2]]
    rows, columns, _ = solve(matrix, iterations=500)
    assert sum(rows) == pytest.approx(1.0)
    assert sum(columns) == pytest.approx(1.0)
    assert all(value >= 0.0 for value in rows + columns)


def test_value_lies_between_maximin_and_minimax():
    """The game value is bracketed by the two pure bounds, by definition."""
    matrix = [[0.4, -0.6], [-0.7, 0.5], [0.0, -0.1]]
    lower = max(min(row) for row in matrix)
    upper = min(max(row[col] for row in matrix) for col in range(2))
    _, _, value = solve(matrix, iterations=2000)
    assert lower - TOLERANCE <= value <= upper + TOLERANCE


def test_dominated_row_gets_almost_no_weight():
    """A row that is worse in every column must not be played."""
    matrix = [[0.9, 0.8], [-0.9, -0.8]]
    rows, _, _ = solve(matrix, iterations=500)
    assert rows[1] < TOLERANCE


def test_asymmetric_shape_is_handled():
    """The real matrices are up to 10x5; rows and columns are never equal."""
    matrix = [[0.1 * (row - col) for col in range(5)] for row in range(10)]
    rows, columns, _ = solve(matrix, iterations=200)
    assert (len(rows), len(columns)) == (10, 5)


@pytest.mark.parametrize(
    ("draw", "expected"), [(0.0, 0), (0.29, 0), (0.31, 1), (0.79, 1), (0.81, 2)]
)
def test_sample_partitions_the_unit_interval(draw, expected):
    """Sampling is a pure function of the draw, so a logged seed replays exactly."""
    assert sample((0.3, 0.5, 0.2), draw) == expected


def test_sample_never_runs_off_the_end():
    """Floating-point sums slightly under 1.0 must not raise on a draw near 1."""
    assert sample((0.333333, 0.333333, 0.333333), 0.999999) == 2


def test_zero_regret_falls_back_to_uniform():
    """A constant matrix has no preference; every action is equally optimal.

    A tableau solver would return a vertex (a pure strategy) here. Returning
    uniform matters: constant matrices happen in the wide-open early game, and a
    pure choice there is a deterministic tell for the whole opening.
    """
    rows, columns, value = solve([[0.5, 0.5], [0.5, 0.5]], iterations=100)
    assert value == pytest.approx(0.5)
    assert sum(rows) == pytest.approx(1.0)
    assert sum(columns) == pytest.approx(1.0)
