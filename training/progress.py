"""Mutable run-loop bookkeeping for training/loop.py -- split out at the
150-code-line gate (repeats the 03-05/03-06/03-07 pattern). Pure data plus
small pure methods; no engine/pool/checkpoint calls live here.
"""

from __future__ import annotations

from dataclasses import dataclass

from training.harness import EpisodeResult


@dataclass
class RunProgress:
    """The counters RunState is built from at every checkpoint (D-24)."""

    episode: int = 0
    cop_episodes: int = 0
    thief_episodes: int = 0
    csv_rows: int = 0

    def role_episodes(self, role: str) -> int:
        return self.cop_episodes if role == "cop" else self.thief_episodes

    def advance(self, role: str) -> None:
        self.episode += 1
        if role == "cop":
            self.cop_episodes += 1
        else:
            self.thief_episodes += 1


@dataclass
class RoleAccumulator:
    """Aggregates episodes since this role's last curve row (D-25).

    `winrate_vs_baseline` is tracked against `opponent_kind == "heuristic"`
    draws specifically -- the pool's literal baseline member -- rather than
    every sampled opponent, so the column means what its name says.
    """

    reward_sum: float = 0.0
    decisions_sum: int = 0
    fallback_sum: int = 0
    episodes: int = 0
    baseline_wins: int = 0
    baseline_games: int = 0

    def record(self, result: EpisodeResult, opponent_kind: str) -> None:
        self.reward_sum += result.learner_reward_total
        self.decisions_sum += result.learner_decisions
        self.fallback_sum += result.learner_fallbacks
        self.episodes += 1
        if opponent_kind == "heuristic":
            self.baseline_games += 1
            self.baseline_wins += 1 if result.learner_won else 0

    def as_row(self, *, episode: int, epsilon: float, alpha: float, role: str) -> dict:
        return {
            "episode": episode,
            "epsilon": epsilon,
            "alpha": alpha,
            "mean_reward": self.reward_sum / self.episodes if self.episodes else 0.0,
            "winrate_vs_baseline": (
                self.baseline_wins / self.baseline_games if self.baseline_games else 0.0
            ),
            "fallback_rate": (
                self.fallback_sum / self.decisions_sum if self.decisions_sum else 0.0
            ),
            "role": role,
        }

    def reset(self) -> None:
        self.reward_sum = 0.0
        self.decisions_sum = 0
        self.fallback_sum = 0
        self.episodes = 0
        self.baseline_wins = 0
        self.baseline_games = 0
