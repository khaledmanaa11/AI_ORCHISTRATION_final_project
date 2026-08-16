"""GATE-3 criterion 1 -- shortest-path competence to a KNOWN target (STRAT-04).

Pins the book Sec10.4 stage-3 milestone criterion, quoted verbatim from
`.planning/ROADMAP.md:95`:

    "Given a known target location, the agent computes and walks the shortest
     path with no manual intervention"

`docs/TODO.md`'s Phase-3 header carries the same criterion in short form
("Gate: agent walks the shortest path to a known target unaided").

**Restoration note (rule 38).** The original `tests/integration/test_shortest_path.py`
drove `HeuristicBrain` and was DELETED in commit `f3d9847` when the run-1 tabular
stack was retired, with no replacement -- so from 2026-08-08 until this file landed
on 2026-08-16 the phase's first Sec10.4 criterion carried ZERO automated evidence.
The phase PRD's AC-1..AC-9 (`docs/phases/phase-3/PRD.md` Sec3) does not cover it
either. This file restores the coverage against the brain that actually ships,
`value_search` (docs/PRD_matrix_mover.md), built from real config alone through
`registry.build_brain` -- never instantiated directly.

**How the claim is made falsifiable.** The thief is FROZEN (it plays STAY every
turn, see `shortest_path_harness.walk_unaided`), so the target is a genuinely
fixed, known location rather than a moving one. Three assertions together, because
no one of them is enough:

1. the run ends in a real `Outcome.CAPTURE`;
2. on every turn the cop MOVES, its barrier-aware BFS distance to the target drops
   by EXACTLY 1 -- a shortest walk, not merely a non-increasing one;
3. `move_turns + barrier_turns == initial BFS distance`. Barrier turns are exempt
   from (2) because a seal does not move the cop, and (3) is what stops that
   exemption from being a loophole: a cop that sealed forever, or dawdled, blows
   the budget. Measured shape -- the cop spends its final turn(s) sealing rather
   than stepping (rules 46/47), so `move_turns == initial - barrier_turns` exactly.

`test_the_gate_fails_a_cop_that_ignores_distance` is the revert probe: the same
three assertions inverted against a deliberately distance-ignoring stub, so the
gate is proven able to fail. Every board coordinate is derived from
`default_params`; nothing here is a literal board number (CLAUDE.md rule 1).
"""

from __future__ import annotations

import pytest

from pursuit.constants import Outcome
from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.strategy import registry
from tests.integration.conftest import strategy_params
from tests.integration.shortest_path_harness import (
    SCENARIOS,
    DistanceIgnoringCop,
    distance,
    scenario_states,
    walk_unaided,
)


def test_the_scenario_set_is_not_empty(default_params: GameParams) -> None:
    """Anti-vacuity guard: pytest SKIPS an empty parametrize set in silence, the
    trap plan 05-12 hit. Also pins that every name below builds a real state."""
    assert SCENARIOS, "the parametrized scenario set is empty -- the gate is vacuous"
    assert set(scenario_states(default_params)) == set(SCENARIOS)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_walks_the_shortest_path_to_a_known_target_with_no_manual_intervention(
    default_params: GameParams, scenario: str
) -> None:
    start = scenario_states(default_params)[scenario]
    initial = distance(start, start.thief, default_params)
    brain = registry.build_brain("cop", strategy_params("cop"), default_params)

    moves, barriers, outcome, steps = walk_unaided(brain, start, default_params)

    assert outcome is Outcome.CAPTURE, f"{scenario}: never captured the frozen target"
    for before, after in steps:
        assert before is not None and after is not None, (
            f"{scenario}: the cop stood off the passable graph across a move turn "
            f"({before} -> {after}) -- it sealed its own cell (book Sec3.4) and the "
            f"distance to the target is undefined from there"
        )
        assert before - after == 1, f"{scenario}: a move turn went {before} -> {after}"
    assert moves + barriers == initial, (
        f"{scenario}: {moves} move + {barriers} barrier turns to capture, but the "
        f"shortest path is {initial} -- the walk was not shortest"
    )


def test_the_gate_fails_a_cop_that_ignores_distance(default_params: GameParams) -> None:
    """Non-vacuity: the three assertions above must be able to FAIL. A gate test
    that cannot fail is worse than no test."""
    start = engine.make_state(default_params)
    initial = distance(start, start.thief, default_params)

    moves, barriers, outcome, steps = walk_unaided(
        DistanceIgnoringCop(default_params), start, default_params
    )

    assert outcome is not Outcome.CAPTURE
    assert any(before - after != 1 for before, after in steps)
    assert moves + barriers != initial
