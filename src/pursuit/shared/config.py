"""Fail-loud config loader for game_params.json (D-05).

load_game_params() is the single entry point for all numeric game parameters.
Every required key and type is validated at load time — nothing is deferred to
play time.  A malformed config raises immediately; there is no silent default.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from pursuit.constants import ConfigKey


@dataclass(frozen=True)
class GameParams:
    """Typed, immutable container for all values read from game_params.json.

    Constructed only by load_game_params() — callers never build this directly.
    """

    board_size: int
    cop_start: tuple
    thief_start: tuple
    barrier_quota: int
    move_ceiling: int
    survival_threshold: int
    score_capture_cop: int
    score_capture_thief: int
    score_survival_cop: int
    score_survival_thief: int
    score_tie: int
    version: str


def _require_key(data: dict, key: str) -> object:
    """Raise KeyError with a descriptive message if key is absent from data."""
    if key not in data:
        raise KeyError(f"Required key '{key}' missing from game_params.json")
    return data[key]


def _require_int(data: dict, key: str) -> int:
    """Return data[key] as int; raise TypeError if the value is not an int."""
    value = _require_key(data, key)
    if not isinstance(value, int):
        raise TypeError(
            f"game_params.json field '{key}' must be int, got {type(value).__name__!r}"
        )
    return value


def load_game_params(path: "Path | str") -> GameParams:
    """Load and validate game parameters from a game_params.json file.

    Parameters
    ----------
    path:
        Filesystem path to a JSON file matching the game_params.json schema.

    Returns
    -------
    GameParams
        Fully-populated, immutable parameters object.

    Raises
    ------
    KeyError
        If any required top-level or scoring sub-key is absent.
    TypeError
        If any numeric field carries a non-integer value.
    """
    with Path(path).open() as fh:
        data = json.load(fh)

    # Validate and extract top-level required keys.
    board_size = _require_int(data, ConfigKey.BOARD_SIZE)
    barrier_quota = _require_int(data, ConfigKey.BARRIER_QUOTA)
    move_ceiling = _require_int(data, ConfigKey.MOVE_CEILING)
    survival_threshold = _require_int(data, ConfigKey.SURVIVAL_THRESHOLD)
    cop_start = tuple(_require_key(data, ConfigKey.COP_START))
    thief_start = tuple(_require_key(data, ConfigKey.THIEF_START))
    version = str(_require_key(data, ConfigKey.VERSION))

    # Validate scoring sub-object.
    scoring = _require_key(data, ConfigKey.SCORING)
    capture = _require_key(scoring, ConfigKey.SCORE_CAPTURE)
    survival = _require_key(scoring, ConfigKey.SCORE_SURVIVAL)
    tie = _require_key(scoring, ConfigKey.SCORE_TIE)
    _require_key(scoring, ConfigKey.SCORE_TECHNICAL_LOSS)

    return GameParams(
        board_size=board_size,
        cop_start=cop_start,
        thief_start=thief_start,
        barrier_quota=barrier_quota,
        move_ceiling=move_ceiling,
        survival_threshold=survival_threshold,
        score_capture_cop=capture[0],
        score_capture_thief=capture[1],
        score_survival_cop=survival[0],
        score_survival_thief=survival[1],
        score_tie=tie[0],
        version=version,
    )
