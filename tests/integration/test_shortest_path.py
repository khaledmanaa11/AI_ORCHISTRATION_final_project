"""GATE-1 / E1 -- shortest-path competence (STRAT-04, PRD §10.4 criterion a).

Drives ONE brain (`HeuristicBrain`, the always-playable STRAT-02 walker --
its `_pick_move` delegates entirely to the same `fallback.pick()` a
`QLearningBrain` falls back to) toward a KNOWN, FROZEN target through
`pursuit.sdk.engine` only. No test-side code ever chooses a move -- only
`brain._pick_move` does, and the "no manual intervention" clause is proven
by construction, not by convention: `_walk_unaided` never overrides a
returned move.

Both an open board and a barrier-pocket board (the case a naive
Manhattan-greedy walker dead-ends on, AI-SPEC FM-3 / E4) must reach the
target in exactly `bfs_oracle` turns with no revisited cell.
"""

from __future__ import annotations

import pytest

from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.base import Observation
from pursuit.strategy.encoding import blocked_mask
from pursuit.strategy.heuristic import HeuristicBrain
from pursuit.strategy.pathfind import Coord, bfs
from tests.integration.conftest import strategy_params


def _cop_brain(default_params: GameParams) -> HeuristicBrain:
    return HeuristicBrain(role="cop", params=strategy_params("cop"), game_params=default_params)


def _walk_unaided(
    brain: HeuristicBrain, state: GameState, target: Coord, params: GameParams
) -> list[Coord]:
    """Repeatedly call `brain._pick_move` + `engine.apply_cop_action` until
    the cop reaches `target` or the `move_ceiling` budget is exhausted.

    `_pick_move`, not `_decide_move`, is used deliberately: it isolates the
    STRAT-04 walking claim from the cop's separate barrier sub-policy
    (03-07), so a barrier placed en route can never be blamed for -- or
    credited toward -- the shortest-path result measured here.
    """
    visited = [state.cop]
    for _ in range(params.move_ceiling + 1):
        if state.cop == target:
            return visited
        obs = Observation(
            own_cell=state.cop,
            target_cell=target,
            blocked_mask=blocked_mask(state, state.cop, "cop", params),
            barriers_used=state.barriers_placed,
            turn_index=state.turn,
        )
        decision = brain._pick_move(obs, state)
        state, _ = engine.apply_cop_action(state, decision.move, None, params)
        visited.append(state.cop)
    pytest.fail(f"walk did not reach {target} within move_ceiling budget -- oscillation or dead end")
    return visited  # pragma: no cover -- pytest.fail always raises


def test_open_board_matches_bfs_oracle_with_no_manual_intervention(
    default_params: GameParams,
) -> None:
    state = engine.make_state(default_params)
    target = state.thief
    oracle_distance, _ = bfs(state, state.cop, target, "cop", default_params)

    visited = _walk_unaided(_cop_brain(default_params), state, target, default_params)

    assert len(visited) - 1 == oracle_distance
    assert len(visited) == len(set(visited)), "walk revisited a cell"


def test_barrier_pocket_matches_bfs_oracle_with_no_manual_intervention(
    default_params: GameParams,
) -> None:
    """A wall across the middle column with gaps only at the two far board
    edges (`tests/unit/strategy/test_pathfind.py`'s own pocket fixture,
    QUAL-02): the naive Manhattan-nearest neighbour walks straight into the
    wall and stalls there forever; only a barrier-aware walker arrives."""
    size = default_params.board_size
    mid = size // 2
    wall = frozenset((row, mid) for row in range(1, size - 1))
    cop_start, target = (mid, mid - 2), (mid, mid + 2)
    state = GameState(
        cop=cop_start, thief=target, barriers=wall, barriers_placed=len(wall), turn=0
    )
    oracle_distance, _ = bfs(state, cop_start, target, "cop", default_params)

    visited = _walk_unaided(_cop_brain(default_params), state, target, default_params)

    assert len(visited) - 1 == oracle_distance
    assert len(visited) == len(set(visited)), "walk revisited a cell"
