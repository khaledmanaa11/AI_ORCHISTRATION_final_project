"""Tests for training/eval_stats.py -- GATE-4's statistical honesty (E5).

Pure-math module, no game/config fixtures needed. Known-value checks pin the
McNemar exact test and the two-proportion z against hand-computed numbers,
not just "runs without crashing" -- a sign-flipped or off-by-one formula
here would silently make GATE-4 meaningless.
"""

from __future__ import annotations

import pytest

from training.eval_stats import (
    GateVerdict,
    evaluate_gate,
    mcnemar_exact_pvalue,
    normal_sf,
    two_proportion_z,
)


def test_mcnemar_zero_discordant_pairs_is_not_significant() -> None:
    assert mcnemar_exact_pvalue(0, 0) == 1.0


def test_mcnemar_known_value_extreme_discordance() -> None:
    # n=10, k=0: p = 2 * C(10,0) / 2**10 = 2/1024
    assert mcnemar_exact_pvalue(0, 10) == pytest.approx(2 / 1024)


def test_mcnemar_known_value_moderate_discordance() -> None:
    # n=10, k=1: p = 2 * (C(10,0) + C(10,1)) / 2**10 = 2 * 11/1024
    assert mcnemar_exact_pvalue(1, 9) == pytest.approx(2 * 11 / 1024)


def test_mcnemar_is_symmetric_in_its_two_arguments() -> None:
    assert mcnemar_exact_pvalue(2, 8) == mcnemar_exact_pvalue(8, 2)


def test_mcnemar_caps_at_one_rather_than_overshooting() -> None:
    assert mcnemar_exact_pvalue(1, 1) == 1.0


def test_two_proportion_z_zero_when_either_sample_empty() -> None:
    assert two_proportion_z(5, 0, 5, 10) == 0.0
    assert two_proportion_z(5, 10, 5, 0) == 0.0


def test_two_proportion_z_zero_when_proportions_identical() -> None:
    assert two_proportion_z(50, 100, 50, 100) == 0.0


def test_two_proportion_z_positive_when_a_beats_b() -> None:
    z = two_proportion_z(80, 100, 50, 100)
    assert z == pytest.approx(4.4476, abs=1e-3)


def test_two_proportion_z_sign_flips_when_arguments_swap() -> None:
    assert two_proportion_z(80, 100, 50, 100) == pytest.approx(
        -two_proportion_z(50, 100, 80, 100)
    )


def test_normal_sf_at_zero_is_one_half() -> None:
    assert normal_sf(0.0) == pytest.approx(0.5)


def test_normal_sf_decreases_as_z_increases() -> None:
    assert normal_sf(2.0) < normal_sf(1.0) < normal_sf(0.0)


def _gate(**overrides) -> GateVerdict:
    fields = {
        "role": "cop",
        "learner_wins": 130,
        "baseline_wins": 100,
        "n_games": 200,
        "learner_only_wins": 40,
        "baseline_only_wins": 10,
        "win_rate_margin": 0.10,
        "min_win_rate_absolute": 0.55,
        "significance_alpha": 0.05,
    }
    fields.update(overrides)
    return evaluate_gate(**fields)


def test_evaluate_gate_passes_when_all_three_conditions_hold() -> None:
    verdict = _gate()
    assert verdict.learner_win_rate == pytest.approx(0.65)
    assert verdict.baseline_win_rate == pytest.approx(0.50)
    assert verdict.margin == pytest.approx(0.15)
    assert verdict.meets_margin is True
    assert verdict.meets_absolute_floor is True
    assert verdict.is_significant is True
    assert verdict.passed is True


def test_evaluate_gate_fails_below_the_margin() -> None:
    verdict = _gate(learner_wins=105, learner_only_wins=10, baseline_only_wins=5)
    assert verdict.meets_margin is False
    assert verdict.passed is False


def test_evaluate_gate_fails_below_the_absolute_floor() -> None:
    """A weak baseline can make the MARGIN trivially clearable; the absolute
    floor guards exactly that degenerate case (AI-SPEC Sec5)."""
    verdict = _gate(
        learner_wins=105, baseline_wins=10, learner_only_wins=100, baseline_only_wins=0,
    )
    assert verdict.learner_win_rate == pytest.approx(0.525)
    assert verdict.meets_margin is True
    assert verdict.meets_absolute_floor is False
    assert verdict.passed is False


def test_evaluate_gate_fails_when_not_significant() -> None:
    """A margin that clears the bar on tiny, noisy discordant counts must
    not pass without significance (AI-SPEC Sec5 MDE discussion)."""
    verdict = _gate(learner_wins=130, baseline_wins=100, learner_only_wins=2, baseline_only_wins=1)
    assert verdict.meets_margin is True
    assert verdict.is_significant is False
    assert verdict.passed is False


def test_evaluate_gate_never_shares_state_across_roles() -> None:
    """D-25: two independent calls for the two roles never share an object."""
    cop = _gate(role="cop")
    thief = _gate(role="thief", learner_wins=90, baseline_wins=100, learner_only_wins=5, baseline_only_wins=15)
    assert cop.role == "cop"
    assert thief.role == "thief"
    assert cop.passed != thief.passed
