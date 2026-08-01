"""QLearningBrain: e-greedy tabular Q-policy with a visit-count fallback (STRAT-01/07).

Implements docs/PRD_rl_strategy.md Sec5 (update rule, e-greedy exploration) and
Sec6 (STRAT-02 fallback trigger) exactly -- a disagreement with the PRD is a bug
here, not a choice. Training that fills the table is 03-08; this module only
selects moves from a table already on disk and applies the one-line update.

Instance state only (D-03, project rule 2): role/params/game_params/table/rng
are all set once in __init__; two brains (any role combination) never share
one of these objects.
"""

from __future__ import annotations

import dataclasses
import random

from pursuit.constants import Action, MoveSource, cell_for
from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy import fallback
from pursuit.strategy.barriers import choose_barrier
from pursuit.strategy.base import BrainBase, Decision, Observation
from pursuit.strategy.encoding import encode_state
from pursuit.strategy.qtable import QTable

QLEARNING_BRAIN_NAME = "pursuit.strategy.qlearning:QLearningBrain"

_ACTION_COUNT = len(Action)


class QLearningBrain(BrainBase):
    """Table argmax when a state is sufficiently visited; fallback otherwise."""

    def __init__(
        self,
        *,
        role: str,
        params: StrategyParams,
        game_params: GameParams,
        rng: random.Random | None = None,
        table: QTable | None = None,
    ) -> None:
        self._role = role
        self._params = params
        self._game_params = game_params
        self._rng = rng if rng is not None else random.Random()
        # Loaded ONCE here (E11) -- a missing/corrupt table fails loud via
        # QTable.load, never silently plays a trained agent as random.
        # 03-08's sparring pool instead injects an in-memory, read-only
        # snapshot (training.sparring.ReadOnlyQTable) for a frozen past-self
        # opponent, skipping disk I/O entirely -- `table` is duck-typed
        # (get/set/visits/best_action/bump_visit), never required to be a
        # real QTable instance.
        self._table = table if table is not None else QTable.load(params.qtable_path)
        # Mutable per-instance knobs: 03-08's training loop reassigns both
        # every episode from their decaying schedules (D-25); match/eval
        # play never touches them, so they stay at config's epsilon_eval
        # (0.0, greedy) / params.alpha.
        self.epsilon = params.epsilon_eval
        self.alpha = params.alpha

    def _pick_move(self, obs: Observation, state: GameState) -> Decision:
        key = encode_state(obs, self._params, self._game_params)
        if self._table.visits(key) < self._params.min_visits:
            return fallback.pick(obs, state, self._role, self._game_params)
        if self._rng.random() < self.epsilon:
            return self._explore(state)
        action = self._table.best_action(key)
        move = cell_for(Action(action), obs.own_cell)
        return Decision(move=move, source=MoveSource.QTABLE)

    def _explore(self, state: GameState) -> Decision:
        """Uniformly random LEGAL action (PRD Sec5) -- still source=QTABLE:
        this is the policy exploring inside its own trained region, not a
        delegation to the heuristic fallback."""
        legal = sorted(get_legal_moves(state, self._role, self._game_params))
        move = self._rng.choice(legal)
        return Decision(move=move, source=MoveSource.QTABLE)

    def _decide_move(self, obs: Observation, state: GameState) -> Decision:
        """Movement first, then the cop's barrier stage (D-12); the thief's
        barrier is unconditionally None -- not "usually None" (STRAT-05)."""
        movement = self._pick_move(obs, state)
        barrier = None
        if self._role == "cop":
            post_move = dataclasses.replace(state, cop=movement.move)
            barrier = choose_barrier(
                post_move, self._game_params, obs.target_cell, self._params.barrier_min_gain
            )
        return Decision(move=movement.move, source=movement.source, barrier=barrier)

    def update(self, prev_key: str, action: int, reward: float, next_key: str) -> None:
        """One Q-learning step, PRD Sec5, verbatim; bumps prev_key's visit
        count. A plain method so 03-08's harness drives it directly rather
        than reaching into the table itself."""
        old = self._table.get(prev_key, action)
        best_next = max(self._table.get(next_key, a) for a in range(_ACTION_COUNT))
        target = reward + self._params.gamma * best_next
        self._table.set(prev_key, action, old + self.alpha * (target - old))
        self._table.bump_visit(prev_key)
