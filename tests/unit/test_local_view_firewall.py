"""The rules 8-9 firewall (D-74): a serialised `LocalView` cannot carry the
opponent's true cell, and the scan that proves it can itself fail.

Rule 9 (`docs/RULES.md:30`) makes displaying the full objective board state
in the live interface a PROJECT DISQUALIFICATION, and `RULES.md:115` ranks
it third among the cheapest ways to score zero. The data that would trigger
it is on every agent process by design -- `ctx.state` is the engine's true
joint position -- so the firewall has to be a field-set property, proven by
a scan, not an import rule.

Three tests carry the weight and none of them works alone:
  (a) the opponent's true cell appears NOWHERE in the serialised view;
  (b) THE COUNTER-CONTROL -- the identical scanner run over a deliberately
      leaky view REPORTS the leak. Without (b), (a) is satisfied by a
      scanner that always returns clean;
  (c) the same scanner, over the same honest payload, DOES find the cells
      the view is entitled to carry -- so (a) cannot be passing because the
      walker never reached the data.
"""

from __future__ import annotations

import dataclasses

import pytest
from pursuit.sdk.local_view import BeliefView, HintView, LocalView, ScentView

from tests.unit import local_view_fixtures as fx

_SERIALISED_FORMS = ("asdict", "json")

#: The closed field set (D-74). A new field here is a deliberate act that
#: must be argued against rule 9, never something that arrives by accident.
_EXPECTED_FIELDS = (
    "role",
    "board_size",
    "turn",
    "own_cell",
    "declared_barriers",
    "barriers_placed",
    "belief",
    "scent",
    "hints",
    "machine_state",
    "idle_seconds",
    "watchdog_threshold_seconds",
)

_FORBIDDEN_ANNOTATIONS = ("GameState", "AgentContext", "dict", "Any", "object")


@pytest.fixture
def view(tmp_path, default_params, network_params):
    return fx.honest_view(tmp_path, default_params, network_params)


@pytest.mark.parametrize("form", _SERIALISED_FORMS)
def test_opponent_true_cell_is_absent_from_the_serialised_view(view, form):
    """(a) The load-bearing assertion. The context this view was built from
    holds `thief=(5, 3)`; the view must not express it in any encoding."""
    assert len(_SERIALISED_FORMS) == 2, "a thinned form list would skip silently"
    payload = fx.payloads(view)[form]
    hits = fx.coordinate_hits(payload, fx.OPPONENT_CELL, view.board_size)
    assert hits == [], f"rule 9 leak in the {form} view: {hits}"


def test_the_same_scanner_finds_the_cells_the_view_may_carry(view):
    """(c) Anti-vacuity. Own cell, every declared barrier and the belief
    argmax are all legitimately displayable, and the scanner finds each of
    them in the very payload test (a) reports clean."""
    payload = fx.payloads(view)["asdict"]
    legal = (fx.OWN_CELL, fx.BELIEF_ARGMAX, *sorted(fx.BARRIERS))
    assert len(legal) == 4
    for cell in legal:
        assert fx.coordinate_hits(payload, cell, view.board_size), (
            f"the scanner never reached {cell}, so its clean verdict proves nothing"
        )


def test_a_leaky_view_is_reported_by_the_identical_scanner(view):
    """(b) THE COUNTER-CONTROL. The honest view with the true opponent cell
    bolted on -- the tempting debugging shortcut -- must be caught."""
    leaky = fx.LeakyLocalView(honest=view, true_opponent_cell=fx.OPPONENT_CELL)
    hits = fx.coordinate_hits(
        dataclasses.asdict(leaky), fx.OPPONENT_CELL, view.board_size
    )
    assert hits, "the scanner cannot see a leak, so its clean verdicts are worthless"
    assert any("true_opponent_cell" in hit for hit in hits)


def test_every_leak_encoding_the_scanner_claims_is_actually_reported(view):
    """Per-branch counter-control: each encoding `coordinate_hits` claims to
    catch is planted and must be caught. Looped, not parametrised, so a
    thinned variant set FAILS the count instead of silently skipping."""
    tree = fx.payloads(view)["asdict"]
    variants = fx.leak_variants(tree, fx.OPPONENT_CELL, view.board_size)
    assert len(variants) == 5, "a thinned encoding set would prove less than it claims"
    for name, leaky in variants.items():
        hits = fx.coordinate_hits(leaky, fx.OPPONENT_CELL, view.board_size)
        assert hits, f"encoding {name!r} slipped past the scanner"


def test_local_view_field_set_is_closed(view):
    """The field set IS the mitigation: no `GameState`, no `AgentContext`,
    no free-form dict and no 'extras' escape hatch."""
    names = tuple(f.name for f in dataclasses.fields(LocalView))
    assert names == _EXPECTED_FIELDS
    annotations = " ".join(str(f.type) for f in dataclasses.fields(LocalView))
    for forbidden in _FORBIDDEN_ANNOTATIONS:
        assert forbidden not in annotations, f"LocalView.{forbidden} would re-open the leak"


def test_every_view_dataclass_is_frozen():
    """A mutable view could have the opponent cell attached after the fact,
    which is how a debugging shortcut gets in without touching this file."""
    classes = (LocalView, BeliefView, ScentView, HintView)
    assert len(classes) == 4
    for cls in classes:
        assert cls.__dataclass_params__.frozen, f"{cls.__name__} must be frozen"
    hint = HintView(sender="thief", turn=1, text="x", claimed_intent=None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        hint.text = "y"
