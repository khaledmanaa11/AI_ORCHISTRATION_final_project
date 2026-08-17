"""The rules 8-9 read model (D-74): everything a live view may render, and
structurally nothing else.

Rule 9 (`docs/RULES.md:30`) makes displaying the full objective board state
in the live interface a **project disqualification**, and `RULES.md:115`
ranks it third among the cheapest ways to score zero -- "the tempting
debugging shortcut". The data that triggers it is on every agent process by
design: `GameState` (`shared/state.py`) is exactly
`{cop, thief, barriers, barriers_placed, turn}`, and a cop's turn loop reads
`ctx.state.thief` legitimately from turn 1 (`turn_language.py:57`). The leak
is therefore a FIELD READ, not an import, and no import rule can prevent it.

THE MITIGATION IS THE FIELD SET. `LocalView` is a CLOSED set of frozen
dataclasses that cannot express an opponent's true cell:

  * own position, the declared barriers and the barrier count -- barriers are
    declared on the wire (rule 22) and are shared knowledge on both sides;
  * the belief grid over the opponent -- our own posterior, DENSE and
    row-major, so no coordinate is ever a value in it;
  * the sensed scent, both grids, densified for the same reason;
  * the hint log, with each sender's SELF-DECLARED intent flag -- a claim we
    received, never a verified fact;
  * turn, state-machine state and the freeze timer.

There is no `GameState` field, no `AgentContext` field, no free-form `dict`
and no `extras` escape hatch: each of those would re-open the leak by
construction, and `tests/unit/test_local_view_firewall.py` pins the field
names so a new one cannot arrive by accident.

This module lives in `sdk/`, NOT in `gui/`, because `pyproject.toml:38`
omits `*/gui/*` from coverage -- redaction logic under `gui/` would be
invisible to the `fail_under = 85` gate and would look like it had passed.
`scripts/check_local_truth.py` enforces the boundary from the other side.
"""

from __future__ import annotations

from dataclasses import dataclass

from pursuit.shared.state import Coord

#: A dense, row-major board of floats. Positional by design: a coordinate-
#: KEYED grid would put every cell on the board into the view AS A VALUE,
#: the opponent's true cell among them.
Grid = tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class BeliefView:
    """Our own posterior over where the opponent MIGHT be -- a belief, never
    an observation. `argmax` is the cell this peer considers most likely and
    is routinely wrong; that is exactly why it is legal to draw."""

    rows: Grid
    entropy: float
    argmax: Coord
    reliability: float


@dataclass(frozen=True)
class ScentView:
    """Both scent grids this peer maintains (D-49). `opponent` is our own
    RECONSTRUCTION of the opponent's trail from what the protocol revealed,
    one turn behind -- not a live reading of where it is now."""

    own: Grid
    opponent: Grid


@dataclass(frozen=True)
class HintView:
    """One hint as it was received or sent.

    `claimed_intent` is the SENDER's own flag (`Intent`, D-47): on an
    inbound hint it is what the opponent asserts about its own honesty, and
    believing it is the receiver's mistake to make. `turn` is the sender's
    stamp and may be absent, because inbound payloads are validated as
    nothing more than a dict (05-12's boundary rule)."""

    sender: str
    turn: int | None
    text: str
    claimed_intent: str | None


@dataclass(frozen=True)
class LocalView:
    """One peer's whole renderable truth for one refresh tick.

    Frozen so a caller cannot bolt a field on after construction, which is
    how the debugging shortcut gets in without anyone editing this file.
    """

    role: str
    board_size: int
    turn: int
    own_cell: Coord
    declared_barriers: tuple[Coord, ...]
    barriers_placed: int
    belief: BeliefView | None
    scent: ScentView | None
    hints: tuple[HintView, ...]
    machine_state: str
    idle_seconds: float | None
    watchdog_threshold_seconds: float
