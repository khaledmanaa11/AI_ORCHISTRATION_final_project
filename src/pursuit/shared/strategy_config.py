"""Fail-loud config loader for strategy.json (D-18, QUAL-02, QUAL-11)."""

# Third consumer of loader_helpers (QUAL-02) — no private validator copies
# live here. reward_* keys are the learner's own shaping signal, deliberately
# distinct from game_params.json's asymmetric per-role league scoring values
# (D-18). artifacts_dir empty-defaults to a LOCALAPPDATA-derived path so a
# multi-MB Q-table is never rewritten inside the OneDrive-synced repo (D-22).
# brain_class resolves whichever of police_class/thief_class the loaded
# per-role file carries — only one is ever present in a given file.
#
# StrategyParams and the schema table live in strategy_schema.py (150-line
# split, 03-13) — re-exported below so every existing import site keeps
# working unchanged (`from pursuit.shared.strategy_config import
# StrategyParams`), ruff F401-clean via __all__.

import json
import os
from pathlib import Path

from pursuit.config_keys import StrategyKey, TrainingKey
from pursuit.shared.loader_helpers import require_key, require_str
from pursuit.shared.strategy_schema import (
    EVAL_GROUP,
    MONITORING_GROUP,
    SCHEMA,
    STRATEGY_GROUP,
    TRAINING_GROUP,
    StrategyParams,
)

__all__ = ["StrategyParams", "load_strategy_config"]

STRATEGY_CONFIG_SOURCE = "strategy.json"


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
    groups = {
        STRATEGY_GROUP: strategy,
        TRAINING_GROUP: training,
        EVAL_GROUP: eval_group,
        MONITORING_GROUP: monitoring,
    }

    fields = {"brain_class": _resolve_brain_class(strategy, source=STRATEGY_CONFIG_SOURCE)}

    for name, group_name, key, requirer, unit_interval in SCHEMA:
        group = groups[group_name]
        value = requirer(group, key.value, source=STRATEGY_CONFIG_SOURCE)
        if unit_interval:
            _check_unit_interval(value, key.value, source=STRATEGY_CONFIG_SOURCE)
        fields[name] = value

    fields["artifacts_dir"] = _resolve_artifacts_dir(
        require_str(training, TrainingKey.ARTIFACTS_DIR.value, source=STRATEGY_CONFIG_SOURCE)
    )

    return StrategyParams(**fields)
