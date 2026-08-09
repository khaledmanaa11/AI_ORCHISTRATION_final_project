"""LANG-02 / rule 27 outgoing coordinate guard, shared by transport AND
language (D-47, 04-10).

Moved out of `network/hint_payload.py` (04-04) into `shared/`: 04-10's
`services/llm/bluff.py` also needs this exact check -- `compose()`'s own
must_haves requires validating the composed hint with the SAME function
`build_hint` already uses, not a second regex copy (CLAUDE.md "extract at
2+ copies"). `services/` importing `network/` (or vice versa) is not an
established dependency anywhere in this codebase, and no existing plan
requires it; rather than open a new cross-layer edge for one function,
this follows the exact precedent 04-08 already set for `Intent` and
`DirectionWord`/`Origin`: a cross-cutting piece two layers both need moves
down into `shared/`, the project's documented legal seam
(`scripts/check_no_llm_in_strategy.py`'s own docstring: "pursuit.shared
stays unguarded on purpose -- it is the legal seam for cross-cutting
types"). `network/hint_payload.py` re-exports the name, so every existing
`from pursuit.network.hint_payload import assert_no_coordinates` call site
is unchanged.
"""

from __future__ import annotations

import re

_DIGIT_PAIR = re.compile(r"\d+\s*,\s*\d+")
_ROW_COLUMN = re.compile(r"\brow\s+\d+\s+col(?:umn)?\s+\d+\b", re.IGNORECASE)


def assert_no_coordinates(text: str) -> None:
    """LANG-02 / rule 27 outgoing guard: raise ValueError if `text` carries
    a digit pair (covers both "3,4" and "(3, 4)") or a bare "row N column
    M" grid reference. SEND path only -- we must never EMIT an illegal
    hint; what we RECEIVE is data, not ours to police."""
    if _DIGIT_PAIR.search(text) or _ROW_COLUMN.search(text):
        raise ValueError(f"hint text carries a coordinate-shaped reference: {text!r}")
