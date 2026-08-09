"""Verdict types for the NET-06 deadline tracker (D-13).

Split out of deadline.py only because the retry-ladder logic plus this many
dataclasses/enum exceeded the 150-code-line gate (Segal Table 5) -- never to
compress either file. deadline.py re-exports every name defined here through
its own __all__, so importers (the tests, 02-09, 02-10) see one unchanged
surface: `from pursuit.network.deadline import CallOutcome, TechnicalWin,
TechnicalWinReason`.
"""

from dataclasses import dataclass
from enum import Enum


class TechnicalWinReason(Enum):
    """Why a technical win was declared (NET-06, D-67/SEC-05).

    The enum exists so the reason is never a magic string (QUAL-11).
    AUDIT_HASH_MISMATCH (06-03) is additive -- TechnicalWin/CallOutcome are
    unchanged; the Final-Reveal audit reuses this SAME dataclass, never a
    second, parallel verdict type.
    """

    OPPONENT_UNRESPONSIVE = "opponent_unresponsive"
    AUDIT_HASH_MISMATCH = "audit_hash_mismatch"


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
