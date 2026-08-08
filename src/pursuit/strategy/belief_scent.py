"""Scent likelihood: inverting the locked decay law (D-42, Task 3).

scent_likelihood() never chases the strongest cell directly -- Sec4.4's
named failure mode. It reads the field's single freshest cell (the trail's
peak strength -- decay() scales the whole field uniformly, so it never
reorders which cell is strongest), inverts that strength into an implied AGE
via expected_strength_after() (step 1), turns the age into a freshness
weight (step 2), and runs that weight forward through belief_motion.spread()
for exactly `age` joint turns (step 3) -- so the returned grid describes
where the trail predicts the opponent IS now, never where it WAS.

Projecting a point mass through `age` >= 1 rounds of spread() would, left
alone, still leave that SAME point as the single highest-weighted cell:
`spread()`'s legal action set always includes STAY, so a "lazy" symmetric
walk keeps its mode at the origin no matter how many joint turns it runs for
(a textbook property of a symmetric random walk, verified numerically while
building this module, not a corner case). That is precisely "chasing the
strongest cell" wearing a diffused disguise, so once age >= 1 the origin's
own projected contribution is dropped: a genuinely stale reading is itself
evidence AGAINST "stayed put the whole time" -- if the opponent really had
not moved, continued occupancy would keep re-emitting at full strength
(scentfield.py's emit_opponent), and the reading would not have decayed at
all. age == 0 is exempt (a fresh trail legitimately IS still there).

Every cell defaults to the NEUTRAL likelihood (1.0): a trail below
`config.epsilon` everywhere explains nothing and is left neutral, never
zeroed (BeliefMap invariant 2 -- a reading with no information must not be
able to zero the map).
"""

from __future__ import annotations

from pursuit.shared.belief_config import BeliefParams
from pursuit.shared.config import GameParams
from pursuit.shared.scent_config import ScentModel
from pursuit.shared.state import GameState
from pursuit.strategy.belief_motion import Coord, Grid, spread
from pursuit.strategy.scent import expected_strength_after
from pursuit.strategy.scentfield import ScentField

_NEUTRAL = 1.0


def scent_likelihood(
    opponent_field: ScentField,
    role: str,
    state: GameState,
    params: GameParams,
    model: ScentModel,
    config: BeliefParams,
) -> Grid:
    """Return a likelihood grid over `role`'s position from the opponent's
    locally-reconstructed scent trail (opponent_field.strength("opponent", ...)).

    `role`, `state` and `params` are exactly what belief_motion.spread()
    needs to project the peak forward -- this function calls spread() with
    the SAME legal-motion model predict() uses, never a shortcut.
    """
    size = params.board_size
    likelihood: Grid = [[_NEUTRAL] * size for _ in range(size)]
    peak = opponent_field.freshest("opponent")
    if peak is None:
        return likelihood
    strength = opponent_field.strength("opponent", peak)
    if strength < config.epsilon:
        return likelihood

    age = inverted_age(strength, model, config.age_cap)
    projected: Grid = [[0.0] * size for _ in range(size)]
    projected[peak[0]][peak[1]] = config.freshness_decay**age
    for _ in range(age):
        projected = spread(projected, role, state, params)
    if age >= 1:
        _drop_origin(projected, peak)

    for row in range(size):
        for col in range(size):
            likelihood[row][col] += config.scent_weight * projected[row][col]
    return likelihood


def _drop_origin(projected: Grid, peak: Coord) -> None:
    """Zero the deposit cell's own projected weight in place -- see module
    docstring for why a stale (age >= 1) reading must not still credit
    "never moved" with the walk's self-renewal advantage."""
    projected[peak[0]][peak[1]] = 0.0


def inverted_age(strength: float, model: ScentModel, age_cap: int) -> int:
    """Return the integer age in [0, age_cap] whose expected_strength_after()
    is closest to `strength` -- the D-42 inversion, searched directly
    against scent.py's single source of truth for the decay law rather than
    re-deriving its closed form a second time (and sidestepping the
    div-by-zero a log-domain inversion would hit if decay were ever
    configured to 0).
    """
    best_age = 0
    best_gap = abs(expected_strength_after(model, 0) - strength)
    for age in range(1, age_cap + 1):
        gap = abs(expected_strength_after(model, age) - strength)
        if gap < best_gap:
            best_gap = gap
            best_age = age
    return best_age
