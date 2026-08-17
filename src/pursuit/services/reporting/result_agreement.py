"""Rule 35's agreement record -- what THIS side claims, what the peer claimed,
and whether the two agree -- derived from data already on the wire (D-75).

THE SCHEMA AND THE FIVE NAMED REASONS ARE `result_agreement_fields.py`, split
out at the 150-code-line gate and re-exported here, so callers keep one import
path. What follows is the extraction and the verdict.

RULE 35 ZEROES BOTH TEAMS. `docs/RULES.md:76`: "Agree the result with the
opponent; **each team sends its own separate report**. Non-reporting, or
contradictory reports, by **one** team disqualifies the game and scores **0 for
both teams**." That makes this the report's most dangerous field, and the
danger is not a crash -- it is a comfortable lie.

`agreed` IS THREE-VALUED, AND DEFAULTING IT IS A FALSE DECLARATION.
`capture_declaration.declares_capture` sends `GAME_OVER` only when the outcome
is a capture AND this side is the cop -- "The thief stays silent; it has
nothing to declare and rule 21 asks nothing of it." So on a SURVIVAL game no
peer claim exists on either side, and even on a capture game only the THIEF
receives one. `peer_outcome` is then legitimately absent, and an
implementation that defaults it to our own outcome writes `agreed: true` onto
every silent game -- a fabricated agreement, under the one rule whose sanction
is zero for both teams. `agreed` is `True`, `False`, or `None` WITH A STATED
REASON, and is never inferred.

NO NEW PROTOCOL (D-75). No `MessageType`, no tool, no payload key: the peer's
claim is read out of the `message_received` record that
`capture_declaration.record_received_declaration` already writes, through that
module's own `OUTCOME_KEY` spelling rather than a second copy of the string.

A MALFORMED PEER CLAIM IS EVIDENCE, NOT A CRASH. `security/audit.py` writes
the boundary rule once for the whole project: "ANY function that reads a
structure the PEER sent must treat malformed input as a NAMED MISMATCH, never
as an exception. Not a crash, and not a free pass either."

THE AUDIT VERDICT IS PASSED IN, NEVER RE-EXTRACTED. `log_join.join_game`
already reduces the `audit_verdict` record to `{matched, turn}` for the `log_`
artifact, and `end_of_game` hands that same object here. One extraction, two
artifacts, and they cannot disagree about the verdict -- the discipline
`capture_declaration` keeps for the capture claim itself, applied to the audit.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.constants import Outcome
from pursuit.network.capture_declaration import OUTCOME_KEY
from pursuit.network.envelope import EnvelopeKey, MessageType
from pursuit.network.event_log import EventField, EventType
from pursuit.services.reporting.log_read import read_tolerating_partial_tail
from pursuit.services.reporting.result_agreement_fields import (
    AGREEMENT_CONTRADICTED,
    AGREEMENT_MATCHED,
    AGREEMENT_UNPARSEABLE,
    NO_OWN_OUTCOME,
    NO_PEER_CLAIM,
    AgreementField,
    AgreementRecord,
)

__all__ = (
    "AGREEMENT_CONTRADICTED",
    "AGREEMENT_MATCHED",
    "AGREEMENT_UNPARSEABLE",
    "NO_OWN_OUTCOME",
    "NO_PEER_CLAIM",
    "AgreementField",
    "AgreementRecord",
    "build_agreement",
    "peer_outcome_claims",
)


def peer_outcome_claims(records: list[dict]) -> list[object]:
    """Every inbound GAME_OVER claim's RAW `outcome` value, in log order.

    Raw on purpose: parsing happens one step later, so a claim that arrives in
    an unexpected shape still counts as a claim that was made. A claim whose
    payload is not even a dict contributes `None` -- present, unreadable.
    """
    claims: list[object] = []
    for record in records:
        if record.get(EventField.EVENT) != EventType.MESSAGE_RECEIVED.value:
            continue
        envelope = record.get(EventField.ENVELOPE)
        if not isinstance(envelope, dict):
            continue
        if envelope.get(EnvelopeKey.TYPE) != MessageType.GAME_OVER.value:
            continue
        payload = envelope.get(EnvelopeKey.PAYLOAD)
        claims.append(payload.get(OUTCOME_KEY) if isinstance(payload, dict) else None)
    return claims


def _parsed_outcome(value: object) -> str | None:
    """A recognised `Outcome` value, or `None` for every other shape."""
    if not isinstance(value, str):
        return None
    try:
        return Outcome(value).value
    except ValueError:
        return None


def _verdict(own: str | None, peer: str | None, *, present: bool) -> tuple[bool | None, str]:
    """The three-valued decision, with the reason that names the branch."""
    if not present:
        return None, NO_PEER_CLAIM
    if peer is None:
        return False, AGREEMENT_UNPARSEABLE
    if own is None:
        return None, NO_OWN_OUTCOME
    if own == peer:
        return True, AGREEMENT_MATCHED
    return False, AGREEMENT_CONTRADICTED


def build_agreement(
    log_path: Path | str, *, own_outcome: Outcome | None, audit_verdict: dict | None
) -> AgreementRecord:
    """This game's rule-35 record, read off this side's own wire log.

    The LAST claim wins when a peer sent more than one: the log is append-only
    evidence and its last word is the peer's final position, the same rule
    `record_technical_loss` states for this side's own `game_over` records.

    Reads through `log_read.read_tolerating_partial_tail`, so a game whose last
    line was cut off by a crash still yields a report -- which is exactly when
    rule 32's per-game sanction would otherwise bite.
    """
    records, _truncated = read_tolerating_partial_tail(log_path)
    claims = peer_outcome_claims(records)
    own = own_outcome.value if own_outcome is not None else None
    peer = _parsed_outcome(claims[-1]) if claims else None
    agreed, reason = _verdict(own, peer, present=bool(claims))
    return AgreementRecord(
        own_outcome=own,
        peer_outcome=peer,
        peer_claim_present=bool(claims),
        audit_verdict=audit_verdict,
        agreed=agreed,
        reason=reason,
    )
