"""Fail-loud config loader for strategy.json (D-18, QUAL-02, QUAL-11).

Run-2 (docs/PRD_matrix_mover.md): the whole file is one `[strategy]` group
-- `police_class`/`thief_class` (whichever this role's file carries) plus
`weights_path`, `epsilon_eval`, `max_decision_ms`. The old `[training]`/
`[eval]`/`[monitoring]` groups existed only for the run-1 Q-learner's
offline harness and GATE-4 statistical gate, both retired; requiring an
empty group here would just be a second kind of dead key.

StrategyParams and the schema table live in strategy_schema.py, re-exported
below so every existing import site keeps working unchanged (`from
pursuit.shared.strategy_config import StrategyParams`), ruff F401-clean via
__all__.
"""

import json
from pathlib import Path

from pursuit.config_keys import StrategyKey
from pursuit.shared.loader_helpers import require_key, require_str
from pursuit.shared.strategy_schema import SCHEMA, STRATEGY_GROUP, StrategyParams

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


def load_strategy_config(path: "Path | str") -> StrategyParams:
    """Load and validate every field the live decision path reads; fails
    loud with the key name."""
    with Path(path).open() as fh:
        data = json.load(fh)

    strategy = require_key(data, STRATEGY_GROUP, source=STRATEGY_CONFIG_SOURCE)
    fields = {"brain_class": _resolve_brain_class(strategy, source=STRATEGY_CONFIG_SOURCE)}

    for name, key, requirer, unit_interval in SCHEMA:
        value = requirer(strategy, key.value, source=STRATEGY_CONFIG_SOURCE)
        if unit_interval:
            _check_unit_interval(value, key.value, source=STRATEGY_CONFIG_SOURCE)
        fields[name] = value

    return StrategyParams(**fields)
