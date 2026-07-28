"""Stubs for BASE-08 — config load and error path tests."""

import pytest


def test_config_loads_board_size() -> None:
    """Config loads board_size from game_params.json (no hardcoded value)."""
    pytest.skip("stub — implemented in plan 01-01")


def test_config_loads_barrier_quota() -> None:
    """Config loads barrier_quota from game_params.json."""
    pytest.skip("stub — implemented in plan 01-01")


def test_config_loads_scoring() -> None:
    """Config loads the full scoring sub-dict from game_params.json."""
    pytest.skip("stub — implemented in plan 01-01")


def test_missing_key_raises() -> None:
    """A missing required key raises an error at load time, not silently."""
    pytest.skip("stub — implemented in plan 01-01")
