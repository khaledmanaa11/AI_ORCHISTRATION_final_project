"""Tests for BASE-08 — config load and error path tests."""

import json
from pathlib import Path

import pytest
from pursuit.shared.config import load_game_params

POLICE_CONFIG = Path(__file__).parent.parent.parent / "config" / "police" / "game_params.json"


def test_config_loads_board_size(default_params: dict) -> None:
    """Config loads board_size from game_params.json (no hardcoded value)."""
    params = load_game_params(POLICE_CONFIG)
    assert params.board_size == default_params["board_size"]


def test_config_loads_barrier_quota(default_params: dict) -> None:
    """Config loads barrier_quota from game_params.json."""
    params = load_game_params(POLICE_CONFIG)
    assert params.barrier_quota == default_params["barrier_quota"]


def test_config_loads_scoring(default_params: dict) -> None:
    """Config loads the full scoring sub-dict from game_params.json."""
    params = load_game_params(POLICE_CONFIG)
    assert params.score_capture_cop == default_params["scoring"]["capture"][0]
    assert params.score_capture_thief == default_params["scoring"]["capture"][1]
    assert params.score_survival_cop == default_params["scoring"]["survival"][0]
    assert params.score_survival_thief == default_params["scoring"]["survival"][1]
    assert params.score_tie == default_params["scoring"]["tie"][0]


def test_missing_key_raises(tmp_path: Path) -> None:
    """A missing required key raises an error at load time, not silently."""
    bad_config = {
        "origin": "top-left",
        "cop_start": [0, 0],
        "thief_start": [3, 3],
        "movement": "orthogonal",
        "barrier_quota": 14,
        "move_ceiling": 35,
        "survival_threshold": 35,
        "version": "1.00",
        "scoring": {
            "capture": [20, 5],
            "survival": [5, 10],
            "tie": [2, 2],
            "technical_loss": [0, 0],
        },
    }
    config_file = tmp_path / "game_params.json"
    config_file.write_text(json.dumps(bad_config))
    with pytest.raises((KeyError, ValueError)):
        load_game_params(config_file)


def test_wrong_type_raises(tmp_path: Path) -> None:
    """A wrong-type field raises an error at load time."""
    bad_config = {
        "board_size": "seven",
        "origin": "top-left",
        "cop_start": [0, 0],
        "thief_start": [3, 3],
        "movement": "orthogonal",
        "barrier_quota": 14,
        "move_ceiling": 35,
        "survival_threshold": 35,
        "version": "1.00",
        "scoring": {
            "capture": [20, 5],
            "survival": [5, 10],
            "tie": [2, 2],
            "technical_loss": [0, 0],
        },
    }
    config_file = tmp_path / "game_params.json"
    config_file.write_text(json.dumps(bad_config))
    with pytest.raises((TypeError, ValueError)):
        load_game_params(config_file)


def test_config_board_size_is_int(default_params: dict) -> None:
    """board_size accessor returns an int, not a string or float."""
    params = load_game_params(POLICE_CONFIG)
    assert isinstance(params.board_size, int)
