"""Verdict types for the NET-06 deadline tracker (D-13).

Split out of deadline.py only because the retry-ladder logic plus this many
dataclasses/enum exceeded the 150-code-line gate (Segal Table 5) -- never to
compress either file. deadline.py re-exports every name defined here through
its own __all__, so importers (the tests, 02-09, 02-10) see one unchanged
surface: `from pursuit.network.deadline import CallOutcome, TechnicalWin,
TechnicalWinReason`.
"""

import time
from dataclasses import dataclass
from enum import Enum


class TechnicalWinReason(Enum):
    """Why a technical win was declared (NET-06, D-67/SEC-05).

    The enum exists so the reason is never a magic string (QUAL-11).
    AUDIT_HASH_MISMATCH (06-03) and PEER_PROTOCOL_ERROR (06-06) are both
    additive -- TechnicalWin/CallOutcome are unchanged; the Final-Reveal
    audit and the peer-fault path reuse this SAME dataclass, never a
    second, parallel verdict type.
    """

    OPPONENT_UNRESPONSIVE = "opponent_unresponsive"
    AUDIT_HASH_MISMATCH = "audit_hash_mismatch"
    # 06-06: the opponent's tool body REJECTED our call (fastmcp ToolError)
    # -- distinct from OPPONENT_UNRESPONSIVE, which means they never
    # answered at all. A peer that rejects promptly is not unresponsive,
    # and the log should not claim it was.
    PEER_PROTOCOL_ERROR = "peer_protocol_error"


@dataclass(frozen=True)
class TechnicalWin:
    """Measured evidence for a NET-06 technical-win declaration (D-13).

    Every field is measured by call_with_retry's own retry ladder -- never
    assumed or defaulted -- so the declaration this carries is defensible at
    audit (RULES.md rules 16/22: a false declaration is disqualifying).
    """

    reason: TechnicalWinReason
    attempts: int
    timeout_seconds: float
    backoff_seconds: float
    elapsed_seconds: float
    last_error: str

    def as_evidence(self) -> dict:
        """Return a json.dumps-serializable dict for the JSONL event log.

        The reason is rendered as its `.value` string, not the enum object
        itself -- enums are not JSON-serializable. Shaped to drop straight
        into 02-04's JSONL record under event="technical_win".
        """
        return {
            "reason": self.reason.value,
            "attempts": self.attempts,
            "timeout_seconds": self.timeout_seconds,
            "backoff_seconds": self.backoff_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "last_error": self.last_error,
        }


def peer_protocol_verdict(error: object, started: float) -> TechnicalWin:
    """Build the verdict for a peer whose tool body REJECTED our call (06-06).

    `started` is a `time.monotonic()` stamp taken before the call, so
    `elapsed_seconds` is genuinely measured -- never fabricated (rules
    16/22). `attempts`/`timeout_seconds`/`backoff_seconds` are structural:
    no retry ladder governs a rejection, because `deadline.call_with_retry`
    re-raises `ToolError` without retrying by design. This mirrors exactly
    how 06-03's AUDIT_HASH_MISMATCH already fills the same dataclass.

    Takes the error as a plain object and stringifies it, so this module
    keeps its zero-dependency shape (no fastmcp import here).
    """
    return TechnicalWin(
        reason=TechnicalWinReason.PEER_PROTOCOL_ERROR,
        attempts=1,
        timeout_seconds=0.0,
        backoff_seconds=0.0,
        elapsed_seconds=time.monotonic() - started,
        last_error=str(error),
    )


@dataclass(frozen=True)
class CallOutcome:
    """The result of one call_with_retry ladder: success value or verdict."""

    value: object | None
    verdict: TechnicalWin | None
    attempts: int

    @property
    def succeeded(self) -> bool:
        """True when the call succeeded on some attempt (verdict is None)."""
        return self.verdict is None
