"""HeuristicBrain: the fully playable non-learned baseline (STRAT-02, GATE-4).

`_pick_move` delegates entirely to `fallback.pick()` -- HeuristicBrain has no
Q-table and no learning; it *is* the heuristic, so there is exactly one
implementation of the pursue/evade heuristic anywhere in the codebase
(QUAL-02, `fallback.py` owns it). This makes HeuristicBrain both the
fallback's logic home during a live game and the objective GATE-4 opponent
`QLearningBrain` (03-06) must beat (D-07, D-14).

Instance state only (D-03, project rule 2): role/params/game_params are
plain instance attributes set once at construction, never a module-level
mutable global or a class-level attribute -- two HeuristicBrain instances
(one per process, one per role) cannot observe or mutate each other.
"""

from __future__ import annotations

from pursuit.constants import MoveSource
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy import fallback
from pursuit.strategy.barriers import cop_decision
from pursuit.strategy.base import BrainBase, Decision, Observation

HEURISTIC_BRAIN_NAME = "pursuit.strategy.heuristic:HeuristicBrain"


class HeuristicBrain(BrainBase):
    """Bayes+BFS fallback only -- playable for either role from turn 1, no training required."""

    def __init__(self, *, role: str, params: StrategyParams, game_params: GameParams) -> None:
        self._role = role
        self._params = params
        self._game_params = game_params

    def _pick_move(self, obs: Observation, state: GameState) -> Decision:
        picked = fallback.pick(obs, state, self._role, self._game_params)
        return Decision(move=picked.move, source=MoveSource.HEURISTIC)

    def _decide_move(self, obs: Observation, state: GameState) -> Decision:
        """Move XOR barrier for the cop via the shared `cop_decision` (D-12);
        the thief's barrier is unconditionally None -- not "usually None"
        (STRAT-05)."""
        movement = self._pick_move(obs, state)
        if self._role != "cop":
            return Decision(move=movement.move, source=movement.source)
        return cop_decision(
            movement,
            state,
            self._game_params,
            obs.target_cell,
            self._params.barrier_min_gain,
        )
