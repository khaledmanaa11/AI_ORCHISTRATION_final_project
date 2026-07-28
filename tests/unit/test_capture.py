"""Stubs for BASE-03 through BASE-07 — capture detection and scoring tests."""

import pytest


def test_cop_on_thief_capture() -> None:
    """Cop moving onto thief's cell triggers CAPTURE (BASE-03)."""
    pytest.skip("stub — implemented in plan 01-03")


def test_barrier_on_thief_capture() -> None:
    """Cop placing a barrier on thief's cell triggers CAPTURE (BASE-04)."""
    pytest.skip("stub — implemented in plan 01-03")


def test_no_legal_move_capture() -> None:
    """Thief with no legal moves is captured at the start of its turn (BASE-05)."""
    pytest.skip("stub — implemented in plan 01-03")


def test_one_move_available_no_capture() -> None:
    """Thief with exactly one legal move is NOT captured (BASE-05 negative)."""
    pytest.skip("stub — implemented in plan 01-03")


def test_survival_at_threshold() -> None:
    """Reaching the survival_threshold without a capture → SURVIVAL outcome (BASE-06)."""
    pytest.skip("stub — implemented in plan 01-03")


def test_game_continues_below_threshold() -> None:
    """Before the survival_threshold is reached the game continues (BASE-06 negative)."""
    pytest.skip("stub — implemented in plan 01-03")


def test_capture_score() -> None:
    """CAPTURE outcome returns cop=20, thief=5 from the scoring config (BASE-07)."""
    pytest.skip("stub — implemented in plan 01-03")


def test_survival_score() -> None:
    """SURVIVAL outcome returns cop=5, thief=10 from the scoring config (BASE-07)."""
    pytest.skip("stub — implemented in plan 01-03")
