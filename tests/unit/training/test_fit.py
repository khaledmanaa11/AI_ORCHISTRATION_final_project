"""Outcome regression: the FACT-target gradient, Adagrad, and sample extraction.

The target is the game's actual result, never a bootstrap (module doc), so the
loss/gradient formulas are pinned exactly: v = tanh(w.phi); L = (v - z)^2. A
perfectly-fitted sample must drive both to zero, and one Adagrad step on the
real gradient must reduce the loss it was computed from.
"""

from __future__ import annotations

from math import tanh

import pytest

from pursuit.constants import Outcome
from pursuit.shared.state import GameState
from pursuit.strategy.features import FEATURE_COUNT, phi
from training.fit import Adagrad, evaluate_loss, gradient, samples_from
from training.joint_game import GameRecord


def _state(cop, thief, barriers=frozenset(), placed=0, turn=0):
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=turn)


def test_gradient_of_a_perfectly_fitted_sample_is_near_zero(default_params):
    state = _state((2, 2), (4, 5))
    weights = tuple(0.05 * index for index in range(FEATURE_COUNT))
    raw = sum(w * x for w, x in zip(weights, phi(state, default_params), strict=True))
    target = tanh(raw)
    grad, loss = gradient(weights, [(state, target)], default_params)
    assert loss == pytest.approx(0.0, abs=1e-9)
    assert all(component == pytest.approx(0.0, abs=1e-9) for component in grad)


def test_gradient_points_downhill(default_params):
    """One Adagrad step on the true gradient must reduce the loss it came from."""
    samples = [(_state((0, 0), (6, 6)), 1.0), (_state((3, 3), (3, 4)), -1.0)]
    weights = tuple(0.0 for _ in range(FEATURE_COUNT))
    grad, loss_before = gradient(weights, samples, default_params)
    updated = Adagrad(rate=0.5).step(weights, grad)
    loss_after = evaluate_loss(updated, samples, default_params)
    assert loss_after < loss_before


def test_adagrad_shrinks_later_steps_for_a_repeated_large_gradient():
    optimizer = Adagrad(rate=1.0, size=1)
    weights = (0.0,)
    large_gradient = [10.0]
    first = optimizer.step(weights, large_gradient)
    second = optimizer.step(first, large_gradient)
    first_step = abs(weights[0] - first[0])
    second_step = abs(first[0] - second[0])
    assert second_step < first_step


def test_samples_from_drops_the_opening_state_and_the_terminal_state(default_params):
    states = (
        _state((0, 0), (6, 6), turn=0),
        _state((0, 1), (6, 5), turn=1),
        _state((0, 2), (6, 4), turn=2),
        _state((0, 3), (6, 3), turn=3),
    )
    record = GameRecord(outcome=Outcome.CAPTURE, states=states, turns=3)
    pairs = samples_from([record], default_params)
    assert [state for state, _ in pairs] == list(states[1:-1])


def test_samples_from_uses_the_records_cop_target(default_params):
    states = (_state((0, 0), (6, 6)), _state((0, 1), (6, 5)), _state((0, 2), (6, 4)))
    capture = GameRecord(outcome=Outcome.CAPTURE, states=states, turns=2)
    survival = GameRecord(outcome=Outcome.SURVIVAL, states=states, turns=2)
    assert all(target == 1.0 for _, target in samples_from([capture], default_params))
    assert all(target == -1.0 for _, target in samples_from([survival], default_params))


def test_evaluate_loss_matches_gradients_loss(default_params):
    samples = [(_state((0, 0), (6, 6)), 1.0)]
    weights = tuple(0.1 * index for index in range(FEATURE_COUNT))
    _, expected = gradient(weights, samples, default_params)
    assert evaluate_loss(weights, samples, default_params) == pytest.approx(expected)
