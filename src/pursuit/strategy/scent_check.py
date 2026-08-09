"""The book's own lie-detector: Sec4.4, p.30 (PDF 46), implemented literally
(D-51).

The thief declares "I moved north"; the expected trail there, one decay step
after a fresh deposit, is `expected_strength_after(model, 1)` --
`0.9*(1-0.10) = 0.81` with the locked Table 16 numbers, the book's own worked
example. Measuring approximately zero there while a strong trail sits
elsewhere is the book's own contradiction signal: "the cop concludes with
high confidence that the thief is lying." This module returns HOW SURE, in
[0, 1], not a boolean -- the strength of the disagreement is what
`reliability.py`'s step size needs (see that module's `observe`).

Two guards keep an opponent from ever being penalised for our own lack of
information: an EMPTY trail (nothing sensed yet, early game) and an
UNTESTABLE claim (no region or cells -- a bare heading cannot be checked
against a place) both score zero, never treated as evidence of a lie.

`opponent_field` is THIS peer's own local reconstruction of the OTHER side's
trail (`ScentField.opponent`, D-49) -- never a transmitted value. Reading it
here is exactly the book's closing line: "the scent map cannot lie... what is
exposed here is a verbal hint caught as false, not a false trail (which does
not exist)."
"""

from __future__ import annotations

from pursuit.shared.belief_config import BeliefParams
from pursuit.shared.inference import Coord, Inference
from pursuit.shared.scent_config import ScentModel
from pursuit.strategy.regions import region_cells
from pursuit.strategy.scent import expected_strength_after
from pursuit.strategy.scentfield import ScentField

#: How many decay steps a "just claimed" position implies. Structural, not
#: tunable: a hint describes an action just taken THIS turn, so the trail it
#: implies is exactly one decay step past a fresh full-strength deposit --
#: the book's own worked example (0.9 -> 0.81) is precisely this number.
_CLAIM_AGE = 1


def contradicts(
    inference: Inference,
    opponent_field: ScentField,
    model: ScentModel,
    config: BeliefParams,
) -> float:
    """How strongly `inference`'s claimed location disagrees with the trail
    we have actually sensed, in [0, 1].

    0 means consistent, untestable (no region or cells to check), or nothing
    sensed yet. 1 is the book's own worst case: claimed somewhere with no
    trail at all while a full-strength trail sits elsewhere. Scaling by
    `peak_strength` (how strong the field's own best reading is) is what
    keeps a faint, ambiguous trail from being read as a confident lie --
    only a REAL trail sitting elsewhere makes a claim's empty spot damning.
    """
    if not inference.is_evidence:
        return 0.0
    peak = opponent_field.freshest("opponent")
    if peak is None:
        return 0.0
    peak_strength = opponent_field.strength("opponent", peak)
    if peak_strength < config.epsilon:
        return 0.0

    claimed = _claimed_cells(inference, opponent_field.board_size)
    expected = expected_strength_after(model, _CLAIM_AGE)
    measured = max(opponent_field.strength("opponent", cell) for cell in claimed)
    unexplained = max(0.0, expected - measured) / expected
    elsewhere = min(1.0, peak_strength / expected)
    return min(1.0, unexplained * elsewhere)


def _claimed_cells(inference: Inference, board_size: int) -> frozenset[Coord]:
    """The cells `inference` implicates: explicit cells if the decoder gave
    any, else the claimed region's cells.

    `inference.is_evidence` (checked by the only caller, `contradicts`)
    guarantees region or cells is present, so this is never empty here.
    """
    if inference.cells:
        return frozenset(inference.cells)
    return region_cells(inference.region, board_size)
