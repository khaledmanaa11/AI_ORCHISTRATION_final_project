"""Fail-loud config loader for strategy.json (D-18, QUAL-02, QUAL-11)."""

# Third consumer of loader_helpers (QUAL-02) — no private validator copies
# live here. reward_* keys are the learner's own shaping signal, deliberately
# distinct from game_params.json's asymmetric per-role league scoring values
# (D-18). artifacts_dir empty-defaults to a LOCALAPPDATA-derived path so a
# multi-MB Q-table is never rewritten inside the OneDrive-synced repo (D-22).
# brain_class resolves whichever of police_class/thief_class the loaded
# per-role file carries — only one is ever present in a given file.

import json
import os
from dataclasses import dataclass
from pathlib import Path

from pursuit.config_keys import StrategyKey, TrainingKey
from pursuit.shared.loader_helpers import (
    require_float,
    require_int,
    require_key,
    require_list,
    require_str,
)

STRATEGY_CONFIG_SOURCE = "strategy.json"


@dataclass(frozen=True)
class StrategyParams:
    """Immutable container for every Phase-3 hyperparameter (QUAL-11)."""

    brain_class: str
    qtable_path: str
    min_visits: int
    turn_bucket_fractions: list
    epsilon_eval: float
    max_decision_ms: int
    oscillation_window: int
    oscillation_limit: int
    barrier_min_gain: int
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
    fallback_rate_alert: float
    q_margin_alert: float


def _resolve_brain_class(strategy: dict, *, source: str) -> str:
    """Read this role's own police_class/thief_class key, whichever is present."""
    if StrategyKey.POLICE_CLASS.value in strategy:
        return require_str(strategy, StrategyKey.POLICE_CLASS.value, source=source)
    return require_str(strategy, StrategyKey.THIEF_CLASS.value, source=source)


def _check_unit_interval(value: float, key: str, *, source: str) -> None:
    """Raise ValueError if value falls outside the closed interval [0, 1]."""
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{source} field '{key}' must be within [0, 1], got {value}")


def _resolve_artifacts_dir(raw_value: str) -> str:
    """Empty artifacts_dir resolves under LOCALAPPDATA, never a literal path (D-22)."""
    if raw_value:
        return raw_value
    base = os.environ.get("LOCALAPPDATA", "")
    return str(Path(base, "pursuit", "training")) if base else raw_value


