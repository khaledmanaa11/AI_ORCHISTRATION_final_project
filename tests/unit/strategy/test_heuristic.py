"""Tests for HeuristicBrain -- the fully playable STRAT-02 baseline (GATE-4)."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

from pursuit.constants import MoveSource
from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams, load_strategy_config
from pursuit.strategy import registry
from pursuit.strategy.base import Observation
from pursuit.strategy.heuristic import HEURISTIC_BRAIN_NAME, HeuristicBrain

_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"
_STRATEGY_PATHS = {
    "cop": _CONFIG_DIR / "police" / "strategy.json",
    "thief": _CONFIG_DIR / "thief" / "strategy.json",
}


def _heuristic_params(role: str) -> StrategyParams:
    """Real per-role strategy.json with brain_class swapped to HeuristicBrain
    -- 03-06 has not landed QLearningBrain yet, so this is how build_brain is
    proven "from config" ahead of that plan."""
    return dataclasses.replace(
        load_strategy_config(_STRATEGY_PATHS[role]), brain_class=HEURISTIC_BRAIN_NAME
    )


def _obs_from_state(state: GameState, agent: str) -> Observation:
    own = state.cop if agent == "cop" else state.thief
    target = state.thief if agent == "cop" else state.cop
    return Observation(
        own_cell=own, target_cell=target, blocked_mask=0, barriers_used=0, turn_index=state.turn
    )


def test_builds_via_build_brain_from_config_for_both_roles(default_params: GameParams) -> None:
    cop_brain = registry.build_brain("cop", _heuristic_params("cop"), default_params)
    thief_brain = registry.build_brain("thief", _heuristic_params("thief"), default_params)
    assert isinstance(cop_brain, HeuristicBrain)
    assert isinstance(thief_brain, HeuristicBrain)


def test_every_decision_carries_heuristic_source(default_params: GameParams) -> None:
    brain = HeuristicBrain(role="cop", params=_heuristic_params("cop"), game_params=default_params)
    state = engine.make_state(default_params)
    decision = brain._decide_move(_obs_from_state(state, "cop"), state)
    assert decision.source is MoveSource.HEURISTIC
    # 03-07: the fresh initial state is a wide-open board with no chokepoint,
    # so choose_barrier legitimately returns None here too -- see
    # test_barriers.py for the wired, non-None case.
    assert decision.barrier is None


def test_two_instances_are_independent(default_params: GameParams) -> None:
    cop_brain = HeuristicBrain(role="cop", params=_heuristic_params("cop"), game_params=default_params)
    thief_brain = HeuristicBrain(
        role="thief", params=_heuristic_params("thief"), game_params=default_params
    )
    assert cop_brain is not thief_brain
    cop_brain._role = "mutated"
    assert thief_brain._role == "thief"


def test_no_class_level_mutable_state() -> None:
    """D-03/project rule 2: nothing on HeuristicBrain's class body could let
    one instance's state leak into another's -- only __init__-assigned
    instance attributes exist."""
    tree = ast.parse(Path("src/pursuit/strategy/heuristic.py").read_text(encoding="utf-8"))
    class_node = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    for node in class_node.body:
        assert not isinstance(node, ast.Assign | ast.AnnAssign)


def test_plays_a_complete_game_to_terminal_outcome(default_params: GameParams) -> None:
    cop_brain = HeuristicBrain(role="cop", params=_heuristic_params("cop"), game_params=default_params)
    thief_brain = HeuristicBrain(
        role="thief", params=_heuristic_params("thief"), game_params=default_params
    )
    state = engine.make_state(default_params)

    outcome = None
    for _ in range(default_params.move_ceiling):
        cop_decision = cop_brain._decide_move(_obs_from_state(state, "cop"), state)
        state, outcome = engine.apply_cop_action(
            state, cop_decision.move, cop_decision.barrier, default_params
        )
        if outcome is not None:
            break
        thief_decision = thief_brain._decide_move(_obs_from_state(state, "thief"), state)
        state, outcome = engine.apply_thief_move(state, thief_decision.move, default_params)
        if outcome is not None:
            break

    assert outcome is not None
