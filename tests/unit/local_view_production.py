"""Drive a belief the way PRODUCTION drives it, and try to invert what gets
published (07-11).

Not a `test_*.py` file on purpose, so pytest collects nothing from it -- the
`local_view_fixtures.py` / `_fakes_agent.py` precedent. It imports nothing
from `local_view_fixtures`, which imports FROM here: one direction only.

WHY THIS MODULE EXISTS. 07-03's firewall asked "does the true cell appear as
a VALUE in the serialised view", and answered no. It could not ask the
question that actually decides rule 9: can the true cell be RECOVERED from
what a rules-compliant GUI would DRAW? A heatmap need not print a coordinate
to display one. `observe_exact` collapses the posterior to a delta,
`belief_motion.spread` disperses that delta over exactly the true cell's
legal destinations, and `BeliefMap.update` multiplies pointwise so a zeroed
cell never reopens -- so the published support is the legal-move PLUS
centred on the true pre-move cell, and the centre of a plus inverts uniquely.
`geometric_inversion` below is that inversion, run as an attacker would.
"""

from __future__ import annotations

import pathlib

from pursuit.network.turn_language import known_opponent_cell
from pursuit.shared.belief_config import load_belief_config
from pursuit.shared.inference import NO_EVIDENCE

#: One legal step, in L1 distance. Movement is orthogonal
#: (`config/*/game_params.json`: `"movement": "orthogonal"`), so a single
#: action moves a cell by exactly 1 in L1 or leaves it where it was.
STEP_RADIUS = 1

_POLICE_CONFIG = pathlib.Path(__file__).parents[2] / "config" / "police" / "belief.json"


def display_floors():
    """The SHIPPED publication floors (`belief.json`'s `display` group).

    Read from the real config, never restated as a literal here: a test that
    hard-codes the threshold it is guarding stops guarding it the moment the
    config moves (CLAUDE.md rule 1, D-18 discipline)."""
    return load_belief_config(_POLICE_CONFIG).display


def seed_belief_as_production_does(ctx, agent: str = "cop") -> None:
    """Run ONE real turn of the shipped decision path against `ctx`.

    This is what `turn_language.choose_destination` does every turn:
    `known_opponent_cell(ctx, "cop")` returns `ctx.state.thief` verbatim on
    any turn > 0, and it is handed straight to `BeliefAdapter.decide` as
    `known_cell`. 07-03's fixture instead called
    `observe_exact(BELIEF_ARGMAX)` on a cell production never supplies and
    never called `emit_opponent` at all, so `scent.opponent` was an all-zero
    grid in every one of its thirty probes -- the single field carrying the
    true cell at full source strength was empty in every test written to
    protect it.
    """
    ctx.brain.decide(
        ctx.state, NO_EVIDENCE, ctx.scent_field, ctx.rules,
        known_cell=known_opponent_cell(ctx, agent),
    )


def support_cells(grid) -> list[tuple[int, int]]:
    """Every cell in a dense row-major grid carrying strictly positive mass."""
    return [
        (row, col)
        for row, cells in enumerate(grid)
        for col, value in enumerate(cells)
        if value > 0.0
    ]


def grid_argmax(grid) -> tuple[int, int]:
    """The strongest cell in a dense row-major grid, ties broken row-major --
    matching `BeliefMap.argmax`'s own deterministic convention, so the scent
    grid is attacked exactly the way the belief grid is."""
    best = (0, 0)
    for row, cells in enumerate(grid):
        for col, value in enumerate(cells):
            if value > grid[best[0]][best[1]]:
                best = (row, col)
    return best


def geometric_inversion(support, board_size: int) -> list[tuple[int, int]]:
    """Every board cell within one legal step of EVERY cell in `support`.

    THE ATTACK, not a coordinate scan. If the published support is one
    cell's legal-destination set, this returns that cell and nothing else --
    the true pre-move position, recovered from a heatmap that never printed
    a coordinate. Candidates range over the WHOLE board, not just the
    support, so nothing is assumed about where the answer might be.

    A support of six or more cells cannot fit inside any single cell's step
    neighbourhood (STAY plus four orthogonal moves is five cells), so this
    returns `[]` -- which is why `display.min_support_cells` is floored above
    that number rather than at a round one.
    """
    if not support:
        return []
    return [
        (row, col)
        for row in range(board_size)
        for col in range(board_size)
        if all(
            abs(row - s_row) + abs(col - s_col) <= STEP_RADIUS for s_row, s_col in support
        )
    ]
