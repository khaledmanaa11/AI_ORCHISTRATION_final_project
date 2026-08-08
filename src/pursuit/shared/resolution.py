"""Negotiated simultaneous-turn resolution semantics (RULES-RESOLUTION.md Sec3/Sec5).

Two of the six terminal predicates are undefined by the book -- the barrier race
(the thief steps into the cell being sealed) and the swap (the two agents trade
cells). Book Sec3.2 p.18 says the game contract is negotiated per pair of teams
and is "a floor, not a ceiling", so these are agreed data, not engine assumptions.

Why they do NOT live in game_params.json: rule 11 requires that file byte-identical
on both sides and handshake.py aborts before move 1 on a digest mismatch. New keys
there would differ from every peer that has not adopted them -- 0/0 on games that
never start. This block is optional and separate; absent an agreement we fall back
to BOOK_ONLY, which is exactly what a book-faithful peer computes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pursuit.config_keys import ResolutionKey

RESOLUTION_SOURCE = "resolution.json"


@dataclass(frozen=True)
class ResolutionRules:
    """The two negotiated terminal predicates. Book predicates are unconditional."""

    capture_on_barrier_race: bool
    capture_on_swap: bool


#: What a book-faithful peer computes with no negotiation. The safe default.
BOOK_ONLY = ResolutionRules(capture_on_barrier_race=False, capture_on_swap=False)

#: What we propose in the pre-game declaration. Capture-favouring: the cop seat
#: carries the higher reward (20 vs 10) and the swap is physically absurd.
PREFERRED = ResolutionRules(capture_on_barrier_race=True, capture_on_swap=True)


def load_resolution_rules(path: Path | str | None) -> ResolutionRules:
    """Load an agreed resolution block, or BOOK_ONLY when there is no agreement.

    Parameters
    ----------
    path:
        Filesystem path to a negotiated resolution.json, or None. A missing file
        is not an error -- it means no agreement was reached, which is a valid
        and common state (Sec5). A malformed file IS an error and raises.

    Returns
    -------
    ResolutionRules
        The agreed rules, or BOOK_ONLY when no block was supplied.

    Raises
    ------
    TypeError
        If a present key carries a non-boolean value.
    """
    if path is None:
        return BOOK_ONLY
    resolved = Path(path)
    if not resolved.exists():
        return BOOK_ONLY

    with resolved.open() as handle:
        data = json.load(handle)

    return ResolutionRules(
        capture_on_barrier_race=_require_bool(data, ResolutionKey.CAPTURE_ON_BARRIER_RACE),
        capture_on_swap=_require_bool(data, ResolutionKey.CAPTURE_ON_SWAP),
    )


def as_declaration(rules: ResolutionRules) -> dict:
    """Return the canonical dict form for the pre-game declaration and the log.

    Key order is irrelevant -- every consumer serialises with sort_keys=True --
    but the field names must match ResolutionKey exactly so a peer reading our
    declaration reconstructs the same ResolutionRules we ran.
    """
    return {
        str(ResolutionKey.CAPTURE_ON_BARRIER_RACE): rules.capture_on_barrier_race,
        str(ResolutionKey.CAPTURE_ON_SWAP): rules.capture_on_swap,
    }


def _require_bool(data: dict, key: str) -> bool:
    """Return data[key] as a bool; absent means "not agreed" -> False (BOOK_ONLY)."""
    if key not in data:
        return False
    value = data[key]
    if not isinstance(value, bool):
        raise TypeError(
            f"{RESOLUTION_SOURCE}: key {key!r} must be a boolean, got {type(value).__name__}"
        )
    return value
