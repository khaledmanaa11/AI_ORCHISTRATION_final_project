"""The outer, resumable training run driver (Task 4, STRAT-06).

`run_episode` (harness.py) plays ONE game; this module decides WHICH game to
play next -- resuming from `run_state.json` if present, sampling a frozen
opponent once per episode (RESEARCH Sec2), alternating which role learns
(D-25), stepping the epsilon/alpha schedules, admitting pool snapshots and
writing checkpoints/curve rows on their own cadences, and handling the
Windows realities RESEARCH Sec3 documents (no SIGTERM, sleep, OneDrive).

A single, shared `random.Random(seed)` drives opponent sampling AND both
brains' own exploration draws (each `QLearningBrain` is constructed with
this same instance) -- not a per-brain sub-seed. That is what makes
`RunState.rng_state` (one `getstate()`) reproduce the WHOLE run, matching
runstate.py's own single-field design; it is a training-pipeline
determinism choice, unrelated to project rule 2, which governs the two
DEPLOYED agent processes, not this offline, single-process harness.
"""

from __future__ import annotations

import atexit
import logging
import random
import sys
from pathlib import Path

from pursuit.shared.config import load_game_params
from pursuit.shared.strategy_config import load_strategy_config
from pursuit.strategy.qlearning import QLearningBrain
from training import artifacts, curves, runstate, sparring
from training.harness import EpisodeConfig, Player, run_episode
from training.loop_setup import (
    build_pool,
    build_run_state,
    load_or_init,
    require_shared_run_fields,
    win32_keep_awake,
    win32_release,
    write_checkpoint,
)
from training.progress import RoleAccumulator, RunProgress
from training.run_config import RunResult, TrainingRunConfig

__all__ = ["TrainingRunConfig", "RunResult", "run_training"]

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def run_training(config: TrainingRunConfig) -> RunResult:
    """Resume-or-start, run to `episodes`, always leave a final checkpoint."""
    require_shared_run_fields(config.cop_params, config.thief_params)
    rng = random.Random(config.cop_params.seed)
    tables, progress = load_or_init(config, rng)
    brains = _build_brains(config, tables, rng)
    pools = {
        "cop": build_pool("cop", config.cop_params, config.game_params, rng),
        "thief": build_pool("thief", config.thief_params, config.game_params, rng),
    }
    role_params = {"cop": config.cop_params, "thief": config.thief_params}
    accumulators = {"cop": RoleAccumulator(), "thief": RoleAccumulator()}
    cw = curves.open_curve(
        artifacts.curve_path(config.cop_params), seed=config.cop_params.seed,
        config_hash=runstate.combined_config_hash(config.cop_params, config.thief_params),
    )

    def _checkpoint_now() -> None:
        write_checkpoint(config, tables, progress, rng)

    win32_keep_awake()
    atexit.register(_checkpoint_now)
    try:
        _run_episodes(config, brains, tables, pools, role_params, accumulators, progress, cw, rng, _checkpoint_now)
    finally:
        curves.close(cw)
        _checkpoint_now()
        atexit.unregister(_checkpoint_now)
        win32_release()

    return RunResult(
        cop_table=tables["cop"], thief_table=tables["thief"],
        run_state=build_run_state(config, progress, rng),
    )


def _build_brains(config: TrainingRunConfig, tables: dict, rng: random.Random) -> dict:
    return {
        role: QLearningBrain(
            role=role, params=getattr(config, f"{role}_params"),
            game_params=config.game_params, rng=rng, table=tables[role],
        )
        for role in ("cop", "thief")
    }


def _run_episodes(config, brains, tables, pools, role_params, accumulators, progress, cw, rng, checkpoint_now) -> None:
    total = config.cop_params.episodes
    while progress.episode < total:
        role = "cop" if progress.episode % 2 == 0 else "thief"
        opponent_role = "thief" if role == "cop" else "cop"
        params, learner = role_params[role], brains[role]
        learner.epsilon = runstate.epsilon_at(progress.role_episodes(role), params)
        learner.alpha = runstate.alpha_at(progress.role_episodes(role), params)

        opponent = sparring.sample_opponent(pools[opponent_role], rng, role_params[opponent_role])
        result = run_episode(
            Player(role=role, brain=learner),
            Player(role=opponent_role, brain=opponent.brain),
            EpisodeConfig(game_params=config.game_params, learner_params=params),
            rng,
        )
        progress.advance(role)
        accumulators[role].record(result, opponent.kind)
        _maybe_log_curve(cw, accumulators[role], progress, role, learner, params.curve_log_every)

        if progress.episode % params.pool_snapshot_every == 0:
            pools["cop"].admit(tables["cop"])
            pools["thief"].admit(tables["thief"])
        if progress.episode % params.checkpoint_every == 0:
            checkpoint_now()


def _maybe_log_curve(
    cw, acc: RoleAccumulator, progress: RunProgress, role: str, learner: QLearningBrain, cadence: int
) -> None:
    if progress.role_episodes(role) % cadence != 0:
        return
    row = acc.as_row(episode=progress.episode, epsilon=learner.epsilon, alpha=learner.alpha, role=role)
    curves.append(cw, row)
    progress.csv_rows += 1
    acc.reset()


def _load_run_config() -> TrainingRunConfig:
    """`config/{police,thief}/game_params.json` are identical byte-for-byte
    (D-06); either side's copy is the shared GameParams for the run."""
    return TrainingRunConfig(
        game_params=load_game_params(_CONFIG_DIR / "police" / "game_params.json"),
        cop_params=load_strategy_config(_CONFIG_DIR / "police" / "strategy.json"),
        thief_params=load_strategy_config(_CONFIG_DIR / "thief" / "strategy.json"),
    )


def main() -> int:
    """`uv run python -m training.loop` -- the operator's overnight-run entry
    point (03-10-PLAN.md Task 4). Resumable: re-running after an interruption
    continues from the last checkpoint (D-24)."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    result = run_training(_load_run_config())
    print(
        f"run_training finished at episode {result.run_state.episode} "
        f"(cop_episodes={result.run_state.cop_episodes}, "
        f"thief_episodes={result.run_state.thief_episodes})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
