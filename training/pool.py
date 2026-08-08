"""The opponent pool: who our policy actually plays during self-play.

Pure self-play learns to beat its own past selves and nothing else, and the
measured cost of that is in this repo already -- the sweep that motivated this
pool found a thief weight that survives 64% against a barrier-using chaser and
10% against a barrier-blind one. A policy tuned against one archetype is actively
wrong against the other, and we do not get to choose which one the league sends.

So the pool is anchored by FIXED, non-drifting members. The prior and the two
naive archetypes never improve, which is the point: they keep measuring the same
thing all the way through the run, and a generation that starts losing to them
has regressed no matter what the self-play curve says.
"""

from __future__ import annotations

import random

from pursuit.shared.config import GameParams
from pursuit.shared.resolution import ResolutionRules
from pursuit.strategy.naive import ChaserCop, GreedyEvader
from pursuit.strategy.valuebrain import ValueSearchBrain
from pursuit.strategy.weights import PRIOR

CURRENT = "current"
PAST = "past"
PRIOR_ANCHOR = "prior"
NAIVE = "naive"
NAIVE_BLIND = "naive_blind"

#: Sampling weights. Self-play is the largest single share because it is the only
#: member that keeps getting harder, but together the fixed anchors outweigh it:
#: robustness against an unknown opponent beats squeezing the last points out of
#: an opponent we already beat.
MIX = (
    (CURRENT, 0.35),
    (PAST, 0.20),
    (PRIOR_ANCHOR, 0.15),
    (NAIVE, 0.20),
    (NAIVE_BLIND, 0.10),
)


def sample_kind(rng: random.Random) -> str:
    """Draw one pool member by MIX."""
    draw = rng.random()
    cumulative = 0.0
    for kind, share in MIX:
        cumulative += share
        if draw < cumulative:
            return kind
    return MIX[-1][0]


def build(
    kind: str,
    role: str,
    weights: tuple,
    snapshots: list,
    params: GameParams,
    rules: ResolutionRules,
    rng: random.Random,
) -> object:
    """Construct the pool member *kind* for *role*.

    `snapshots` holds frozen past weight vectors; an empty list degrades PAST to
    the prior rather than silently reusing the current weights, which would make
    an early generation pure self-play without saying so.
    """
    if kind == NAIVE:
        return _naive(role, params, rng, use_barriers=True)
    if kind == NAIVE_BLIND:
        return _naive(role, params, rng, use_barriers=False)

    vector = weights
    if kind == PRIOR_ANCHOR:
        vector = PRIOR
    elif kind == PAST:
        vector = rng.choice(snapshots) if snapshots else PRIOR

    return ValueSearchBrain(
        role, game_params=params, rules=rules, weights=vector, rng=random.Random(rng.random())
    )


def _naive(role: str, params: GameParams, rng: random.Random, *, use_barriers: bool):
    """The archetype for *role*. The thief has no barrier variant to vary."""
    seed = random.Random(rng.random())
    if role == "cop":
        return ChaserCop("cop", game_params=params, use_barriers=use_barriers, rng=seed)
    return GreedyEvader("thief", game_params=params, rng=seed)


def learner(
    role: str,
    weights: tuple,
    params: GameParams,
    rules: ResolutionRules,
    rng: random.Random,
    epsilon: float,
) -> ValueSearchBrain:
    """Build the seat under training, with exploration switched on."""
    return ValueSearchBrain(
        role,
        game_params=params,
        rules=rules,
        weights=weights,
        epsilon=epsilon,
        rng=random.Random(rng.random()),
    )
