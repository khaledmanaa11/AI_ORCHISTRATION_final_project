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

This module deliberately holds the WORDS only, never the (row, col) vectors
they resolve to: that resolution depends on the negotiated axis origin
(PARAMETERS.md Table 13 row 3) and stays in `move_payload.py` with the
`_axis_signs` logic that owns it.
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
