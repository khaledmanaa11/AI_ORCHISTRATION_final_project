"""Stubs for BASE-02 — barrier placement and quota tests."""

import pytest


def test_barrier_placed_makes_cell_impassable() -> None:
    """A successfully placed barrier makes the cell impassable to both agents."""
    pytest.skip("stub — implemented in plan 01-02")


def test_quota_exceeded() -> None:
    """Attempting to place a barrier when quota is 0 is rejected."""
    pytest.skip("stub — implemented in plan 01-02")


def test_rejected_no_quota_cost() -> None:
    """A rejected placement (over-quota or invalid target) does not consume quota."""
    pytest.skip("stub — implemented in plan 01-02")


def test_barrier_on_occupied_rejected() -> None:
    """Placing a barrier on a cell occupied by the opponent is a capture, not a placement."""
    pytest.skip("stub — implemented in plan 01-02")


def test_barrier_on_own_cell_rejected() -> None:
    """Placing a barrier on the cop's own cell is rejected."""
    pytest.skip("stub — implemented in plan 01-02")
