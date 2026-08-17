"""Typed container + validation for belief.json's `display` group (07-11):
the two floors below which a peer's belief may not be PUBLISHED to a view.

Split out of `shared/belief_config.py` at the 150-code-line ceiling, same
reasoning as `shared/belief_toggle_config.py`'s own docstring.

WHY A FLOOR EXISTS AT ALL. Rule 9 (`docs/RULES.md:30`) forbids displaying
the objective board state in the live interface. A heatmap does not have to
print a coordinate to display one: 07-11 measured a published cop posterior
whose support was exactly `[(4,3),(5,2),(5,3),(5,4),(6,3)]` -- the legal-move
PLUS centred on the thief's true pre-move cell -- from which the centre
inverts back to `(5,3)` uniquely. The sealed-thief endgame is worse still:
`argmax (0,0)`, `entropy -0.0`, `lit cells [(0,0,1.0)]`, a one-pixel heatmap
painted on the truth. Both are caught by a floor and by nothing else, since
neither renders a coordinate as a value.

NEITHER NUMBER IS INVENTED and neither is a `docs/PARAMETERS.md` value; both
are DERIVED and labelled engineering defaults (D-18 discipline), as every
other number in belief.json already is:

* `min_support_cells` -- one cell's legal destination set is STAY plus the
  four orthogonal moves, i.e. never more than `len(DIRECTION_WORDS)` = 5
  cells (`shared/directions.py`, the vocabulary `sdk/actions.py` moves in).
  A support of SIX or more therefore cannot fit inside any single cell's
  step neighbourhood, so the geometric inversion above returns nothing --
  structurally impossible, not merely unlikely.
* `min_entropy_bits` -- one full bit is the entropy of a fair coin between
  two cells. Below that the map effectively NAMES a cell whatever its
  support size, and naming the opponent's cell is the thing rule 9 forbids.
"""

from __future__ import annotations

from dataclasses import dataclass

from pursuit.shared.belief_keys import BeliefKey
from pursuit.shared.directions import DIRECTION_WORDS
from pursuit.shared.loader_helpers import require_float, require_int, require_key

#: The largest a single cell's legal destination set can be -- STAY plus the
#: four orthogonal moves. Derived from the movement vocabulary rather than
#: written down as a 5, so a rules change that widened movement would move
#: this with it instead of leaving a stale literal behind.
MAX_STEP_NEIGHBOURHOOD = len(DIRECTION_WORDS)


@dataclass(frozen=True)
class DisplayFloors:
    """Typed, immutable container for belief.json's `display` group. Never
    constructed directly outside `load_display_floors()`."""

    min_entropy_bits: float
    min_support_cells: int


def load_display_floors(data: dict, *, source: str) -> DisplayFloors:
    """Read and validate the `display` group out of an already-parsed
    belief.json payload.

    Takes the WHOLE payload rather than a path so `load_belief_config()`
    stays the single file-opening entry point (its own docstring's promise).

    Raises
    ------
    KeyError
        If the group or either field is absent.
    TypeError
        If either field carries the wrong type.
    ValueError
        If either field is below the derived minimum -- see
        `validate_display_floors`.
    """
    group = require_key(data, BeliefKey.GROUP_DISPLAY.value, source=source)
    floors = DisplayFloors(
        min_entropy_bits=require_float(
            group, BeliefKey.MIN_ENTROPY_BITS.value, source=source
        ),
        min_support_cells=require_int(
            group, BeliefKey.MIN_SUPPORT_CELLS.value, source=source
        ),
    )
    validate_display_floors(floors, source=source)
    return floors


def validate_display_floors(floors: DisplayFloors, *, source: str) -> None:
    """Raise ValueError naming the offending field.

    `min_support_cells` is refused at or below `MAX_STEP_NEIGHBOURHOOD`: a
    floor of 5 or less permits a support that fits inside one cell's step
    neighbourhood, which is precisely the shape the geometric inversion
    recovers a unique centre from. A floor that admits the measured leak is
    not a floor.
    """
    if floors.min_entropy_bits <= 0.0:
        raise ValueError(
            f"{source}: 'display.min_entropy_bits' must be > 0, got {floors.min_entropy_bits}"
        )
    if floors.min_support_cells <= MAX_STEP_NEIGHBOURHOOD:
        raise ValueError(
            f"{source}: 'display.min_support_cells' ({floors.min_support_cells}) must be "
            f"> {MAX_STEP_NEIGHBOURHOOD}, the largest legal-move neighbourhood -- a smaller "
            f"floor admits a support the geometric inversion recovers a unique centre from"
        )
