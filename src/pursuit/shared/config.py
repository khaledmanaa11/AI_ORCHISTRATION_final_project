"""Fail-loud config loader for game_params.json (D-05).

load_game_params() is the single entry point for all numeric game parameters.
Every required key and type is validated at load time — nothing is deferred to
play time.  A malformed config raises immediately; there is no silent default.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from pursuit.constants import ConfigKey
from pursuit.shared.loader_helpers import require_int, require_key

GAME_PARAMS_SOURCE = "game_params.json"


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
    score_technical_loss_cop: int
    score_technical_loss_thief: int
    version: str


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
    board_size = require_int(data, ConfigKey.BOARD_SIZE, source=GAME_PARAMS_SOURCE)
    barrier_quota = require_int(data, ConfigKey.BARRIER_QUOTA, source=GAME_PARAMS_SOURCE)
    move_ceiling = require_int(data, ConfigKey.MOVE_CEILING, source=GAME_PARAMS_SOURCE)
    survival_threshold = require_int(
        data, ConfigKey.SURVIVAL_THRESHOLD, source=GAME_PARAMS_SOURCE
    )
    cop_start = tuple(require_key(data, ConfigKey.COP_START, source=GAME_PARAMS_SOURCE))
    thief_start = tuple(
        require_key(data, ConfigKey.THIEF_START, source=GAME_PARAMS_SOURCE)
    )
    version = str(require_key(data, ConfigKey.VERSION, source=GAME_PARAMS_SOURCE))

    # Validate scoring sub-object.
    scoring = require_key(data, ConfigKey.SCORING, source=GAME_PARAMS_SOURCE)
    capture = require_key(scoring, ConfigKey.SCORE_CAPTURE, source=GAME_PARAMS_SOURCE)
    survival = require_key(scoring, ConfigKey.SCORE_SURVIVAL, source=GAME_PARAMS_SOURCE)
    tie = require_key(scoring, ConfigKey.SCORE_TIE, source=GAME_PARAMS_SOURCE)
    technical_loss = require_key(
        scoring, ConfigKey.SCORE_TECHNICAL_LOSS, source=GAME_PARAMS_SOURCE
    )

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
        score_technical_loss_cop=technical_loss[0],
        score_technical_loss_thief=technical_loss[1],
        version=version,
    )
