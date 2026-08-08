"""Tests for outcome scoring (BASE-07, D-14).

Extracted from the now-deleted test_capture.py (plan 03-14, joint-turn
migration): shared/capture.py and its capture/survival tests are superseded
by sdk/terminal.py and test_terminal.py, but shared/outcome.py -- and
score_outcome -- is untouched engine.py-facade code (`engine.score`) that
still needs its own dedicated coverage, so these six tests move here rather
than disappearing with the rest of test_capture.py.
"""

import dataclasses

import pytest

from pursuit.constants import Outcome
from pursuit.shared.outcome import score_outcome


def test_capture_score(default_params) -> None:
    """CAPTURE outcome scores come from params.score_capture_* (BASE-07, D-14)."""
    cop_score, thief_score = score_outcome(Outcome.CAPTURE, default_params)
    assert cop_score == default_params.score_capture_cop
    assert thief_score == default_params.score_capture_thief


def test_survival_score(default_params) -> None:
    """SURVIVAL outcome scores come from params.score_survival_* (BASE-07, D-14)."""
    cop_score, thief_score = score_outcome(Outcome.SURVIVAL, default_params)
    assert cop_score == default_params.score_survival_cop
    assert thief_score == default_params.score_survival_thief


def test_tie_score(default_params) -> None:
    """TIE outcome returns (score_tie, score_tie) from params (D-14)."""
    cop_score, thief_score = score_outcome(Outcome.TIE, default_params)
    assert cop_score == default_params.score_tie
    assert thief_score == default_params.score_tie


def test_technical_loss_score(default_params) -> None:
    """TECHNICAL_LOSS outcome scores come from params.score_technical_loss_* (BASE-07)."""
    cop_score, thief_score = score_outcome(Outcome.TECHNICAL_LOSS, default_params)
    assert cop_score == default_params.score_technical_loss_cop
    assert thief_score == default_params.score_technical_loss_thief


def test_technical_loss_score_from_config(default_params) -> None:
    """TECHNICAL_LOSS score is config-sourced, not hardcoded (CR-02, BASE-07).

    Build a params object with non-zero technical_loss values and confirm
    score_outcome returns those exact values, proving no literal (0, 0) exists.
    """
    custom = dataclasses.replace(
        default_params,
        score_technical_loss_cop=7,
        score_technical_loss_thief=3,
    )
    cop_score, thief_score = score_outcome(Outcome.TECHNICAL_LOSS, custom)
    assert cop_score == 7
    assert thief_score == 3


def test_score_outcome_invalid_raises(default_params) -> None:
    """Unrecognised outcome raises ValueError (correctness guard)."""
    with pytest.raises(ValueError, match="Unrecognised outcome"):
        score_outcome("not_an_outcome", default_params)  # type: ignore[arg-type]
