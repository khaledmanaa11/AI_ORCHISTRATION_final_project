"""Once-per-run setup/teardown for training/loop.py -- split out at the
150-code-line gate (repeats the 03-05/03-06/03-07 pattern). Everything here
runs at most once per run (resume-or-init, final checkpoint, Windows
guards), never once per episode, so loop.py's own episode loop stays small.
"""

from __future__ import annotations

import ctypes
import logging
import random
import sys
from collections import deque
from typing import TYPE_CHECKING

from pursuit.shared.config import GameParams
from pursuit.shared.strategy_config import StrategyParams
from training import artifacts, checkpoint, curves, runstate, sparring_reference
from training.progress import RunProgress
from training.runstate import RunState
from training.sparring import SparringPool

if TYPE_CHECKING:
    from training.run_config import TrainingRunConfig

logger = logging.getLogger(__name__)

_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001
_SHARED_RUN_FIELDS = (
    "seed", "episodes", "checkpoint_every", "pool_snapshot_every", "artifacts_dir",
)


def require_shared_run_fields(cop_params: StrategyParams, thief_params: StrategyParams) -> None:
    """One run/one RNG/one cadence set. `cop.json`/`thief.json` may
    legitimately differ in `brain_class`/`qtable_path`/`reward_*`, but a
    mismatch on these run-level scalars would desync a resumed run from the
    seed its own checkpoint was produced under."""
    mismatched = [
        name for name in _SHARED_RUN_FIELDS
        if getattr(cop_params, name) != getattr(thief_params, name)
    ]
    if mismatched:
        raise ValueError(f"cop/thief strategy.json disagree on run-level fields: {mismatched}")


def build_pool(
    role: str, params: StrategyParams, game_params: GameParams, rng: random.Random
) -> SparringPool:
    """Pool of `role`-playing opponents -- built once per run (D-21)."""
    reference = sparring_reference.build_reference_opponent(
        role, params.reference_impl_path, game_params, rng
    )
    return SparringPool(
        opponent_role=role, opponent_params=params, game_params=game_params,
        ring=deque(maxlen=params.pool_size), reference=reference,
    )


def load_or_init(config: TrainingRunConfig, rng: random.Random) -> tuple[dict, RunProgress]:
    """Resume tables + progress from `run_state.json`, or start fresh."""
    tables = {
        "cop": artifacts.load_or_new_table(artifacts.table_checkpoint_path(config.cop_params)),
        "thief": artifacts.load_or_new_table(artifacts.table_checkpoint_path(config.thief_params)),
    }
    payload = checkpoint.load_checkpoint(artifacts.run_state_path(config.cop_params))
    if payload is None:
        return tables, RunProgress()
    state = RunState.from_payload(payload)
    expected = runstate.combined_config_hash(config.cop_params, config.thief_params)
    if state.config_hash != expected:
        logger.warning("resumed config_hash %r != current config %r", state.config_hash, expected)
    runstate.restore_rng_state(rng, state.rng_state)
    removed = curves.truncate_after(artifacts.curve_path(config.cop_params), state.episode)
    logger.info("resumed at episode %d (truncated %d curve rows past it, D-24)", state.episode, removed)
    progress = RunProgress(
        episode=state.episode, cop_episodes=state.cop_episodes,
        thief_episodes=state.thief_episodes, csv_rows=state.csv_row_count,
    )
    return tables, progress


def build_run_state(config: TrainingRunConfig, progress: RunProgress, rng: random.Random) -> RunState:
    return RunState(
        episode=progress.episode, cop_episodes=progress.cop_episodes,
        thief_episodes=progress.thief_episodes, seed=config.cop_params.seed,
        config_hash=runstate.combined_config_hash(config.cop_params, config.thief_params),
        csv_row_count=progress.csv_rows, rng_state=runstate.capture_rng_state(rng),
    )


def write_checkpoint(
    config: TrainingRunConfig, tables: dict, progress: RunProgress, rng: random.Random
) -> None:
    """Whole-run checkpoint (D-24): both tables plus the run manifest."""
    tables["cop"].save(artifacts.table_checkpoint_path(config.cop_params))
    tables["thief"].save(artifacts.table_checkpoint_path(config.thief_params))
    payload = build_run_state(config, progress, rng).to_payload()
    checkpoint.save_checkpoint(artifacts.run_state_path(config.cop_params), payload)


def win32_keep_awake() -> None:
    """Sleep kills an overnight run (RESEARCH Sec3); no-op off Windows."""
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED)


def win32_release() -> None:
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)
