"""Structural constants and enumerations for the pursuit engine.

No numeric game values live here (D-07). All game numbers are in game_params.json.
"""

from enum import Enum


class Direction(Enum):
    """Orthogonal movement directions plus stay-in-place.

    Each value is a (row_delta, col_delta) tuple.
    NORTH decrements the row (top-left origin), SOUTH increments.
    """

    NORTH = (-1, 0)
    SOUTH = (1, 0)
    EAST = (0, 1)
    WEST = (0, -1)
    STAY = (0, 0)


class CellState(Enum):
    """Possible contents of a board cell."""

    EMPTY = "empty"
    BARRIER = "barrier"
    COP = "cop"
    THIEF = "thief"


class Outcome(Enum):
    """All four game outcomes (D-14).

    Phase 1 only produces CAPTURE and SURVIVAL.
    TIE is a series aggregate (Phase 8).
    TECHNICAL_LOSS is triggered by crypto audit / false declaration (Phase 6-7).
    """

    CAPTURE = "capture"
    SURVIVAL = "survival"
    TIE = "tie"
    TECHNICAL_LOSS = "technical_loss"


class ConfigKey:
    """String keys matching the exact field names in game_params.json (D-05).

    Use these constants instead of bare string literals when accessing config data
    to avoid magic strings and make key renames detectable at a single point.
    """

    VERSION = "version"
    BOARD_SIZE = "board_size"
    ORIGIN = "origin"
    COP_START = "cop_start"
    THIEF_START = "thief_start"
    MOVEMENT = "movement"
    BARRIER_QUOTA = "barrier_quota"
    MOVE_CEILING = "move_ceiling"
    SURVIVAL_THRESHOLD = "survival_threshold"
    SCORING = "scoring"
    SCORE_CAPTURE = "capture"
    SCORE_SURVIVAL = "survival"
    SCORE_TIE = "tie"
    SCORE_TECHNICAL_LOSS = "technical_loss"


class NetworkConfigKey:
    """String keys matching the exact field names in network.json (D-04).

    Structural only — no numeric value appears here. Every network number lives
    in config/{police,thief}/network.json (QUAL-11). The ENV_* entries are the
    D-16 override variable names 02-01 passes to os.environ.get().
    """

    HOST = "host"
    PORT = "port"
    OPPONENT_URL = "opponent_url"
    RESPONSE_TIMEOUT = "response_timeout"
    WATCHDOG_THRESHOLD = "watchdog_threshold"
    WATCHDOG_POLL_SECONDS = "watchdog_poll_seconds"
    RETRY_COUNT = "retry_count"
    BACKOFF_SECONDS = "backoff_seconds"
    ENV_HOST = "PURSUIT_HOST"
    ENV_PORT = "PURSUIT_PORT"
    ENV_OPPONENT_URL = "PURSUIT_OPPONENT_URL"
