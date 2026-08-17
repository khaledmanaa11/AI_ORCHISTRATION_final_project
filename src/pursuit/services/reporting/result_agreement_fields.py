"""The rule-35 agreement record's key names, its five named reasons, and the
record itself.

Split out of `result_agreement.py` at the 150-code-line gate (Segal Table 5,
the combined module measured 161) along the seam the
`log_artifact_fields.py` / `artifact_declaration_fields.py` precedent already
established: the SCHEMA and the five sentences a grader reads are one subject,
the extraction and the verdict are another. `result_agreement.py` re-exports
every public name below, so callers keep ONE import path.

Split, never compressed: not one line of any docstring or body was shortened
to make room.

THE REASONS ARE THE ARTIFACT'S PROSE, so they live where they can be read as a
set. `agreed: null` is only honest when something says WHY it is null, and the
whole point of naming them here is that no branch can be added without a
sentence to go with it.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = (
    "AGREEMENT_CONTRADICTED",
    "AGREEMENT_MATCHED",
    "AGREEMENT_UNPARSEABLE",
    "NO_OWN_OUTCOME",
    "NO_PEER_CLAIM",
    "AgreementField",
    "AgreementRecord",
)

AGREEMENT_MATCHED = "own and peer outcome claims agree"

AGREEMENT_CONTRADICTED = (
    "own and peer outcome claims contradict; rule 35 requires the disagreement "
    "REPORTED, never smoothed away"
)

AGREEMENT_UNPARSEABLE = (
    "the peer sent a GAME_OVER claim this side cannot parse as an outcome; "
    "recorded as a named non-agreement rather than raised (security/audit.py's "
    "boundary rule)"
)

NO_PEER_CLAIM = (
    "no peer GAME_OVER claim exists: rule 21 gives the Capture Claim to the cop "
    "alone, so a survival game -- and the cop's own seat in any game -- "
    "legitimately receives none. Absent, never inferred from our own outcome"
)

NO_OWN_OUTCOME = "this side reached no outcome, so there is nothing of ours to agree with"


class AgreementField:
    """The record's key names in the emitted artifact -- named once so the
    builder, the reader and the tests cannot drift onto three spellings."""

    OWN_OUTCOME = "own_outcome"
    PEER_OUTCOME = "peer_outcome"
    PEER_CLAIM_PRESENT = "peer_claim_present"
    AUDIT_VERDICT = "audit_verdict"
    AGREED = "agreed"
    REASON = "reason"


@dataclass(frozen=True)
class AgreementRecord:
    """One game's rule-35 evidence.

    `peer_claim_present` is carried BESIDE `peer_outcome` because "the peer
    sent nothing" and "the peer sent something unreadable" are different facts
    about the peer, and collapsing them onto a single `None` would hide the
    second one behind the first.
    """

    own_outcome: str | None
    peer_outcome: str | None
    peer_claim_present: bool
    audit_verdict: dict | None
    agreed: bool | None
    reason: str

    def to_dict(self) -> dict:
        """The JSON-native form the `result_` artifact embeds."""
        return {
            AgreementField.OWN_OUTCOME: self.own_outcome,
            AgreementField.PEER_OUTCOME: self.peer_outcome,
            AgreementField.PEER_CLAIM_PRESENT: self.peer_claim_present,
            AgreementField.AUDIT_VERDICT: self.audit_verdict,
            AgreementField.AGREED: self.agreed,
            AgreementField.REASON: self.reason,
        }
