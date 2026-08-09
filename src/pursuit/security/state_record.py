"""D-60: the committer's own local-view state record.

`build_state_record()` returns EXACTLY the five fixed fields -- `game_id`,
`turn`, `role`, `position:{row,col}`, `barriers_remaining` -- nothing added,
nothing omitted. Per book Sec5.3.1 the content is per-committer (anti-replay
binding to a specific step); peers share the canonical-JSON RECIPE, not each
other's state contents. This module takes plain values only, never an
`AgentContext` -- it has zero `pursuit.network` import, matching the
package's own boundary.
"""

from __future__ import annotations

from enum import Enum


class StateRecordKey(str, Enum):
    """Field names in the D-60 state record."""

    GAME_ID = "game_id"
    TURN = "turn"
    ROLE = "role"
    POSITION = "position"
    BARRIERS_REMAINING = "barriers_remaining"

    def __str__(self) -> str:
        return self.value


def _require_non_bool_int(value: object, label: str) -> None:
    """Reject anything that is not a plain int, bool included (bool < int).

    A local 4-line duplicate of `envelope.py`'s own guard -- not imported
    across packages, matching this exact guard's existing 3-site precedent
    (Pitfall 3).
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"build_state_record: {label} must be an int, got {type(value).__name__}")


def build_state_record(
    *,
    game_id: str,
    turn: int,
    role: str,
    position: tuple[int, int],
    barriers_remaining: int,
) -> dict:
    """Return the D-60 fixed field set.

    Raises
    ------
    TypeError
        If `turn` or `barriers_remaining` is not a plain int (a bool is
        rejected).
    """
    _require_non_bool_int(turn, "turn")
    _require_non_bool_int(barriers_remaining, "barriers_remaining")

    return {
        StateRecordKey.GAME_ID.value: game_id,
        StateRecordKey.TURN.value: turn,
        StateRecordKey.ROLE.value: role,
        StateRecordKey.POSITION.value: {"row": position[0], "col": position[1]},
        StateRecordKey.BARRIERS_REMAINING.value: barriers_remaining,
    }
