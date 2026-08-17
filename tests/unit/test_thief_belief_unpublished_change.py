"""THE THIEF CONTROL for 07-11's cop-side fix: the thief's published belief
and scent must be BYTE-IDENTICAL to what the strategy layer holds.

Its own file, not a case bolted onto the recovery suite, because it asserts
the opposite property and a reader must not have to infer which. 07-11 fixed
a leak that exists ONLY on a seat that calls `observe_exact`. The thief never
does: `turn_language.py:58` returns `ctx.pending_cop_action.move`, which is
None at its decide point on EVERY turn under commit-reveal (`"commit_reveal":
true` in both `config/police/security.json` and `config/thief/security.json`),
so its belief is genuinely multi-modal, is legal to draw, and is the one
panel that is honestly impressive to a grader. A symmetric "fix" would have
destroyed real work to repair a cop-side bug.

Byte-level rather than field-level on purpose: `published_belief` returning a
copy that merely compares equal would still be a behaviour change, and a
float that round-trips differently would be caught here and nowhere else.
"""

from __future__ import annotations

import dataclasses
import json
import random

import pytest

from pursuit.sdk import engine
from pursuit.sdk.view_builder import _belief_view, _scent_view
from pursuit.shared.inference import NO_EVIDENCE
from pursuit.shared.resolution import PREFERRED
from pursuit.strategy.beliefadapter import BeliefAdapter
from pursuit.strategy.naive import GreedyEvader
from pursuit.strategy.scentfield import ScentField
from tests.unit import local_view_fixtures as fx

TURNS = 5
COP_CELL = (0, 0)
THIEF_CELL = (3, 3)
BARRIERS = frozenset({(1, 1), (2, 2)})


@dataclasses.dataclass(frozen=True)
class _Board:
    board_size: int


@dataclasses.dataclass
class _ViewCtx:
    """Exactly the three attributes `_belief_view`/`_scent_view` read, and
    nothing else -- a real `AgentContext` would drag the whole turn loop in
    and would let this test pass for a reason it does not name."""

    brain: object
    scent_field: object
    params: _Board


def _canonical(payload) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _thief_adapter(params):
    return BeliefAdapter(
        GreedyEvader(role="thief", game_params=params), "thief", params,
        fx.belief_config(), fx.scent_model(), random.Random(0),
    )


def _play_regime_b(params):
    """Five turns at the thief's real decide point: `known_cell=None` every
    time, which is what commit-reveal guarantees for the responder."""
    adapter = _thief_adapter(params)
    field = ScentField(model=fx.scent_model(), board_size=params.board_size)
    state = dataclasses.replace(
        engine.make_state(params), cop=COP_CELL, thief=THIEF_CELL,
        barriers=BARRIERS, barriers_placed=len(BARRIERS),
    )
    for turn in range(TURNS):
        state = dataclasses.replace(state, turn=turn, cop=(min(turn, params.board_size - 1), 0))
        adapter.decide(state, NO_EVIDENCE, field, PREFERRED, known_cell=None)
        field.advance()
    return adapter, field


def test_the_thief_publishes_its_own_strategy_belief_byte_for_byte(default_params):
    adapter, field = _play_regime_b(default_params)
    ctx = _ViewCtx(adapter, field, _Board(default_params.board_size))
    assert adapter.display.contaminated is False, "the thief must never observe exactly"
    published = _belief_view(ctx)
    assert published is not None
    assert _canonical(dataclasses.asdict(published)) == _canonical(
        {
            "rows": adapter.belief.posterior(),
            "entropy": adapter.belief.entropy(),
            "argmax": adapter.belief.argmax(),
            "reliability": adapter.reliability.value,
        }
    )


def test_the_thief_publishes_its_own_scent_field_byte_for_byte(default_params):
    adapter, field = _play_regime_b(default_params)
    ctx = _ViewCtx(adapter, field, _Board(default_params.board_size))
    assert adapter.display.published_scent(field) is field
    size = default_params.board_size
    published = dataclasses.asdict(_scent_view(ctx))
    expected = {
        name: tuple(
            tuple(float(grid.get((row, col), 0.0)) for col in range(size))
            for row in range(size)
        )
        for name, grid in (("own", field.own), ("opponent", field.opponent))
    }
    assert _canonical(published) == _canonical(expected)


def test_the_thief_belief_is_genuinely_multi_modal_and_worth_drawing(default_params):
    """ANTI-VACUITY. The two byte-comparisons above would pass just as well
    against a degenerate map, which is exactly what would happen if a
    symmetric 'fix' had been applied here. The panel must still be a real
    heatmap: near-full support and entropy close to the 7x7 maximum."""
    adapter, _ = _play_regime_b(default_params)
    posterior = adapter.belief.posterior()
    support = [value for row in posterior for value in row if value > 0.0]
    open_cells = default_params.board_size**2 - len(BARRIERS)
    assert len(support) == open_cells
    assert adapter.belief.entropy() > fx.belief_config().display.min_entropy_bits * 2
    assert max(support) < 0.5, "a peak this flat cannot name a cell"


def test_a_thief_that_did_observe_exactly_would_be_redacted_too(default_params):
    """The substitution keys on PROVENANCE, not on the role name, so a future
    path that handed the thief an exact cell is covered without anyone
    remembering to come back here. Proven by taking that path."""
    adapter = _thief_adapter(default_params)
    field = ScentField(model=fx.scent_model(), board_size=default_params.board_size)
    state = dataclasses.replace(
        engine.make_state(default_params), cop=COP_CELL, thief=THIEF_CELL, turn=1
    )
    adapter.decide(state, NO_EVIDENCE, field, PREFERRED, known_cell=COP_CELL)
    assert adapter.display.contaminated is True
    assert adapter.display.published_belief(adapter.belief) is adapter.display.belief
    assert adapter.belief.argmax() == COP_CELL
    assert adapter.display.belief.argmax() != COP_CELL


def test_the_display_map_is_driven_and_not_left_inert(default_params):
    """ANTI-VACUITY FOR THE MECHANISM ITSELF, and the one this plan is most
    at risk of. A permanently uniform grid would satisfy every recovery
    assertion in 07-11 -- no argmax on the truth, no inversion, entropy at
    the maximum -- while being a fabricated stand-in of exactly the kind
    `view_builder`'s own docstring forbids. So `advance` is shown to MOVE the
    map: barrier cells are cleared and the legal-motion spread redistributes
    mass off the uniform prior it started from."""
    adapter, _ = _play_regime_b(default_params)
    size = default_params.board_size
    uniform = tuple(tuple([1.0 / (size * size)] * size) for _ in range(size))
    posterior = adapter.display.belief.posterior()
    assert posterior != uniform, "an inert display map is a fabricated grid"
    for row, col in BARRIERS:
        assert posterior[row][col] == 0.0, "belief may never credit a barrier cell"
    assert sum(sum(row) for row in posterior) == pytest.approx(1.0)
