"""Stubs for §10.4 gate integration tests — full game-loop scenarios."""

import pytest


def test_legal_turn_sequence() -> None:
    """A sequence of legal turns runs without error through the engine (GATE-1)."""
    pytest.skip("stub — implemented in plan 01-04")


def test_quota_gate_mid_game() -> None:
    """Barrier quota is correctly enforced mid-game; rejections cost no quota (GATE-2)."""
    pytest.skip("stub — implemented in plan 01-04")


def test_all_three_capture_types() -> None:
    """All three capture types (cop-on-thief, barrier-on-thief, no-legal-move) are
    reachable via the engine in a full turn sequence (GATE-3)."""
    pytest.skip("stub — implemented in plan 01-04")
