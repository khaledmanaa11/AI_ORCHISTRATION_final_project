"""Shared helpers for the 07-03 rules 8-9 firewall tests (D-74).

Not a `test_*.py` file on purpose, so pytest collects nothing from it --
the `_fakes_agent.py` / `artifact_config_fixtures.py` precedent.

THE COORDINATES BELOW ARE CHOSEN, NOT ARBITRARY. `OPPONENT_CELL` differs
from `OWN_CELL` and from every cell in `BARRIERS`, because each of those is
a cell an HONEST view is entitled to carry: if the opponent happened to
stand on one of them the leak scan would fire on a legitimate field, and the
test would be measuring a coincidence instead of the firewall. Its row-major
flat index (5*7+3 = 38) and its column-major flat index (3*7+5 = 26) are
likewise distinct from every other integer the honest view carries --
board_size 7, turn 4, barriers_placed 2, the hint turn stamp 2, and the
coordinate components {0, 1, 2, 6} -- so a flat-index hit can only mean a
real leak.

07-11 REPLACED THIS MODULE'S BELIEF AND SCENT SEEDING, because neither
modelled production and a green test on either proved nothing:

* `scent_field` never called `emit_opponent`, so `view.scent.opponent` was
  an ALL-ZERO grid in every one of 07-03's thirty probes -- while in
  production `BeliefAdapter.decide` stamps the kernel on the opponent's true
  cell at the configured source strength on every Regime-A turn.
* `honest_context` seeded belief with `observe_exact(BELIEF_ARGMAX)`, a cell
  production never supplies. The real path passes `ctx.state.thief`. The
  fixed `BELIEF_ARGMAX` constant is therefore GONE: what a view publishes as
  its argmax is now whatever the shipped pipeline produces, and the tests
  that need it read it off the view and assert it is not the true cell --
  which is the property that actually matters.

Both now run through `local_view_production.seed_belief_as_production_does`.

The SCANNER half -- `payloads`, `coordinate_hits`, `leak_variants`, `walk`
and `LeakyLocalView` -- moved to `local_view_scanner.py` at the same time,
at the 150-code-line gate. The seam is real: this module BUILDS views and
imports production code to do it; that one only INSPECTS a serialised one.
"""

from __future__ import annotations

import dataclasses
import pathlib
import random

from pursuit.sdk.view_builder import HintHistory, build_local_view
from pursuit.shared.belief_config import load_belief_config
from pursuit.shared.scent_config import load_scent_model
from pursuit.strategy.beliefadapter import BeliefAdapter
from pursuit.strategy.naive import ChaserCop
from pursuit.strategy.scentfield import ScentField
from tests.unit._fakes_agent import make_ctx
from tests.unit.local_view_production import seed_belief_as_production_does

_CONFIG = pathlib.Path(__file__).parents[2] / "config" / "police"

OWN_CELL = (0, 0)
OPPONENT_CELL = (5, 3)
BARRIERS = frozenset({(1, 1), (2, 2)})
TURN = 4
BARRIERS_PLACED = 2
IDLE_SECONDS = 1.5
INCOMING_HINT = {"text": "the north-west corner is empty", "intent": "lie", "turn": 2}


def belief_adapter(params):
    """A real `BeliefAdapter` -- the type `view_builder` isinstance-checks."""
    return BeliefAdapter(
        ChaserCop(role="cop", game_params=params),
        "cop",
        params,
        load_belief_config(_CONFIG / "belief.json"),
        load_scent_model(_CONFIG / "scent.json"),
        random.Random(0),
    )


def scent_field(params, cell=OWN_CELL):
    """The field as production leaves it BEFORE this turn's `decide()` runs:
    our own trail only. The opponent deposit is not seeded here because it
    is not seeded there either -- `emit_opponent` is called from inside
    `BeliefAdapter.decide`, so a context with no adapter genuinely never
    grows one, and leaving that grid empty for `with_belief=False` is
    faithful rather than vacuous."""
    field = ScentField(
        model=load_scent_model(_CONFIG / "scent.json"), board_size=params.board_size
    )
    field.emit_own(cell)
    return field


def honest_context(tmp_path, default_params, network_params, *, with_belief=True):
    """A REAL `AgentContext` holding the engine's true joint position --
    which is the point: every agent process legitimately has it."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police")
    ctx.state = dataclasses.replace(
        ctx.state,
        cop=OWN_CELL,
        thief=OPPONENT_CELL,
        barriers=BARRIERS,
        barriers_placed=BARRIERS_PLACED,
        turn=TURN,
    )
    ctx.scent_field = scent_field(default_params)
    ctx.incoming_hints = {"thief": dict(INCOMING_HINT)}
    if with_belief:
        ctx.brain = belief_adapter(default_params)
        seed_belief_as_production_does(ctx)
    return ctx


def honest_view(tmp_path, default_params, network_params, **kwargs):
    ctx = honest_context(tmp_path, default_params, network_params, **kwargs)
    return build_local_view(ctx, HintHistory(), idle_seconds=IDLE_SECONDS)
