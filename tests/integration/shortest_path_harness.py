"""Harness for `test_shortest_path.py` -- GATE-3 criterion 1 (STRAT-04).

Split out of the test module for the Segal Table-5 150-line limit (split, never
compress). Holds the frozen-thief walker, the barrier-aware BFS metric, the named
start set, and the revert-probe brain the non-vacuity test drives.

The probe brain lives here rather than in `src/` for the same reason
`late_peer_harness.py` holds its `linger=False` revert: a gate test proves it can
fail against a synthetic stub, never by editing real source.

Every board coordinate is derived from the caller's `GameParams`; nothing in this
module is a literal board number (CLAUDE.md rule 1).
"""

from __future__ import annotations

from pursuit.constants import MoveSource
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction, cop_actions
from pursuit.shared.config import GameParams
from pursuit.shared.resolution import PREFERRED
from pursuit.shared.state import GameState
from pursuit.strategy.base import BrainBase, Decision, Observation
from pursuit.strategy.graphcache import distances, passable

Coord = tuple[int, int]

#: Named starts, not one lucky board: the canonical opening, the opposite corner,
#: an edge-to-edge run, a start already inside seal range, and the barrier pocket a
#: Manhattan-greedy walker dead-ends in. Kept as names so `parametrize` needs no
#: `default_params`, which is a fixture and cannot be read at collection time.
SCENARIOS = (
    "canonical_opening",
    "far_corner_cop",
    "long_diagonal",
    "same_row_short",
    "already_in_seal_range",
    "barrier_pocket",
    "edge_to_edge",
)


def _at(cop: Coord, thief: Coord, barriers: frozenset = frozenset()) -> GameState:
    return GameState(
        cop=cop, thief=thief, barriers=barriers, barriers_placed=len(barriers), turn=0
    )


def scenario_states(params: GameParams) -> dict[str, GameState]:
    """Build every start named in `SCENARIOS` from `params` alone."""
    size = params.board_size
    mid = size // 2
    wall = frozenset((row, mid) for row in range(1, size - 1))
    row, col = params.thief_start
    return {
        "canonical_opening": engine.make_state(params),
        "far_corner_cop": _at((size - 1, size - 1), params.thief_start),
        "long_diagonal": _at((0, size - 1), (size - 1, 0)),
        "same_row_short": _at((row, 0), params.thief_start),
        "already_in_seal_range": _at((row, col - 1), params.thief_start),
        "barrier_pocket": _at((mid, mid - 2), (mid, mid + 2), wall),
        "edge_to_edge": _at((0, mid), (size - 1, mid)),
    }


def distance(state: GameState, target: Coord, params: GameParams) -> int | None:
    """Barrier-aware BFS hop count from the cop's cell to *target*.

    `None` when the cop's cell is not in the target's component -- which on a move
    turn is itself a failure, so the caller asserts on it rather than absorbing it.
    """
    return distances(passable(state.barriers, params.board_size), target).get(state.cop)


def walk_unaided(brain: BrainBase, state: GameState, params: GameParams) -> tuple:
    """Drive *brain* against a FROZEN thief until capture or the move ceiling.

    The thief's move is `state.thief` every turn -- STAY is unconditionally legal
    (`sdk.actions.thief_actions`) -- so the target is a genuinely fixed, known
    location. No code here ever overrides what `brain._decide_move` returned: that
    is the criterion's "no manual intervention" clause proven by construction.

    Returns `(moves, barriers, outcome, steps)`, where `steps` holds the
    `(before, after)` BFS distance of every turn on which the cop actually MOVED.
    Barrier turns are absent from `steps` -- a seal does not move the cop -- which
    is why the caller must also bound `moves + barriers`.
    """
    target = state.thief
    moves = barriers = 0
    steps: list[tuple[int | None, int | None]] = []
    outcome = None
    for _ in range(params.move_ceiling):
        before = distance(state, target, params)
        observation = Observation(
            own_cell=state.cop,
            target_cell=target,
            blocked_mask=0,
            barriers_used=state.barriers_placed,
            turn_index=state.turn,
        )
        decision = brain._decide_move(observation, state)
        action = (
            CopAction(barrier=decision.barrier)
            if decision.barrier is not None
            else CopAction(move=decision.move)
        )
        state, outcome = engine.resolve_turn(state, action, target, params, PREFERRED)
        if action.is_barrier:
            barriers += 1
        else:
            moves += 1
            steps.append((before, distance(state, target, params)))
        if outcome is not None:
            break
    return moves, barriers, outcome, steps


class DistanceIgnoringCop(BrainBase):
    """A cop that steps to whichever legal cell is FURTHEST from the target.

    The revert probe. It never seals and never closes, so it must fail every
    clause of the gate -- which is what makes the gate non-vacuous.
    """

    def __init__(self, game_params: GameParams) -> None:
        self.role = "cop"
        self.game_params = game_params

    def _pick_move(self, obs: Observation, state: GameState) -> Decision:
        return self._decide_move(obs, state)

    def _decide_move(self, obs: Observation, state: GameState) -> Decision:
        size = self.game_params.board_size
        reach = distances(passable(state.barriers, size), state.thief)
        cells = [a.move for a in cop_actions(state, self.game_params) if not a.is_barrier]
        furthest = max(cells, key=lambda cell: reach.get(cell, -1))
        return Decision(move=furthest, source=MoveSource.HEURISTIC, barrier=None)
