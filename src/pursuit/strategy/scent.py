"""The book's emission kernel and decay law, pure and I/O-free (D-50, Sec4.3).

Two operations over a ScentModel and a board size: emission() overlays the
Figure-4 kernel centred on an agent's cell, clipped at the board edge; decay()
applies the law tau(t+1) = max(0, (1-rho)*tau(t) + delta_tau) to an existing
field. The caller composes them -- emission() supplies delta_tau, decay()
applies rho -- so neither function knows about the other, and ScentField
(scentfield.py) is the one place that calls both.

expected_strength_after() is the closed form of n decay-only steps: it is the
scent-likelihood inversion D-42 needs (belief map, a later plan) and the
quantity Sec4.4's lie-detection worked example computes, so it lives here
rather than being re-derived downstream.
"""

from __future__ import annotations

from pursuit.shared.scent_config import ScentModel

#: Local alias for clarity, matching board.py/state.py's own local Coord alias.
Coord = tuple[int, int]

#: Field values below this are dropped by decay() so a 35-turn game does not
#: accumulate a long tail of near-zero floats. An engineering default, not a
#: Table 16 value -- no fixed number is read from this module.
_EPSILON = 1e-6


def emission(model: ScentModel, centre: Coord, board_size: int) -> dict[Coord, float]:
    """Return the kernel's contribution to the field from an agent at centre.

    Clipped at the board edge: offsets landing outside [0, board_size) are
    dropped, never wrapped and never folded back onto an in-board cell.
    """
    half = model.window // 2
    row0, col0 = centre
    delta: dict[Coord, float] = {}
    for i, row in enumerate(model.kernel):
        r = row0 + (i - half)
        if not 0 <= r < board_size:
            continue
        for j, value in enumerate(row):
            c = col0 + (j - half)
            if not 0 <= c < board_size:
                continue
            delta[(r, c)] = value
    return delta


def decay(field: dict[Coord, float], model: ScentModel) -> dict[Coord, float]:
    """Apply one turn of the Sec4.3 decay law with no re-emission.

    tau(t+1) = max(0, (1-rho)*tau(t) + delta_tau), delta_tau = 0 here -- the
    caller adds any new emission() separately, so the two operations compose
    without either one knowing about the other. Cells that decay below
    _EPSILON are dropped rather than kept as a near-zero float, and max(0, ..)
    guarantees no cell is ever negative, even given an adversarial input.
    """
    retain = 1.0 - model.decay
    result: dict[Coord, float] = {}
    for cell, strength in field.items():
        next_strength = max(0.0, retain * strength)
        if next_strength >= _EPSILON:
            result[cell] = next_strength
    return result


def expected_strength_after(model: ScentModel, turns: int) -> float:
    """Strength a source cell (tau=source) retains after `turns` decay-only
    steps with no re-emission -- the closed form of repeated decay()."""
    return model.source * (1.0 - model.decay) ** turns
