"""Outcome regression: fit the 15 weights so tanh(w.phi) predicts who won.

Deliberately NOT bootstrapped. A TD target is an estimate produced by the same
weights being updated, which under a moving opponent is the non-stationarity trap
that made run 1's tabular learner chase its own tail. The target here is a FACT --
the game's actual result -- so a generation's update cannot be corrupted by its
own errors, only by its sampling.

The loss is squared error on the squashed evaluation, which is what the search
already consumes as a leaf value:

    v = tanh(w . phi(s));  L = (v - z)^2;  dL/dw = 2 (v - z) (1 - v^2) phi(s)

z is +1 when the cop won and -1 when the thief did. One game therefore trains
BOTH seats at once: the states are shared and the sign convention is the same
zero-sum one the mover uses, so there is no second vector and no second run.

Adagrad scales each weight's step by its own gradient history. Feature scales
differ by an order of magnitude here (a 0/1 indicator against a normalised cycle
rank), and a single global learning rate would either crawl on one or diverge on
the other.
"""

from __future__ import annotations

from math import tanh

from pursuit.shared.config import GameParams
from pursuit.strategy.features import FEATURE_COUNT, phi

#: Guards the Adagrad denominator against a division by zero on a feature that
#: has not yet produced any gradient.
_EPSILON = 1e-8


class Adagrad:
    """Per-weight adaptive step sizes, accumulated across the whole run."""

    def __init__(self, rate: float, size: int = FEATURE_COUNT) -> None:
        """Start every accumulator at zero; `rate` is the base step size."""
        self.rate = rate
        self.history = [0.0] * size

    def step(self, weights: tuple, gradient: list) -> tuple:
        """Return weights moved one step down *gradient*."""
        updated = []
        for index, (weight, slope) in enumerate(zip(weights, gradient, strict=True)):
            self.history[index] += slope * slope
            scale = self.rate / (self.history[index] ** 0.5 + _EPSILON)
            updated.append(weight - scale * slope)
        return tuple(updated)


def gradient(
    weights: tuple, samples: list, params: GameParams
) -> tuple:
    """Mean loss gradient and mean loss over (state, target) samples.

    Returns
    -------
    tuple[list[float], float]
        The averaged gradient and the averaged squared error, so a caller can
        report the loss curve rule 42 wants without recomputing it.
    """
    totals = [0.0] * FEATURE_COUNT
    loss = 0.0
    for state, target in samples:
        vector = phi(state, params)
        raw = sum(w * x for w, x in zip(weights, vector, strict=True))
        value = tanh(raw)
        error = value - target
        loss += error * error
        # d/dw tanh(w.x) = (1 - tanh^2) x, so the chain rule gives 2 e (1-v^2) x.
        scale = 2.0 * error * (1.0 - value * value)
        for index, component in enumerate(vector):
            totals[index] += scale * component
    count = max(1, len(samples))
    return [total / count for total in totals], loss / count


def samples_from(records: list, params: GameParams, skip_opening: int = 1) -> list:
    """Flatten finished games into (state, cop_target) pairs.

    The first `skip_opening` states of each game are dropped: every game shares
    its opening, so those states carry no discriminating signal and simply pull
    every weight toward the base rate of the pool.

    The terminal state is dropped too. Its value is decided by the resolver, not
    by the evaluation, and fitting the evaluation to it teaches the leaf to
    predict something the search already knows exactly.
    """
    pairs = []
    for record in records:
        target = record.cop_target
        body = record.states[skip_opening:-1]
        pairs.extend((state, target) for state in body)
    return pairs


def evaluate_loss(weights: tuple, samples: list, params: GameParams) -> float:
    """Mean squared error of *weights* on *samples*, without updating anything."""
    _, loss = gradient(weights, samples, params)
    return loss
