"""Zero-sum matrix game solver: pure saddle point, else regret matching.

This is the module that makes the agent unexploitable, and it is the thing tabular
Q-learning structurally could not provide. Under simultaneous moves there is no
"best action" independent of the opponent's choice -- the optimal play at a
contact square is often a MIXED strategy, and `argmax` over a Q-row is
deterministic by construction. The repo's own measurement of that gap: a search
cop captures a deterministic evader 96% of the time and a uniformly mixing one
36%. We play the thief seat in half of every league match.

Rows are the maximiser (cop), columns the minimiser (thief). The value returned
is the cop's, so the thief's is its negation.

Two-stage by design: `pure_saddle` is exact, deterministic and costs O(rows*cols),
and it settles the large majority of positions. Regret matching (Hart &
Mas-Colell 2000) runs only when the saddle genuinely does not exist -- which is
exactly where mixing is genuinely required.
"""

from __future__ import annotations

_TOLERANCE = 1e-9


def pure_saddle(matrix: list) -> tuple | None:
    """Return (row, col) of a pure saddle point, or None if the game needs mixing.

    A saddle exists when max_i min_j M[i][j] == min_j max_i M[i][j]. Where it
    exists, the pure maximin pair IS the equilibrium, and playing it keeps the
    decision deterministic -- which makes a replay reproduce exactly, with no RNG
    involved at all.
    """
    row_mins = [min(row) for row in matrix]
    lower = max(row_mins)
    col_maxes = [max(row[col] for row in matrix) for col in range(len(matrix[0]))]
    upper = min(col_maxes)
    if abs(lower - upper) > _TOLERANCE:
        return None
    row = row_mins.index(lower)
    col = min(range(len(matrix[0])), key=lambda c: matrix[row][c])
    return row, col


def solve(matrix: list, iterations: int) -> tuple:
    """Return (row_strategy, col_strategy, cop_value) for a zero-sum matrix.

    Parameters
    ----------
    matrix:
        Payoffs to the row player (the cop), indexed [row][col].
    iterations:
        Regret-matching iterations, used only when no pure saddle exists.

    Returns
    -------
    tuple[tuple[float, ...], tuple[float, ...], float]
        Probability vectors over rows and columns, and the game's value.
        Both vectors sum to 1. A pure saddle yields one-hot vectors.
    """
    saddle = pure_saddle(matrix)
    if saddle is not None:
        row, col = saddle
        rows = tuple(1.0 if i == row else 0.0 for i in range(len(matrix)))
        cols = tuple(1.0 if j == col else 0.0 for j in range(len(matrix[0])))
        return rows, cols, matrix[row][col]
    return _regret_match(matrix, iterations)


def _regret_match(matrix: list, iterations: int) -> tuple:
    """Hart & Mas-Colell regret matching; the AVERAGE strategies converge to Nash.

    The average is what converges, not the current-iterate strategy -- returning
    the latter is the classic implementation error and yields a policy that
    oscillates instead of mixing.
    """
    n_rows, n_cols = len(matrix), len(matrix[0])
    row_regret, col_regret = [0.0] * n_rows, [0.0] * n_cols
    row_total, col_total = [0.0] * n_rows, [0.0] * n_cols

    for _ in range(iterations):
        row_strategy = _from_regret(row_regret)
        col_strategy = _from_regret(col_regret)
        for i in range(n_rows):
            row_total[i] += row_strategy[i]
        for j in range(n_cols):
            col_total[j] += col_strategy[j]

        # The cop maximises: regret is the gain from having played row i instead.
        row_utility = [
            sum(matrix[i][j] * col_strategy[j] for j in range(n_cols)) for i in range(n_rows)
        ]
        expected = sum(row_strategy[i] * row_utility[i] for i in range(n_rows))
        for i in range(n_rows):
            row_regret[i] += row_utility[i] - expected

        # The thief minimises the same quantity, so its utility is the negation.
        col_utility = [
            -sum(matrix[i][j] * row_strategy[i] for i in range(n_rows)) for j in range(n_cols)
        ]
        col_expected = sum(col_strategy[j] * col_utility[j] for j in range(n_cols))
        for j in range(n_cols):
            col_regret[j] += col_utility[j] - col_expected

    rows = _normalise(row_total)
    cols = _normalise(col_total)
    value = sum(
        rows[i] * matrix[i][j] * cols[j] for i in range(n_rows) for j in range(n_cols)
    )
    return rows, cols, value


def _from_regret(regret: list) -> tuple:
    """Strategy proportional to positive regret; uniform when none is positive."""
    positive = [value if value > 0.0 else 0.0 for value in regret]
    total = sum(positive)
    if total <= _TOLERANCE:
        share = 1.0 / len(regret)
        return tuple(share for _ in regret)
    return tuple(value / total for value in positive)


def _normalise(totals: list) -> tuple:
    """Scale a non-negative accumulator to a probability vector."""
    total = sum(totals)
    if total <= _TOLERANCE:
        share = 1.0 / len(totals)
        return tuple(share for _ in totals)
    return tuple(value / total for value in totals)


def sample(strategy: tuple, draw: float) -> int:
    """Return the index *draw* in [0,1) selects from *strategy*.

    Takes the random draw as an argument rather than calling a module RNG, so the
    caller owns reproducibility: the live agent draws from a per-game seed that
    is logged, and the replay viewer reproduces the game exactly (rule 20).
    """
    cumulative = 0.0
    for index, probability in enumerate(strategy):
        cumulative += probability
        if draw < cumulative:
            return index
    return len(strategy) - 1
