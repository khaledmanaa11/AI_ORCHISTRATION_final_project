"""GATE-4 criterion 1's 'does a decoded hint move the posterior' spy
(04-14 Task 1, must_haves #1: "the mean absolute change in belief
posterior on those turns").

Wraps `BeliefAdapter.decide` for the duration of a measurement run to
record the belief posterior's L1 change on every call, bucketed by whether
that turn's `Inference` carried evidence. This never edits
`strategy/beliefadapter.py`: the real method runs completely unchanged,
called through the exact same public entry point every real game already
uses -- the spy only reads `self.belief.posterior()` immediately before and
after, the same technique `tests/integration/test_language_pipeline.py`'s
own Figure-7 order test already uses to observe a real call without
modifying it (must_haves: "the measurement describes the shipped game and
not a special build").
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field

from pursuit.strategy import beliefadapter


@dataclass
class BeliefDeltaLog:
    """Accumulates one `decide()` call's posterior-change measurement per
    entry, split by whether that turn's hint decoded to evidence."""

    evidence_deltas: list[float] = field(default_factory=list)
    no_evidence_deltas: list[float] = field(default_factory=list)

    @property
    def turns(self) -> int:
        return len(self.evidence_deltas) + len(self.no_evidence_deltas)

    @property
    def evidence_fraction(self) -> float:
        return len(self.evidence_deltas) / self.turns if self.turns else 0.0

    @property
    def mean_evidence_delta(self) -> float:
        deltas = self.evidence_deltas
        return sum(deltas) / len(deltas) if deltas else 0.0


def _posterior_l1(before: tuple, after: tuple) -> float:
    """Sum of absolute per-cell differences between two posteriors (an L1
    distance) -- zero means "the update changed nothing"."""
    return sum(
        abs(a - b)
        for row_b, row_a in zip(before, after, strict=True)
        for b, a in zip(row_b, row_a, strict=True)
    )


@contextmanager
def spy_belief_deltas(log: BeliefDeltaLog):
    """Patch `BeliefAdapter.decide` for the `with` block's lifetime; always
    restores the original method, even if the block raises."""
    original = beliefadapter.BeliefAdapter.decide

    def spied(self, state, inference, opponent_field, rules, *, known_cell=None):
        before = self.belief.posterior()
        decision = original(self, state, inference, opponent_field, rules, known_cell=known_cell)
        after = self.belief.posterior()
        delta = _posterior_l1(before, after)
        bucket = log.evidence_deltas if inference.is_evidence else log.no_evidence_deltas
        bucket.append(delta)
        return decision

    beliefadapter.BeliefAdapter.decide = spied
    try:
        yield log
    finally:
        beliefadapter.BeliefAdapter.decide = original
