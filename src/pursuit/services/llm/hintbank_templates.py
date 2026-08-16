"""The template bank's DATA: phrasings and slot fillers, no selection logic
(D-39, LANG-01, 04-10).

Split from `hintbank.py` at the 150-code-line gate (Segal Table 5): this
module is a pure, side-effect-free data table (CLAUDE.md "split files, never
compress code to fit"). `hintbank.py` owns selection (the seeded RNG, the
no-repeat rotation, import-time validation); this module owns only WHAT can
be said.

Every phrasing takes a single `{slot}` fill, even the two kinds
(`BARRIER`/`CAPTURE`) that carry no board fact of their own -- `_EVENT_*`
below fills their slot with an optional flourish clause instead of a place
name, so `HintBank.select()` can treat every `(ClaimKind, Intent)` key
identically: one template, one slot, one filler table, regardless of kind.

Arena landmark names are New York-specific (the shipped `game_arena`
default, Table 14 row 1) as an engineering simplification, not a
geography engine: a match that negotiates a different named arena still
gets the GENERIC bucket's directional language whenever it wants it, and
the arena bucket is only reached at all when `game_arena` is non-empty
(D-39, Sec6.5.1). Extending this to a real per-arena landmark database is
future work, not required by this phase.
"""

from __future__ import annotations

from pursuit.shared.deception_types import ClaimKind, Intent
from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import Region

#: Real-place slot fillers for a LOCATION claim, keyed by the claimed sector.
ARENA_REGION_PLACE: dict[Region, str] = {
    Region.NORTH: "Central Park",
    Region.NORTHEAST: "the Upper East Side",
    Region.EAST: "the East River piers",
    Region.SOUTHEAST: "the Financial District",
    Region.SOUTH: "Battery Park",
    Region.SOUTHWEST: "the Hudson docks",
    Region.WEST: "the West Side piers",
    Region.NORTHWEST: "Harlem",
    Region.CENTER: "Times Square",
}

#: Generic (arena-empty) slot fillers for a LOCATION claim.
GENERIC_REGION_PLACE: dict[Region, str] = {
    Region.NORTH: "the north edge",
    Region.NORTHEAST: "the northeast corner",
    Region.EAST: "the east edge",
    Region.SOUTHEAST: "the southeast corner",
    Region.SOUTH: "the south edge",
    Region.SOUTHWEST: "the southwest corner",
    Region.WEST: "the west edge",
    Region.NORTHWEST: "the northwest corner",
    Region.CENTER: "the middle of the board",
}

#: Real-place slot fillers for a HEADING claim, keyed by the claimed word.
ARENA_HEADING_PLACE: dict[DirectionWord, str] = {
    DirectionWord.NORTH: "making for Central Park",
    DirectionWord.SOUTH: "making for Battery Park",
    DirectionWord.EAST: "making for the East River",
    DirectionWord.WEST: "making for the Hudson piers",
    DirectionWord.STAY: "holding position by Times Square",
}

#: Generic (arena-empty) slot fillers for a HEADING claim.
GENERIC_HEADING_PLACE: dict[DirectionWord, str] = {
    DirectionWord.NORTH: "moving north",
    DirectionWord.SOUTH: "moving south",
    DirectionWord.EAST: "moving east",
    DirectionWord.WEST: "moving west",
    DirectionWord.STAY: "holding position",
}

#: BARRIER/CAPTURE carry no region or heading -- the slot is an optional
#: flourish clause instead, present only in the arena flavour.
EVENT_ARENA_CLAUSE = ", right by Times Square"
EVENT_GENERIC_CLAUSE = ""

LOCATION_TEMPLATES: tuple[str, ...] = (
    "I'm holed up near {slot}.",
    "You'll find me close to {slot}.",
    "Word is I'm hiding around {slot}.",
    "Last seen not far from {slot}.",
)

HEADING_TEMPLATES: tuple[str, ...] = (
    "Right now I'm {slot}.",
    "As of this turn I'm {slot}.",
    "For what it's worth, I'm {slot}.",
    "Truth is, I'm {slot}.",
)

BARRIER_TEMPLATES: tuple[str, ...] = (
    "Barrier placed exactly as declared{slot}.",
    "That barrier is mine, no more and no less{slot}.",
    "Placed the barrier right where I said I would{slot}.",
)

CAPTURE_TEMPLATES: tuple[str, ...] = (
    "Capture confirmed, exactly as declared{slot}.",
    "That's a capture, plain and simple{slot}.",
    "Confirmed capture, no dispute{slot}.",
)

#: Every legal (ClaimKind, Intent) pair (BARRIER/CAPTURE never pair with
#: LIE -- DeceptionPlan.__post_init__ makes that combination unconstructable)
#: mapped to its own phrasing set. `hintbank.py`'s import-time check walks
#: every entry here with every filler this module defines.
#:
#: 05-15 (G10), stated plainly rather than left to be re-discovered: the two
#: TRUTH-only rows below have NO POLICY CALLER. All four DeceptionPlan
#: constructions in deception_cop.py/deception_thief.py hardcode
#: kind=ClaimKind.LOCATION, and the barrier/capture DECLARATIONS are not hint
#: utterances at all -- the barrier rides inside the committed action
#: (PRD_commit_reveal.md Sec2.2, D-66/SEC-07) and the capture is the
#: GAME_OVER envelope (network/capture_declaration.py). The rows are kept
#: anyway, and that is a MEASURED decision, not inertia: BANK must be TOTAL
#: over every (kind, intent) pair __post_init__ permits, because
#: HintBank.select indexes it directly and its own docstring promises it
#: "cannot KeyError for a real DeceptionPlan". Deleting these two rows was
#: probed -- 4 tests fail, one of them a KeyError escaping bluff.compose(),
#: whose whole contract is having no failure mode. Reserved and total by
#: design; see docs/PRD_deception.md Sec2.1.1.
BANK: dict[tuple[ClaimKind, Intent], tuple[str, ...]] = {
    (ClaimKind.LOCATION, Intent.TRUTH): LOCATION_TEMPLATES,
    (ClaimKind.LOCATION, Intent.LIE): LOCATION_TEMPLATES,
    (ClaimKind.HEADING, Intent.TRUTH): HEADING_TEMPLATES,
    (ClaimKind.HEADING, Intent.LIE): HEADING_TEMPLATES,
    (ClaimKind.BARRIER, Intent.TRUTH): BARRIER_TEMPLATES,
    (ClaimKind.CAPTURE, Intent.TRUTH): CAPTURE_TEMPLATES,
}
