"""Tests for the bounded, adaptive reliability coefficient (Task 2, D-51)."""

import pathlib

import pytest

from pursuit.shared.belief_config import load_belief_config
from pursuit.strategy.reliability import Reliability

_CONFIG_DIR = pathlib.Path(__file__).parents[3] / "config"
POLICE_BELIEF = _CONFIG_DIR / "police" / "belief.json"

_MANY_OBSERVATIONS = 1000


@pytest.fixture
def belief_cfg():
    return load_belief_config(POLICE_BELIEF)


def test_a_fresh_instance_reports_the_configured_prior(belief_cfg):
    assert Reliability(belief_cfg.reliability).value == belief_cfg.reliability.prior


def test_a_thousand_maximal_contradictions_settle_at_r_min_never_below(belief_cfg):
    reliability = Reliability(belief_cfg.reliability)
    for _ in range(_MANY_OBSERVATIONS):
        reliability.observe(1.0)
        assert reliability.value >= belief_cfg.reliability.r_min
    assert reliability.value == belief_cfg.reliability.r_min


def test_a_thousand_consistent_hints_settle_at_the_prior_never_above_r_max(belief_cfg):
    reliability = Reliability(belief_cfg.reliability)
    for _ in range(_MANY_OBSERVATIONS):
        reliability.observe(0.0)
        assert reliability.value <= belief_cfg.reliability.r_max
    assert reliability.value == pytest.approx(belief_cfg.reliability.prior)


def test_recovery_climbs_back_toward_the_prior_after_a_drop(belief_cfg):
    reliability = Reliability(belief_cfg.reliability)
    for _ in range(50):
        reliability.observe(1.0)
    dropped = reliability.value
    assert dropped == belief_cfg.reliability.r_min
    for _ in range(_MANY_OBSERVATIONS):
        reliability.observe(0.0)
    assert reliability.value == pytest.approx(belief_cfg.reliability.prior)
    assert reliability.value > dropped


def test_a_bigger_contradiction_score_produces_a_bigger_downward_step(belief_cfg):
    small = Reliability(belief_cfg.reliability)
    big = Reliability(belief_cfg.reliability)
    small.observe(0.1)
    big.observe(0.9)
    assert big.value < small.value


def test_two_instances_never_share_state(belief_cfg):
    first = Reliability(belief_cfg.reliability)
    second = Reliability(belief_cfg.reliability)
    first.observe(1.0)
    assert second.value == belief_cfg.reliability.prior
    assert first.value != second.value


def test_out_of_range_score_raises(belief_cfg):
    reliability = Reliability(belief_cfg.reliability)
    with pytest.raises(ValueError, match="contradiction_score"):
        reliability.observe(1.5)
    with pytest.raises(ValueError, match="contradiction_score"):
        reliability.observe(-0.1)


def test_value_stays_within_bounds_under_a_mixed_observation_sequence(belief_cfg):
    reliability = Reliability(belief_cfg.reliability)
    scores = [0.0, 1.0, 0.3, 0.0, 0.7, 0.0, 1.0, 0.0, 0.05, 0.0]
    for score in scores * 20:
        reliability.observe(score)
        assert belief_cfg.reliability.r_min <= reliability.value <= belief_cfg.reliability.r_max
