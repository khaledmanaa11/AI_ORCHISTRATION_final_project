"""What the algorithm decided to claim, and whether it is true (D-36, LANG-03).

`DeceptionPlan` is built by `strategy/deception.py` from the board and the
belief map, BEFORE any text exists. Plan 04-10 turns it into fifteen English
words and has no say in either field. That ordering is a correctness
property, not a style preference: book Sec5.3.1 seals
`SHA256(State || Move || Intent || Nonce)`, so an intent flag decided *after*
the sentence was written would be a forgeable claim about the agent's own
good faith.

**Rules 15/16 and 21/22 are carved out in the TYPE, not in a caller's
memory.** A barrier declaration and a capture declaration are always
truthful, and a false capture claim is immediate disqualification with zero
score and no appeal. `__post_init__` is the gate, so there is no construction
path -- not a helper, not `dataclasses.replace`, not a test double -- that can
produce a lying plan for either kind.

`Intent` lives here rather than in `network/hint_payload.py`, where 04-04
first declared it: `strategy/` may not import `pursuit.network` at all
(STRAT-03, enforced by `scripts/check_no_llm_in_strategy.py`), and the
planner that DECIDES the flag must name the same type the wire serialises.
`hint_payload.py` re-exports it, so every existing call site is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import Region


class Intent(str, Enum):
    """LANG-03: the hint's pre-committed truthfulness flag. Never optional,
    never inferred -- Phase 6 hashes it alongside the move, so it exists now
    in the shape Phase 6 will seal."""

    TRUTH = "truth"
    LIE = "lie"


class ClaimKind(str, Enum):
    """What a hint is ABOUT. Two kinds may lie; two never may."""

    LOCATION = "location"
    """A claim about which sector we are in. May be a lie."""

    HEADING = "heading"
    """A claim about which way we are moving. May be a lie."""

    BARRIER = "barrier"
    """A barrier placement declaration. ALWAYS TRUE -- rules 15, 16."""

    CAPTURE = "capture"
    """A capture declaration. ALWAYS TRUE -- rules 21, 22; a false one is
    immediate disqualification, zero score, no appeal."""


#: The kinds that can never carry `Intent.LIE`, with the rule that says so.
ALWAYS_TRUE_KINDS: dict[ClaimKind, str] = {
    ClaimKind.BARRIER: "rules 15/16 (a barrier declaration is always truthful)",
    ClaimKind.CAPTURE: "rules 21/22 (a false capture declaration is immediate "
    "disqualification, zero score, no appeal)",
}


@dataclass(frozen=True)
class DeceptionPlan:
    """One turn's claim: the intent flag, the kind, what we will say, and
    what was actually true.

    Both the claim and the truth are recorded. The event log therefore proves
    the flag was honest about ITSELF -- an auditor can check that a plan
    marked `TRUTH` really did state the true value, which is the only part of
    a deception system that has to be verifiable.
    """

    intent: Intent
    kind: ClaimKind
    claimed_region: Region | None = None
    claimed_heading: DirectionWord | None = None
    true_region: Region | None = None
    true_heading: DirectionWord | None = None

    def __post_init__(self) -> None:
        """Reject, loudly, the two states that would disqualify the team.

        Reaching either branch means a caller has a logic error, not that the
        game reached an unusual position -- so this raises rather than
        silently coercing the flag, which would hide the bug behind a hint
        that looks fine on the wire.
        """
        if self.intent is Intent.LIE and self.kind in ALWAYS_TRUE_KINDS:
            raise ValueError(
                f"DeceptionPlan: a {self.kind.value} claim can never be a lie -- "
                f"{ALWAYS_TRUE_KINDS[self.kind]}"
            )
        stated, actual = self._claim_pair()
        if self.intent is Intent.TRUTH and actual is not None and stated != actual:
            raise ValueError(
                f"DeceptionPlan: intent is 'truth' but the {self.kind.value} claim "
                f"{stated!r} is not the true value {actual!r}"
            )

    def _claim_pair(self) -> tuple[object | None, object | None]:
        """`(claimed, true)` for whichever field this kind is about.

        BARRIER and CAPTURE carry no sector or heading of their own -- the
        declaration's content is the placement or the capture itself, which
        the protocol already transmits -- so they compare as (None, None) and
        the truth check above is a no-op for them. Their honesty is enforced
        by the first branch instead.
        """
        if self.kind is ClaimKind.LOCATION:
            return self.claimed_region, self.true_region
        if self.kind is ClaimKind.HEADING:
            return self.claimed_heading, self.true_heading
        return None, None

    @property
    def is_lie(self) -> bool:
        """True when this plan deliberately misstates the board."""
        return self.intent is Intent.LIE
