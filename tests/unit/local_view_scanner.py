"""07-03's leak SCANNER, and the deliberately leaky payloads that prove it
can fail.

Split out of `local_view_fixtures.py` by 07-11 at the 150-code-line gate
(Segal Table 5) once that module's own docstring had to record why its
belief and scent seeding were replaced. The seam is a real one: everything
here is about INSPECTING a serialised view, nothing about BUILDING one, and
this half imports no `pursuit` production code at all.

Not a `test_*.py` file on purpose, so pytest collects nothing from it.

WHAT THIS SCANNER CANNOT DO, stated here so no future reader mistakes a
clean verdict for compliance: it finds a coordinate that appears as a VALUE.
It cannot see a coordinate that is DRAWN -- a belief support shaped like one
cell's legal-move set names that cell without any integer pair appearing
anywhere. Deleting `BeliefView.argmax` would make every function below
report clean with the rules 8-9 leak fully intact. That question is asked by
`test_local_truth_recovery.py` instead, and both files are needed.
"""

from __future__ import annotations

import dataclasses
import json


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
