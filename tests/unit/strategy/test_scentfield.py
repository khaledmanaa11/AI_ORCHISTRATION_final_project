"""Tests for ScentField: two independent per-peer grids, no shared state (D-49)."""

import pathlib

import pytest

from pursuit.shared.scent_config import load_scent_model
from pursuit.strategy.scent import decay, expected_strength_after
from pursuit.strategy.scentfield import ScentField

_SCENT_CONFIG = pathlib.Path(__file__).parents[3] / "config" / "police" / "scent.json"
_BOARD_SIZE = 7


@pytest.fixture(scope="module")
def model():
    return load_scent_model(_SCENT_CONFIG)


@pytest.fixture
def field_(model):
    return ScentField(model=model, board_size=_BOARD_SIZE)


def test_emit_own_adds_the_kernel_to_the_own_grid(field_, model):
    field_.emit_own((3, 3))
    assert field_.strength("own", (3, 3)) == model.source


def test_emit_own_never_perturbs_opponent(field_):
    field_.emit_own((3, 3))
    assert field_.strength("opponent", (3, 3)) == 0.0
    assert field_.opponent == {}


def test_emit_opponent_never_perturbs_own(field_):
    field_.emit_opponent((3, 3))
    assert field_.strength("own", (3, 3)) == 0.0
    assert field_.own == {}


def test_emit_opponent_weight_scales_the_kernel(field_, model):
    field_.emit_opponent((3, 3), weight=0.5)
    assert field_.strength("opponent", (3, 3)) == pytest.approx(model.source * 0.5)


def test_advance_decays_both_grids_by_exactly_one_step(field_, model):
    field_.emit_own((3, 3))
    field_.emit_opponent((1, 1))
    field_.advance()
    expected_own = decay({(3, 3): model.source}, model)
    expected_opp = decay({(1, 1): model.source}, model)
    assert field_.strength("own", (3, 3)) == pytest.approx(expected_own[(3, 3)])
    assert field_.strength("opponent", (1, 1)) == pytest.approx(expected_opp[(1, 1)])


def test_advance_applied_once_is_not_twice(field_, model):
    field_.emit_own((3, 3))
    field_.advance()
    once = field_.strength("own", (3, 3))
    twice_expected = decay(decay({(3, 3): model.source}, model), model)[(3, 3)]
    assert once != pytest.approx(twice_expected)


def test_snapshot_mutation_does_not_affect_the_original(field_):
    field_.emit_own((3, 3))
    snap = field_.snapshot()
    snap.emit_own((0, 0))
    assert (0, 0) not in field_.own
    assert (0, 0) in snap.own


def test_original_mutation_after_snapshot_does_not_affect_the_snapshot(field_):
    field_.emit_own((3, 3))
    snap = field_.snapshot()
    field_.emit_own((0, 0))
    assert (0, 0) not in snap.own
    assert (0, 0) in field_.own


def test_freshest_returns_the_strongest_cell(field_):
    field_.emit_own((3, 3))
    assert field_.freshest("own") == (3, 3)


def test_freshest_is_none_when_the_grid_is_empty(field_):
    assert field_.freshest("own") is None


def test_strength_unknown_grid_raises(field_):
    with pytest.raises(ValueError, match="unknown grid"):
        field_.strength("nonexistent", (0, 0))


def test_35_turns_from_a_single_deposit_matches_the_closed_form(field_, model):
    field_.emit_own((3, 3))
    for _ in range(35):
        field_.advance()
    assert field_.strength("own", (3, 3)) == pytest.approx(
        expected_strength_after(model, 35), abs=1e-6
    )


def test_35_turns_never_produces_a_negative_value(field_):
    field_.emit_own((3, 3))
    for _ in range(35):
        field_.advance()
    assert all(v >= 0.0 for v in field_.own.values())
    assert all(v >= 0.0 for v in field_.opponent.values())
