"""Structural constants and enumerations for the pursuit engine.

No numeric game values live here (D-07). All game numbers are in game_params.json.
"""

from enum import Enum, IntEnum


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


class StrategyKey(str, Enum):
    """Keys for the `[strategy]` group of strategy.json (D-18, QUAL-11).

    This group is read by the live per-turn decision path (src/pursuit/strategy/**
    in later Phase-3 plans): brain selection, the Q-table path, and the online
    guardrail thresholds. No numeric value appears here — every number lives in
    config/{police,thief}/strategy.json.
    """

    GROUP = "strategy"
    POLICE_CLASS = "police_class"
    THIEF_CLASS = "thief_class"
    QTABLE_PATH = "qtable_path"
    MIN_VISITS = "min_visits"
    TURN_BUCKET_FRACTIONS = "turn_bucket_fractions"
    EPSILON_EVAL = "epsilon_eval"
    MAX_DECISION_MS = "max_decision_ms"
    OSCILLATION_WINDOW = "oscillation_window"
    OSCILLATION_LIMIT = "oscillation_limit"


class TrainingKey(str, Enum):
    """Keys for the `[training]`/`[eval]`/`[monitoring]` groups of strategy.json.

    These are offline-harness (training/) and Phase-7 reporting inputs, never
    read by the live per-turn decision path — that separation is what keeps
    StrategyKey small (D-18).
    """

    TRAINING_GROUP = "training"
    EVAL_GROUP = "eval"
    MONITORING_GROUP = "monitoring"
    ALPHA = "alpha"
    GAMMA = "gamma"
    EPSILON_START = "epsilon_start"
    EPSILON_FLOOR = "epsilon_floor"
    EPSILON_DECAY_EPISODES = "epsilon_decay_episodes"
    ALPHA_FLOOR = "alpha_floor"
    ALPHA_DECAY_EPISODES = "alpha_decay_episodes"
    EPISODES = "episodes"
    CHECKPOINT_EVERY = "checkpoint_every"
    CURVE_LOG_EVERY = "curve_log_every"
    SPARRING_MIX = "sparring_mix"
    POOL_SNAPSHOT_EVERY = "pool_snapshot_every"
    POOL_SIZE = "pool_size"
    SELFPLAY_DELTA = "selfplay_delta"
    SEED = "seed"
    ARTIFACTS_DIR = "artifacts_dir"
    REFERENCE_IMPL_PATH = "reference_impl_path"
    REWARD_CAPTURE = "reward_capture"
    REWARD_SURVIVAL = "reward_survival"
    REWARD_STEP = "reward_step"
    REWARD_BARRIER_GAIN = "reward_barrier_gain"
    EVAL_SCENARIOS = "eval_scenarios"
    REPEATS_PER_SCENARIO = "repeats_per_scenario"
    EVAL_GAMES = "eval_games"
    EVAL_GAMES_CI = "eval_games_ci"
    WIN_RATE_MARGIN = "win_rate_margin"
    MIN_WIN_RATE_ABSOLUTE = "min_win_rate_absolute"
    SIGNIFICANCE_ALPHA = "significance_alpha"
    CONVERGENCE_WINDOW = "convergence_window"
    CONVERGENCE_TOLERANCE = "convergence_tolerance"
    MAX_TABLE_KEYS = "max_table_keys"
    FALLBACK_RATE_GATE = "fallback_rate_gate"
    EVAL_SEED_OFFSET = "eval_seed_offset"
    FALLBACK_RATE_ALERT = "fallback_rate_alert"
    Q_MARGIN_ALERT = "q_margin_alert"


class MoveSource(str, Enum):
    """Decision.source provenance (AI-SPEC Sec5 E2/E3); never defaults to QTABLE."""

    QTABLE = "qtable"
    FALLBACK = "fallback"
    HEURISTIC = "heuristic"


class Action(IntEnum):
    """Canonical 5-action space (STRAT-01); order is FROZEN -- never renumber."""

    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3
    STAY = 4


def cell_for(action: Action, own_cell: tuple[int, int]) -> tuple[int, int]:
    """Return the cell reached by taking action from own_cell."""
    row_delta, col_delta = Direction[action.name].value
    return (own_cell[0] + row_delta, own_cell[1] + col_delta)


def action_for(own_cell: tuple[int, int], dest: tuple[int, int]) -> Action:
    """Return the Action from own_cell to dest; raises ValueError if not adjacent."""
    delta = (dest[0] - own_cell[0], dest[1] - own_cell[1])
    for action in Action:
        if Direction[action.name].value == delta:
            return action
    raise ValueError(f"No Action maps {own_cell} to {dest} (delta {delta})")
