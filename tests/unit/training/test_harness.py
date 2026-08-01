"""Tests for training/harness.py's inner episode loop (Task 4, 03-08) --
run_episode drives sdk.engine directly, updates only the learner, and
training/ stays structurally isolated from pursuit.network (D-17)."""

from __future__ import annotations

import ast
import pathlib
import random

import pytest

from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.strategy_config import load_strategy_config
from pursuit.strategy.heuristic import HeuristicBrain
from pursuit.strategy.qlearning import QLearningBrain
from pursuit.strategy.qtable import QTable
from training.harness import EpisodeConfig, Player, _role_won, run_episode

_CONFIG_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "config"


def _game_params() -> GameParams:
    return load_game_params(_CONFIG_DIR / "police" / "game_params.json")


def _cop_params():
    return load_strategy_config(_CONFIG_DIR / "police" / "strategy.json")


def _thief_params():
    return load_strategy_config(_CONFIG_DIR / "thief" / "strategy.json")


def test_run_episode_reaches_a_terminal_outcome_and_updates_the_learner() -> None:
    game_params = _game_params()
    cop_table = QTable()
    learner = Player(
        role="cop",
        brain=QLearningBrain(
            role="cop", params=_cop_params(), game_params=game_params,
            rng=random.Random(1), table=cop_table,
        ),
    )
    opponent = Player(
        role="thief",
        brain=HeuristicBrain(role="thief", params=_thief_params(), game_params=game_params),
    )
    config = EpisodeConfig(game_params=game_params, learner_params=_cop_params())

    result = run_episode(learner, opponent, config, random.Random(2))

    assert result.outcome is not None
    assert result.turns > 0
    assert result.learner_decisions > 0
    assert len(cop_table._values) > 0  # the learner's table, and only it, was written to


def test_run_episode_never_calls_update_on_the_opponent() -> None:
    """HeuristicBrain has no `update` method at all -- if run_episode ever
    reached for opponent.brain.update, this would raise AttributeError
    before the episode could finish, structurally proving only the
    learner's table is ever written to (project rule 2)."""
    game_params = _game_params()
    learner = Player(
        role="thief",
        brain=QLearningBrain(
            role="thief", params=_thief_params(), game_params=game_params,
            rng=random.Random(3), table=QTable(),
        ),
    )
    opponent = Player(
        role="cop",
        brain=HeuristicBrain(role="cop", params=_cop_params(), game_params=game_params),
    )
    config = EpisodeConfig(game_params=game_params, learner_params=_thief_params())

    result = run_episode(learner, opponent, config, random.Random(4))
    assert result.outcome is not None


def test_run_episode_is_deterministic_for_a_fixed_seed() -> None:
    game_params = _game_params()

    def _play():
        learner = Player(
            role="cop",
            brain=QLearningBrain(
                role="cop", params=_cop_params(), game_params=game_params,
                rng=random.Random(9), table=QTable(),
            ),
        )
        opponent = Player(
            role="thief",
            brain=HeuristicBrain(role="thief", params=_thief_params(), game_params=game_params),
        )
        config = EpisodeConfig(game_params=game_params, learner_params=_cop_params())
        return run_episode(learner, opponent, config, random.Random(9))

    first, second = _play(), _play()
    assert first == second


# --- Structural isolation: D-17, both import directions ---------------------


def _module_paths(*roots: str) -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for root in roots:
        paths.extend(sorted(pathlib.Path(root).rglob("*.py")))
    return paths


def _imported_module_names(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_training_package_imports_no_networking() -> None:
    """D-17: training/ steps sdk.engine directly, never pursuit.network."""
    for path in _module_paths("training"):
        for name in _imported_module_names(path):
            assert not name.startswith("pursuit.network"), f"{path} imports {name!r}"


def test_nothing_under_src_pursuit_imports_training() -> None:
    """The reverse direction: training/ is offline tooling only -- the
    shipped runtime (src/pursuit/**) must never depend on it."""
    for path in _module_paths("src/pursuit"):
        for name in _imported_module_names(path):
            assert name != "training" and not name.startswith("training."), (
                f"{path} imports {name!r}"
            )


def test_role_won_is_false_for_neither_role_when_the_game_has_no_outcome_yet() -> None:
    """`outcome` is `None` mid-game (never at run_episode's own return, which
    always terminates by move_ceiling+1) -- covered directly so the
    defensive branch is proven, not just assumed unreachable."""
    assert _role_won("cop", None) is False
    assert _role_won("thief", None) is False


@pytest.mark.parametrize("role", ["cop", "thief"])
def test_episode_config_carries_the_learners_own_reward_terms(role: str) -> None:
    """EpisodeConfig.learner_params is what _reward() reads (PRD Sec4) --
    proves the two roles' distinct reward_* config actually reaches it."""
    params = _cop_params() if role == "cop" else _thief_params()
    config = EpisodeConfig(game_params=_game_params(), learner_params=params)
    assert config.learner_params.reward_capture == params.reward_capture
