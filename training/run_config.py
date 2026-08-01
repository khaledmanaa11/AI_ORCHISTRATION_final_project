"""Run-level dataclasses shared by training/loop.py and training/loop_setup.py.

Split into their own module so those two can both depend on the types
without importing each other (loop_setup.py's helpers are called BY
loop.py's run_training(), never the reverse).
"""

from __future__ import annotations

from dataclasses import dataclass

from pursuit.shared.config import GameParams
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy.qtable import QTable
from training.runstate import RunState


@dataclass(frozen=True)
class TrainingRunConfig:
    """One shared GameParams; cop/thief each keep their own StrategyParams
    (brain_class, qtable_path, and reward_* legitimately differ per role)."""

    game_params: GameParams
    cop_params: StrategyParams
    thief_params: StrategyParams


@dataclass
class RunResult:
    """What run_training() hands back -- both final tables plus the
    manifest a caller can inspect without re-reading it off disk."""

    cop_table: QTable
    thief_table: QTable
    run_state: RunState
