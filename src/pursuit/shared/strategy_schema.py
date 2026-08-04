"""StrategyParams + the field/key/validator schema table for strategy.json.

Split out of strategy_config.py at the 150-code-line gate (measured 138 before this
plan's +15 net fields; see 03-13-SUMMARY.md). `strategy_config.py` keeps the loader
functions and re-exports `StrategyParams` from here so its ~20 existing import sites
across training/ and tests/ need no change (ruff F401-clean via `__all__`).

Every field here is an engineering default unless the field's own SUMMARY entry says
otherwise (D-18, project rule 1) — none is claimed as a docs/PARAMETERS.md value.
Schema rows carry the group's KEY NAME (a string), not a parsed dict — the loader in
strategy_config.py resolves the actual group dict at load time and looks it up.
"""

from dataclasses import dataclass

from pursuit.config_keys import StrategyKey, TrainingKey
from pursuit.shared.loader_helpers import require_float, require_int, require_list, require_str

STRATEGY_GROUP = "strategy"
TRAINING_GROUP = "training"
EVAL_GROUP = "eval"
MONITORING_GROUP = "monitoring"


@dataclass(frozen=True)
class StrategyParams:
    """Immutable container for every Phase-3 hyperparameter (QUAL-11)."""

    brain_class: str
    qtable_path: str
    min_visits: int
    epsilon_eval: float
    max_decision_ms: int
    oscillation_window: int
    oscillation_limit: int
    barrier_min_gain: int
    search_depth_cap: int
    feature_scale_divisor: float
    weights_path: str
    learner_rule: str
    barrier_candidate_min_degree: int
    barrier_weight_cycle_rank: float
    barrier_weight_component_size: float
    barrier_weight_territory: float
    barrier_weight_distance: float
    alpha: float
    gamma: float
    epsilon_start: float
    epsilon_floor: float
    epsilon_decay_episodes: int
    alpha_floor: float
    alpha_decay_episodes: int
    episodes: int
    checkpoint_every: int
    curve_log_every: int
    sparring_mix: list
    pool_snapshot_every: int
    pool_size: int
    selfplay_delta: float
    pfsp_exponent: float
    weak_opponent_floor: int
    seed: int
    artifacts_dir: str
    reference_impl_path: str
    reward_capture: float
    reward_survival: float
    reward_step: float
    reward_barrier_gain: float
    eval_scenarios: int
    repeats_per_scenario: int
    eval_games: int
    eval_games_ci: int
    win_rate_margin: float
    min_win_rate_absolute: float
    significance_alpha: float
    convergence_window: int
    convergence_tolerance: float
    max_table_keys: int
    fallback_rate_gate: float
    eval_seed_offset: int
    min_distinct_starts: int
    terminal_spread_min: float
    terminal_spread_ratio_max: float
    floor_episode_fraction_max: float
    fallback_rate_alert: float
    q_margin_alert: float


