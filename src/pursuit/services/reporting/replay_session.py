"""Stepping state and every line of text the replay window prints.

`pyproject.toml:38` omits `*/gui/*` from coverage, so the cursor arithmetic
(the advance, the clamp at the last turn, the auto-pause at the end) and all
string building live here, where the `fail_under = 85` gate can see them --
the argument `sdk/view_text.py` already makes for the live dashboard, applied
to the one directory that cannot be measured. `test_gui_structural.py` fails
the moment a `BinOp` or an f-string appears under `gui/`.

NOTHING HERE VERIFIES ANYTHING. `replay_verify` hands this object the checks
it has already made; a session that re-derived a verdict while stepping would
be a second opinion on the one question the screen exists to answer, and the
two could disagree on a tampered file.

SERIALISATION FOR DISPLAY GOES THROUGH `config_hash.canonical_json` -- the
repository's ONE canonicalisation (D-59, SEC-03). Not because a panel caption
needs a canonical form, but because a second `json.dumps(sort_keys=True, ...)`
anywhere in this package is forbidden outright, and a reader should not have
to check which of two spellings a given line is.
"""

from __future__ import annotations

from pursuit.network.config_hash import canonical_json
from pursuit.services.reporting.log_artifact_fields import LogArtifactField
from pursuit.services.reporting.log_turn_fields import (
    HINT_BROADCAST_KEYS,
    TurnField,
    WireSide,
)
from pursuit.services.reporting.replay_verdict import ReplayVerdict, TurnCheck

__all__ = ("SECTION_TITLES", "ReplaySession", "WINDOW_TITLE")

# Unpacked rather than indexed, so a change to the allow-list's length fails
# loudly here instead of silently renaming a caption.
HINT_INTENT_KEY, HINT_TEXT_KEY = HINT_BROADCAST_KEYS

#: The window caption. Names the artifact's role, never a live game.
WINDOW_TITLE = "pursuit -- replay verifier"

#: The panel sections, in the order `blocks()` returns them. `gui/` zips
#: titles to blocks with `strict=True`, so the two can never drift apart.
SECTION_REPLAY = "replay"
SECTION_COMMITMENT = "commit-reveal"
SECTION_HINT = "hint"
SECTION_TITLES = (SECTION_REPLAY, SECTION_COMMITMENT, SECTION_HINT)

FIRST_INDEX = 0
NO_TURNS_LINE = "this artifact carries no turn at all"
ABSENT = "none"
PLAYING = "playing"
PAUSED = "paused"


def _value(value: object) -> str:
    """One field, rendered. `None` prints as an explicit absence rather than
    as `None`, so a missing envelope never reads like a recorded one."""
    return ABSENT if value is None else canonical_json(value)


class ReplaySession:
    """One opened `log_` artifact: its turns, their checks, its verdict, and
    where the operator currently is in it.

    The cursor is an INDEX into `turns`, not a turn number: 07-05's join emits
    turns in sorted local-turn order but is not obliged to start at zero or to
    be contiguous, and a viewer that assumed either would silently show the
    wrong record for a game with a gap.
    """

    def __init__(
        self, artifact: dict, checks: tuple[TurnCheck, ...], verdict: ReplayVerdict, *, source: str
    ) -> None:
        self.artifact = artifact
        self.checks = checks
        self.verdict = verdict
        self.source = source
        self.turns = artifact.get(LogArtifactField.TURNS) or []
        self.index = FIRST_INDEX
        self.playing = False

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    @property
    def at_end(self) -> bool:
        return self.index >= self.turn_count - 1

    def step(self) -> None:
        """Advance one turn, stopping at the last. Reaching the end also
        PAUSES: a viewer that kept firing its timer against a clamped index
        would redraw the same frame forever and look like a freeze."""
        if self.at_end:
            self.playing = False
            return
        self.index += 1

    def back(self) -> None:
        """One turn earlier, stopping at the first."""
        if self.index > FIRST_INDEX:
            self.index -= 1

    def play(self) -> None:
        """Resume. An artifact already at its last turn rewinds first, so the
        button is never a no-op the operator has to guess about."""
        if self.at_end:
            self.index = FIRST_INDEX
        self.playing = self.turn_count > FIRST_INDEX

    def pause(self) -> None:
        self.playing = False

    def current_turn(self) -> dict | None:
        """The turn record under the cursor, or None for an empty artifact."""
        return self.turns[self.index] if self.turns else None

    def current_check(self) -> TurnCheck | None:
        """The check for the turn under the cursor. Positional: `checks` is
        built from the same list in the same order."""
        return self.checks[self.index] if self.index < len(self.checks) else None

    def blocks(self) -> tuple[str, ...]:
        """One ready-to-display block per entry in `SECTION_TITLES`."""
        turn = self.current_turn()
        if turn is None:
            return tuple(NO_TURNS_LINE for _ in SECTION_TITLES)
        return (
            _as_block(self._replay_lines(turn)),
            _as_block(self._commitment_lines(turn)),
            _as_block(_hint_lines(turn)),
        )

    def _replay_lines(self, turn: dict) -> tuple[str, ...]:
        return (
            f"artifact: {self.source}",
            f"role: {_value(self.artifact.get(LogArtifactField.ROLE))}",
            f"turn {turn.get(TurnField.TURN)} -- {self.index + 1} of {self.turn_count}",
            f"transport: {PLAYING if self.playing else PAUSED}",
            f"outcome: {_value(self.artifact.get(LogArtifactField.OUTCOME))}",
        )

    def _commitment_lines(self, turn: dict) -> tuple[str, ...]:
        check = self.current_check()
        commitment = turn.get(TurnField.COMMITMENT) or {}
        revealed = turn.get(TurnField.REVEALED_MOVE) or {}
        return (
            f"h_commit: {_value(turn.get(TurnField.HASH))}",
            f"re-hash: {ABSENT if check is None else check.detail}",
            f"intent (self-declared): {_value(turn.get(TurnField.INTENT))}",
            f"move: {_value(turn.get(TurnField.MOVE))}",
            f"commit sent / acked: {_value(commitment.get(WireSide.SENT))}"
            f" / {_value(commitment.get(WireSide.ACKED))}",
            f"commit received: {_value(commitment.get(WireSide.RECEIVED))}",
            f"reveal received: {_value(revealed.get(WireSide.RECEIVED))}",
        )


def _hint_lines(turn: dict) -> tuple[str, ...]:
    """The hint half. The intent flag is the SENDER's own claim (D-47, rule
    25) and the label says so -- a replay must not present a bluff as a fact."""
    hint = turn.get(TurnField.HINT) or {}
    outgoing = hint.get(WireSide.OUTGOING) or {}
    return (
        f"outgoing [claims: {_value(outgoing.get(HINT_INTENT_KEY))}]:"
        f" {_value(outgoing.get(HINT_TEXT_KEY))}",
        f"hint sent on the wire: {_value(hint.get(WireSide.SENT))}",
        f"hint received: {_value(hint.get(WireSide.RECEIVED))}",
    )


def _as_block(lines: tuple[str, ...]) -> str:
    """Even the newline join is here: `gui/` performs no string building."""
    return "\n".join(lines)
