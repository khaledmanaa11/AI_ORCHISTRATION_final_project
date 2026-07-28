"""Shared pytest fixtures for all test waves."""

import pathlib

import pytest

from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.state import GameState

_POLICE_CONFIG = (
    pathlib.Path(__file__).parent.parent / "config" / "police" / "game_params.json"
)
_POLICE_NETWORK_CONFIG = (
    pathlib.Path(__file__).parent.parent / "config" / "police" / "network.json"
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


@pytest.fixture
def police_network_config() -> pathlib.Path:
    """Path to config/police/network.json (Waves 1-5 read or copy it)."""
    return _POLICE_NETWORK_CONFIG


@pytest.fixture
def network_params():
    """Load config/police/network.json through the Phase-2 loader.

    The import is deliberately INSIDE the fixture body: plan 02-01 creates
    pursuit.shared.network_config, and a module-level import here would break
    collection of the entire suite until then. Only tests that actually request
    this fixture pay the import.
    """
    from pursuit.shared.network_config import load_network_config

    return load_network_config(_POLICE_NETWORK_CONFIG)
