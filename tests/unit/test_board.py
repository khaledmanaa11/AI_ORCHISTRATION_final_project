"""Stubs for BASE-01 — board movement validation tests."""

import pytest


def test_orthogonal_move_accepted() -> None:
    """An orthogonal (N/S/E/W) step to an empty cell is accepted."""
    pytest.skip("stub — implemented in plan 01-01")


def test_diagonal_move_rejected() -> None:
    """A diagonal step is always rejected."""
    pytest.skip("stub — implemented in plan 01-01")


def test_stay_is_legal() -> None:
    """Staying in place is always a legal move."""
    pytest.skip("stub — implemented in plan 01-01")


def test_out_of_bounds_rejected() -> None:
    """A move that would leave the board is rejected."""
    pytest.skip("stub — implemented in plan 01-01")


def test_onto_barrier_rejected() -> None:
    """A move onto a barriered cell is rejected."""
    pytest.skip("stub — implemented in plan 01-01")
