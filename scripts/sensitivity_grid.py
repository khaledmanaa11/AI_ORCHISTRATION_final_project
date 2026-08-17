"""The knobs the sensitivity sweep is allowed to turn, and the three fixed
matchups it turns them against (08-09).

WHY THIS RUNS OFFLINE AND WITHOUT A MODEL. Everything here drives
`training/joint_game.play_game` through `training/arena.run_match` -- the
same loop the Phase-3 learning curves were fitted with. There is no network
call, no API key and no `logs/` read, so the sweep reproduces from a clean
checkout. The cost is real and is stated in `docs/SENSITIVITY.md`: the
opponents are the two naive archetypes, not a league team, and no league
game has been played to calibrate against.

THE OPENING IS THE NEGOTIATED ONE, not randomised starts, because that is
what a league game actually plays (`run_eval.py`'s own distinction). When
the board grows the cop stays in its corner and the thief is re-centred --
Table 13 rows 5-6 describe those seats by POSITION NAME ("corner", "centre")
and both are `negotiable`, so keeping the literal `(3, 3)` on a 11x11 board
would be sweeping two parameters while claiming to sweep one.

Every knob carries the status it believes it has; `sensitivity_status`
refuses the grid when the extract disagrees. See that module for why.
"""

from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass, field
from pathlib import Path

from sensitivity_status import ENGINEERING, MINIMUM, REPO_ROOT

from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.resolution import ResolutionRules, load_resolution_rules
from pursuit.strategy.naive import ChaserCop, GreedyEvader
from pursuit.strategy.valuebrain import DEFAULT_EQUILIBRIUM_ITERATIONS, ValueSearchBrain
from pursuit.strategy.weights import PRIOR, load_weights

CONFIG_DIR = REPO_ROOT / "config" / "police"
SHIPPED_WEIGHTS = REPO_ROOT / "artifacts" / "run2" / "weights.json"
#: Held-out evaluation seed, shared with `training/run_eval.py` so a reader
#: can put the two outputs side by side.
EVAL_SEED = 90210


@dataclass(frozen=True)
class Setting:
    """One fully-specified configuration a match can be played under."""

    params: GameParams
    rules: ResolutionRules
    iterations: int
    weights: tuple
    weights_label: str


@dataclass(frozen=True)
class Knob:
    """One swept dimension: what it is, what it is allowed to be, how to set it."""

    name: str
    status: str
    values: tuple
    read: object
    apply: object
    labels: tuple = ()
    source: str = ""
    note: str = ""
    fmt: object = field(default=str)


def baseline() -> Setting:
    """The shipped configuration -- the point every knob is measured from."""
    return Setting(
        params=load_game_params(CONFIG_DIR / "game_params.json"),
        rules=load_resolution_rules(CONFIG_DIR / "resolution.json"),
        iterations=DEFAULT_EQUILIBRIUM_ITERATIONS,
        weights=load_weights(str(SHIPPED_WEIGHTS)),
        weights_label="run2",
    )


def _board(setting: Setting, value: int) -> Setting:
    centre = value // 2
    params = dataclasses.replace(setting.params, board_size=value, thief_start=(centre, centre))
    return dataclasses.replace(setting, params=params)


def _quota(setting: Setting, value: int) -> Setting:
    return dataclasses.replace(setting, params=dataclasses.replace(
        setting.params, barrier_quota=value))


def _horizon(setting: Setting, value: tuple) -> Setting:
    ceiling, threshold = value
    return dataclasses.replace(setting, params=dataclasses.replace(
        setting.params, move_ceiling=ceiling, survival_threshold=threshold))


def _iterations(setting: Setting, value: int) -> Setting:
    return dataclasses.replace(setting, iterations=value)


def _resolution(setting: Setting, value: tuple) -> Setting:
    race, swap = value
    return dataclasses.replace(setting, rules=ResolutionRules(
        capture_on_barrier_race=race, capture_on_swap=swap))


def _weights(setting: Setting, value: str) -> Setting:
    vector = load_weights(str(SHIPPED_WEIGHTS)) if value == "run2" else PRIOR
    return dataclasses.replace(setting, weights=vector, weights_label=value)


def knobs() -> tuple:
    """The grid. Ordered as `docs/SENSITIVITY.md` reports it."""
    return (
        Knob("board_size", MINIMUM, (7, 9, 11), lambda s: s.params.board_size, _board,
             labels=("board size",),
             note="cop stays in the corner, thief re-centred (Table 13 rows 5-6)"),
        Knob("barrier_quota", MINIMUM, (14, 21, 28), lambda s: s.params.barrier_quota, _quota,
             labels=("barrier quota",)),
        Knob("horizon", MINIMUM, ((35, 35), (50, 50), (70, 70)),
             lambda s: (s.params.move_ceiling, s.params.survival_threshold), _horizon,
             labels=("move ceiling", "survival threshold"),
             note="swept jointly: the shipped config sets them equal",
             fmt=lambda v: f"{v[0]}/{v[1]}"),
        Knob("equilibrium_iterations", ENGINEERING, (50, 200, 800),
             lambda s: s.iterations, _iterations,
             source="src/pursuit/strategy/valuebrain.py:29-32",
             note="regret-matching iterations; the docstring calls 200 converged"),
        Knob("resolution_rules", ENGINEERING,
             ((False, False), (True, False), (False, True), (True, True)),
             lambda s: (s.rules.capture_on_barrier_race, s.rules.capture_on_swap), _resolution,
             source="src/pursuit/shared/resolution.py:1-13",
             note="negotiated per pair of teams; NOT an Appendix F row",
             fmt=lambda v: f"race={str(v[0]).lower()},swap={str(v[1]).lower()}"),
        Knob("weights", ENGINEERING, ("run2", "prior"), lambda s: s.weights_label, _weights,
             source="artifacts/run2/weights.json",
             note="the fitted vector against the hand-written prior"),
    )


def matchups() -> tuple:
    """The three fixed anchors, as `(label, our_seat, opponent_factory)`."""
    return (
        ("thief vs chaser cop (seals)", "thief",
         lambda p, i: ChaserCop("cop", game_params=p, use_barriers=True, rng=random.Random(i))),
        ("thief vs chaser cop (no seals)", "thief",
         lambda p, i: ChaserCop("cop", game_params=p, use_barriers=False, rng=random.Random(i))),
        ("cop vs greedy evader", "cop",
         lambda p, i: GreedyEvader("thief", game_params=p, rng=random.Random(i))),
    )


def our_brain(setting: Setting, seat: str):
    """A factory building OUR seat's brain under *setting*, seeded per game."""
    def build(index: int):
        return ValueSearchBrain(
            seat, game_params=setting.params, rules=setting.rules,
            weights=setting.weights, iterations=setting.iterations,
            rng=random.Random(EVAL_SEED + index),
        )
    return build


def config_paths() -> tuple:
    """Every file the sweep reads. Asserted tracked by the offline probe."""
    return tuple(
        str(Path(path).relative_to(REPO_ROOT)).replace("\\", "/")
        for path in (CONFIG_DIR / "game_params.json", CONFIG_DIR / "resolution.json",
                     SHIPPED_WEIGHTS)
    )
