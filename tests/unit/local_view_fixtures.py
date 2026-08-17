"""Shared helpers for the 07-03 rules 8-9 firewall tests (D-74).

Not a `test_*.py` file on purpose, so pytest collects nothing from it --
the `_fakes_agent.py` / `artifact_config_fixtures.py` precedent.

THE COORDINATES BELOW ARE CHOSEN, NOT ARBITRARY. `OPPONENT_CELL` differs
from `OWN_CELL`, from every cell in `BARRIERS`, and from `BELIEF_ARGMAX`,
because each of those three is a cell an HONEST view is entitled to carry:
if the opponent happened to stand on one of them the leak scan would fire
on a legitimate field, and the test would be measuring a coincidence
instead of the firewall. Its row-major flat index (5*7+3 = 38) and its
column-major flat index (3*7+5 = 26) are likewise distinct from every
other integer the honest view carries -- board_size 7, turn 4,
barriers_placed 2, the hint turn stamp 2, and the coordinate components
{0, 1, 2, 6} -- so a flat-index hit can only mean a real leak.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import random

from pursuit.sdk.view_builder import HintHistory, build_local_view
from pursuit.shared.belief_config import load_belief_config
from pursuit.shared.scent_config import load_scent_model
from pursuit.strategy.beliefadapter import BeliefAdapter
from pursuit.strategy.naive import ChaserCop
from pursuit.strategy.scentfield import ScentField
from tests.unit._fakes_agent import make_ctx

_CONFIG = pathlib.Path(__file__).parents[2] / "config" / "police"

OWN_CELL = (0, 0)
OPPONENT_CELL = (5, 3)
BARRIERS = frozenset({(1, 1), (2, 2)})
BELIEF_ARGMAX = (6, 6)
TURN = 4
BARRIERS_PLACED = 2
IDLE_SECONDS = 1.5
INCOMING_HINT = {"text": "the north-west corner is empty", "intent": "lie", "turn": 2}


@dataclasses.dataclass(frozen=True)
class LeakyLocalView:
    """The debugging shortcut rule 9 disqualifies for, built on purpose: an
    honest `LocalView` with the engine's TRUE opponent cell bolted on.

    Lives in the test tree and is never importable from `pursuit`. It
    exists so the leak scan can be PROVEN able to fail -- without it, the
    absence assertion is satisfied by a scanner that always returns clean.
    """

    honest: object
    true_opponent_cell: tuple


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


def scent_field(params):
    field = ScentField(
        model=load_scent_model(_CONFIG / "scent.json"), board_size=params.board_size
    )
    field.emit_own(OWN_CELL)
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
    if with_belief:
        ctx.brain = belief_adapter(default_params)
        ctx.brain.belief.observe_exact(BELIEF_ARGMAX)
    ctx.scent_field = scent_field(default_params)
    ctx.incoming_hints = {"thief": dict(INCOMING_HINT)}
    return ctx


def honest_view(tmp_path, default_params, network_params, **kwargs):
    ctx = honest_context(tmp_path, default_params, network_params, **kwargs)
    return build_local_view(ctx, HintHistory(), idle_seconds=IDLE_SECONDS)


def payloads(view):
    """Both serialised forms a consumer could plausibly scan: the nested
    `asdict` tree, and the JSON round trip (which turns every tuple into a
    two-element LIST -- a different encoding of the same coordinate)."""
    tree = dataclasses.asdict(view)
    return {"asdict": tree, "json": json.loads(json.dumps(tree))}


def leak_variants(tree, cell, board_size):
    """One deliberately leaky payload per encoding the scanner claims to
    catch, so every branch of `coordinate_hits` is proven to fire."""
    row, col = cell
    return {
        "tuple_pair": {**tree, "true_opponent_cell": (row, col)},
        "reversed_list": {**tree, "true_opponent_cell": [col, row]},
        "row_major_index": {**tree, "true_opponent_index": row * board_size + col},
        "col_major_index": {**tree, "true_opponent_index": col * board_size + row},
        "text_form": {**tree, "debug_note": f"opponent at ({row}, {col})"},
    }


def walk(node, path="$"):
    """Yield (path, node) for every node in a serialised view."""
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk(value, f"{path}.{key}")
    elif isinstance(node, list | tuple):
        for index, value in enumerate(node):
            yield from walk(value, f"{path}[{index}]")


def _int_pair(node):
    """`node` as a two-element list of plain ints, else None. Coordinates
    are `tuple[int, int]` everywhere in this codebase; requiring ints keeps
    a two-cell row of probabilities from reading as a coordinate."""
    values = list(node)
    if len(values) != 2:
        return None
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        return None
    return values


def coordinate_hits(payload, cell, board_size):
    """Every place `cell` appears as a VALUE, in each encoding a view could
    carry it: the pair, the reversed pair, either flat board index, or a
    textual form inside any string leaf."""
    row, col = cell
    pairs = ([row, col], [col, row])
    flats = (row * board_size + col, col * board_size + row)
    texts = (f"({row}, {col})", f"{row},{col}", f"({col}, {row})", f"{col},{row}")
    hits = []
    for path, node in walk(payload):
        if isinstance(node, list | tuple):
            if _int_pair(node) in pairs:
                hits.append(f"{path}: pair {list(node)}")
        elif isinstance(node, bool):
            continue
        elif isinstance(node, int) and node in flats:
            hits.append(f"{path}: flat index {node}")
        elif isinstance(node, str) and any(t in node for t in texts):
            hits.append(f"{path}: text {node!r}")
    return hits
