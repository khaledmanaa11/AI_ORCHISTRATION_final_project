"""Held-out evaluation of a trained weight vector against the fixed anchors.

    uv run python -m training.run_eval --weights artifacts/run2/weights.json

Reports BOTH seats against BOTH cop archetypes, on the negotiated opening and on
randomised starts, with a 95% interval on every rate and the league points each
matchup is worth. The prior is measured in the same run as the baseline, so the
question "did training help" is answered by a comparison rather than by a number
remembered from an earlier session.

The barrier-blind chaser is measured separately on purpose. Our thief's best reply
to a sealing cop is measurably wrong against one that never seals, and reporting
only the average would hide exactly that.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from pursuit.shared.config import load_game_params
from pursuit.shared.resolution import load_resolution_rules
from pursuit.strategy.naive import ChaserCop, GreedyEvader
from pursuit.strategy.valuebrain import ValueSearchBrain
from pursuit.strategy.weights import PRIOR, load_weights
from training.arena import compare, run_match

DEFAULT_CONFIG = Path("config/police")
EVAL_SEED = 90210


def main(argv: list | None = None) -> int:
    """Measure the trained weights against the prior on every fixed matchup."""
    args = _parse(argv)
    params = load_game_params(Path(args.config) / "game_params.json")
    rules = load_resolution_rules(Path(args.config) / "resolution.json")
    trained = load_weights(args.weights) if args.weights else PRIOR

    print(f"n={args.games} per matchup, 95% Wilson intervals, rules={rules}\n")
    for randomise in (False, True):
        header = "randomised starts" if randomise else "negotiated opening (league board)"
        print(f"--- {header} ---")
        for label, matchup in _matchups(params, rules).items():
            base = _measure(label, matchup, PRIOR, args, params, rules, randomise)
            cand = _measure(label, matchup, trained, args, params, rules, randomise)
            print(f"  prior     {base.line()}")
            print(f"  trained   {cand.line()}   {compare(base, cand)}")
        print()
    return 0


def _matchups(params, rules) -> dict:
    """The fixed anchor matchups. Each value is (our_seat, opponent_factory)."""
    return {
        "vs chaser cop (seals)": ("thief", lambda i: ChaserCop(
            "cop", game_params=params, use_barriers=True, rng=random.Random(i))),
        "vs chaser cop (no seals)": ("thief", lambda i: ChaserCop(
            "cop", game_params=params, use_barriers=False, rng=random.Random(i))),
        "vs greedy evader thief": ("cop", lambda i: GreedyEvader(
            "thief", game_params=params, rng=random.Random(i))),
    }


def _measure(label, matchup, weights, args, params, rules, randomise):
    """Run one matchup with *weights* in our seat."""
    seat, opponent = matchup

    def ours(index: int):
        return ValueSearchBrain(
            seat, game_params=params, rules=rules, weights=weights,
            rng=random.Random(EVAL_SEED + index),
        )

    make_cop, make_thief = (ours, opponent) if seat == "cop" else (opponent, ours)
    return run_match(
        label, seat, make_cop, make_thief, args.games, params, rules,
        seed=EVAL_SEED, randomise_starts=randomise,
    )


def _parse(argv: list | None) -> argparse.Namespace:
    """Command-line surface."""
    parser = argparse.ArgumentParser(description="Held-out evaluation of run-2 weights")
    parser.add_argument("--weights", default=None, help="omit to evaluate the prior twice")
    parser.add_argument("--games", type=int, default=300)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
