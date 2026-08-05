"""Integration tests wiring `choose_barrier` into both brains' cop-side
`_decide_move` (STRAT-05, AI-SPEC E9, rules 16/22). Split from
test_barriers.py at the 150-line gate (Rule 3, mirrors 03-05/03-06's own
qtable/qlearning split precedent) -- pure `choose_barrier` unit tests stay in
test_barriers.py; full-game, brain-level honesty tests live here.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams, load_strategy_config
from pursuit.strategy.base import Observation
from pursuit.strategy.heuristic import HEURISTIC_BRAIN_NAME, HeuristicBrain
from pursuit.strategy.qlearning import QLearningBrain
from pursuit.strategy.qtable import QTable
from tests.unit.strategy._qlearning_fixtures import params_for

_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"
_STRATEGY_PATHS = {
    "cop": _CONFIG_DIR / "police" / "strategy.json",
    "thief": _CONFIG_DIR / "thief" / "strategy.json",
}


def _heuristic_params(role: str) -> StrategyParams:
    return dataclasses.replace(
        load_strategy_config(_STRATEGY_PATHS[role]), brain_class=HEURISTIC_BRAIN_NAME
    )


def _obs_from(state: GameState, agent: str) -> Observation:
    own = state.cop if agent == "cop" else state.thief
    target = state.thief if agent == "cop" else state.cop
    return Observation(
        own_cell=own, target_cell=target, blocked_mask=0, barriers_used=0, turn_index=state.turn
    )


def _play_and_check_honesty(cop_brain, thief_brain, params: GameParams) -> int:
    """Drive one full game; assert declared == applied on every cop barrier
    (E9, rules 16/22), quota never exceeded, and the thief never barriers.
    Returns the number of turns that actually declared a barrier."""
    state = engine.make_state(params)
    declared_count = 0
    outcome = None
    for _ in range(params.move_ceiling):
        cop_decision = cop_brain._decide_move(_obs_from(state, "cop"), state)
        before = state
        state, outcome = engine.apply_cop_action(
            state, cop_decision.move, cop_decision.barrier, params
        )
        if cop_decision.barrier is not None:
            declared_count += 1
            assert cop_decision.barrier in state.barriers
            assert cop_decision.barrier not in before.barriers
            assert state.barriers_placed == before.barriers_placed + 1
        assert state.barriers_placed <= params.barrier_quota
        if outcome is not None:
            break
        thief_decision = thief_brain._decide_move(_obs_from(state, "thief"), state)
        assert thief_decision.barrier is None
        state, outcome = engine.apply_thief_move(state, thief_decision.move, params)
        if outcome is not None:
            break
    assert outcome is not None
    return declared_count


def test_full_game_declared_equals_applied_heuristic_both_roles(
    default_params: GameParams,
) -> None:
    cop = HeuristicBrain(role="cop", params=_heuristic_params("cop"), game_params=default_params)
    thief = HeuristicBrain(
        role="thief", params=_heuristic_params("thief"), game_params=default_params
    )
    _play_and_check_honesty(cop, thief, default_params)
    # No `declared > 0` guard here: see the dedicated tripwire test below.


def test_full_game_declared_equals_applied_qlearning_cop(
    tmp_path: Path, default_params: GameParams
) -> None:
    """Same honesty/quota guarantees under QLearningBrain's own `_decide_move`
    -- a separate implementation from HeuristicBrain's, so this is not
    inferred from the test above."""
    qtable_path = tmp_path / "qtable_cop.json"
    QTable().save(qtable_path)
    cop_params = dataclasses.replace(
        load_strategy_config(_STRATEGY_PATHS["cop"]), qtable_path=str(qtable_path)
    )
    cop = QLearningBrain(role="cop", params=cop_params, game_params=default_params)
    thief = HeuristicBrain(
        role="thief", params=_heuristic_params("thief"), game_params=default_params
    )
    # No `declared > 0` guard here either: see the dedicated tripwire test below.
    _play_and_check_honesty(cop, thief, default_params)


def test_barrier_policy_is_currently_inert_under_one_step_rule(
    default_params: GameParams,
) -> None:
    """KNOWN GAP, not desired behaviour -- a tripwire, not a target to defend.

    `choose_barrier` (STRAT-05) scores candidates by how much they lengthen
    the thief's BFS route to the board corner diagonally farthest from the
    cop. The corrected one-step placement rule (rulebook Sec3.4) restricts
    every candidate to the cop's own <=4 orthogonal neighbours, which sit
    nowhere near that far corner for a full game played from the configured
    start positions -- no candidate ever clears `barrier_min_gain`, so the
    cop places ZERO barriers for an entire game. The corner-anchor objective
    cannot work under the one-step rule and is awaiting a strategy rework
    (see barriers.py's module docstring). This assertion MUST fail loudly
    the moment the barrier policy changes that -- update it, don't delete it.
    """
    cop = HeuristicBrain(role="cop", params=_heuristic_params("cop"), game_params=default_params)
    thief = HeuristicBrain(
        role="thief", params=_heuristic_params("thief"), game_params=default_params
    )
    declared = _play_and_check_honesty(cop, thief, default_params)
    assert declared == 0


def test_thief_never_barriers_under_qlearning_brain(
    tmp_path: Path, default_params: GameParams
) -> None:
    """STRAT-05: the thief's Decision.barrier is unconditionally None under
    QLearningBrain too, not just HeuristicBrain (covered above)."""
    params = params_for("thief", tmp_path / "qtable_thief.json")
    QTable().save(params.qtable_path)
    brain = QLearningBrain(role="thief", params=params, game_params=default_params)
    state = engine.make_state(default_params)
    for _ in range(5):
        decision = brain._decide_move(_obs_from(state, "thief"), state)
        assert decision.barrier is None
        state, _ = engine.apply_thief_move(state, decision.move, default_params)
