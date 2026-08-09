"""decode_schema.py: the contract, re-checked on OUR side of the wire (D-41).

Every rejection case returns None rather than a partial object -- the belief
map cannot discount a half-understood inference after the fact.
"""

import json

import pytest

from pursuit.services.llm.decode_schema import DECODE_SCHEMA, validate
from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import Region

BOARD = 7


def good(**overrides) -> dict:
    """A well-formed response object, with named fields overridden."""
    base = {"region": "north", "cells": [], "direction": None, "confidence": 0.8}
    base.update(overrides)
    return base


def test_a_well_formed_object_validates():
    inference = validate(good(), board_size=BOARD, raw_text="hi")
    assert inference is not None
    assert inference.region is Region.NORTH
    assert inference.confidence == 0.8
    assert inference.raw_text == "hi"
    assert inference.direction is None


def test_a_direction_validates_into_the_shared_vocabulary():
    inference = validate(good(direction="east"), board_size=BOARD)
    assert inference is not None
    assert inference.direction is DirectionWord.EAST


def test_cells_validate_into_coordinate_tuples():
    inference = validate(good(cells=[[0, 0], [6, 6]]), board_size=BOARD)
    assert inference is not None
    assert inference.cells == ((0, 0), (6, 6))


@pytest.mark.parametrize("bad", [1.01, -0.1, 42, "0.5", True, None, float("nan")])
def test_out_of_range_or_non_numeric_confidence_is_rejected(bad):
    assert validate(good(confidence=bad), board_size=BOARD) is None


def test_an_unknown_key_is_rejected():
    assert validate(good(surprise="x"), board_size=BOARD) is None


@pytest.mark.parametrize("missing", ["region", "cells", "direction", "confidence"])
def test_a_missing_required_key_is_rejected(missing):
    obj = good()
    del obj[missing]
    assert validate(obj, board_size=BOARD) is None


def test_a_region_outside_the_vocabulary_is_rejected():
    assert validate(good(region="brooklyn"), board_size=BOARD) is None


def test_a_direction_outside_the_vocabulary_is_rejected():
    assert validate(good(direction="northeast"), board_size=BOARD) is None


@pytest.mark.parametrize("cell", [[7, 0], [0, 7], [-1, 0], [0, -1]])
def test_an_off_board_cell_is_rejected(cell):
    """Not filtered -- rejected. An off-board cell means the model was working
    from a board it invented, so the rest of its answer is untrustworthy too."""
    assert validate(good(cells=[cell]), board_size=BOARD) is None


@pytest.mark.parametrize("cells", ["north", [[1]], [[1, 2, 3]], [[1, "2"]], [[True, 0]], [None]])
def test_a_malformed_cells_list_is_rejected(cells):
    assert validate(good(cells=cells), board_size=BOARD) is None


def test_confidence_about_nowhere_is_rejected():
    """The prompt-injection failure mode: confident about nothing at all."""
    assert validate(good(region=None, cells=[], confidence=1.0), board_size=BOARD) is None


def test_a_bare_heading_at_zero_confidence_is_accepted():
    """The heading survives for 04-09's motion model; it is simply not
    positional evidence on its own."""
    inference = validate(
        good(region=None, cells=[], direction="north", confidence=0.0), board_size=BOARD
    )
    assert inference is not None
    assert inference.direction is DirectionWord.NORTH
    assert inference.is_evidence is False


@pytest.mark.parametrize("obj", [None, "north", 5, [], ("region",)])
def test_a_non_dict_response_is_rejected(obj):
    assert validate(obj, board_size=BOARD) is None


def test_schema_round_trips_through_json_dumps():
    assert json.loads(json.dumps(DECODE_SCHEMA)) == DECODE_SCHEMA


def test_schema_carries_no_unsupported_numeric_bound():
    """Structured-output schemas reject `minimum`/`maximum`; the range check
    lives in validate(). A well-meaning "fix" here fails every request."""
    text = json.dumps(DECODE_SCHEMA)
    assert "minimum" not in text
    assert "maximum" not in text


def test_schema_carries_no_union_type_array():
    """`"type": ["string", "null"]` is ALSO rejected by structured outputs
    (400 on every request -- found by the live GATE-4 run, 2026-08-09).
    Nullable fields must use `anyOf` with a `{"type": "null"}` arm."""

    def walk(node):
        if isinstance(node, dict):
            assert not isinstance(node.get("type"), list), node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(DECODE_SCHEMA)
    nullable = [DECODE_SCHEMA["properties"][k] for k in ("region", "direction")]
    for prop in nullable:
        assert {"type": "null"} in prop["anyOf"]


def test_schema_requires_every_property_and_forbids_extras():
    assert set(DECODE_SCHEMA["required"]) == set(DECODE_SCHEMA["properties"])
    assert DECODE_SCHEMA["additionalProperties"] is False
