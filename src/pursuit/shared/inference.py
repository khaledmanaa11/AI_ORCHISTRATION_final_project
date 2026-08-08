"""What one opponent sentence is allowed to become before the belief map is
permitted to see it (D-41, LANG-05/LANG-06).

Lives in `shared/` because BOTH `services/llm/decode.py` (which produces it)
and `strategy/belief_hint.py` (04-09, which consumes it) need the type, and
neither layer may import the other: `scripts/check_no_llm_in_strategy.py`
fails CI the moment anything under `strategy/` imports `pursuit.services`.
`shared/` is that script's own documented "legal seam for cross-cutting
types".

Two things this type deliberately CANNOT express:

1. **A move, an action, a preference or an evaluation.** An `Inference`
   describes where the opponent CLAIMS to be or to be heading -- never what
   we should do about it. Rule 25 / STRAT-07 is a type signature here, not a
   promise in a docstring.
2. **Truthfulness.** `confidence` is the DECODER's confidence that it
   understood the sentence, nothing more. Whether the sentence was HONEST is
   04-09's adaptive reliability coefficient (D-51), applied separately and
   multiplied in later. Folding the two together would let a fluent lie
   carry high weight -- which is precisely the attack a deceiving opponent
   is running (book Sec4.4).

`Region` is a coarse, board-size-agnostic vocabulary on purpose: the decoder
runs in `services/`, which owns no board (04-07 must_haves). Turning a
`Region` into actual cells is `strategy/regions.py`'s job, where the board
already lives.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pursuit.shared.directions import DirectionWord

Coord = tuple[int, int]


class Region(str, Enum):
    """The nine compass sectors of a square board.

    Coarse by design. A hint is one short sentence of natural language --
    *"I'm up by the north end"* carries a sector, not a cell -- and a
    vocabulary finer than the sentences can support would invite the decoder
    to invent precision the text never had.
    """

    NORTH = "north"
    NORTHEAST = "northeast"
    EAST = "east"
    SOUTHEAST = "southeast"
    SOUTH = "south"
    SOUTHWEST = "southwest"
    WEST = "west"
    NORTHWEST = "northwest"
    CENTER = "center"


#: Every region as a plain string, for a JSON-schema `enum` list.
REGION_NAMES: tuple[str, ...] = tuple(region.value for region in Region)


@dataclass(frozen=True)
class Inference:
    """One decoded hint: what the opponent claimed, and how sure we are that
    we READ it correctly (never how sure we are that it was true).

    Fields
    ------
    region:
        The claimed sector, or None when the sentence named no place.
    cells:
        Specific implicated cells, when the sentence was precise enough to
        support them. Usually empty -- `region` is the normal channel.
    direction:
        A claimed heading, when the sentence stated one.
    confidence:
        The decoder's own read-confidence, in [0, 1]. 0 means "this told me
        nothing", and is what every failure path returns.
    raw_text:
        The sentence exactly as received, kept for the event log and the
        Phase-7 replay viewer -- an audit needs the words, not just our
        reading of them.
    """

    region: Region | None = None
    cells: tuple[Coord, ...] = ()
    direction: DirectionWord | None = None
    confidence: float = 0.0
    raw_text: str = ""

    def __post_init__(self) -> None:
        """The [0, 1] bound is enforced by the CONSTRUCTOR, so no code path
        anywhere can hold an Inference carrying an out-of-range weight.

        `decode_schema.validate` checks the same bound before constructing,
        so a bad model response comes back as None (no evidence) instead of
        an exception -- this guard is for OUR OWN callers, which have no
        excuse for building one wrong.
        """
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Inference.confidence must be in [0, 1], got {self.confidence}")

    @property
    def is_evidence(self) -> bool:
        """True when this inference implicates somewhere with non-zero
        confidence -- i.e. when the belief map has something to multiply by.

        A hint that decoded cleanly but named no place is NOT evidence: it
        must leave the posterior untouched, exactly like a decode failure.
        """
        return self.confidence > 0.0 and (self.region is not None or bool(self.cells))


#: The one neutral result. Every failure path in `decode_hint` returns THIS
#: (D-33): an LlmFailure of any reason, a schema violation, an empty hint, a
#: provider that cannot decode at all. The belief map cannot tell a wrong
#: inference from a right one, so a wrong one is strictly worse than none.
NO_EVIDENCE = Inference()


def no_evidence_for(raw_text: str) -> Inference:
    """NO_EVIDENCE, but carrying the text that produced it.

    Same neutral weight; the sentence is preserved so the event log and
    04-14's decode-success rate can tell "the opponent said nothing useful"
    apart from "we failed to read what they said".
    """
    return Inference(raw_text=raw_text)
