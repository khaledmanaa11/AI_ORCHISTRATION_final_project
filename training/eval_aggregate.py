"""Scenario-level GATE-4 aggregation for statistical honesty (D-23, D-25,
AI-SPEC Sec5 E5).

Repeated seeds only add independent evidence when the evaluated brain is
stochastic. With deterministic eval brains, each D-23 scenario is the real
paired unit, so this module keeps replay counts for point estimates while
collapsing significance arithmetic to per-scenario win fractions.
"""

from __future__ import annotations

from collections.abc import Mapping

from pursuit.constants import CellState, Outcome
from training.eval_arms import GameResult

_ROLE_WIN_OUTCOMES = {
    CellState.COP.value: Outcome.CAPTURE,
    CellState.THIEF.value: Outcome.SURVIVAL,
}


def scenario_win_fractions(results: list[GameResult], role: str) -> dict[str, float]:
    """Return each scenario's replay win fraction for `role`."""
    target = _target_outcome(role)
    wins: dict[str, int] = {}
    totals: dict[str, int] = {}
    for result in results:
        totals[result.scenario_id] = totals.get(result.scenario_id, 0) + 1
        wins[result.scenario_id] = wins.get(result.scenario_id, 0) + int(result.outcome is target)
    return {scenario_id: wins.get(scenario_id, 0) / total for scenario_id, total in totals.items()}


def discordant_scenarios(
    learner_fracs: Mapping[str, float], baseline_fracs: Mapping[str, float]
) -> tuple[int, int]:
    """Return learner-only and baseline-only wins over paired scenarios."""
    _assert_same_scenarios(learner_fracs, baseline_fracs)
    learner_only = baseline_only = 0
    for scenario_id, learner_frac in learner_fracs.items():
        baseline_frac = baseline_fracs[scenario_id]
        if learner_frac > baseline_frac:
            learner_only += 1
        elif baseline_frac > learner_frac:
            baseline_only += 1
    return learner_only, baseline_only


def replays_are_degenerate(results: list[GameResult]) -> bool:
    """True when every scenario has one repeated outcome."""
    outcomes: dict[str, set[Outcome | None]] = {}
    for result in results:
        outcomes.setdefault(result.scenario_id, set()).add(result.outcome)
    return all(len(scenario_outcomes) == 1 for scenario_outcomes in outcomes.values())


def _target_outcome(role: str) -> Outcome:
    try:
        return _ROLE_WIN_OUTCOMES[role]
    except KeyError as exc:
        raise ValueError(f"unknown role {role!r}; known roles: {sorted(_ROLE_WIN_OUTCOMES)}") from exc


def _assert_same_scenarios(
    learner_fracs: Mapping[str, float], baseline_fracs: Mapping[str, float]
) -> None:
    learner_ids = set(learner_fracs)
    baseline_ids = set(baseline_fracs)
    if learner_ids != baseline_ids:
        raise ValueError("learner and baseline scenario ids must match for paired evaluation")
