"""Tests for the book's emission kernel and decay law (D-50, Sec4.3)."""

import pathlib

import pytest

from pursuit.shared.scent_config import load_scent_model
from pursuit.strategy.scent import decay, emission, expected_strength_after

_SCENT_CONFIG = pathlib.Path(__file__).parents[3] / "config" / "police" / "scent.json"
_BOARD_SIZE = 7


@pytest.fixture(scope="module")
def model():
    return load_scent_model(_SCENT_CONFIG)


def test_centre_cell_equals_source(model):
    field = emission(model, (3, 3), _BOARD_SIZE)
    assert field[(3, 3)] == model.source


def test_kernel_is_reproduced_exactly_at_every_offset(model):
    field = emission(model, (3, 3), _BOARD_SIZE)
    half = model.window // 2
    for i, row in enumerate(model.kernel):
        for j, value in enumerate(row):
            cell = (3 + (i - half), 3 + (j - half))
            assert field[cell] == value


def test_corner_centre_writes_only_the_in_board_quadrant(model):
    field = emission(model, (0, 0), _BOARD_SIZE)
    half = model.window // 2
    assert all(r >= 0 and c >= 0 for r, c in field)
    assert len(field) == (half + 1) * (half + 1)


def test_far_corner_centre_never_exceeds_board_bounds(model):
    last = _BOARD_SIZE - 1
    field = emission(model, (last, last), _BOARD_SIZE)
    assert all(0 <= r < _BOARD_SIZE and 0 <= c < _BOARD_SIZE for r, c in field)


def test_emission_never_writes_a_negative_index(model):
    field = emission(model, (1, 1), _BOARD_SIZE)
    assert all(r >= 0 and c >= 0 for r, c in field)


def test_decay_once_matches_the_configs_worked_example(model):
    field = decay({(3, 3): model.source}, model)
    assert field[(3, 3)] == pytest.approx(model.worked_example_after)


def test_ten_decays_match_the_closed_form(model):
    field = {(0, 0): model.source}
    for _ in range(10):
        field = decay(field, model)
    assert field[(0, 0)] == pytest.approx(expected_strength_after(model, 10))


def test_decay_never_returns_a_negative_value_for_adversarial_input(model):
    field = decay({(0, 0): -5.0}, model)
    assert all(value >= 0.0 for value in field.values())
    assert field.get((0, 0), 0.0) >= 0.0


def test_decay_drops_cells_that_fall_below_epsilon(model):
    result = decay({(0, 0): 1e-9}, model)
    assert (0, 0) not in result


def test_decay_does_not_mutate_its_input(model):
    field = {(0, 0): model.source}
    decay(field, model)
    assert field == {(0, 0): model.source}


def test_expected_strength_after_zero_turns_is_source(model):
    assert expected_strength_after(model, 0) == model.source


def test_expected_strength_after_matches_one_manual_decay(model):
    manual = decay({(0, 0): model.source}, model)[(0, 0)]
    assert expected_strength_after(model, 1) == pytest.approx(manual)