# (field_name, group_name, key, requirer, is_unit_interval [0, 1] range check)
# fmt: off
SCHEMA = [
    ("qtable_path", STRATEGY_GROUP, StrategyKey.QTABLE_PATH, require_str, False),
    ("min_visits", STRATEGY_GROUP, StrategyKey.MIN_VISITS, require_int, False),
    ("epsilon_eval", STRATEGY_GROUP, StrategyKey.EPSILON_EVAL, require_float, True),
    ("max_decision_ms", STRATEGY_GROUP, StrategyKey.MAX_DECISION_MS, require_int, False),
    ("oscillation_window", STRATEGY_GROUP, StrategyKey.OSCILLATION_WINDOW, require_int, False),
    ("oscillation_limit", STRATEGY_GROUP, StrategyKey.OSCILLATION_LIMIT, require_int, False),
    ("barrier_min_gain", STRATEGY_GROUP, StrategyKey.BARRIER_MIN_GAIN, require_int, False),
    ("search_depth_cap", STRATEGY_GROUP, StrategyKey.SEARCH_DEPTH_CAP, require_int, False),
    ("feature_scale_divisor", STRATEGY_GROUP, StrategyKey.FEATURE_SCALE_DIVISOR, require_float, False),
    ("weights_path", STRATEGY_GROUP, StrategyKey.WEIGHTS_PATH, require_str, False),
    ("learner_rule", STRATEGY_GROUP, StrategyKey.LEARNER_RULE, require_str, False),
    ("barrier_candidate_min_degree", STRATEGY_GROUP, StrategyKey.BARRIER_CANDIDATE_MIN_DEGREE, require_int, False),
    ("barrier_weight_cycle_rank", STRATEGY_GROUP, StrategyKey.BARRIER_WEIGHT_CYCLE_RANK, require_float, False),
    ("barrier_weight_component_size", STRATEGY_GROUP, StrategyKey.BARRIER_WEIGHT_COMPONENT_SIZE, require_float, False),
    ("barrier_weight_territory", STRATEGY_GROUP, StrategyKey.BARRIER_WEIGHT_TERRITORY, require_float, False),
    ("barrier_weight_distance", STRATEGY_GROUP, StrategyKey.BARRIER_WEIGHT_DISTANCE, require_float, False),
    ("alpha", TRAINING_GROUP, TrainingKey.ALPHA, require_float, False),
    ("gamma", TRAINING_GROUP, TrainingKey.GAMMA, require_float, True),
    ("epsilon_start", TRAINING_GROUP, TrainingKey.EPSILON_START, require_float, True),
    ("epsilon_floor", TRAINING_GROUP, TrainingKey.EPSILON_FLOOR, require_float, True),
    ("epsilon_decay_episodes", TRAINING_GROUP, TrainingKey.EPSILON_DECAY_EPISODES, require_int, False),
    ("alpha_floor", TRAINING_GROUP, TrainingKey.ALPHA_FLOOR, require_float, False),
    ("alpha_decay_episodes", TRAINING_GROUP, TrainingKey.ALPHA_DECAY_EPISODES, require_int, False),
    ("episodes", TRAINING_GROUP, TrainingKey.EPISODES, require_int, False),
    ("checkpoint_every", TRAINING_GROUP, TrainingKey.CHECKPOINT_EVERY, require_int, False),
    ("curve_log_every", TRAINING_GROUP, TrainingKey.CURVE_LOG_EVERY, require_int, False),
    ("sparring_mix", TRAINING_GROUP, TrainingKey.SPARRING_MIX, require_list, False),
    ("pool_snapshot_every", TRAINING_GROUP, TrainingKey.POOL_SNAPSHOT_EVERY, require_int, False),
    ("pool_size", TRAINING_GROUP, TrainingKey.POOL_SIZE, require_int, False),
    ("selfplay_delta", TRAINING_GROUP, TrainingKey.SELFPLAY_DELTA, require_float, True),
    ("pfsp_exponent", TRAINING_GROUP, TrainingKey.PFSP_EXPONENT, require_float, False),
    ("weak_opponent_floor", TRAINING_GROUP, TrainingKey.WEAK_OPPONENT_FLOOR, require_int, False),
    ("seed", TRAINING_GROUP, TrainingKey.SEED, require_int, False),
    ("reference_impl_path", TRAINING_GROUP, TrainingKey.REFERENCE_IMPL_PATH, require_str, False),
    ("reward_capture", TRAINING_GROUP, TrainingKey.REWARD_CAPTURE, require_float, False),
    ("reward_survival", TRAINING_GROUP, TrainingKey.REWARD_SURVIVAL, require_float, False),
    ("reward_step", TRAINING_GROUP, TrainingKey.REWARD_STEP, require_float, False),
    ("reward_barrier_gain", TRAINING_GROUP, TrainingKey.REWARD_BARRIER_GAIN, require_float, False),
    ("eval_scenarios", EVAL_GROUP, TrainingKey.EVAL_SCENARIOS, require_int, False),
    ("repeats_per_scenario", EVAL_GROUP, TrainingKey.REPEATS_PER_SCENARIO, require_int, False),
    ("eval_games", EVAL_GROUP, TrainingKey.EVAL_GAMES, require_int, False),
    ("eval_games_ci", EVAL_GROUP, TrainingKey.EVAL_GAMES_CI, require_int, False),
    ("win_rate_margin", EVAL_GROUP, TrainingKey.WIN_RATE_MARGIN, require_float, True),
    ("min_win_rate_absolute", EVAL_GROUP, TrainingKey.MIN_WIN_RATE_ABSOLUTE, require_float, True),
    ("significance_alpha", EVAL_GROUP, TrainingKey.SIGNIFICANCE_ALPHA, require_float, True),
    ("convergence_window", EVAL_GROUP, TrainingKey.CONVERGENCE_WINDOW, require_int, False),
    ("convergence_tolerance", EVAL_GROUP, TrainingKey.CONVERGENCE_TOLERANCE, require_float, False),
    ("max_table_keys", EVAL_GROUP, TrainingKey.MAX_TABLE_KEYS, require_int, False),
    ("fallback_rate_gate", EVAL_GROUP, TrainingKey.FALLBACK_RATE_GATE, require_float, True),
    ("eval_seed_offset", EVAL_GROUP, TrainingKey.EVAL_SEED_OFFSET, require_int, False),
    ("min_distinct_starts", EVAL_GROUP, TrainingKey.MIN_DISTINCT_STARTS, require_int, False),
    ("terminal_spread_min", EVAL_GROUP, TrainingKey.TERMINAL_SPREAD_MIN, require_float, False),
    ("terminal_spread_ratio_max", EVAL_GROUP, TrainingKey.TERMINAL_SPREAD_RATIO_MAX, require_float, False),
    ("floor_episode_fraction_max", EVAL_GROUP, TrainingKey.FLOOR_EPISODE_FRACTION_MAX, require_float, True),
    ("fallback_rate_alert", MONITORING_GROUP, TrainingKey.FALLBACK_RATE_ALERT, require_float, True),
    ("q_margin_alert", MONITORING_GROUP, TrainingKey.Q_MARGIN_ALERT, require_float, True),
]
# fmt: on
