"""Held-out measurement: play a fixed matchup and report a rate with an interval.

Run 1's gate reported 5/20 and 16/20 as bare fractions. At n=20 the 95% interval
on 5/20 spans roughly 0.09 to 0.49 -- wide enough that the result was consistent
with both "badly broken" and "nearly at target", and the post-mortem could not
tell which. Every rate this module reports carries its interval so that cannot
happen again.

Wilson rather than the normal approximation: at the rates that matter here (0.9+
for the cop, near 0 for a failing thief) the normal interval runs past 1.0 and
produces impossible bounds, while Wilson stays inside [0, 1] and keeps its
coverage at small n.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from math import sqrt

from pursuit.shared.config import GameParams
from pursuit.shared.resolution import ResolutionRules
from training.joint_game import play_game
from training.starts import sample_start

#: 1.96 -- the two-sided normal quantile for a 95% interval.
Z_95 = 1.959964


@dataclass(frozen=True)
class MatchResult:
    """One matchup's outcome: how often OUR seat achieved its win condition."""

    label: str
    seat: str
    wins: int
    games: int
    points: float

    @property
    def rate(self) -> float:
        """Our win rate in this matchup."""
        return self.wins / self.games if self.games else 0.0

    @property
    def interval(self) -> tuple:
        """95% Wilson interval on the rate."""
        return wilson(self.wins, self.games)

    def line(self) -> str:
        """One aligned report row, rate with interval and points per game."""
        low, high = self.interval
        return (
            f"{self.label:<34} {self.seat:<5} {self.wins:4d}/{self.games:<4d} "
            f"{self.rate:6.1%}  [{low:5.1%}, {high:5.1%}]  {self.points:5.2f} pts/game"
        )


def wilson(successes: int, total: int, z: float = Z_95) -> tuple:
    """Wilson score interval for a binomial proportion, clamped to [0, 1]."""
    if total == 0:
        return 0.0, 1.0
    rate = successes / total
    denominator = 1.0 + z * z / total
    centre = (rate + z * z / (2 * total)) / denominator
    spread = z * sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - spread), min(1.0, centre + spread)


def run_match(
    label: str,
    seat: str,
    make_cop,
    make_thief,
    games: int,
    params: GameParams,
    rules: ResolutionRules,
    seed: int,
    randomise_starts: bool = False,
) -> MatchResult:
    """Play *games* games of one matchup and score OUR seat.

    Parameters
    ----------
    seat:
        Which seat is ours -- "cop" scores captures, "thief" scores survivals.
    make_cop, make_thief:
        Callables taking the game index and returning a brain, so each game gets
        its own seeded instance and no state leaks between games.
    randomise_starts:
        False measures the negotiated opening, which is what a league game
        actually plays. True measures generalisation across the board.
    """
    rng = random.Random(seed)
    wins = 0
    for index in range(games):
        start = sample_start(params, rng) if randomise_starts else None
        record = play_game(make_cop(index), make_thief(index), params, rules, start)
        wins += record.captured if seat == "cop" else not record.captured

    if seat == "cop":
        won, lost = params.score_capture_cop, params.score_survival_cop
    else:
        won, lost = params.score_survival_thief, params.score_capture_thief
    points = (wins * won + (games - wins) * lost) / games if games else 0.0
    return MatchResult(label=label, seat=seat, wins=wins, games=games, points=points)


def compare(baseline: MatchResult, candidate: MatchResult) -> str:
    """Report whether *candidate* beat *baseline*, and whether it is separable.

    Non-overlapping Wilson intervals is a conservative significance check -- it is
    stricter than a two-proportion z-test, so calling a result significant here
    will not be an artefact of the test choice.
    """
    delta = candidate.rate - baseline.rate
    low, high = candidate.interval
    base_low, base_high = baseline.interval
    separated = low > base_high or high < base_low
    verdict = "SIGNIFICANT" if separated else "not separable"
    return f"{delta:+6.1%} vs baseline  ({verdict} at 95%)"
