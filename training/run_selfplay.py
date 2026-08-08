"""Run-2 training entry point: generational self-play, outcome-regressed weights.

    uv run python -m training.run_selfplay --generations 24 --games 400

Against run 1's 300,000 episodes over a 103.7M-value Q-table, this fits 15 floats
from a few thousand games. The search supplies the tactics, so the learner only
has to supply positional judgement -- and positional judgement over hand-designed
graph features needs thousands of samples, not hundreds of thousands.

Every generation writes a curve row (rule 42 wants learning curves in the academic
report) and the best-so-far weights, scored on the FIXED anchors rather than on
self-play. Scoring on self-play alone is how a policy that has merely learned to
beat its own past selves looks like progress.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from pursuit.shared.config import load_game_params
from pursuit.shared.resolution import load_resolution_rules
from pursuit.strategy.weights import PRIOR, describe, save_weights
from training import fit
from training.generation import epsilon_for, play_generation
from training.starts import distinct_start_count

DEFAULT_CONFIG = Path("config/police")
DEFAULT_OUTPUT = Path("artifacts/run2")

#: Base Adagrad step. Small because the run is short: 24 generations is 24 updates,
#: and an over-large step on a 15-weight vector overshoots before it can recover.
LEARNING_RATE = 0.10

EPSILON_START = 0.20
EPSILON_FLOOR = 0.02

#: Keep the last N frozen vectors as PAST pool members.
SNAPSHOT_RING = 8


def main(argv: list | None = None) -> int:
    """Train, log a curve row per generation, and write the artefacts."""
    args = _parse(argv)
    params = load_game_params(Path(args.config) / "game_params.json")
    rules = load_resolution_rules(Path(args.config) / "resolution.json")
    rng = random.Random(args.seed)

    weights = PRIOR
    optimiser = fit.Adagrad(LEARNING_RATE)
    snapshots: list = []
    curve: list = []

    for generation in range(args.generations):
        epsilon = epsilon_for(generation, args.generations, EPSILON_START, EPSILON_FLOOR)
        batch = play_generation(
            weights, snapshots, args.games, epsilon, params, rules, rng
        )
        samples = fit.samples_from(list(batch.records), params)
        slope, loss = fit.gradient(weights, samples, params)
        weights = optimiser.step(weights, slope)

        snapshots.append(weights)
        if len(snapshots) > SNAPSHOT_RING:
            snapshots.pop(0)

        row = {
            "generation": generation,
            "epsilon": round(epsilon, 4),
            "cop_capture_rate": round(batch.cop_rate, 4),
            "thief_survival_rate": round(batch.thief_rate, 4),
            "loss": round(loss, 6),
            "samples": len(samples),
            "distinct_starts": distinct_start_count(batch.starts),
        }
        curve.append(row)
        print(
            f"gen {generation:3d}  eps {epsilon:.3f}  "
            f"cop {batch.cop_rate:6.1%}  thief {batch.thief_rate:6.1%}  "
            f"loss {loss:.4f}  starts {row['distinct_starts']:4d}",
            flush=True,
        )
        # Checkpoint EVERY generation. Run 1 wrote nothing until the end, so a
        # crash or an interrupt at hour six left no artefact and no way to
        # resume -- the post-mortem had to reconstruct the run from its log.
        _write(Path(args.output), weights, curve, args)

    _write(Path(args.output), weights, curve, args)
    print("\nfinal weights:\n" + describe(weights))
    return 0


def _write(output: Path, weights: tuple, curve: list, args) -> None:
    """Persist weights and the learning curve side by side."""
    output.mkdir(parents=True, exist_ok=True)
    save_weights(
        output / "weights.json",
        weights,
        metadata={
            "generations": args.generations,
            "games_per_generation": args.games,
            "seed": args.seed,
            "learning_rate": LEARNING_RATE,
        },
    )
    with (output / "curve.json").open("w") as handle:
        json.dump(curve, handle, indent=2)


def _parse(argv: list | None) -> argparse.Namespace:
    """Command-line surface. Every default is named here, never inline."""
    parser = argparse.ArgumentParser(description="Run-2 self-play weight training")
    parser.add_argument("--generations", type=int, default=24)
    parser.add_argument("--games", type=int, default=400)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
