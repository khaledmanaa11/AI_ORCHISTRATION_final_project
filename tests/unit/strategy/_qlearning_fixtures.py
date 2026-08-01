"""Shared construction helpers for the QLearningBrain test suite (03-06).

Not a test module itself (no `test_` prefix, so pytest never collects it) --
follows the `tests/unit/_fakes_agent.py` precedent for a shared, non-test
helper file, extracted so `test_qlearning.py` and `test_qlearning_learning.py`
(the 150-line-gate split, see 03-06-SUMMARY.md) do not duplicate the same
fixture-construction code (QUAL-02).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams, load_strategy_config
from pursuit.strategy.base import Observation
from pursuit.strategy.qtable import QTable

CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"
STRATEGY_PATHS = {
    "cop": CONFIG_DIR / "police" / "strategy.json",
    "thief": CONFIG_DIR / "thief" / "strategy.json",
}
MIN_VISITS = load_strategy_config(STRATEGY_PATHS["cop"]).min_visits


def params_for(role: str, qtable_path: Path) -> StrategyParams:
    """Real per-role strategy.json with qtable_path repointed at a tmp file --
    the real artifacts/qtable_<role>.json does not exist until 03-08 trains
    one, and QLearningBrain must fail loud, not silently, without it."""
    return dataclasses.replace(
        load_strategy_config(STRATEGY_PATHS[role]), qtable_path=str(qtable_path)
    )


def make_obs(own=(1, 1), target=(4, 4), blocked=0, barriers=0, turn=0) -> Observation:
    return Observation(
        own_cell=own,
        target_cell=target,
        blocked_mask=blocked,
        barriers_used=barriers,
        turn_index=turn,
    )


def make_state(own, target) -> GameState:
    return GameState(cop=own, thief=target, barriers=frozenset(), barriers_placed=0, turn=0)


def seeded_table(key: str, visits: int, action: int = 2, value: float = 5.0) -> QTable:
    """A table with exactly `visits` recorded against `key`, and a clear
    argmax at `action` -- the value only matters for tests that assert the
    table branch's chosen move (D-08 boundary tests only care about count)."""
    table = QTable()
    table.set(key, action, value)
    for _ in range(visits):
        table.bump_visit(key)
    return table
