"""Tests for BrainBase, Observation, Decision, and the frozen Action/MoveSource
contracts they depend on (STRAT-03, STRAT-07, D-11, D-12)."""

from dataclasses import FrozenInstanceError

import pytest

from pursuit.constants import Action, MoveSource, action_for, cell_for
from pursuit.shared.state import GameState
from pursuit.strategy.base import BrainBase, Decision, Observation


def _obs(**overrides) -> Observation:
    fields = {
        "own_cell": (3, 3),
        "target_cell": (5, 5),
        "blocked_mask": 0,
        "barriers_used": 0,
        "turn_index": 0,
    }
    fields.update(overrides)
    return Observation(**fields)


def _state() -> GameState:
    return GameState(cop=(0, 0), thief=(6, 6), barriers=frozenset(), barriers_placed=0, turn=0)


class _CompleteBrain(BrainBase):
    """Minimal concrete brain implementing both abstract methods."""

    def _pick_move(self, obs: Observation, state: GameState) -> Decision:
        return Decision(move=obs.own_cell, source=MoveSource.HEURISTIC)

    def _decide_move(self, obs: Observation, state: GameState) -> Decision:
        return self._pick_move(obs, state)


class _IncompleteBrain(BrainBase):
    """Implements neither abstract method -- must not be instantiable."""


def test_subclass_with_both_methods_instantiates() -> None:
    brain = _CompleteBrain()
    decision = brain._decide_move(_obs(), _state())
    assert decision.source is MoveSource.HEURISTIC
    assert decision.barrier is None


def test_subclass_missing_methods_cannot_instantiate() -> None:
    with pytest.raises(TypeError):
        _IncompleteBrain()


def test_observation_is_frozen() -> None:
    obs = _obs()
    with pytest.raises(FrozenInstanceError):
        obs.own_cell = (0, 0)  # type: ignore[misc]


def test_decision_is_frozen() -> None:
    decision = Decision(move=(1, 1), source=MoveSource.EQUILIBRIUM)
    with pytest.raises(FrozenInstanceError):
        decision.move = (2, 2)  # type: ignore[misc]


def test_decision_barrier_defaults_to_none() -> None:
    decision = Decision(move=(1, 1), source=MoveSource.FALLBACK)
    assert decision.barrier is None


def test_action_has_exactly_five_pinned_members() -> None:
    assert len(Action) == 5
    assert Action.NORTH == 0
    assert Action.SOUTH == 1
    assert Action.EAST == 2
    assert Action.WEST == 3
    assert Action.STAY == 4


@pytest.mark.parametrize("action", list(Action))
def test_cell_for_action_for_round_trip(action: Action) -> None:
    own_cell = (3, 3)
    dest = cell_for(action, own_cell)
    assert action_for(own_cell, dest) is action


def test_action_for_rejects_non_adjacent_cells() -> None:
    with pytest.raises(ValueError):
        action_for((3, 3), (6, 6))
