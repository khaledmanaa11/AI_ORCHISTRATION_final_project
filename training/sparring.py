"""Sparring pool: weighted opponent sampling, once per episode (RESEARCH Sec2).

Sampling happens ONCE PER EPISODE, never per turn -- a mid-episode swap
breaks the stationarity the Q-target assumes. That is structural here:
sample_opponent is the only function that touches the pool's weights or its
ring buffer, and the episode loop (harness.py) calls it exactly once before
stepping sdk.engine, never again mid-episode.

Weights are training.sparring_mix = [heuristic, past_self, reference]
(0.30/0.50/0.20). A member with zero available candidates (no ring/anchor
yet, or no reference configured) drops out and the remaining weights
RENORMALIZE rather than silently biasing toward whichever branch happens to
catch the leftover mass (D-21, D-23) -- e.g. reference absent renormalizes
0.30/0.50 to 0.375/0.625.

Past-self sampling is delta-uniform (Bansal et al., ICLR 2018): uniform over
the newest `selfplay_delta` fraction of the ring buffer, plus one pinned
anchor snapshot that stays eligible even after the ring has rotated past it,
so the pool can never drift wholesale into one degenerate equilibrium.
"""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field

from pursuit.shared.config import GameParams
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy.base import BrainBase
from pursuit.strategy.heuristic import HeuristicBrain
from pursuit.strategy.qlearning import QLearningBrain
from pursuit.strategy.qtable import QTable

_KINDS = ("heuristic", "past_self", "reference")


class ReadOnlyQTable:
    """A frozen, read-only view over a QTable snapshot (project rule 2).

    get/visits/best_action pass through; set/bump_visit raise, so a learner
    can never mutate the table backing its own sampled opponent -- there is
    no shared LIVE table object between the two, satisfying project rule 2
    structurally, not just by convention.
    """

    def __init__(self, table: QTable) -> None:
        self._table = table

    def get(self, key: str, action: int) -> float:
        return self._table.get(key, action)

    def visits(self, key: str) -> int:
        return self._table.visits(key)

    def best_action(self, key: str) -> int:
        return self._table.best_action(key)

    def set(self, *_args, **_kwargs) -> None:
        raise TypeError("opponent table is frozen/read-only for the episode")

    def bump_visit(self, *_args, **_kwargs) -> None:
        raise TypeError("opponent table is frozen/read-only for the episode")


@dataclass
class SparringPool:
    """One role's opponent pool -- `opponent_role` is who this pool is FOR.

    `ring`/`anchor` hold past-self snapshots of `opponent_role`'s OWN table,
    admitted by the harness on `pool_snapshot_every` cadence. `reference` is
    a pre-built, role-bound adapter brain, or None when unconfigured/absent
    (D-21) -- built once per run, never per episode.
    """

    opponent_role: str
    opponent_params: StrategyParams
    game_params: GameParams
    ring: deque = field(default_factory=lambda: deque(maxlen=1))
    anchor: QTable | None = None
    reference: BrainBase | None = None

    def admit(self, live_table: QTable) -> None:
        """Snapshot `live_table` into the ring via QTable.copy() (QUAL-02) --
        never a disk round trip, so this stays cheap on the
        pool_snapshot_every cadence."""
        snapshot = live_table.copy()
        if self.anchor is None:
            self.anchor = snapshot
        self.ring.append(snapshot)


@dataclass(frozen=True)
class Opponent:
    kind: str
    brain: BrainBase


def sample_opponent(pool: SparringPool, rng: random.Random, params: StrategyParams) -> Opponent:
    """Weighted choice across {heuristic, past_self, reference} (D-21, D-23)."""
    weights = _available_weights(pool, params.sparring_mix)
    kind = rng.choices(list(weights), weights=list(weights.values()), k=1)[0]
    if kind == "heuristic":
        brain = HeuristicBrain(
            role=pool.opponent_role, params=pool.opponent_params, game_params=pool.game_params
        )
    elif kind == "past_self":
        brain = _sample_past_self(pool, rng, params.selfplay_delta)
    else:
        brain = pool.reference
    return Opponent(kind=kind, brain=brain)


def _available_weights(pool: SparringPool, sparring_mix: list) -> dict:
    raw = dict(
        zip(
            _KINDS,
            [
                sparring_mix[0],
                sparring_mix[1] if (pool.ring or pool.anchor is not None) else 0.0,
                sparring_mix[2] if pool.reference is not None else 0.0,
            ],
            strict=True,
        )
    )
    total = sum(raw.values())
    return {kind: weight / total for kind, weight in raw.items() if weight > 0.0}


def _sample_past_self(pool: SparringPool, rng: random.Random, delta: float) -> QLearningBrain:
    newest_n = max(1, math.ceil(len(pool.ring) * delta))
    candidates = list(pool.ring)[-newest_n:]
    if pool.anchor is not None and pool.anchor not in candidates:
        candidates.append(pool.anchor)
    snapshot = rng.choice(candidates)
    return QLearningBrain(
        role=pool.opponent_role,
        params=pool.opponent_params,
        game_params=pool.game_params,
        table=ReadOnlyQTable(snapshot),
    )
