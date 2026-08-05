"""Reward functions for the offline training harness (PRD Sec4; R2 fix, 03-14).

Extracted from `training/harness.py::_reward`. Two pure functions:

- `terminal_reward` sources Table 17's fixed capture/survival magnitudes from
  `GameParams` for the LEARNER's own role -- never the moving role, since
  `engine.apply_cop_action` emits CAPTURE on the cop's turn and
  `engine.apply_thief_move` emits SURVIVAL on the thief's, but both roles
  must receive their own terminal signal (R2). The thief's capture penalty
  is the relative +5-vs-+10 gap already in `GameParams.score_*`; no other
  magnitude is invented here.
- `step_reward` carries the unchanged non-terminal shaping term: a per-step
  cost plus the cop-only barrier-placement bonus.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.shared.config import GameParams
from pursuit.shared.strategy_config import StrategyParams

# (role, outcome) -> the matching GameParams.score_* field name (Table 17).
_TERMINAL_FIELDS = {
    ("cop", Outcome.CAPTURE): "score_capture_cop",
    ("thief", Outcome.CAPTURE): "score_capture_thief",
    ("cop", Outcome.SURVIVAL): "score_survival_cop",
    ("thief", Outcome.SURVIVAL): "score_survival_thief",
}


def terminal_reward(role: str, outcome: Outcome, game_params: GameParams) -> float:
    """Table-17 terminal magnitude for `role` when the episode ends in
    `outcome`. `role` is always the LEARNER's own role, whichever role's
    move actually produced `outcome`.

    Raises on any (role, outcome) pair with no Table-17 mapping -- Phase 3
    emits only CAPTURE and SURVIVAL, and silently returning 0.0 for an
    unmapped pair (e.g. TIE, TECHNICAL_LOSS) would reintroduce the
    zero-signal bug this module exists to close.
    """
    field = _TERMINAL_FIELDS.get((role, outcome))
    if field is None:
        raise ValueError(f"no Table-17 terminal reward for role={role!r} outcome={outcome!r}")
    return float(getattr(game_params, field))


def step_reward(role: str, barrier_placed: bool, params: StrategyParams) -> float:
    """Non-terminal shaping term (PRD Sec4): `params.reward_step`, plus
    `params.reward_barrier_gain` when the cop placed a barrier this step.

    `choose_barrier` (03-07) never proposes a candidate below
    `barrier_min_gain`, so a non-None barrier declaration this step already
    IS "strictly increases the thief's BFS distance to escape" -- no second
    BFS call is needed here to award the bonus.
    """
    reward = params.reward_step
    if role == "cop" and barrier_placed:
        reward += params.reward_barrier_gain
    return reward
