"""Episode loop: steps pursuit.sdk.engine directly, never pursuit.network
(D-17) -- the SDK is pure and synchronous, so episodes run at full
in-process speed. training/loop.py (the outer, resumable run driver, Task 4
continued) calls `run_episode` once per episode with a freshly-sampled,
FROZEN opponent (RESEARCH Sec2) -- only `learner.brain.update(...)` is ever
called; the opponent's `_decide_move` is read-only from this module's view.

R2 fix (03-14): both roles now receive their own Table-17 terminal signal
exactly once per episode, whichever role's move produced it -- CAPTURE is
emitted by `engine.apply_cop_action` on the cop's turn and SURVIVAL by
`engine.apply_thief_move` on the thief's, so the learner's most recent
`(prev_key, action)` this episode is threaded through the loop as `pending`
and updated when the OTHER role's move ends the game. Per-turn mechanics
(the `pending` handoff, terminal delivery, reward attribution) live in
`training/turn.py` (150-line-gate split, same pattern as loop.py/loop_setup.py
in 03-08); this module owns only the episode loop and its result bookkeeping.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from pursuit.constants import Outcome
from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy.base import BrainBase
from training.turn import play_turn


@dataclass(frozen=True)
class Player:
    """A role-bound brain -- either the episode's learner or its opponent."""

    role: str
    brain: BrainBase


@dataclass(frozen=True)
class EpisodeConfig:
    """`learner_params` supplies both the reward_* terms (PRD Sec4) and the
    `turns_remaining` field `encode_state` needs -- both already live on
    StrategyParams/GameParams, so this carries the one object rather than
    unpacking it into separate scalar fields."""

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
    pending: tuple[str, int] | None = None
    outcome: Outcome | None = None
    for _ in range(params.game_params.move_ceiling + 1):
        for role in ("cop", "thief"):
            state, outcome, step, bystander, pending = play_turn(
                state, role, seats, learner, params, pending
            )
            total_reward, decisions, fallbacks = _accumulate(
                step, total_reward, decisions, fallbacks
            )
            if bystander is not None:
                total_reward += bystander
            if outcome is not None:
                break
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
