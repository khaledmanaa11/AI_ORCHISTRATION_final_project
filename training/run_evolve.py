"""Entry point for the (1+lambda)-ES optimiser on league points.

    uv run python -m training.run_evolve --generations 30 --children 8 --games 40

Writes weights.json and curve.json in the same shapes run_selfplay.py does, so
training/run_eval.py can measure either optimiser's artefact without caring which
produced it, and the academic report can plot both curves on one axis.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from pursuit.shared.config import load_game_params
from pursuit.shared.resolution import load_resolution_rules
from pursuit.strategy.weights import PRIOR, describe, load_weights, save_weights
from training.evolve import evolve

DEFAULT_CONFIG = Path("config/police")
DEFAULT_OUTPUT = Path("artifacts/run2_es")

#: Mutation scale. Large enough to escape the prior's basin within a few dozen
#: generations, small enough that a single step cannot destroy a working vector.
SIGMA = 0.25


def main(argv: list | None = None) -> int:
    """Evolve the weights and persist the artefact plus its fitness curve."""
    args = _parse(argv)
    params = load_game_params(Path(args.config) / "game_params.json")
    rules = load_resolution_rules(Path(args.config) / "resolution.json")
    rng = random.Random(args.seed)
    start = load_weights(args.start) if args.start else PRIOR

    curve: list = []

    def record(generation: int, best: float, best_of_batch: float, weights: tuple) -> None:
        """Log one generation, checkpoint the artefact, keep the curve row.

        Checkpointing every generation because an ES run has no cheap way to
        resume otherwise, and because run 1's lesson was that a run which writes
        only at the end is a run you cannot diagnose.
        """
        curve.append(
            {
                "generation": generation,
                "best_fitness": round(best, 4),
                "batch_best": round(best_of_batch, 4),
            }
        )
        _checkpoint(Path(args.output), weights, curve, args)
        print(
            f"gen {generation:3d}  points/game {best:7.3f}  "
            f"batch best {best_of_batch:7.3f}",
            flush=True,
        )

    best = evolve(
        start, args.generations, args.children, args.games, SIGMA,
        params, rules, rng, on_generation=record,
    )

    _checkpoint(Path(args.output), best, curve, args)
    print("\nfinal weights:\n" + describe(best))
    return 0


def _checkpoint(output: Path, weights: tuple, curve: list, args) -> None:
    """Write the current best weights and the fitness curve side by side."""
    output.mkdir(parents=True, exist_ok=True)
    save_weights(
        output / "weights.json",
        weights,
        metadata={
            "optimiser": "(1+lambda)-ES on league points",
            "generations": args.generations,
            "children": args.children,
            "games_per_candidate": args.games,
            "sigma": SIGMA,
            "seed": args.seed,
        },
    )
    with (output / "curve.json").open("w") as handle:
        json.dump(curve, handle, indent=2)


def _parse(argv: list | None) -> argparse.Namespace:
    """Command-line surface."""
    parser = argparse.ArgumentParser(description="Evolve run-2 weights on league points")
    parser.add_argument("--generations", type=int, default=30)
    parser.add_argument("--children", type=int, default=8)
    parser.add_argument("--games", type=int, default=40)
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--start", default=None, help="weights.json to seed from")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
