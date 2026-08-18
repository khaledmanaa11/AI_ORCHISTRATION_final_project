"""Config key string constants for game_params.json / network.json / strategy.json.

Structural only — no numeric value appears here (D-05, D-18, QUAL-11). Split out of
constants.py at the 03-07 150-code-line ceiling (see that module's docstring): the
game-domain enums (Direction, Outcome, MoveSource, Action, ...) stay in constants.py,
config key names live here so a key rename is still detectable at a single point.
"""

from enum import Enum


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


class ResolutionKey(str, Enum):
    """Keys for the optional negotiated resolution block (RULES-RESOLUTION.md Sec5).

    Deliberately NOT part of ConfigKey: game_params.json must stay byte-identical
    with a book-faithful peer (rule 11), so the negotiated predicates live in a
    separate optional file that defaults to BOOK_ONLY when absent.
    """

    CAPTURE_ON_BARRIER_RACE = "capture_on_barrier_race"
    CAPTURE_ON_SWAP = "capture_on_swap"

    def __str__(self) -> str:
        """Return the bare key string so json.dumps emits the field name."""
        return self.value


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


class StrategyKey(str, Enum):
    """Keys for the `[strategy]` group of strategy.json (D-18, QUAL-11).

    This group is read by the live per-turn decision path
    (src/pursuit/strategy/**): brain selection, the trained-weights path, and
    the online eval/timing knobs. No numeric value appears here — every
    number lives in config/{police,thief}/strategy.json. Every Q-learner-only
    key (qtable_path, min_visits, the barrier-search weights, ...) is gone
    with run 1's tabular Q-table (docs/PRD_matrix_mover.md Sec1) — the
    matrix-game mover has no training-time-only hyperparameter left for the
    live loader to validate.
    """

    GROUP = "strategy"
    POLICE_CLASS = "police_class"
    THIEF_CLASS = "thief_class"
    WEIGHTS_PATH = "weights_path"
    EPSILON_EVAL = "epsilon_eval"
    MAX_DECISION_MS = "max_decision_ms"
    LEAF_MODE = "leaf_mode"
    RELAX_TURN = "relax_turn"
