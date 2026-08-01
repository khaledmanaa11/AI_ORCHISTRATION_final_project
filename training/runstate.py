"""RunState: the whole-run checkpoint manifest (D-24), plus the alpha/epsilon
decay schedule (PRD Sec5, D-25) every episode reads to know its current
ε and α before a decision is made.

A checkpoint that only saved the Q-tables would silently restart ε/α and
make a resumed curve unreproducible from its own artifacts -- so RunState
carries everything else: the global episode index, each ROLE's own episode
count (role-alternating training, D-25, means cop and thief do not share
one schedule position), the seed, RNG state, a config hash, and the CSV row
count truncate_after() must agree with on resume.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass

from pursuit.shared.strategy_config import StrategyParams

_RUNSTATE_FIELDS = (
    "episode",
    "cop_episodes",
    "thief_episodes",
    "seed",
    "config_hash",
    "csv_row_count",
    "rng_state",
)


@dataclass(frozen=True)
class RunState:
    """Every field round-trips through JSON exactly (D-24)."""

    episode: int
    cop_episodes: int
    thief_episodes: int
    seed: int
    config_hash: str
    csv_row_count: int
    rng_state: dict

    def to_payload(self) -> dict:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: dict) -> RunState:
        return cls(**{name: payload[name] for name in _RUNSTATE_FIELDS})


def capture_rng_state(rng: random.Random) -> dict:
    """rng.getstate() -> {"version", "keys", "gauss_next"} (RESEARCH Sec3)."""
    version, keys, gauss_next = rng.getstate()
    return {"version": version, "keys": list(keys), "gauss_next": gauss_next}


def restore_rng_state(rng: random.Random, state: dict) -> None:
    """Inverse of capture_rng_state -- the next N draws match exactly."""
    rng.setstate((state["version"], tuple(state["keys"]), state["gauss_next"]))


def config_hash(params: StrategyParams) -> str:
    """SHA-256 of params, canonical-JSON-serialized (sort_keys, no whitespace).

    A small LOCAL reimplementation of this project's one canonicalisation
    convention (see pursuit.network.config_hash.canonical_json) rather than
    an import of it: training/ must carry zero import from pursuit.network
    (D-17) even though config_hash there is transport-agnostic, because the
    verification gate checks the import boundary structurally, not by
    intent.
    """
    canonical = json.dumps(asdict(params), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def epsilon_at(role_episode: int, params: StrategyParams) -> float:
    """Linear decay epsilon_start -> epsilon_floor over epsilon_decay_episodes."""
    span = min(role_episode, params.epsilon_decay_episodes)
    decayed = (params.epsilon_start - params.epsilon_floor) * span / params.epsilon_decay_episodes
    return max(params.epsilon_floor, params.epsilon_start - decayed)


def alpha_at(role_episode: int, params: StrategyParams) -> float:
    """Linear decay alpha -> alpha_floor over alpha_decay_episodes (D-25)."""
    span = min(role_episode, params.alpha_decay_episodes)
    decayed = (params.alpha - params.alpha_floor) * span / params.alpha_decay_episodes
    return max(params.alpha_floor, params.alpha - decayed)
