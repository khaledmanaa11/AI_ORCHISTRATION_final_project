"""hintbank_templates.py: pure data, no selection logic (04-10).

Every module gets a test file (CLAUDE.md) -- this one checks the DATA's own
shape invariants directly; `test_hintbank.py` exercises the selection logic
and the import-time validation that walks every entry defined here.
"""

from pursuit.services.llm.hintbank_templates import (
    ARENA_HEADING_PLACE,
    ARENA_REGION_PLACE,
    BANK,
    EVENT_ARENA_CLAUSE,
    EVENT_GENERIC_CLAUSE,
    GENERIC_HEADING_PLACE,
    GENERIC_REGION_PLACE,
)
from pursuit.shared.deception_types import ALWAYS_TRUE_KINDS, ClaimKind, Intent
from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import Region

_LEGAL_PAIRS = {
    (kind, intent)
    for kind in ClaimKind
    for intent in Intent
    if not (kind in ALWAYS_TRUE_KINDS and intent is Intent.LIE)
}


def test_bank_covers_every_legal_claim_kind_intent_pair():
    """(BARRIER, LIE) and (CAPTURE, LIE) cannot be constructed at all --
    DeceptionPlan.__post_init__ refuses them -- so BANK need not, and must
    not silently claim to, cover them."""
    assert set(BANK) == _LEGAL_PAIRS


def test_every_bank_entry_has_at_least_two_phrasings():
    """Enough per key that a 35-turn game does not repeat a phrasing often
    enough to become a signature."""
    for templates in BANK.values():
        assert len(templates) >= 2


def test_every_bank_template_has_exactly_one_slot():
    for templates in BANK.values():
        for template in templates:
            assert template.count("{slot}") == 1


def test_every_region_has_an_arena_and_a_generic_filler():
    assert set(ARENA_REGION_PLACE) == set(Region)
    assert set(GENERIC_REGION_PLACE) == set(Region)


def test_every_heading_has_an_arena_and_a_generic_filler():
    assert set(ARENA_HEADING_PLACE) == set(DirectionWord)
    assert set(GENERIC_HEADING_PLACE) == set(DirectionWord)


def test_arena_fillers_differ_from_generic_fillers_per_region():
    """The two variants must actually read differently, not just exist."""
    for region in Region:
        assert ARENA_REGION_PLACE[region] != GENERIC_REGION_PLACE[region]


def test_arena_fillers_differ_from_generic_fillers_per_heading():
    for word in DirectionWord:
        assert ARENA_HEADING_PLACE[word] != GENERIC_HEADING_PLACE[word]


def test_event_clauses_differ_between_arena_and_generic():
    assert EVENT_ARENA_CLAUSE != EVENT_GENERIC_CLAUSE
    assert EVENT_GENERIC_CLAUSE == ""


def test_no_filler_is_blank():
    for table in (ARENA_REGION_PLACE, GENERIC_REGION_PLACE, ARENA_HEADING_PLACE, GENERIC_HEADING_PLACE):
        for value in table.values():
            assert value.strip()
