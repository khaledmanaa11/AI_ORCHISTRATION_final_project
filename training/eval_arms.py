"""GATE-4 evaluation arms: baseline (heuristic-vs-heuristic) and the two
learner arms (Q-cop vs heuristic-thief, Q-thief vs heuristic-cop), all
replayed over the identical scenario+seed grid (AI-SPEC Sec5 E5).

Deliberately NOT `training.harness.run_episode`: that function always
live-updates one designated "learner" role's Q-table (a training-only
concern) and has no branch for a brain with no `.update()` at all (the
baseline arm is heuristic-vs-heuristic -- `HeuristicBrain` never learns).
Every eval game here is READ-ONLY: `play_game` never calls `.update()` on
either brain, so a loaded Q-table's on-disk checkpoint is never touched by
evaluation, only ever read.
"""

from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass
from pathlib import Path

from pursuit.constants import Outcome
from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams, load_strategy_config
from pursuit.strategy.base import BrainBase, Observation
from pursuit.strategy.encoding import blocked_mask
from pursuit.strategy.heuristic import HeuristicBrain
from pursuit.strategy.qlearning import QLearningBrain
from pursuit.strategy.qtable import QTable
from training.eval_scenarios import Scenario

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
STRATEGY_PATHS = {
    "cop": _CONFIG_DIR / "police" / "strategy.json",
    "thief": _CONFIG_DIR / "thief" / "strategy.json",
}

ARM_BASELINE = "baseline"
ARM_COP_LEARNER = "cop_learner"
ARM_THIEF_LEARNER = "thief_learner"
ARMS = (ARM_BASELINE, ARM_COP_LEARNER, ARM_THIEF_LEARNER)


class MissingQTableError(FileNotFoundError):
    """Raised when a learner arm's configured qtable_path does not exist yet
    (Task 4 of this plan has not trained one) -- a distinct type so callers
    can tell "no table" apart from any other file-not-found in the stack."""


def strategy_params(role: str, *, qtable_path: Path | str | None = None) -> StrategyParams:
    params = load_strategy_config(STRATEGY_PATHS[role])
    if qtable_path is not None:
        params = dataclasses.replace(params, qtable_path=str(qtable_path))
    return params


def _heuristic(role: str, game_params: GameParams) -> HeuristicBrain:
    return HeuristicBrain(role=role, params=strategy_params(role), game_params=game_params)


def _qlearning(role: str, game_params: GameParams, qtable_path: Path | str, seed: int) -> QLearningBrain:
    if not Path(qtable_path).exists():
        raise MissingQTableError(f"no trained Q-table at {qtable_path}")
    params = strategy_params(role, qtable_path=qtable_path)
    table = QTable.load(qtable_path)
    return QLearningBrain(
        role=role, params=params, game_params=game_params, rng=random.Random(seed), table=table
    )


def build_arm_brains(
    arm: str, game_params: GameParams, seed: int, cop_qtable: Path | str, thief_qtable: Path | str
) -> tuple[BrainBase, BrainBase]:
    """Return `(cop_brain, thief_brain)` for one arm; raises `MissingQTableError`
    for a learner arm whose table does not exist yet."""
    if arm == ARM_BASELINE:
        return _heuristic("cop", game_params), _heuristic("thief", game_params)
    if arm == ARM_COP_LEARNER:
        return _qlearning("cop", game_params, cop_qtable, seed), _heuristic("thief", game_params)
    if arm == ARM_THIEF_LEARNER:
        return _heuristic("cop", game_params), _qlearning("thief", game_params, thief_qtable, seed)
    raise ValueError(f"unknown arm {arm!r}; known arms: {list(ARMS)}")


def _observation(state: GameState, role: str, game_params: GameParams) -> Observation:
    own = state.cop if role == "cop" else state.thief
    target = state.thief if role == "cop" else state.cop
    return Observation(
        own_cell=own,
        target_cell=target,
        blocked_mask=blocked_mask(state, own, role, game_params),
        barriers_used=state.barriers_placed,
        turn_index=state.turn,
    )


@dataclass(frozen=True)
class GameResult:
    scenario_id: str
    seed: int
    outcome: Outcome | None


def play_game(
    cop_brain: BrainBase, thief_brain: BrainBase, scenario: Scenario, seed: int, game_params: GameParams
) -> GameResult:
    """Read-only replay of one scenario to a terminal outcome (or None if the
    move_ceiling budget is exhausted without one -- should not happen since
    `evaluate_turn_end` always fires by `survival_threshold`, kept as a safe
    upper bound rather than an assumption)."""
    state = GameState(
        cop=scenario.cop_start,
        thief=scenario.thief_start,
        barriers=frozenset(scenario.preplaced_barriers),
        barriers_placed=len(scenario.preplaced_barriers),
        turn=scenario.start_turn,
    )
    outcome = None
    for _ in range(game_params.move_ceiling + 1):
        cop_decision = cop_brain._decide_move(_observation(state, "cop", game_params), state)
        state, outcome = engine.apply_cop_action(
            state, cop_decision.move, cop_decision.barrier, game_params
        )
        if outcome is not None:
            break
        thief_decision = thief_brain._decide_move(_observation(state, "thief", game_params), state)
        state, outcome = engine.apply_thief_move(state, thief_decision.move, game_params)
        if outcome is not None:
            break
    return GameResult(scenario_id=scenario.id, seed=seed, outcome=outcome)
