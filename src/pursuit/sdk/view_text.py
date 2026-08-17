"""Every line of text the live sidebar prints, derived here rather than in
`gui/` -- the same coverage argument as `view_render` (`pyproject.toml:38`
omits `*/gui/*`, so a formatter placed there would be untested and would look
like the >=85% gate had passed).

EVERY LINE IS BUILT FROM `LocalView` AND FROM NOTHING ELSE. The sidebar is
the panel most likely to acquire a "just for debugging" field, so the rule is
stated where the strings are made: if a line wants a fact the published view
does not carry, that is a finding to report, never a reason to reach back
into `ctx.state`, into `ctx.brain.belief`, or into the JSONL audit log (D7-8
-- `belief_snapshot` writes the TRUE argmax there, correctly, and no live
panel may read it).

An absent reading prints as absent. `idle_seconds` is None whenever the
injected watchdog exposes no reading, and a fabricated `0.0` there would
claim the agent had just been touched.
"""

from __future__ import annotations

from pursuit.sdk.local_view import HintView, LocalView

#: Presentation only: how many decimals a float reading prints with.
DECIMALS = 2

#: Printed where a reading genuinely has no value, never a stand-in number.
ABSENT = "unknown"

#: The honest empty belief panel (belief disabled this game, or 07-11's
#: publication floor refusing a map that would name a cell).
NO_BELIEF_LINE = "no belief published this turn"

#: The sender label `view_builder.OWN_HINT_SENDER` uses for our own hints.
NO_HINTS_LINE = "no hints yet"

#: What an unrecognised or missing intent flag prints as. The flag is the
#: SENDER's own claim (D-47), never a verified fact -- the label says so.
UNDECLARED_INTENT = "undeclared"

#: The sidebar sections, in the order `sidebar_blocks` returns them. `gui/`
#: zips titles to blocks with `strict=True`, so the two can never drift.
SECTION_STATUS = "this peer"
SECTION_BELIEF = "published belief"
SECTION_HINTS = "hint log"
SIDEBAR_TITLES = (SECTION_STATUS, SECTION_BELIEF, SECTION_HINTS)

#: The window's own caption. Names the seat, not the game: one window per
#: agent PROCESS (D-76), and neither window can see the other's view.
WINDOW_TITLE = "pursuit -- live local view"


def status_lines(view: LocalView) -> tuple[str, ...]:
    """Role, turn, machine state, own position and the barrier count."""
    return (
        f"role: {view.role}",
        f"turn: {view.turn}",
        f"state: {view.machine_state}",
        f"own cell: {_cell(view.own_cell)}",
        f"barriers placed: {view.barriers_placed}",
        f"barriers declared: {len(view.declared_barriers)}",
    )


def belief_lines(view: LocalView) -> tuple[str, ...]:
    """The belief panel's caption. `argmax` here is the PUBLISHED map's --
    `strategy/display_belief.py` decides which map that is, and on a seat that
    took an exact observation it is deliberately not the strategy map."""
    if view.belief is None:
        return (NO_BELIEF_LINE,)
    return (
        f"entropy: {_number(view.belief.entropy)} bits",
        f"reliability: {_number(view.belief.reliability)}",
        f"peak cell: {_cell(view.belief.argmax)}",
        f"lit cells: {_support(view)}",
    )


def timer_line(view: LocalView) -> str:
    """The freeze timer: idle seconds against the watchdog's own threshold."""
    idle = ABSENT if view.idle_seconds is None else _number(view.idle_seconds)
    return f"idle: {idle} / {_number(view.watchdog_threshold_seconds)} s"


def hint_lines(view: LocalView) -> tuple[str, ...]:
    """The hint log, oldest first, one line per entry."""
    return tuple(_hint_line(hint) for hint in view.hints) or (NO_HINTS_LINE,)


def sidebar_blocks(view: LocalView) -> tuple[str, ...]:
    """One ready-to-display block per entry in `SIDEBAR_TITLES`, in that
    order. Even the newline join lives here: `gui/` is coverage-omitted, so
    the rule is that it performs no string building at all."""
    return (
        as_block(status_lines(view) + (timer_line(view),)),
        as_block(belief_lines(view)),
        as_block(hint_lines(view)),
    )


def as_block(lines: tuple[str, ...]) -> str:
    return "\n".join(lines)


def _hint_line(hint: HintView) -> str:
    turn = ABSENT if hint.turn is None else str(hint.turn)
    intent = hint.claimed_intent or UNDECLARED_INTENT
    return f"t{turn} {hint.sender} [claims: {intent}] {hint.text}"


def _support(view: LocalView) -> int:
    return sum(1 for row in view.belief.rows for value in row if value > 0.0)


def _cell(cell: tuple[int, int]) -> str:
    return f"({cell[0]}, {cell[1]})"


def _number(value: float) -> str:
    return f"{value:.{DECIMALS}f}"
