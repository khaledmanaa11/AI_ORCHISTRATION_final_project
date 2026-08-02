"""Orchestrates the three GATE-4 arms over the D-23 scenario+seed grid and
turns raw game outcomes into per-role `GateVerdict`s.

AI-SPEC Sec5 E5 significance is scenario-level evidence, not deterministic
replay count. D-25 still requires independent role verdicts: `verdicts` is
keyed by role and each entry stands alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pursuit.constants import Outcome
from pursuit.shared.config import GameParams, load_game_params
from training.eval_aggregate import (
    discordant_scenarios,
    replays_are_degenerate,
    scenario_win_fractions,
)
from training.eval_arms import (
    ARM_BASELINE,
    ARM_COP_LEARNER,
    ARM_THIEF_LEARNER,
    GameResult,
    MissingQTableError,
    build_arm_brains,
    play_game,
    strategy_params,
)
from training.eval_scenarios import (
    DEFAULT_SCENARIOS_PATH,
    Scenario,
    assert_seeds_held_out,
    load_scenarios,
    repeat_seeds,
)
from training.eval_stats import GateVerdict, evaluate_gate

_GAME_PARAMS_PATH = Path(__file__).resolve().parent.parent / "config" / "police" / "game_params.json"


@dataclass(frozen=True)
class EvaluationReport:
    repeats: int
    n_scenarios: int
    verdicts: dict[str, GateVerdict]
    errors: dict[str, str]
    baseline_win_rates: dict[str, float]
    replays_degenerate: bool


def run_arm(
    arm: str, scenarios: list[Scenario], repeats: int, game_params: GameParams,
    cop_qtable: Path | str, thief_qtable: Path | str,
) -> list[GameResult]:
    results = []
    for scenario in scenarios:
        for seed in repeat_seeds(scenario, repeats):
            cop_brain, thief_brain = build_arm_brains(arm, game_params, seed, cop_qtable, thief_qtable)
            results.append(play_game(cop_brain, thief_brain, scenario, seed, game_params))
    return results


def _role_won(result: GameResult, role: str) -> bool:
    target = Outcome.CAPTURE if role == "cop" else Outcome.SURVIVAL
    return result.outcome is target


def _effective_wins(win_fractions: dict[str, float]) -> int:
    return int(round(sum(win_fractions.values())))


def _gate_for_role(role: str, learner_results, baseline_results, params) -> GateVerdict:
    learner_fracs = scenario_win_fractions(learner_results, role)
    baseline_fracs = scenario_win_fractions(baseline_results, role)
    learner_only, baseline_only = discordant_scenarios(learner_fracs, baseline_fracs)
    return evaluate_gate(
        role=role,
        learner_wins=sum(_role_won(r, role) for r in learner_results),
        baseline_wins=sum(_role_won(r, role) for r in baseline_results),
        n_games=len(learner_results),
        n_effective=len(learner_fracs),
        learner_effective_wins=_effective_wins(learner_fracs),
        baseline_effective_wins=_effective_wins(baseline_fracs),
        learner_only_wins=learner_only,
        baseline_only_wins=baseline_only,
        win_rate_margin=params.win_rate_margin,
        min_win_rate_absolute=params.min_win_rate_absolute,
        significance_alpha=params.significance_alpha,
    )


def _assert_scenario_grid_matches_config(scenarios: list[Scenario], params) -> None:
    assert len(scenarios) == params.eval_scenarios, (
        f"eval_scenarios.json has {len(scenarios)} entries, config expects {params.eval_scenarios}"
    )
    assert params.eval_scenarios * params.repeats_per_scenario == params.eval_games, (
        f"{params.eval_scenarios} * {params.repeats_per_scenario} "
        f"!= eval_games ({params.eval_games})"
    )


def run_evaluation(*, full: bool, scenarios_path: Path | str = DEFAULT_SCENARIOS_PATH) -> EvaluationReport:
    cop_params, thief_params = strategy_params("cop"), strategy_params("thief")
    scenarios = load_scenarios(scenarios_path)
    assert_seeds_held_out(scenarios, cop_params)
    _assert_scenario_grid_matches_config(scenarios, cop_params)

    game_params = load_game_params(_GAME_PARAMS_PATH)
    repeats = (
        cop_params.repeats_per_scenario if full else max(1, cop_params.eval_games_ci // len(scenarios))
    )

    baseline = run_arm(
        ARM_BASELINE, scenarios, repeats, game_params, cop_params.qtable_path, thief_params.qtable_path
    )
    baseline_win_rates = {
        role: sum(_role_won(r, role) for r in baseline) / len(baseline) for role in ("cop", "thief")
    }
    verdicts: dict[str, GateVerdict] = {}
    errors: dict[str, str] = {}
    degenerate_arms = [replays_are_degenerate(baseline)]
    for role, arm, params in (("cop", ARM_COP_LEARNER, cop_params), ("thief", ARM_THIEF_LEARNER, thief_params)):
        try:
            learner = run_arm(
                arm, scenarios, repeats, game_params, cop_params.qtable_path, thief_params.qtable_path
            )
        except MissingQTableError as exc:
            errors[role] = str(exc)
            continue
        degenerate_arms.append(replays_are_degenerate(learner))
        verdicts[role] = _gate_for_role(role, learner, baseline, params)

    return EvaluationReport(
        repeats=repeats, n_scenarios=len(scenarios), verdicts=verdicts, errors=errors,
        baseline_win_rates=baseline_win_rates, replays_degenerate=all(degenerate_arms),
    )
