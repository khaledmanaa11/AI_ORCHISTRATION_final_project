"""play_game: the one game loop, and the simultaneity property that defines it.

The contract that matters (module doc): both brains decide from the SAME
pre-turn state before either action is resolved. A caller that interleaves the
two calls with a resolve has reintroduced the sequential bug this phase
removes -- which is exactly what the identity check below asserts.
"""

from __future__ import annotations

from pursuit.constants import MoveSource, Outcome
from pursuit.sdk.actions import CopAction
from pursuit.shared.resolution import PREFERRED
from pursuit.shared.state import GameState
from pursuit.strategy.base import Decision
from training.joint_game import observe, play_game, to_cop_action


def _state(cop, thief, barriers=frozenset(), placed=0, turn=0):
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=turn)


class _StayBrain:
    """Records every state it's handed and always stays in place."""

    def __init__(self, role):
        self.role = role
        self.states = []

    def _decide_move(self, obs, state):
        self.states.append(state)
        own = state.cop if self.role == "cop" else state.thief
        return Decision(move=own, source=MoveSource.HEURISTIC, barrier=None)


class _FixedBrain:
    """Always returns the same pre-built Decision -- for a scripted capture."""

    def __init__(self, decision):
        self.decision = decision

    def _decide_move(self, obs, state):
        return self.decision


def test_play_game_returns_a_terminal_outcome(default_params):
    start = _state((0, 0), (6, 6))
    record = play_game(_StayBrain("cop"), _StayBrain("thief"), default_params, PREFERRED, start=start)
    assert record.outcome is Outcome.SURVIVAL


def test_states_start_at_the_start_state_and_end_at_the_terminal_state(default_params):
    start = _state((0, 0), (6, 6))
    record = play_game(_StayBrain("cop"), _StayBrain("thief"), default_params, PREFERRED, start=start)
    assert record.states[0] == start
    assert record.states[-1].turn == default_params.survival_threshold


def test_turns_is_consistent_with_the_record_length(default_params):
    start = _state((0, 0), (6, 6))
    record = play_game(_StayBrain("cop"), _StayBrain("thief"), default_params, PREFERRED, start=start)
    assert record.turns == len(record.states) - 1


def test_cop_target_matches_a_survival_outcome(default_params):
    start = _state((0, 0), (6, 6))
    record = play_game(_StayBrain("cop"), _StayBrain("thief"), default_params, PREFERRED, start=start)
    assert record.cop_target == -1.0
    assert record.captured is False


def test_cop_target_matches_a_capture_outcome(default_params):
    """Rule 46: the barrier lands on the thief's PRE-move cell -- capture no
    matter what the thief's fixed reply is."""
    start = _state((3, 3), (3, 4))
    cop = _FixedBrain(Decision(move=(3, 3), source=MoveSource.HEURISTIC, barrier=(3, 4)))
    thief = _FixedBrain(Decision(move=(3, 5), source=MoveSource.HEURISTIC, barrier=None))
    record = play_game(cop, thief, default_params, PREFERRED, start=start)
    assert record.outcome is Outcome.CAPTURE
    assert record.cop_target == 1.0
    assert record.captured is True


def test_observe_reports_each_roles_own_and_target_cell(default_params):
    state = _state((1, 2), (4, 5))
    cop_obs = observe(state, "cop")
    thief_obs = observe(state, "thief")
    assert (cop_obs.own_cell, cop_obs.target_cell) == (state.cop, state.thief)
    assert (thief_obs.own_cell, thief_obs.target_cell) == (state.thief, state.cop)


def test_to_cop_action_maps_a_barrier_decision():
    decision = Decision(move=(2, 2), source=MoveSource.HEURISTIC, barrier=(2, 3))
    assert to_cop_action(decision) == CopAction(barrier=(2, 3))


def test_to_cop_action_maps_a_plain_move_decision():
    decision = Decision(move=(2, 2), source=MoveSource.HEURISTIC, barrier=None)
    assert to_cop_action(decision) == CopAction(move=(2, 2))


def test_both_brains_decide_from_the_identical_state_object(default_params):
    """The property this phase exists to guarantee: no interleaved resolve ever
    lets one seat see the other's already-applied move."""
    start = _state((0, 0), (6, 6))
    cop, thief = _StayBrain("cop"), _StayBrain("thief")
    play_game(cop, thief, default_params, PREFERRED, start=start)
    assert len(cop.states) == len(thief.states) > 0
    for cop_state, thief_state in zip(cop.states, thief.states, strict=True):
        assert cop_state is thief_state
