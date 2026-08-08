"""Play one batch-synchronous generation of self-play games.

Weights are FROZEN for the whole generation and updated once at the end. That is
not a performance convenience -- it removes within-batch non-stationarity by
construction. If the weights moved mid-batch, every sample would be drawn against
a slightly different opponent than the one the update is fitted to, which is the
same moving-target failure that made run 1's learner unable to converge.

The learner alternates seats game by game. One weight vector serves both, so a
generation that trained only the cop would drift the thief's judgement as a side
effect and nobody would notice until the gate.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from pursuit.shared.config import GameParams
from pursuit.shared.resolution import ResolutionRules
from training import pool
from training.joint_game import play_game
from training.starts import sample_start


@dataclass(frozen=True)
class GenerationResult:
    """Everything one generation produced, for the update and for the curve."""

    records: tuple
    cop_games: int
    cop_captures: int
    thief_games: int
    thief_survivals: int
    starts: tuple

    @property
    def cop_rate(self) -> float:
        """Capture rate while the learner held the cop seat."""
        return self.cop_captures / self.cop_games if self.cop_games else 0.0

    @property
    def thief_rate(self) -> float:
        """Survival rate while the learner held the thief seat."""
        return self.thief_survivals / self.thief_games if self.thief_games else 0.0


def play_generation(
    weights: tuple,
    snapshots: list,
    games: int,
    epsilon: float,
    params: GameParams,
    rules: ResolutionRules,
    rng: random.Random,
) -> GenerationResult:
    """Play *games* games with frozen *weights* and return the batch.

    Seats alternate strictly rather than randomly so every generation reports
    both rates on the same sample size -- a noisy split would make the two curves
    incomparable across generations for no benefit.
    """
    records = []
    starts = []
    cop_games = cop_captures = thief_games = thief_survivals = 0

    for index in range(games):
        learner_role = "cop" if index % 2 == 0 else "thief"
        opponent_role = "thief" if learner_role == "cop" else "cop"
        kind = pool.sample_kind(rng)

        learner = pool.learner(learner_role, weights, params, rules, rng, epsilon)
        opponent = pool.build(kind, opponent_role, weights, snapshots, params, rules, rng)
        cop_brain, thief_brain = (
            (learner, opponent) if learner_role == "cop" else (opponent, learner)
        )

        start = sample_start(params, rng)
        starts.append(start)
        record = play_game(cop_brain, thief_brain, params, rules, start)
        records.append(record)

        if learner_role == "cop":
            cop_games += 1
            cop_captures += record.captured
        else:
            thief_games += 1
            thief_survivals += not record.captured

    return GenerationResult(
        records=tuple(records),
        cop_games=cop_games,
        cop_captures=cop_captures,
        thief_games=thief_games,
        thief_survivals=thief_survivals,
        starts=tuple(starts),
    )


def epsilon_for(generation: int, total: int, start: float, floor: float) -> float:
    """Linear exploration decay from *start* to *floor* across the run.

    Linear rather than geometric on purpose: geometric decay spends most of the
    run at the floor, and the later generations are exactly where the pool is
    hardest and fresh states are most worth reaching.
    """
    if total <= 1:
        return floor
    share = generation / (total - 1)
    return start + (floor - start) * share
