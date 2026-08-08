"""(1+lambda) evolution strategy on the TRUE objective: league points per game.

Outcome regression fits P(cop wins), which is a proxy. This optimises the thing
the league actually scores -- expected points summed across both seats against the
fixed anchors -- with no gradient, no bootstrap and no proxy in between.

Two properties make it the right second opinion rather than a gimmick:

  * It cannot be fooled by a well-fitted value that plays badly. Fitness IS play.
  * Common random numbers. Every candidate in a generation is measured on the
    SAME game seeds, so a difference in fitness is a difference in weights and
    not a difference in luck. Without this, a 40-game sample is far too noisy to
    rank candidates and the search follows noise.

Which optimiser ships is decided by held-out evaluation (training/run_eval.py),
not by preference.
"""

from __future__ import annotations

import random

from pursuit.shared.config import GameParams
from pursuit.shared.resolution import ResolutionRules
from pursuit.strategy.naive import ChaserCop, GreedyEvader
from pursuit.strategy.valuebrain import ValueSearchBrain
from training.joint_game import play_game
from training.starts import sample_start

#: Anchors the fitness is measured against, as (our_seat, factory kwargs).
_COP_ANCHORS = ({"use_barriers": True}, {"use_barriers": False})


def fitness(
    weights: tuple,
    games: int,
    params: GameParams,
    rules: ResolutionRules,
    seeds: list,
) -> float:
    """Expected league points per game, summed over both seats.

    Raw points rather than a normalised rate on purpose: a capture is worth 20 to
    the cop and a survival 10 to the thief, so the objective already encodes which
    seat is worth more. Ceiling effects then handle the rest -- once the cop seat
    saturates, every remaining gradient is in the thief seat, which is exactly
    where the headroom is.
    """
    total = 0.0
    for seat_seed in seeds[:games]:
        total += _cop_points(weights, params, rules, seat_seed)
        for anchor in _COP_ANCHORS:
            total += _thief_points(weights, params, rules, seat_seed, anchor)
    return total / max(1, len(seeds[:games]))


def _cop_points(weights, params, rules, seed) -> float:
    """Our cop against the greedy evader."""
    rng = random.Random(seed)
    record = play_game(
        ValueSearchBrain("cop", game_params=params, rules=rules, weights=weights,
                         rng=random.Random(seed)),
        GreedyEvader("thief", game_params=params, rng=random.Random(seed + 1)),
        params, rules, sample_start(params, rng),
    )
    return params.score_capture_cop if record.captured else params.score_survival_cop


def _thief_points(weights, params, rules, seed, anchor) -> float:
    """Our thief against one chaser variant."""
    rng = random.Random(seed)
    record = play_game(
        ChaserCop("cop", game_params=params, rng=random.Random(seed + 2), **anchor),
        ValueSearchBrain("thief", game_params=params, rules=rules, weights=weights,
                         rng=random.Random(seed)),
        params, rules, sample_start(params, rng),
    )
    return params.score_capture_thief if record.captured else params.score_survival_thief


def mutate(weights: tuple, sigma: float, rng: random.Random) -> tuple:
    """Gaussian perturbation of every weight."""
    return tuple(weight + rng.gauss(0.0, sigma) for weight in weights)


def evolve(
    parent: tuple,
    generations: int,
    children: int,
    games: int,
    sigma: float,
    params: GameParams,
    rules: ResolutionRules,
    rng: random.Random,
    on_generation=None,
) -> tuple:
    """Run (1+lambda)-ES and return the best weights found.

    Elitist: the parent is re-evaluated on each generation's fresh seeds and only
    replaced by a child that beats it on those SAME seeds. A child that wins only
    because it drew easier games can never be promoted.
    """
    best = parent
    for generation in range(generations):
        seeds = [rng.randrange(1 << 30) for _ in range(games)]
        best_score = fitness(best, games, params, rules, seeds)
        scores = [best_score]

        for _ in range(children):
            candidate = mutate(best, sigma, rng)
            score = fitness(candidate, games, params, rules, seeds)
            scores.append(score)
            if score > best_score:
                best, best_score = candidate, score

        if on_generation is not None:
            on_generation(generation, best_score, max(scores), best)
    return best
