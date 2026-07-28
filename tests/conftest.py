"""Shared pytest fixtures for all test waves."""

import json
import pathlib

import pytest


@pytest.fixture(scope="session")
def default_params() -> dict:
    """Load and return the canonical game parameters from config/police/game_params.json."""
    config_path = (
        pathlib.Path(__file__).parent.parent
        / "config"
        / "police"
        / "game_params.json"
    )
    with config_path.open() as fh:
        return json.load(fh)


@pytest.fixture
def start_state(default_params: dict) -> dict:
    """Return a dict representing the canonical initial game state.

    Values are drawn from default_params only — no hardcoded numbers.
    """
    cop_start = tuple(default_params["cop_start"])
    thief_start = tuple(default_params["thief_start"])
    return {
        "cop_pos": cop_start,
        "thief_pos": thief_start,
        "barriers": frozenset(),
        "turn": 0,
        "barrier_quota_remaining": default_params["barrier_quota"],
    }
