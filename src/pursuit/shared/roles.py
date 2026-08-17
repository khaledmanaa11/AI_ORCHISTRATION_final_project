"""The two role vocabularies and the single bridge between them (D-01).

`role.json` speaks {"police", "thief"}; the SDK engine and `GameState`'s own
field names speak {"cop", "thief"}. `engine_agent` is the ONE place that
mismatch is resolved and `opponent_role` is the ONE place the inbound-sender
expectation is, and both used to live in `network/orchestrator.py` -- moved
here VERBATIM by 07-03, and re-exported from there unchanged, so every
existing `from pursuit.network.orchestrator import engine_agent` call site
keeps working with zero edits.

The move is not tidying. `sdk/view_builder.py` (the rules 8-9 read model,
D-74) has to know which `GameState` field is OUR OWN cell, and so will the
07-06 GUI -- and neither may import `pursuit.network`: `sdk` importing
`network` inverts the layering that `network/agent_context.py` already
established in the other direction, and `scripts/check_local_truth.py`
forbids a `gui/` module from importing `pursuit.network` outright. Leaving
the mapping in `orchestrator.py` would therefore have meant a SECOND copy
of the "police"/"thief" literals -- exactly the "second, driftable copy"
`opponent_role`'s own docstring warns against. `shared/` is the seam both
layers may import, so the vocabulary stays defined once.
"""

from __future__ import annotations

POLICE = "police"
THIEF = "thief"
COP = "cop"


def engine_agent(role: str) -> str:
    """Bridge role.json's {"police","thief"} to the SDK's {"cop","thief"}
    (D-01) -- the one place this Phase-2 name mismatch is resolved."""
    if role == POLICE:
        return COP
    if role == THIEF:
        return THIEF
    raise ValueError(f"unknown role {role!r}; expected 'police' or 'thief'")


def opponent_role(role: str) -> str:
    """The role this agent expects on every inbound envelope's `sender`
    (06-06). Lives here beside `engine_agent` because this module owns the
    {"police","thief"} vocabulary -- adding the literals anywhere else
    would be a second, driftable copy."""
    if role == POLICE:
        return THIEF
    if role == THIEF:
        return POLICE
    raise ValueError(f"unknown role {role!r}; expected 'police' or 'thief'")
