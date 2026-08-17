"""Run the one-factor-at-a-time sensitivity sweep and record every number
it publishes (08-09).

    uv run python scripts/sensitivity_sweep.py                 # 200 games/matchup
    uv run python scripts/sensitivity_sweep.py --games 40      # a quick pass

Writes `artifacts/sensitivity/sweep.json`. `docs/SENSITIVITY.md`'s tables
are RENDERED from that file by `sensitivity_report.py` and a unit test
re-renders them and compares, so a number cannot be edited into the document
by hand and survive.

OFAT, not a full grid: every configuration differs from the shipped baseline
in exactly ONE knob, so an effect is attributable. A full factorial over six
knobs would be 216 cells and would not answer "which knob moves the outcome"
any better at this sample size.

The sweep NEVER touches `config/*/games_played.json`. It plays through
`training/joint_game`, which has no counter, no network and no artifact
writer -- the counter lives in the network agent stack this file never
imports.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from sensitivity_grid import (  # noqa: E402
    EVAL_SEED,
    baseline,
    config_paths,
    knobs,
    matchups,
    our_brain,
)
from sensitivity_status import (  # noqa: E402
    fixed_parameters,
    refuse_downward,
    refuse_fixed,
)

from training.arena import run_match  # noqa: E402

OUT_PATH = Path(_REPO_ROOT) / "artifacts" / "sensitivity" / "sweep.json"
DEFAULT_GAMES = 200


def measure(setting, games: int) -> dict:
    """Every matchup's rate under one configuration."""
    results = {}
    for label, seat, opponent in matchups():
        ours = our_brain(setting, seat)

        def theirs(index, factory=opponent, params=setting.params):
            return factory(params, index)

        make_cop, make_thief = (ours, theirs) if seat == "cop" else (theirs, ours)
        match = run_match(label, seat, make_cop, make_thief, games,
                          setting.params, setting.rules, seed=EVAL_SEED)
        low, high = match.interval
        results[label] = {
            "seat": seat, "wins": match.wins, "games": match.games,
            "rate": match.rate, "ci_low": low, "ci_high": high,
            "points_per_game": match.points,
        }
    return results


def sweep(games: int) -> dict:
    """The whole grid, baseline first, with the legality checks up front."""
    grid = knobs()
    refuse_fixed(grid)
    base = baseline()
    refuse_downward(grid, base)

    started = time.time()
    cells = [{"knob": "baseline", "value": "shipped", "is_baseline": True,
              "matchups": measure(base, games)}]
    for knob in grid:
        current = knob.read(base)
        for value in knob.values:
            if value == current:
                continue
            cells.append({
                "knob": knob.name, "value": knob.fmt(value),
                "status": knob.status, "labels": list(knob.labels),
                "source": knob.source, "note": knob.note, "is_baseline": False,
                "matchups": measure(knob.apply(base, value), games),
            })
    return {
        "games_per_matchup": games,
        "eval_seed": EVAL_SEED,
        "baseline": _describe(base),
        "fixed_parameters_not_varied": list(fixed_parameters()),
        "inputs": list(config_paths()),
        "wall_time_seconds": round(time.time() - started, 1),
        "cells": cells,
    }


def _describe(setting) -> dict:
    """The shipped values every delta is measured against."""
    return {
        "board_size": setting.params.board_size,
        "barrier_quota": setting.params.barrier_quota,
        "horizon": f"{setting.params.move_ceiling}/{setting.params.survival_threshold}",
        "equilibrium_iterations": setting.iterations,
        "resolution_rules": (f"race={str(setting.rules.capture_on_barrier_race).lower()},"
                             f"swap={str(setting.rules.capture_on_swap).lower()}"),
        "weights": setting.weights_label,
        "cop_start": list(setting.params.cop_start),
        "thief_start": list(setting.params.thief_start),
    }


def main(argv=None) -> int:
    """Run the sweep and write the JSON the documents are rendered from."""
    parser = argparse.ArgumentParser(description="OFAT sensitivity sweep (offline)")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES)
    parser.add_argument("--out", default=str(OUT_PATH))
    args = parser.parse_args(argv)

    data = sweep(args.games)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(data['cells'])} configurations, {args.games} games/matchup, "
          f"{data['wall_time_seconds']}s -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
