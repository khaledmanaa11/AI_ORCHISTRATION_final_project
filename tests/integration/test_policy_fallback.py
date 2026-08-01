"""GATE-2 / E3 + E4 -- Q-policy with fallback (STRAT-01/02, PRD §10.4 b).

E3: a state key with `visits >= min_visits` is served by the table's argmax
(`decision.source is QTABLE`); a key below threshold -- including the
boundary itself, swept from both sides -- is served by the fallback. Built
through `registry.build_brain` from real per-role config (STRAT-03), not by
constructing `QLearningBrain` directly, so this gate also proves the config
seam routes correctly, not just the class in isolation.

E4: on a barrier-pocket board, the fallback never prefers a move that is
Manhattan-closer but BFS-further -- the naive-Manhattan failure signature
AI-SPEC FM-3 names.
"""

from __future__ import annotations

import dataclasses

import pytest

from pursuit.constants import MoveSource
from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy import fallback, registry
from pursuit.strategy.base import Observation
from pursuit.strategy.encoding import encode_state
from pursuit.strategy.pathfind import UNREACHABLE, bfs
from pursuit.strategy.qtable import QTable
from tests.integration.conftest import strategy_params

_OBS = Observation(own_cell=(1, 1), target_cell=(4, 4), blocked_mask=0, barriers_used=0, turn_index=0)


def _seeded_table(key: str, visits: int, action: int = 2, value: float = 5.0) -> QTable:
    table = QTable()
    table.set(key, action, value)
    for _ in range(visits):
        table.bump_visit(key)
    return table


@pytest.mark.parametrize("visits", range(0, 24))
def test_min_visits_boundary_routes_decision_source(
    tmp_path, default_params: GameParams, visits: int
) -> None:
    """Swept across every point 0..min_visits+3 (min_visits=20 in the real
    config): the boundary itself, not just its two extremes, is asserted."""
    params = strategy_params("cop", qtable_path=tmp_path / "qtable.json")
    key = encode_state(_OBS, params, default_params)
    _seeded_table(key, visits).save(params.qtable_path)

    brain = registry.build_brain("cop", params, default_params)
    state = GameState(
        cop=_OBS.own_cell, thief=_OBS.target_cell, barriers=frozenset(), barriers_placed=0, turn=0
    )
    decision = brain._pick_move(_OBS, state)

    expected = MoveSource.QTABLE if visits >= params.min_visits else MoveSource.FALLBACK
    assert decision.source is expected


def _wall_pocket_fixture(default_params: GameParams):
    """Same wall shape as `test_pathfind.py`'s own pocket fixture (QUAL-02):
    gaps only at the two far board edges force a real detour."""
    size = default_params.board_size
    mid = size // 2
    wall = frozenset((row, mid) for row in range(1, size - 1))
    cop_start, target = (mid, mid - 2), (mid, mid + 2)
    state = GameState(cop=cop_start, thief=target, barriers=wall, barriers_placed=len(wall), turn=0)
    return state, cop_start, target


def test_barrier_pocket_fallback_never_prefers_manhattan_over_bfs(
    default_params: GameParams,
) -> None:
    state, cop_start, target = _wall_pocket_fixture(default_params)
    obs = dataclasses.replace(_OBS, own_cell=cop_start, target_cell=target, barriers_used=state.barriers_placed)

    decision = fallback.pick(obs, state, "cop", default_params)

    candidates = sorted(get_legal_moves(state, "cop", default_params))
    naive_move = min(candidates, key=lambda c: abs(c[0] - target[0]) + abs(c[1] - target[1]))
    naive_distance, _ = bfs(
        dataclasses.replace(state, cop=naive_move), naive_move, target, "cop", default_params
    )
    chosen_distance, _ = bfs(
        dataclasses.replace(state, cop=decision.move), decision.move, target, "cop", default_params
    )

    assert chosen_distance != UNREACHABLE
    assert decision.move != naive_move, (
        "fallback picked the raw-Manhattan-nearest candidate -- "
        "exactly the naive-Manhattan failure signature (AI-SPEC FM-3)"
    )
    assert chosen_distance <= naive_distance
