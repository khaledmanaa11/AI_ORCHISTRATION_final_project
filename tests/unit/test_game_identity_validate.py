"""05-12 / G7: the peer-game_id safety gate, and the line it must NOT cross.

Two halves, and the second is the one that matters. The first proves the
gate rejects what was MEASURED to relocate our log, raise, or poison the
candidate set. The second proves it rejects NOTHING ELSE -- a foreign league
implementation is an honest peer, and 05-10 already recorded what happens
when a hardening pass forgets that: an `isinstance(turn, int)` rule would
have converted a peer sending `3.0` (which audits correctly, measured) into
a technical loss. Falsely accusing an honest opponent is a disqualification
(rules 16/22), so the fairness half of this file carries more weight than
the hostile half.
"""

from __future__ import annotations

import pytest

from pursuit.network.game_identity_validate import _MAX_PEER_GAME_ID, usable_peer_game_id

# Every id an honest league entrant could plausibly publish. NONE of these is
# our own convention (16 lower-case hex), which is exactly the point.
HONEST_FOREIGN = [
    "3f2504e0-4f89-11d3-9a0c-0305e82c3301",  # RFC-4122 UUID, hyphens
    "AABBCCDDEEFF0011",                       # UPPER-case hex
    "a" * 64,                                 # a SHA-256 as the id
    "khm-mn17_game_2026-08-16",               # team-code label with _ and -
    "g1",                                     # far shorter than ours
    "משחק-1",             # non-ASCII (Hebrew), legal in a filename
    "game.001",                               # an interior dot, not a traversal
    "x" * _MAX_PEER_GAME_ID,                  # exactly AT the bound
]

UNSAFE = [
    ("unhashable dict", {}),
    ("unhashable list", []),
    ("non-str int", 7),
    ("non-str float", 3.5),
    ("non-str bool", True),
    ("absent", None),
    ("empty", ""),
    ("parent ref", "../../evil"),
    ("bare parent", ".."),
    ("posix separator", "logs/evil"),
    ("windows separator", "logs\\evil"),
    ("embedded nul", "a\x00b"),
    ("newline", "a\nb"),
    ("drive colon", "C:evil"),
    ("wildcard", "ev*l"),
    ("trailing dot", "evil."),
    ("trailing space", "evil "),
    ("leading space", " evil"),
    ("one over the bound", "x" * (_MAX_PEER_GAME_ID + 1)),
    ("wildly over the bound", "x" * 5000),
]


@pytest.mark.parametrize(("label", "value"), UNSAFE, ids=[label for label, _ in UNSAFE])
def test_an_unsafe_peer_game_id_reads_as_no_id_published(label, value):
    """Each of these was measured at `0437559` to raise, relocate our log,
    or build a candidate set excluding the peer's own real id. None of them
    can be a filename stem, so all of them mean the same thing: this peer
    published no id we can use."""
    assert usable_peer_game_id(value) is None, label


@pytest.mark.parametrize("value", HONEST_FOREIGN)
def test_an_honest_foreign_convention_passes_unchanged(value):
    """THE CONTROL THIS PLAN TURNS ON. `audit_state.py` checks the committed
    game_id by MEMBERSHIP rather than equality precisely so a peer may keep
    its own convention; a gate that rejected these would put the peer's real
    id outside the candidate set and re-open the false accusation from the
    other direction. Returned VERBATIM -- never normalised, lower-cased or
    re-encoded, because the string must still equal what the peer commits."""
    assert usable_peer_game_id(value) == value


def test_the_bound_is_a_boundary_not_a_convention():
    """The length rule admits everything up to the derived structural limit
    and rejects only past it -- an off-by-one here would silently start
    rejecting honest peers as their ids grew."""
    assert usable_peer_game_id("x" * _MAX_PEER_GAME_ID) is not None
    assert usable_peer_game_id("x" * (_MAX_PEER_GAME_ID + 1)) is None


def test_the_bound_leaves_real_room_for_every_derived_filename():
    """`write_declaration` builds `declaration_{id}_peer.json` (22 fixed
    characters) and `ledger_path` builds `{id}.ledger.jsonl` (14). The
    255-byte single-component limit every target filesystem enforces is the
    real ceiling; the constant must sit below it with the affixes counted."""
    assert _MAX_PEER_GAME_ID + len("declaration__peer.json") < 255
    assert _MAX_PEER_GAME_ID + len(".ledger.jsonl") < 255
