"""Tests for the self-play opponent pool (training/pool.py).

Anchored by three FIXED, non-drifting members (the prior and both naive
archetypes) so self-play cannot learn only to beat its own past selves --
this file proves each pool member actually builds the brain its name
promises, and that PAST degrades to the prior when no snapshot exists yet.
"""

from __future__ import annotations

import random

from pursuit.shared.resolution import PREFERRED
from pursuit.strategy.naive import ChaserCop, GreedyEvader
from pursuit.strategy.valuebrain import ValueSearchBrain
from pursuit.strategy.weights import PRIOR
from training import pool

_CURRENT_WEIGHTS = tuple(0.1 * i for i in range(15))
_SNAPSHOT = tuple(0.2 * i for i in range(15))


def test_sample_kind_always_returns_a_known_member(default_params) -> None:
    rng = random.Random(0)
    seen = {pool.sample_kind(rng) for _ in range(500)}
    assert seen <= {kind for kind, _ in pool.MIX}


def test_sample_kind_covers_every_member_given_enough_draws() -> None:
    rng = random.Random(1)
    seen = {pool.sample_kind(rng) for _ in range(2000)}
    assert seen == {kind for kind, _ in pool.MIX}


def test_build_naive_returns_sealing_chaser_cop(default_params) -> None:
    brain = pool.build(
        pool.NAIVE, "cop", _CURRENT_WEIGHTS, [], default_params, PREFERRED, random.Random(0)
    )
    assert isinstance(brain, ChaserCop)
    assert brain.use_barriers is True


def test_build_naive_blind_returns_non_sealing_chaser_cop(default_params) -> None:
    brain = pool.build(
        pool.NAIVE_BLIND, "cop", _CURRENT_WEIGHTS, [], default_params, PREFERRED, random.Random(0)
    )
    assert isinstance(brain, ChaserCop)
    assert brain.use_barriers is False


def test_build_naive_for_thief_role_returns_greedy_evader(default_params) -> None:
    brain = pool.build(
        pool.NAIVE, "thief", _CURRENT_WEIGHTS, [], default_params, PREFERRED, random.Random(0)
    )
    assert isinstance(brain, GreedyEvader)


def test_build_prior_anchor_uses_the_prior_weights(default_params) -> None:
    brain = pool.build(
        pool.PRIOR_ANCHOR, "cop", _CURRENT_WEIGHTS, [], default_params, PREFERRED, random.Random(0)
    )
    assert isinstance(brain, ValueSearchBrain)
    assert brain.weights == PRIOR


def test_build_current_uses_the_passed_weights(default_params) -> None:
    brain = pool.build(
        pool.CURRENT, "cop", _CURRENT_WEIGHTS, [], default_params, PREFERRED, random.Random(0)
    )
    assert brain.weights == _CURRENT_WEIGHTS


def test_build_past_falls_back_to_prior_with_no_snapshots(default_params) -> None:
    brain = pool.build(
        pool.PAST, "cop", _CURRENT_WEIGHTS, [], default_params, PREFERRED, random.Random(0)
    )
    assert brain.weights == PRIOR


def test_build_past_draws_from_the_snapshot_ring(default_params) -> None:
    brain = pool.build(
        pool.PAST, "cop", _CURRENT_WEIGHTS, [_SNAPSHOT], default_params, PREFERRED, random.Random(0)
    )
    assert brain.weights == _SNAPSHOT


def test_learner_builds_a_value_search_brain_with_the_requested_epsilon(default_params) -> None:
    brain = pool.learner(
        "thief", _CURRENT_WEIGHTS, default_params, PREFERRED, random.Random(0), epsilon=0.3
    )
    assert isinstance(brain, ValueSearchBrain)
    assert brain.role == "thief"
    assert brain.epsilon == 0.3
    assert brain.weights == _CURRENT_WEIGHTS
