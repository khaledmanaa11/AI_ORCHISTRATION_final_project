"""Per-turn mechanics for training/harness.py's episode loop -- split out at
the 150-code-line gate (03-14, repeats the established 03-05..03-13 pattern).
`play_turn` decides-then-applies one role's move and delivers the learner's
own Q-update; this is also where R2's terminal-by-opponent case is handled --
see harness.py's module docstring for the full R2/R4 account.

`Player`/`EpisodeConfig` are imported only under `TYPE_CHECKING` -- this
module is a leaf `training.harness` depends on, so a runtime import the other
way would be circular; the deferred-annotation-string mechanics
(`from __future__ import annotations`) make the type-only import safe.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pursuit.constants import MoveSource, Outcome, action_for
from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.base import Decision, Observation
from pursuit.strategy.encoding import blocked_mask, encode_state
from training.rewards import step_reward, terminal_reward

if TYPE_CHECKING:
    from training.harness import EpisodeConfig, Player

_NO_NEXT_KEY = ""  # terminal=True updates never read next_key (R4) -- placeholder only.


def play_turn(
    state: GameState,
    role: str,
    seats: dict,
    learner: Player,
    params: EpisodeConfig,
    pending: tuple[str, int] | None,
) -> tuple:
    obs = _observation(state, role, params.game_params)
    decision = seats[role].brain._decide_move(obs, state)
    if role == "cop":
        next_state, outcome = engine.apply_cop_action(
            state, decision.move, decision.barrier, params.game_params
        )
    else:
        next_state, outcome = engine.apply_thief_move(state, decision.move, params.game_params)

    step, bystander = None, None
    if role == learner.role:
        prev_key = encode_state(obs, params.learner_params, params.game_params)
        action = int(action_for(obs.own_cell, decision.move))
        reward = _update_learner(learner, prev_key, action, outcome, next_state, decision, params)
        step = (reward, decision.source is MoveSource.FALLBACK)
        pending = (prev_key, action)
    elif outcome is not None and pending is not None:
        # The OPPONENT's move ended the episode -- the learner never decided
        # this turn, so attribute the terminal transition to its most recent
        # (prev_key, action) this episode instead of fabricating one (R2).
        prev_key, action = pending
        reward = terminal_reward(learner.role, outcome, params.game_params)
        learner.brain.update(prev_key, action, reward, _NO_NEXT_KEY, terminal=True)
        bystander = reward
    return next_state, outcome, step, bystander, pending


def _update_learner(
    learner: Player,
    prev_key: str,
    action: int,
    outcome: Outcome | None,
    next_state: GameState,
    decision: Decision,
    params: EpisodeConfig,
) -> float:
    """Deliver the learner's own transition -- terminal (R2/R4) when this
    move ended the episode, ordinary step-shaped otherwise (PRD Sec4)."""
    if outcome is not None:
        reward = terminal_reward(learner.role, outcome, params.game_params)
        learner.brain.update(prev_key, action, reward, _NO_NEXT_KEY, terminal=True)
        return reward
    reward = step_reward(learner.role, decision.barrier is not None, params.learner_params)
    next_obs = _observation(next_state, learner.role, params.game_params)
    next_key = encode_state(next_obs, params.learner_params, params.game_params)
    learner.brain.update(prev_key, action, reward, next_key, terminal=False)
    return reward


def _observation(state: GameState, role: str, game_params: GameParams) -> Observation:
    own = state.cop if role == "cop" else state.thief
    target = state.thief if role == "cop" else state.cop  # known-target contract (D-11)
    return Observation(
        own_cell=own,
        target_cell=target,
        blocked_mask=blocked_mask(state, own, role, game_params),
        barriers_used=state.barriers_placed,
        turn_index=state.turn,
    )
