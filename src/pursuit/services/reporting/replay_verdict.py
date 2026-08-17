"""The THREE verdicts a replay viewer may reach, and the exact words for each.

Split out of `replay_verify.py` as the dependency-free leaf -- the
`log_artifact_fields.py` / `artifact_names.py` precedent, along the same seam:
the WORDS and the SHAPES are a spec surface a reader must know, while loading
and re-hashing are the mechanics. `replay_verify.py` re-exports every public
name below, so the Tk layer keeps ONE import path (which is also the one path
`scripts/check_local_truth.py:80` allows a `gui/` module to reach).

WHY THE LITERALS LIVE HERE AND NOT IN `gui/`. `pyproject.toml:38` omits
`*/gui/*` from coverage, so a banner string defined in the Tk layer is
untested AND invisible to the `fail_under = 85` gate; and a test asserting a
second copy of the string would prove nothing about the screen. Sec10.4
criterion 3 quotes `Verified OK` VERBATIM -- it is a fixed literal, not a
message to reword.

THE THIRD STATE IS THE WHOLE POINT OF THIS MODULE.
`security/audit_record.py:34-36` records that its verdict is "vacuously True
for an empty list", and for the AUDIT that is correct: a peer with no records
has published nothing to disagree with, and rule 36 sanctions that separately.
On a SCREEN it is a lie. A grader reading `Verified OK` over a zero-turn
artifact is being told the cryptography checked out when nothing was checked,
which is the same defect this repository has already shipped once. So an
artifact carrying no committed turn reaches `NOTHING_TO_VERIFY`, a state that
is neither of the other two, and the aggregate is never evaluated for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = (
    "BANNER_COLOURS",
    "FAILED_PREFIX",
    "NOTHING_TO_VERIFY",
    "VERIFIED_OK",
    "ReplayVerdict",
    "TurnCheck",
    "VerdictState",
    "banner_colour",
    "failed_banner",
    "ratio_detail",
    "seal_failed_banner",
)

#: docs Sec10.4 criterion 3, verbatim. The banner reads EXACTLY this and
#: nothing else -- no counts appended, no prefix -- when, and only when, every
#: committed turn re-hashed. The counts go on `ReplayVerdict.detail`, so a test
#: can assert equality against this literal rather than a substring.
VERIFIED_OK = "Verified OK"

#: The artifact carried no committed turn. Never `Verified OK`.
NOTHING_TO_VERIFY = "Nothing to verify"

#: A failing banner always continues by NAMING what failed.
FAILED_PREFIX = "FAILED"

#: How the counts are stated beneath the banner.
RATIO_LABEL = "committed turns re-hash"

#: The seal covers fields the per-turn hashes cannot see -- `outcome`,
#: `audit_verdict`, `prior_game_uids`, `truncated_tail` and the hint text.
SEAL_FAILED_DETAIL = "the artifact seal does not recompute"


class VerdictState(str, Enum):
    """Which of the three the screen is showing. A distinct member for the
    empty case, so no caller can reach it by testing `not is_ok`."""

    OK = "ok"
    FAILED = "failed"
    NOTHING_TO_VERIFY = "nothing_to_verify"


#: Presentation only, and named rather than inline (CLAUDE.md's hardcoded-value
#: rule) -- no game parameter is expressible as a colour.
OK_COLOUR = "#1b7f3b"
FAILED_COLOUR = "#b00020"
NEUTRAL_COLOUR = "#4a4a4a"

BANNER_COLOURS = {
    VerdictState.OK: OK_COLOUR,
    VerdictState.FAILED: FAILED_COLOUR,
    VerdictState.NOTHING_TO_VERIFY: NEUTRAL_COLOUR,
}


@dataclass(frozen=True)
class TurnCheck:
    """One turn's re-hash result. `committed` is False for a turn that carries
    no `h_commit` at all -- a trailing game-over turn is the ordinary case, and
    counting it would make the ratio a lie (07-05's own warning)."""

    turn: int
    committed: bool
    ok: bool
    detail: str


@dataclass(frozen=True)
class ReplayVerdict:
    """The whole-file verdict: the state, the words on the banner, and the
    counts that earned them."""

    state: VerdictState
    banner: str
    detail: str
    verified: int
    committed: int

    @property
    def is_ok(self) -> bool:
        """True only for `VerdictState.OK`. Deliberately identity on the
        member rather than a string comparison, so a future fourth state
        cannot become OK by spelling."""
        return self.state is VerdictState.OK


def banner_colour(state: VerdictState) -> str:
    """The banner's foreground for one state -- derived here because `gui/`
    is coverage-omitted and may hold no derivation at all."""
    return BANNER_COLOURS[state]


def failed_banner(check: TurnCheck) -> str:
    """`FAILED` NAMING THE TURN. A viewer that reports failure without saying
    which turn sends a third party back to re-derive the whole file."""
    return f"{FAILED_PREFIX} -- turn {check.turn}: {check.detail}"


def seal_failed_banner() -> str:
    """`FAILED` for a body that re-hashes turn by turn but whose seal does
    not: something outside the committed payloads was altered."""
    return f"{FAILED_PREFIX} -- {SEAL_FAILED_DETAIL}"


def ratio_detail(verified: int, committed: int) -> str:
    """The counts line. Shown under every banner including
    `NOTHING_TO_VERIFY`, where it reads `0/0` and says so plainly."""
    return f"{verified}/{committed} {RATIO_LABEL}"
