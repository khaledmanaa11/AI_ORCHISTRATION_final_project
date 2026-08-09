"""The decode contract, on both sides of the wire (D-41).

`DECODE_SCHEMA` is sent as `output_config.format`'s `json_schema` so the
model is CONSTRAINED to the shape. `validate()` re-checks the response after
it comes back, because **a schema on the request is a request, not a
guarantee**: constrained decoding can be unavailable, silently disabled, or
served by a fallback path, and the only thing that guarantees our types is
our own check on our own side.

Rejection is total and returns None -- never a partial parse, never a regex
scrape of "most of" a broken object. A half-understood inference reaches the
belief map indistinguishable from a correct one, and the map has no way to
discount it afterwards; no evidence is strictly better than wrong evidence.
"""

from __future__ import annotations

from pursuit.shared.directions import DIRECTION_WORDS, DirectionWord
from pursuit.shared.inference import REGION_NAMES, Coord, Inference, Region

SCHEMA_NAME = "hint_inference"

# Structured-output schemas do NOT support numeric bounds: `minimum`/`maximum`
# on `confidence` are rejected by the API, so the [0, 1] range check lives in
# validate() below and MUST stay there. Do not "fix" this by adding a
# `minimum` keyword -- the request fails outright and every hint degrades to
# no-evidence (D-33) with nothing in the logs pointing at the schema.
DECODE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "region": {"type": ["string", "null"], "enum": [*REGION_NAMES, None]},
        "cells": {
            "type": "array",
            "items": {"type": "array", "items": {"type": "integer"}},
        },
        "direction": {"type": ["string", "null"], "enum": [*DIRECTION_WORDS, None]},
        "confidence": {"type": "number"},
    },
    "required": ["region", "cells", "direction", "confidence"],
    "additionalProperties": False,
}

_ALLOWED_KEYS = frozenset(DECODE_SCHEMA["properties"])


def validate(obj: object, *, board_size: int, raw_text: str = "") -> Inference | None:
    """Re-check a decoder response and turn it into an `Inference`, or None.

    Returns None -- never raises, never partially parses -- when the object
    is not a dict, carries an unknown key, omits a required one, puts
    `confidence` outside [0, 1], names a region or direction outside the
    vocabulary, gives a malformed or off-board cell, or claims non-zero
    confidence while implicating nowhere at all (a confident inference about
    nothing is a contradiction, and would otherwise reach the belief map as
    a neutral-but-weighted update).
    """
    if not isinstance(obj, dict):
        return None
    # Exact set equality, not a subset test in either direction: every schema
    # property is `required` AND `additionalProperties` is False, so anything
    # other than precisely these four keys is a response we did not ask for.
    if set(obj) != _ALLOWED_KEYS:
        return None

    confidence = _confidence(obj["confidence"])
    if confidence is None:
        return None
    region = _member(obj["region"], Region)
    direction = _member(obj["direction"], DirectionWord)
    if (region is None) != (obj["region"] is None):
        return None
    if (direction is None) != (obj["direction"] is None):
        return None

    cells = _cells(obj["cells"], board_size)
    if cells is None:
        return None
    if confidence > 0.0 and region is None and not cells:
        return None

    return Inference(
        region=region,
        cells=cells,
        direction=direction,
        confidence=confidence,
        raw_text=raw_text,
    )


def _confidence(value: object) -> float | None:
    """The confidence as a bounded float, or None if it is not a real number
    in [0, 1]. `bool` is excluded explicitly -- it is an `int` subclass in
    Python and `True` would otherwise sail through as 1.0."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    if not 0.0 <= float(value) <= 1.0:
        return None
    return float(value)


def _member(value: object, enum_type: type) -> object | None:
    """`value` as a member of `enum_type`, or None when it is null or outside
    the vocabulary. The caller distinguishes the two cases by comparing the
    raw value against None -- an unknown STRING is a rejection, an explicit
    null is a legitimate "the sentence did not say"."""
    if value is None or not isinstance(value, str):
        return None
    try:
        return enum_type(value)
    except ValueError:
        return None


def _cells(value: object, board_size: int) -> tuple[Coord, ...] | None:
    """The implicated cells as in-bounds coordinate pairs, or None if the
    list is malformed or any cell is off the board.

    An off-board cell is a rejection rather than a filter: it means the
    model was working from a board it invented, so the REST of its answer is
    not trustworthy either.
    """
    if not isinstance(value, list):
        return None
    cells: list[Coord] = []
    for item in value:
        if not isinstance(item, list | tuple) or len(item) != 2:
            return None
        row, col = item
        for axis in (row, col):
            if isinstance(axis, bool) or not isinstance(axis, int):
                return None
        if not (0 <= row < board_size and 0 <= col < board_size):
            return None
        cells.append((row, col))
    return tuple(cells)