def load_strategy_config(path: "Path | str") -> StrategyParams:
    """Load and validate every Phase-3 hyperparameter; fails loud with the key name."""
    with Path(path).open() as fh:
        data = json.load(fh)

    strategy = require_key(data, StrategyKey.GROUP.value, source=STRATEGY_CONFIG_SOURCE)
    training = require_key(data, TrainingKey.TRAINING_GROUP.value, source=STRATEGY_CONFIG_SOURCE)
    eval_group = require_key(data, TrainingKey.EVAL_GROUP.value, source=STRATEGY_CONFIG_SOURCE)
    monitoring = require_key(data, TrainingKey.MONITORING_GROUP.value, source=STRATEGY_CONFIG_SOURCE)

    fields = {"brain_class": _resolve_brain_class(strategy, source=STRATEGY_CONFIG_SOURCE)}

    # (field_name, group, key, requirer, is_unit_interval [0, 1] range check)
    # fmt: off
    schema = [
        ("qtable_path", strategy, StrategyKey.QTABLE_PATH, require_str, False),
        ("min_visits", strategy, StrategyKey.MIN_VISITS, require_int, False),
        ("turn_bucket_fractions", strategy, StrategyKey.TURN_BUCKET_FRACTIONS, require_list, False),
        ("epsilon_eval", strategy, StrategyKey.EPSILON_EVAL, require_float, True),
        ("max_decision_ms", strategy, StrategyKey.MAX_DECISION_MS, require_int, False),
        ("oscillation_window", strategy, StrategyKey.OSCILLATION_WINDOW, require_int, False),
        ("oscillation_limit", strategy, StrategyKey.OSCILLATION_LIMIT, require_int, False),
        ("barrier_min_gain", strategy, StrategyKey.BARRIER_MIN_GAIN, require_int, False),
        ("alpha", training, TrainingKey.ALPHA, require_float, False),
        ("gamma", training, TrainingKey.GAMMA, require_float, True),
        ("epsilon_start", training, TrainingKey.EPSILON_START, require_float, True),
        ("epsilon_floor", training, TrainingKey.EPSILON_FLOOR, require_float, True),
        ("epsilon_decay_episodes", training, TrainingKey.EPSILON_DECAY_EPISODES, require_int, False),
        ("alpha_floor", training, TrainingKey.ALPHA_FLOOR, require_float, False),
        ("alpha_decay_episodes", training, TrainingKey.ALPHA_DECAY_EPISODES, require_int, False),
        ("episodes", training, TrainingKey.EPISODES, require_int, False),
        ("checkpoint_every", training, TrainingKey.CHECKPOINT_EVERY, require_int, False),
        ("curve_log_every", training, TrainingKey.CURVE_LOG_EVERY, require_int, False),
        ("sparring_mix", training, TrainingKey.SPARRING_MIX, require_list, False),
        ("pool_snapshot_every", training, TrainingKey.POOL_SNAPSHOT_EVERY, require_int, False),
        ("pool_size", training, TrainingKey.POOL_SIZE, require_int, False),
        ("selfplay_delta", training, TrainingKey.SELFPLAY_DELTA, require_float, True),
        ("seed", training, TrainingKey.SEED, require_int, False),
        ("reference_impl_path", training, TrainingKey.REFERENCE_IMPL_PATH, require_str, False),
        ("reward_capture", training, TrainingKey.REWARD_CAPTURE, require_float, False),
        ("reward_survival", training, TrainingKey.REWARD_SURVIVAL, require_float, False),
        ("reward_step", training, TrainingKey.REWARD_STEP, require_float, False),
        ("reward_barrier_gain", training, TrainingKey.REWARD_BARRIER_GAIN, require_float, False),
        ("eval_scenarios", eval_group, TrainingKey.EVAL_SCENARIOS, require_int, False),
        ("repeats_per_scenario", eval_group, TrainingKey.REPEATS_PER_SCENARIO, require_int, False),
        ("eval_games", eval_group, TrainingKey.EVAL_GAMES, require_int, False),
        ("eval_games_ci", eval_group, TrainingKey.EVAL_GAMES_CI, require_int, False),
        ("win_rate_margin", eval_group, TrainingKey.WIN_RATE_MARGIN, require_float, True),
        ("min_win_rate_absolute", eval_group, TrainingKey.MIN_WIN_RATE_ABSOLUTE, require_float, True),
        ("significance_alpha", eval_group, TrainingKey.SIGNIFICANCE_ALPHA, require_float, True),
        ("convergence_window", eval_group, TrainingKey.CONVERGENCE_WINDOW, require_int, False),
        ("convergence_tolerance", eval_group, TrainingKey.CONVERGENCE_TOLERANCE, require_float, False),
        ("max_table_keys", eval_group, TrainingKey.MAX_TABLE_KEYS, require_int, False),
        ("fallback_rate_gate", eval_group, TrainingKey.FALLBACK_RATE_GATE, require_float, True),
        ("eval_seed_offset", eval_group, TrainingKey.EVAL_SEED_OFFSET, require_int, False),
        ("fallback_rate_alert", monitoring, TrainingKey.FALLBACK_RATE_ALERT, require_float, True),
        ("q_margin_alert", monitoring, TrainingKey.Q_MARGIN_ALERT, require_float, True),
    ]
    # fmt: on

    for name, group, key, requirer, unit_interval in schema:
        value = requirer(group, key.value, source=STRATEGY_CONFIG_SOURCE)
        if unit_interval:
            _check_unit_interval(value, key.value, source=STRATEGY_CONFIG_SOURCE)
        fields[name] = value

    fields["artifacts_dir"] = _resolve_artifacts_dir(
        require_str(training, TrainingKey.ARTIFACTS_DIR.value, source=STRATEGY_CONFIG_SOURCE)
    )

    return StrategyParams(**fields)
