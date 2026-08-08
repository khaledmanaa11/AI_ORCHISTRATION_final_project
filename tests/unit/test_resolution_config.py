"""The negotiated resolution block: proposal, defaults, and fail-loud parsing.

The safety property this file exists to protect: a MISSING block must degrade to
BOOK_ONLY silently (no agreement is a normal state), while a MALFORMED block must
raise. Getting that backwards would let us run capture-favouring rules against a
peer running the book, and a divergence at the rule-36 mutual audit is a 0/0
technical loss -- worse than any algorithmic mistake.
"""

import json
import pathlib

import pytest

from pursuit.shared.resolution import (
    BOOK_ONLY,
    PREFERRED,
    ResolutionRules,
    as_declaration,
    load_resolution_rules,
)

_CONFIG = pathlib.Path(__file__).parent.parent.parent / "config"


@pytest.mark.parametrize("seat", ["police", "thief"])
def test_shipped_proposal_is_our_preferred_reading(seat):
    """Both seats propose the same block -- an asymmetric proposal is unagreeable."""
    assert load_resolution_rules(_CONFIG / seat / "resolution.json") == PREFERRED


def test_absent_path_degrades_to_book_only():
    """No agreement is a normal state, not an error."""
    assert load_resolution_rules(None) is BOOK_ONLY


def test_missing_file_degrades_to_book_only(tmp_path):
    """A peer that sends no block leaves us computing exactly what it computes."""
    assert load_resolution_rules(tmp_path / "absent.json") is BOOK_ONLY


def test_partial_block_defaults_the_absent_key_to_false(tmp_path):
    """An unmentioned predicate was not agreed, so it stays off."""
    path = tmp_path / "resolution.json"
    path.write_text(json.dumps({"capture_on_swap": True}))
    assert load_resolution_rules(path) == ResolutionRules(
        capture_on_barrier_race=False, capture_on_swap=True
    )


def test_non_boolean_value_raises(tmp_path):
    """Fail loud: a truthy string must never be coerced into an agreed rule."""
    path = tmp_path / "resolution.json"
    path.write_text(json.dumps({"capture_on_swap": "yes"}))
    with pytest.raises(TypeError, match="must be a boolean"):
        load_resolution_rules(path)


def test_declaration_round_trips_through_the_loader(tmp_path):
    """What we declare to the peer must reconstruct the rules we actually ran."""
    path = tmp_path / "resolution.json"
    path.write_text(json.dumps(as_declaration(PREFERRED), sort_keys=True))
    assert load_resolution_rules(path) == PREFERRED


def test_declaration_keys_are_plain_strings():
    """json.dumps must emit field names, not 'ResolutionKey.CAPTURE_ON_SWAP'."""
    declaration = as_declaration(BOOK_ONLY)
    assert set(declaration) == {"capture_on_barrier_race", "capture_on_swap"}
    assert json.loads(json.dumps(declaration, sort_keys=True)) == declaration
