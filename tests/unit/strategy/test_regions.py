"""strategy/regions.py: the one translation from named sector to cells."""

import pytest

from pursuit.shared.directions import Origin
from pursuit.shared.inference import Region
from pursuit.strategy.regions import (
    region_cells,
    region_center,
    region_distance,
    region_of,
)


def test_every_cell_belongs_to_exactly_one_region(default_params):
    size = default_params.board_size
    covered = [cell for region in Region for cell in region_cells(region, size)]
    assert len(covered) == size * size
    assert len(set(covered)) == size * size


def test_region_cells_agrees_with_region_of(default_params):
    """The two are derived from one another by construction; this is the
    assertion that keeps them that way if someone optimises one of them."""
    size = default_params.board_size
    for region in Region:
        for cell in region_cells(region, size):
            assert region_of(cell, size) is region


def test_no_region_is_empty(default_params):
    for region in Region:
        assert region_cells(region, default_params.board_size)


def test_the_corners_land_in_the_corner_sectors(default_params):
    size = default_params.board_size
    last = size - 1
    assert region_of((0, 0), size) is Region.NORTHWEST
    assert region_of((0, last), size) is Region.NORTHEAST
    assert region_of((last, 0), size) is Region.SOUTHWEST
    assert region_of((last, last), size) is Region.SOUTHEAST


def test_the_middle_cell_is_the_centre(default_params):
    size = default_params.board_size
    assert region_of((size // 2, size // 2), size) is Region.CENTER


def test_north_is_the_low_row_under_a_top_left_origin(default_params):
    """Matching pursuit.constants.Direction.NORTH == (-1, 0)."""
    size = default_params.board_size
    assert region_of((0, size // 2), size) is Region.NORTH
    assert region_of((size - 1, size // 2), size) is Region.SOUTH


def test_a_bottom_left_origin_flips_the_row_axis(default_params):
    """Table 13 row 3 is negotiable; the sectors must follow the agreement,
    not assume the shipped default."""
    size = default_params.board_size
    origin = Origin.BOTTOM_LEFT.value
    assert region_of((0, size // 2), size, origin=origin) is Region.SOUTH
    assert region_of((size - 1, size // 2), size, origin=origin) is Region.NORTH


def test_a_top_right_origin_flips_the_column_axis(default_params):
    size = default_params.board_size
    origin = Origin.TOP_RIGHT.value
    assert region_of((size // 2, 0), size, origin=origin) is Region.EAST
    assert region_of((size // 2, size - 1), size, origin=origin) is Region.WEST


def test_a_regions_centre_lies_inside_it(default_params):
    size = default_params.board_size
    for region in Region:
        assert region_center(region, size) in region_cells(region, size)


def test_region_distance_is_zero_to_itself(default_params):
    for region in Region:
        assert region_distance(region, region, default_params.board_size) == 0


def test_region_distance_is_symmetric(default_params):
    size = default_params.board_size
    for a in Region:
        for b in Region:
            assert region_distance(a, b, size) == region_distance(b, a, size)


def test_opposite_corners_are_the_furthest_apart(default_params):
    size = default_params.board_size
    corner_to_corner = region_distance(Region.NORTHWEST, Region.SOUTHEAST, size)
    for a in Region:
        for b in Region:
            assert region_distance(a, b, size) <= corner_to_corner


@pytest.mark.parametrize("size", [3, 4, 7, 9, 12])
def test_the_split_survives_other_board_sizes(size):
    """board_size is a MINIMUM in Table 13, so a league opponent may agree a
    larger board; the sector split must not assume seven."""
    covered = [cell for region in Region for cell in region_cells(region, size)]
    assert len(covered) == size * size
    assert all(region_cells(region, size) for region in Region)
