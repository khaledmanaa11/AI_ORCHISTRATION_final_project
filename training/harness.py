"""Episode loop: steps pursuit.sdk.engine directly, never pursuit.network
(D-17) -- the SDK is pure and synchronous, so episodes run at full
in-process speed. training/loop.py (the outer, resumable run driver, Task 4
continued) calls `run_episode` once per episode with a freshly-sampled,
FROZEN opponent (RESEARCH Sec2) -- only `learner.brain.update(...)` is ever
called; the opponent's `_decide_move` is read-only from this module's view.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from pursuit.constants import MoveSource, Outcome, action_for
from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy.base import BrainBase, Decision, Observation
from pursuit.strategy.encoding import blocked_mask, encode_state


@dataclass(frozen=True)
class Player:
    """A role-bound brain -- either the episode's learner or its opponent."""

    role: str
    brain: BrainBase


@dataclass(frozen=True)
class EpisodeConfig:
    """`learner_params` supplies both the reward_* terms (PRD Sec4) and the
    turn_bucket_fractions encode_state needs -- both already live on
    StrategyParams, so this carries the one object rather than unpacking it
    into four separate scalar fields."""

    game_params: GameParams
    learner_params: StrategyParams


@dataclass(frozen=True)
class EpisodeResult:
    outcome: Outcome
    turns: int
    learner_reward_total: float
    learner_decisions: int
    learner_fallbacks: int
    learner_won: bool


def run_episode(
    learner: Player, opponent: Player, params: EpisodeConfig, rng: random.Random
) -> EpisodeResult:
    """Drive one full game, cop-then-thief per turn (D-12's own order).

    `rng` is accepted for signature symmetry with the sampling call this
    always follows in training/loop.py; per-turn exploration randomness is
    already owned by each brain's own seeded instance rng (D-19), so this
    loop itself never draws from it.
    """
    seats = {learner.role: learner, opponent.role: opponent}
    state = engine.make_state(params.game_params)
    total_reward, decisions, fallbacks = 0.0, 0, 0
    outcome: Outcome | None = None
    for _ in range(params.game_params.move_ceiling + 1):
        state, outcome, step = _turn(state, "cop", seats, learner, params)
        total_reward, decisions, fallbacks = _accumulate(step, total_reward, decisions, fallbacks)
        if outcome is not None:
            break
        state, outcome, step = _turn(state, "thief", seats, learner, params)
        total_reward, decisions, fallbacks = _accumulate(step, total_reward, decisions, fallbacks)
        if outcome is not None:
            break
    return EpisodeResult(
        outcome=outcome,
        turns=state.turn,
        learner_reward_total=total_reward,
        learner_decisions=decisions,
        learner_fallbacks=fallbacks,
        learner_won=_role_won(learner.role, outcome),
    )


def _turn(
    state: GameState, role: str, seats: dict, learner: Player, params: EpisodeConfig
) -> tuple:
    obs = _observation(state, role, params.game_params)
    decision = seats[role].brain._decide_move(obs, state)
    if role == "cop":
        next_state, outcome = engine.apply_cop_action(
            state, decision.move, decision.barrier, params.game_params
        )
    else:
        next_state, outcome = engine.apply_thief_move(state, decision.move, params.game_params)
    reward = _reward(role, outcome, decision.barrier is not None, params.learner_params)
    step = None
    if role == learner.role:
        _update_learner(learner, decision, obs, next_state, reward, params)
        step = (reward, decision.source is MoveSource.FALLBACK)
    return next_state, outcome, step


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


def _reward(role: str, outcome: Outcome | None, barrier_placed: bool, params: StrategyParams) -> float:
    """PRD Sec4. `choose_barrier` never proposes a candidate below
    `barrier_min_gain` (03-07), so a non-None barrier declaration this step
    already IS "strictly increases the thief's BFS distance to escape" --
    no second BFS call is needed to award the shaping term."""
    if outcome is Outcome.CAPTURE:
        return params.reward_capture if role == "cop" else 0.0
    if outcome is Outcome.SURVIVAL:
        return params.reward_survival if role == "thief" else 0.0
    step = params.reward_step
    if role == "cop" and barrier_placed:
        step += params.reward_barrier_gain
    return step


def _update_learner(
    learner: Player,
    decision: Decision,
    obs: Observation,
    next_state: GameState,
    reward: float,
    params: EpisodeConfig,
) -> None:
    prev_key = encode_state(obs, params.learner_params, params.game_params)
    next_obs = _observation(next_state, learner.role, params.game_params)
    next_key = encode_state(next_obs, params.learner_params, params.game_params)
    action = action_for(obs.own_cell, decision.move)
    learner.brain.update(prev_key, int(action), reward, next_key)


def _accumulate(step: tuple | None, total_reward: float, decisions: int, fallbacks: int) -> tuple:
    if step is None:
        return total_reward, decisions, fallbacks
    reward, was_fallback = step
    return total_reward + reward, decisions + 1, fallbacks + (1 if was_fallback else 0)


def _role_won(role: str, outcome: Outcome | None) -> bool:
    if outcome is Outcome.CAPTURE:
        return role == "cop"
    if outcome is Outcome.SURVIVAL:
        return role == "thief"
    return False
