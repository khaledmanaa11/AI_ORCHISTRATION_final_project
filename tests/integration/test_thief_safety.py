"""D-31 regression guard: two arms differing ONLY by whether the thief's
N[cop] safety filter (`safety.safe_moves`) is applied, replayed over the
same starts, must show the filtered thief performing at least as well
(committed grid) and no worse than a stated noise band (random starts) --
while the filter actually strips a candidate at least once and the filtered
thief never ends a turn inside N[cop] while an outside destination existed.
A no-op filter cannot pass this test.

NOT a re-measurement of D-31's headline 296/300 = 0.987 vs 283/300 = 0.943
(n=300 random starts, see `safety.py`'s own docstring) -- this module is a
regression guard only. n=60 cannot resolve a 4.4-point effect: at n=60,
p ~= 0.95, the 95% binomial half-width is ~= 1.96 * sqrt(0.95*0.05/60)
~= 0.055, so `REGRESSION_TOLERANCE = 0.05` below is roughly one noise band,
not a re-measurement bar.

Budget: 2 arms x (20 committed GATE-4 scenarios + 60 random starts) = 160
games. The plan's own context section estimated ~100ms/game (~16s total,
inside a <=30s target) -- that estimate does NOT reproduce here: measured
via `pytest --durations=5`, this module takes ~34s (~215ms/game average).
`cProfile` traces the difference to `barriers.py::choose_barrier` (03-07,
pre-existing, out of this plan's scope) -- ~80% of per-game cost is that
BFS-per-candidate barrier scan the cop already ran before this plan, not
anything this plan adds. Recorded honestly rather than cut to fit: `n=60`
is not reduced (it is load-bearing for the tolerance derivation above) and
barrier placement is not disabled (that would repeat D-31's own flawed
control, which this module explicitly does not reproduce, see below).

D-31's own disabled-barrier control is deliberately NOT reproduced here --
that control was itself flawed (the scenarios still carry pre-placed
barriers), so repeating it would just repeat the flaw.
"""

from __future__ import annotations

import random

import pytest

from pursuit.constants import Outcome
from pursuit.shared.config import GameParams
from pursuit.strategy import fallback, safety
from training import eval_arms
from training.eval_scenarios import DEFAULT_SCENARIOS_PATH, Scenario, load_scenarios

N_RANDOM_STARTS = 60  # engineering default -- see module docstring for the derivation
REGRESSION_TOLERANCE = 0.05  # engineering default -- ~one binomial noise band at n=60
_RANDOM_START_SEED = 314159  # named constant (D-19: seeded random.Random, never secrets)
_UNUSED_QTABLE = "unused.json"  # ARM_BASELINE never reads either qtable path


def _random_start_scenarios(game_params: GameParams, n: int, seed: int) -> list[Scenario]:
    """`n` uniform, distinct, non-adjacent (cop, thief) placements on an
    empty board -- D-31's own random-start design, test-local (not 03-15's
    committed `training/starts.py`, which this plan does not own)."""
    rng = random.Random(seed)
    size = game_params.board_size
    cells = [(row, col) for row in range(size) for col in range(size)]
    scenarios = []
    for i in range(n):
        cop, thief = rng.sample(cells, 2)
        while abs(cop[0] - thief[0]) + abs(cop[1] - thief[1]) <= 1:
            cop, thief = rng.sample(cells, 2)
        scenarios.append(
            Scenario(
                id=f"random_{i:03d}",
                group="random",
                seed=seed + i,
                cop_start=cop,
                thief_start=thief,
                preplaced_barriers=(),
                role_under_test="thief",
                expected="regression_guard",
            )
        )
    return scenarios


def _no_op_safe_moves(candidates, state, params):
    """The control arm: legal candidates pass through unfiltered -- the
    thief's pre-D-31 behaviour."""
    return candidates


def _spy_safe_moves(bound_calls: list[int], violations: list[tuple]):
    """Wraps the real `safe_moves`: records every call that actually
    stripped a candidate, and re-checks its never-inside-N[cop]-when-an-
    outside-cell-existed contract against the real state seen this turn."""
    real = safety.safe_moves

    def _spy(candidates, state, params):
        forbidden = safety.closed_neighbourhood(state, params)
        result = real(candidates, state, params)
        if result != candidates:
            bound_calls.append(1)
        if any(cell not in forbidden for cell in candidates):
            violations.extend(cell for cell in result if cell in forbidden)
        return result

    return _spy


def _play_all(cop_brain, thief_brain, scenarios, game_params) -> list[eval_arms.GameResult]:
    return [
        eval_arms.play_game(cop_brain, thief_brain, scenario, scenario.seed, game_params)
        for scenario in scenarios
    ]


def _thief_survived(result: eval_arms.GameResult) -> bool:
    return result.outcome is Outcome.SURVIVAL


def test_filter_never_regresses_and_actually_binds(
    monkeypatch: pytest.MonkeyPatch, default_params: GameParams
) -> None:
    grid = load_scenarios(DEFAULT_SCENARIOS_PATH)
    random_starts = _random_start_scenarios(default_params, N_RANDOM_STARTS, _RANDOM_START_SEED)
    all_scenarios = grid + random_starts

    cop_brain, thief_brain = eval_arms.build_arm_brains(
        eval_arms.ARM_BASELINE,
        default_params,
        seed=0,
        cop_qtable=_UNUSED_QTABLE,
        thief_qtable=_UNUSED_QTABLE,
    )

    bound_calls: list[int] = []
    violations: list[tuple] = []
    with monkeypatch.context() as patched:
        patched.setattr(fallback, "safe_moves", _spy_safe_moves(bound_calls, violations))
        filtered = _play_all(cop_brain, thief_brain, all_scenarios, default_params)

    with monkeypatch.context() as patched:
        patched.setattr(fallback, "safe_moves", _no_op_safe_moves)
        unfiltered = _play_all(cop_brain, thief_brain, all_scenarios, default_params)

    assert not violations, (
        "filtered thief ended a turn inside N[cop] while an outside destination "
        f"existed: {violations[:5]}"
    )
    assert len(bound_calls) > 0, "filter never removed a candidate across 160 games -- vacuous"

    n_grid = len(grid)
    grid_filtered = sum(_thief_survived(r) for r in filtered[:n_grid])
    grid_unfiltered = sum(_thief_survived(r) for r in unfiltered[:n_grid])
    assert grid_filtered >= grid_unfiltered, (
        f"grid: filtered thief survived {grid_filtered}/{n_grid}, "
        f"unfiltered {grid_unfiltered}/{n_grid} -- filter regressed"
    )

    random_filtered_rate = sum(_thief_survived(r) for r in filtered[n_grid:]) / N_RANDOM_STARTS
    random_unfiltered_rate = sum(_thief_survived(r) for r in unfiltered[n_grid:]) / N_RANDOM_STARTS
    assert random_filtered_rate >= random_unfiltered_rate - REGRESSION_TOLERANCE, (
        f"random starts: filtered {random_filtered_rate:.3f} vs unfiltered "
        f"{random_unfiltered_rate:.3f} -- exceeds the {REGRESSION_TOLERANCE} noise band"
    )
