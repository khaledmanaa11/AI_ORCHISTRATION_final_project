"""Read a published snapshot back into a `LocalView` (D-76).

The GUI process is fed by this module and by nothing else. It is the read
half of `view_publish` and it deliberately reconstructs THE SAME frozen
dataclasses rather than handing the GUI a raw dict: a second read model is
exactly what `07-06-PLAN.md`'s non-goals forbid, and a dict would let a panel
index a key the closed field set does not have.

TOTAL OVER A HALF-WRITTEN FILE, for the same reason `view_builder` is total
over hostile peer data: the writer runs on the agent's event loop and the
reader runs in another process on its own timer, so the reader WILL sometimes
arrive mid-rotation. `durable_write_json` writes to a temp file, rotates the
old target to `.prev` and then replaces, so `load_json_with_fallback` covers
both the briefly-absent and the corrupt cases; anything it cannot parse
yields `None` and the dashboard keeps the frame it already has. A viewer that
dies because it read one turn too early is worse than one that is one turn
stale.
"""

from __future__ import annotations

import json
from pathlib import Path

from pursuit.sdk.local_view import BeliefView, Grid, HintView, LocalView, ScentView
from pursuit.shared.durable_write import load_json_with_fallback
from pursuit.shared.state import Coord


def read_snapshot(path: Path | str) -> LocalView | None:
    """The published view at `path`, or None when there is nothing readable
    there yet."""
    try:
        payload = load_json_with_fallback(path)
    except (OSError, json.JSONDecodeError):
        return None
    return decode_view(payload)


def decode_view(payload: object) -> LocalView | None:
    """One published tree as a `LocalView`, or None when it is not one.

    The exception list is the shape of the failure, not a blanket catch: a
    truncated tree raises `KeyError`/`TypeError`, a field that arrived as the
    wrong type raises `ValueError`.
    """
    if not isinstance(payload, dict):
        return None
    try:
        return LocalView(
            role=str(payload["role"]),
            board_size=int(payload["board_size"]),
            turn=int(payload["turn"]),
            own_cell=_coord(payload["own_cell"]),
            declared_barriers=tuple(_coord(pair) for pair in payload["declared_barriers"]),
            barriers_placed=int(payload["barriers_placed"]),
            belief=_belief(payload["belief"]),
            scent=_scent(payload["scent"]),
            hints=tuple(_hint(node) for node in payload["hints"]),
            machine_state=str(payload["machine_state"]),
            idle_seconds=_optional_float(payload["idle_seconds"]),
            watchdog_threshold_seconds=float(payload["watchdog_threshold_seconds"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _coord(pair: object) -> Coord:
    row, col = pair  # type: ignore[misc]
    return (int(row), int(col))


def _grid(rows: object) -> Grid:
    return tuple(tuple(float(value) for value in row) for row in rows)  # type: ignore[union-attr]


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)  # type: ignore[arg-type]


def _belief(node: object) -> BeliefView | None:
    if node is None:
        return None
    return BeliefView(
        rows=_grid(node["rows"]),
        entropy=float(node["entropy"]),
        argmax=_coord(node["argmax"]),
        reliability=float(node["reliability"]),
    )


def _scent(node: object) -> ScentView | None:
    if node is None:
        return None
    return ScentView(own=_grid(node["own"]), opponent=_grid(node["opponent"]))


def _hint(node: object) -> HintView:
    return HintView(
        sender=str(node["sender"]),
        turn=None if node["turn"] is None else int(node["turn"]),
        text=str(node["text"]),
        claimed_intent=None if node["claimed_intent"] is None else str(node["claimed_intent"]),
    )
