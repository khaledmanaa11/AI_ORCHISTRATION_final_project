"""`DisplayBelief`: rule 9's one owner (07-11, docs/PRD_display_belief.md).

Three properties carry the weight here, and the recovery half of the story
lives in `tests/unit/test_local_truth_recovery.py` rather than in this file:

  (a) an UNCONTAMINATED seat is passed through identically -- this is what
      keeps the cop-side fix from silently degrading the thief, whose belief
      is genuinely multi-modal and is the one panel legal to draw as-is;
  (b) the floor guard actually FIRES, and fires on both panels;
  (c) the display map is never handed an exact observation, whatever the
      strategy map was handed.
"""

from __future__ import annotations

import dataclasses
import pathlib

from pursuit.sdk import engine
from pursuit.shared.belief_config import load_belief_config
from pursuit.shared.scent_config import load_scent_model
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.display_belief import DisplayBelief, positive_cells
from pursuit.strategy.scentfield import ScentField

_CONFIG = pathlib.Path(__file__).parents[3] / "config" / "police"

TRUE_CELL = (5, 3)
OWN_CELL = (0, 0)


def _floors():
    return load_belief_config(_CONFIG / "belief.json").display


def _display(params):
    return DisplayBelief(
        params.board_size, "thief", load_scent_model(_CONFIG / "scent.json"), _floors()
    )


def _neutral(params):
    """A likelihood that explains everything equally -- `hint_likelihood`'s
    own shape when no hint arrived, so `advance` runs its real code path."""
    size = params.board_size
    return [[1.0] * size for _ in range(size)]


def _state(params):
    return dataclasses.replace(
        engine.make_state(params), cop=OWN_CELL, thief=TRUE_CELL, turn=4
    )


def test_an_uncontaminated_seat_is_published_unchanged(default_params):
    """(a) THE THIEF CONTROL, in one assertion: identity, not a copy that
    happens to compare equal. A symmetric 'fix' would destroy real work."""
    display = _display(default_params)
    strategy = BeliefMap(default_params.board_size, "thief")
    actual = ScentField(
        model=load_scent_model(_CONFIG / "scent.json"), board_size=default_params.board_size
    )
    actual.emit_own(OWN_CELL)
    display.advance(
        _state(default_params), _neutral(default_params), default_params, observed_exact=False
    )
    assert display.contaminated is False
    assert display.published_belief(strategy) is strategy
    assert display.published_scent(actual) is actual


def test_a_contaminated_seat_publishes_the_display_map_instead(default_params):
    """The substitution fires on PROVENANCE, not on a role name."""
    display = _display(default_params)
    strategy = BeliefMap(default_params.board_size, "thief")
    strategy.observe_exact(TRUE_CELL)
    display.advance(
        _state(default_params), _neutral(default_params), default_params, observed_exact=True
    )
    assert display.contaminated is True
    published = display.published_belief(strategy)
    assert published is display.belief
    assert published is not strategy
    assert published.argmax() != TRUE_CELL
    assert published.entropy() >= _floors().min_entropy_bits


def test_contamination_is_sticky_across_later_regime_b_turns(default_params):
    """One exact observation poisons the strategy map for the rest of the
    game -- `belief.py:80` multiplies pointwise, so a zeroed cell never
    reopens. The flag must not clear on the next `observed_exact=False`."""
    display = _display(default_params)
    state, neutral = _state(default_params), _neutral(default_params)
    display.advance(state, neutral, default_params, observed_exact=True)
    display.advance(state, neutral, default_params, observed_exact=False)
    assert display.contaminated is True


def test_the_floor_guard_fires_on_both_panels(default_params):
    """(b) COUNTER-CONTROL for the floors. The honest pipeline cannot reach a
    delta, so the guard is forced here by collapsing the display map by hand
    -- without this, `publishable()` could be `return True` and every other
    test in the repository would still pass."""
    display = _display(default_params)
    strategy = BeliefMap(default_params.board_size, "thief")
    actual = ScentField(
        model=load_scent_model(_CONFIG / "scent.json"), board_size=default_params.board_size
    )
    actual.emit_own(OWN_CELL)
    display.advance(
        _state(default_params), _neutral(default_params), default_params, observed_exact=True
    )
    assert display.publishable() is True
    display.belief.observe_exact(TRUE_CELL)
    assert display.publishable() is False
    assert display.published_belief(strategy) is None
    redacted = display.published_scent(actual)
    assert redacted.opponent == {}
    assert redacted.own == actual.own


def test_the_display_map_diverges_from_a_strategy_map_that_observed_exactly(default_params):
    """(c) The two maps are separate objects fed different evidence -- the
    whole mechanism in one assertion."""
    display = _display(default_params)
    display.advance(
        _state(default_params), _neutral(default_params), default_params, observed_exact=True
    )
    support = positive_cells(display.belief.posterior())
    assert len(support) >= _floors().min_support_cells
    assert display.belief.posterior()[TRUE_CELL[0]][TRUE_CELL[1]] < 1.0


def test_positive_cells_skips_zero_mass(default_params):
    """A barrier or a delta's zero cells must not become board_size**2 no-op
    emissions every turn."""
    grid = ((0.0, 0.5), (0.5, 0.0))
    assert positive_cells(grid) == [((0, 1), 0.5), ((1, 0), 0.5)]
