"""The fixed eval scenario set (PRD GATE-4, AI-SPEC Sec5 Reference Dataset, D-23).

`artifacts/eval_scenarios.json` is authored and committed by this plan
(03-10) -- this module only reads it; nothing here regenerates the file, so
results stay comparable across every checkpoint that is ever evaluated
against it.

Held-out seeds (D-23): each scenario's `seed` is
`training_seed + eval_seed_offset + index` -- a fixed, large offset
(10,000,000) above the training run's own seed. Training in this codebase
draws its ENTIRE run from one `random.Random(seed)` stream (03-08 D-19), not
a discrete per-episode seed set, so the disjointness guarantee that is
actually meaningful here -- and the one `assert_seeds_held_out` checks, in
code -- is that every eval seed is strictly greater than that single
training seed value and that the eval seeds are themselves pairwise
distinct.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pursuit.shared.strategy_config import StrategyParams

Coord = tuple[int, int]

DEFAULT_SCENARIOS_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "eval_scenarios.json"


@dataclass(frozen=True)
class Scenario:
    """One fixed starting configuration, replayed identically by every arm."""

    id: str
    group: str
    seed: int
    cop_start: Coord
    thief_start: Coord
    preplaced_barriers: tuple[Coord, ...]
    role_under_test: str
    expected: str
    start_turn: int = 0


def load_scenarios(path: Path | str = DEFAULT_SCENARIOS_PATH) -> list[Scenario]:
    """Load and validate every entry; fails loud on a malformed file rather
    than silently evaluating against an empty or partial scenario set."""
    with Path(path).open(encoding="utf-8") as fh:
        raw = json.load(fh)
    scenarios = [_from_entry(entry) for entry in raw["scenarios"]]
    if not scenarios:
        raise ValueError(f"{path}: eval scenario file has zero scenarios")
    return scenarios


def _from_entry(entry: dict) -> Scenario:
    return Scenario(
        id=entry["id"],
        group=entry["group"],
        seed=int(entry["seed"]),
        cop_start=tuple(entry["cop_start"]),
        thief_start=tuple(entry["thief_start"]),
        preplaced_barriers=tuple(tuple(cell) for cell in entry["preplaced_barriers"]),
        role_under_test=entry["role_under_test"],
        expected=entry["expected"],
        start_turn=int(entry.get("start_turn", 0)),
    )


def assert_seeds_held_out(scenarios: list[Scenario], params: StrategyParams) -> None:
    """D-23, executable, never a comment: every scenario seed must lie
    strictly above the training run's own seed value (see module docstring
    for why that is the meaningful disjointness claim in this codebase's
    single-seed-stream training design)."""
    seeds = [scenario.seed for scenario in scenarios]
    assert len(set(seeds)) == len(seeds), "eval scenario seeds must be pairwise distinct"
    assert min(seeds) > params.seed, (
        f"eval seeds must be held out above the training seed ({params.seed}); "
        f"got minimum {min(seeds)}"
    )


def repeat_seeds(scenario: Scenario, repeats: int) -> list[int]:
    """`repeats` independent seeds derived from the scenario's own held-out
    seed -- never a fresh, unlogged random draw."""
    return [scenario.seed + i for i in range(repeats)]
