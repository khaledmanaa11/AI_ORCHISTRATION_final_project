"""GATE-4 statistical honesty (AI-SPEC Sec5 "Statistical honesty of the E5
bar"): McNemar's exact test over the paired, discordant outcomes is the
primary gate; the unpaired two-proportion z-test is reported as a
conservative cross-check. Pure `math` stdlib -- no scipy dependency for two
small closed-form tests.

The null is the MEASURED heuristic-vs-heuristic baseline win rate for that
role, never an assumed 50% -- the game is not role-symmetric (D-23's own
must_have wording).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def mcnemar_exact_pvalue(learner_only_wins: int, baseline_only_wins: int) -> float:
    """Two-sided exact McNemar p-value over the discordant pairs.

    `learner_only_wins` (b): the learner's role won a paired trial the
    baseline's identical replay did not. `baseline_only_wins` (c): the
    reverse. Concordant pairs (both won or both lost) carry no information
    about a MARGIN and are correctly excluded from n = b + c.
    """
    n = learner_only_wins + baseline_only_wins
    if n == 0:
        return 1.0
    k = min(learner_only_wins, baseline_only_wins)
    cumulative = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2 * cumulative)


def two_proportion_z(wins_a: int, n_a: int, wins_b: int, n_b: int) -> float:
    """Conservative unpaired cross-check; 0.0 when either sample is empty or
    the pooled variance is degenerate."""
    if n_a == 0 or n_b == 0:
        return 0.0
    p_a, p_b = wins_a / n_a, wins_b / n_b
    p_pool = (wins_a + wins_b) / (n_a + n_b)
    variance = p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b)
    if variance <= 0:
        return 0.0
    return (p_a - p_b) / math.sqrt(variance)


def normal_sf(z: float) -> float:
    """One-sided upper-tail survival function of the standard normal."""
    return 0.5 * math.erfc(z / math.sqrt(2))


@dataclass(frozen=True)
class GateVerdict:
    """One role's GATE-4 verdict -- never averaged or shared across roles (D-25)."""

    role: str
    n_games: int
    n_effective: int
    learner_win_rate: float
    baseline_win_rate: float
    margin: float
    mcnemar_p: float
    z_score: float
    z_p_one_sided: float
    meets_margin: bool
    meets_absolute_floor: bool
    is_significant: bool
    passed: bool


def evaluate_gate(
    *,
    role: str,
    learner_wins: int,
    baseline_wins: int,
    n_games: int,
    n_effective: int,
    learner_effective_wins: int,
    baseline_effective_wins: int,
    learner_only_wins: int,
    baseline_only_wins: int,
    win_rate_margin: float,
    min_win_rate_absolute: float,
    significance_alpha: float,
) -> GateVerdict:
    """E5's full bar: margin over the MEASURED baseline, an absolute floor
    (guards a trivially weak baseline), and paired-test significance -- all
    three must hold (STRAT-01, D-23)."""
    _assert_counts_in_range(
        learner_wins=learner_wins,
        baseline_wins=baseline_wins,
        n_games=n_games,
        learner_effective_wins=learner_effective_wins,
        baseline_effective_wins=baseline_effective_wins,
        learner_only_wins=learner_only_wins,
        baseline_only_wins=baseline_only_wins,
        n_effective=n_effective,
    )
    learner_rate = learner_wins / n_games
    baseline_rate = baseline_wins / n_games
    margin = learner_rate - baseline_rate
    mcnemar_p = mcnemar_exact_pvalue(learner_only_wins, baseline_only_wins)
    z = two_proportion_z(
        learner_effective_wins, n_effective, baseline_effective_wins, n_effective
    )
    meets_margin = margin >= win_rate_margin
    meets_floor = learner_rate >= min_win_rate_absolute
    significant = mcnemar_p < significance_alpha
    return GateVerdict(
        role=role,
        n_games=n_games,
        n_effective=n_effective,
        learner_win_rate=learner_rate,
        baseline_win_rate=baseline_rate,
        margin=margin,
        mcnemar_p=mcnemar_p,
        z_score=z,
        z_p_one_sided=normal_sf(z),
        meets_margin=meets_margin,
        meets_absolute_floor=meets_floor,
        is_significant=significant,
        passed=meets_margin and meets_floor and significant,
    )


def _assert_counts_in_range(
    *,
    learner_wins: int,
    baseline_wins: int,
    n_games: int,
    learner_effective_wins: int,
    baseline_effective_wins: int,
    learner_only_wins: int,
    baseline_only_wins: int,
    n_effective: int,
) -> None:
    if n_games <= 0:
        raise ValueError("n_games must be positive")
    if n_effective <= 0:
        raise ValueError("n_effective must be positive")
    _assert_wins_in_range("learner_wins", learner_wins, n_games)
    _assert_wins_in_range("baseline_wins", baseline_wins, n_games)
    _assert_wins_in_range("learner_effective_wins", learner_effective_wins, n_effective)
    _assert_wins_in_range("baseline_effective_wins", baseline_effective_wins, n_effective)
    if learner_only_wins < 0 or baseline_only_wins < 0:
        raise ValueError("discordant scenario counts must be non-negative")
    if learner_only_wins + baseline_only_wins > n_effective:
        raise ValueError("discordant scenario counts cannot exceed n_effective")


def _assert_wins_in_range(label: str, wins: int, n_trials: int) -> None:
    if wins < 0 or wins > n_trials:
        raise ValueError(f"{label} must be between 0 and its trial count")
