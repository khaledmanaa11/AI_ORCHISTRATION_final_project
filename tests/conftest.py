"""Shared pytest fixtures for all test waves."""

import pathlib

import pytest

from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.state import GameState

_POLICE_CONFIG = (
    pathlib.Path(__file__).parent.parent / "config" / "police" / "game_params.json"
)


@pytest.fixture(scope="session")
def default_params() -> GameParams:
    """Load and return the canonical game parameters from config/police/game_params.json."""
    return load_game_params(_POLICE_CONFIG)


@pytest.fixture
def start_state(default_params: GameParams) -> GameState:
    """Return the canonical initial GameState drawn from default_params.

    Values come from default_params only — no hardcoded numbers.
    """
    return GameState(
        cop=default_params.cop_start,
        thief=default_params.thief_start,
        barriers=frozenset(),
        barriers_placed=0,
        turn=0,
    )
