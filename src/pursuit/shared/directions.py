"""The five-word heading vocabulary, in ONE place.

Three subsystems name the same five headings and must agree on the spelling
or they silently stop understanding each other:

- `network/move_payload.py` (04-04) puts a heading on the wire as the D-53
  direction token that replaced Phase 2's forbidden `{x, y}` coordinates.
- `services/llm/decode_schema.py` (04-07) constrains the decoder's
  `direction` field to it, so a decoded *"I am heading north"* lands in the
  same vocabulary a move token uses.
- `strategy/deception*.py` (04-08) picks a claimed heading from it, before
  any text exists.

It lives in `shared/` rather than in `network/` because `strategy/` may not
import `pursuit.network` at all -- `scripts/check_no_llm_in_strategy.py`
fails CI on that import (STRAT-03), and `shared/` is that script's own
documented "legal seam for cross-cutting types". A second copy of the five
words under `strategy/` would satisfy the gate and violate CLAUDE.md's
"extract at 2+ copies" instead, so the vocabulary moved down rather than
being duplicated sideways. `network/move_payload.py` re-exports the name, so
every existing `from pursuit.network.move_payload import DirectionWord`
keeps working.

It also owns the negotiated axis ORIGIN (PARAMETERS.md Table 13 row 3), for
the same reason: which corner is cell (0, 0) decides what the word "north"
means, and `network/move_payload.py` (the wire), `strategy/regions.py` (the
nine sectors) and `strategy/deception_*.py` (a claimed sector) must all
resolve it the same way or they disagree about the board while every test
passes. `axis_signs()` is the one place that mapping is written down.

What stays OUT of this module is the full word -> (row, col) vector
resolution: that also needs the five base vectors, and those belong beside
the wire codec that validates a step against `sdk/actions.py`.
"""

from enum import Enum


class DirectionWord(str, Enum):
    """A heading named in words. No integer ever names a cell (rule 27)."""

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    STAY = "stay"


#: Every heading as a plain string, in declaration order -- for a JSON-schema
#: `enum` list and for any caller that needs the vocabulary without importing
#: the enum type itself.
DIRECTION_WORDS: tuple[str, ...] = tuple(word.value for word in DirectionWord)


class Origin(str, Enum):
    """Which corner is cell (0, 0) -- PARAMETERS.md Table 13 row 3.

    `game_params.json` ships "top-left", which reproduces
    `pursuit.constants.Direction`'s own convention exactly.
    """

    TOP_LEFT = "top-left"
    BOTTOM_LEFT = "bottom-left"
    TOP_RIGHT = "top-right"
    BOTTOM_RIGHT = "bottom-right"


DEFAULT_ORIGIN = Origin.TOP_LEFT.value


def axis_signs(origin: str) -> tuple[int, int]:
    """`(row_sign, col_sign)` for `origin`.

    Negate the row axis for a bottom-* corner, the column axis for a *-right
    corner. A sign of +1 means "increasing index runs south / east", which is
    what "top-left" gives and what every board helper assumes by default.
    """
    row_sign = -1 if origin.startswith("bottom") else 1
    col_sign = -1 if origin.endswith("right") else 1
    return row_sign, col_sign
