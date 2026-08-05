"""R2 proof: both roles receive their own Table-17 terminal signal exactly
once per episode, whichever role's move produced it (03-14).

Driven entirely by a scripted recording double (`ScriptedBrain`) -- no
QLearningBrain, no QTable, no encoded-key assertion anywhere in this file.
Positions come from `default_params` (config/police/game_params.json,
cop_start=(0,0) thief_start=(3,3)); the move script itself is just a
Manhattan-shortest path between the two, not a game-parameter value.
"""

from __future__ import annotations

import pathlib
import random
from dataclasses import dataclass, field

import pytest

from pursuit.constants import MoveSource, Outcome
from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.strategy_config import load_strategy_config
from pursuit.strategy.base import Decision
from training.harness import EpisodeConfig, Player, run_episode

_CONFIG_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "config"

# Shortest orthogonal path from cop_start (0,0) to thief_start (3,3): one cell
# per step, row-then-col -- not a PARAMETERS.md value, just this test's script.
_COP_PATH_TO_THIEF = [(1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3)]


@dataclass
class ScriptedBrain:
    """Fake brain: `_decide_move` pops a pre-scripted destination (STAY once
    the queue is empty); `update` records every call's (reward, terminal)
    pair. Stands in for both learner and opponent -- `run_episode` never
    calls `.update` on the opponent (proven elsewhere), so only a learner's
    ScriptedBrain ever accumulates `calls`."""

    role: str
    moves: list[tuple[int, int]] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)

    def _decide_move(self, obs, state):
        move = self.moves.pop(0) if self.moves else obs.own_cell
        return Decision(move=move, source=MoveSource.QTABLE, barrier=None)

    def update(self, prev_key, action, reward, next_key, *, terminal=False):
        self.calls.append({"reward": reward, "terminal": terminal})


def _game_params() -> GameParams:
    return load_game_params(_CONFIG_DIR / "police" / "game_params.json")


def _strategy_params(role: str):
    name = "police" if role == "cop" else "thief"
    return load_strategy_config(_CONFIG_DIR / name / "strategy.json")


def _capture_episode(learner_role: str):
    """Cop walks straight onto the thief (who never moves) -- deterministic
    CAPTURE, always on the cop's 6th move. Returns (result, learner_brain,
    opponent_brain)."""
    game_params = _game_params()
    cop_brain = ScriptedBrain(role="cop", moves=list(_COP_PATH_TO_THIEF))
    thief_brain = ScriptedBrain(role="thief")  # empty queue -- always STAY
    brains = {"cop": cop_brain, "thief": thief_brain}
    opponent_role = "thief" if learner_role == "cop" else "cop"
    learner = Player(role=learner_role, brain=brains[learner_role])
    opponent = Player(role=opponent_role, brain=brains[opponent_role])
    config = EpisodeConfig(game_params=game_params, learner_params=_strategy_params(learner_role))
    result = run_episode(learner, opponent, config, rng=random.Random(0))
    return result, brains[learner_role], brains[opponent_role]


def _survival_episode(learner_role: str):
    """Neither side ever moves off its start cell -- no capture is possible,
    so the game runs to `survival_threshold` and SURVIVAL fires."""
    game_params = _game_params()
    cop_brain = ScriptedBrain(role="cop")  # empty queue -- always STAY
    thief_brain = ScriptedBrain(role="thief")  # empty queue -- always STAY
    brains = {"cop": cop_brain, "thief": thief_brain}
    opponent_role = "thief" if learner_role == "cop" else "cop"
    learner = Player(role=learner_role, brain=brains[learner_role])
    opponent = Player(role=opponent_role, brain=brains[opponent_role])
    config = EpisodeConfig(game_params=game_params, learner_params=_strategy_params(learner_role))
    result = run_episode(learner, opponent, config, rng=random.Random(0))
    return result, brains[learner_role]


def test_thief_learner_captured_by_the_cop_gets_exactly_one_terminal_update():
    """Direct inverse of the measured 300/300 one-update-worth-(-0.01) bug:
    the THIEF is not the mover, yet it must still receive its own capture
    penalty exactly once."""
    game_params = _game_params()
    result, thief_brain, cop_brain = _capture_episode("thief")

    assert result.outcome is Outcome.CAPTURE
    terminal_calls = [c for c in thief_brain.calls if c["terminal"]]
    assert len(terminal_calls) == 1
    assert terminal_calls[0]["reward"] == game_params.score_capture_thief
    assert cop_brain.calls == []  # opponent's table is never written to (project rule 2)


def test_cop_learner_gets_exactly_one_terminal_update_when_the_thief_survives():
    game_params = _game_params()
    result, cop_brain = _survival_episode("cop")

    assert result.outcome is Outcome.SURVIVAL
    terminal_calls = [c for c in cop_brain.calls if c["terminal"]]
    assert len(terminal_calls) == 1
    assert terminal_calls[0]["reward"] == game_params.score_survival_cop


def test_learners_own_terminal_move_yields_one_update_not_two():
    """The cop learner IS the mover that ends the game -- the `if`/`elif`
    split in `training/turn.py::play_turn` must fire exactly one branch."""
    result, cop_brain, _ = _capture_episode("cop")

    assert result.outcome is Outcome.CAPTURE
    terminal_calls = [c for c in cop_brain.calls if c["terminal"]]
    assert len(terminal_calls) == 1


@pytest.mark.parametrize("learner_role", ["cop", "thief"])
def test_terminal_updates_equal_episode_count_over_a_batch(learner_role: str):
    episodes = 3
    terminal_updates = 0
    for _ in range(episodes):
        result, learner_brain, _ = _capture_episode(learner_role)
        assert result.outcome is Outcome.CAPTURE
        terminal_updates += sum(1 for c in learner_brain.calls if c["terminal"])
    assert terminal_updates == episodes


def test_learner_decisions_counts_decisions_only_not_the_bystander_terminal():
    """The thief learner decides 5 times (rounds 0-4) before the cop's 6th
    move captures it on round 5 -- `learner_decisions` must equal exactly
    that, unaffected by the bystander terminal delivery."""
    result, thief_brain, _ = _capture_episode("thief")
    assert result.learner_decisions == 5
    assert len(thief_brain.calls) == 5 + 1  # 5 non-terminal + 1 terminal


def test_learner_reward_total_includes_the_bystander_terminal_reward():
    """5 non-terminal thief steps (reward_step each) plus exactly one
    bystander terminal (score_capture_thief) -- not just the step total."""
    game_params = _game_params()
    thief_params = _strategy_params("thief")
    result, _, _ = _capture_episode("thief")
    expected = 5 * thief_params.reward_step + game_params.score_capture_thief
    assert result.learner_reward_total == pytest.approx(expected)
