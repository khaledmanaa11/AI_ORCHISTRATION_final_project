"""Artifact path resolution for the offline training harness (D-22).

Every per-run MUTABLE artifact (Q-table checkpoints, `run_state.json`, the
learning-curve CSV) lives under `StrategyParams.artifacts_dir` -- outside the
OneDrive-synced repo by default. This is deliberately NOT the same path as
the role's configured `qtable_path` (e.g. `artifacts/qtable_police.json`),
which names the FINAL BLESSED table copied into the repo at run end
(RESEARCH Sec3) -- rewriting a multi-MB table every `checkpoint_every`
episodes at that repo-relative path would churn OneDrive on every interval.
Copying the final table into the repo is a later plan's concern.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy.qtable import QTable

RUN_STATE_FILENAME = "run_state.json"
CURVE_FILENAME = "curves.csv"


def table_checkpoint_path(params: StrategyParams) -> Path:
    """`artifacts_dir / <basename of the role's configured qtable_path>`."""
    return Path(params.artifacts_dir) / Path(params.qtable_path).name


def run_state_path(params: StrategyParams) -> Path:
    """One manifest for the whole run (both roles) -- RunState carries each
    role's own episode counter (D-25), so one file is enough."""
    return Path(params.artifacts_dir) / RUN_STATE_FILENAME


def curve_path(params: StrategyParams) -> Path:
    """One CSV for the whole run; the `role` column (D-25) keeps the two
    curves separable without needing two files."""
    return Path(params.artifacts_dir) / CURVE_FILENAME


def load_or_new_table(path: Path) -> QTable:
    """Resume a role's table if its checkpoint exists; start fresh otherwise.

    A genuinely absent checkpoint (first run ever) is not the corrupt-file
    case `QTable.load()` itself already fails loud on.
    """
    if not path.exists():
        return QTable()
    return QTable.load(path)
