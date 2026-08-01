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

    This group is read by the live per-turn decision path (src/pursuit/strategy/**):
    brain selection, the Q-table path, the cop's barrier-gain threshold (03-07), and
    the online guardrail thresholds. No numeric value appears here — every number
    lives in config/{police,thief}/strategy.json.
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
    BARRIER_MIN_GAIN = "barrier_min_gain"


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
