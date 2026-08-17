"""Rule 35's agreement record: true, false, or honestly unknown -- never invented.

The plan's three named cases (a), (b) and (c). The peer-controlled shapes --
case (d) -- and the scanner's own control live in
`test_result_agreement_edges.py`, split at the 150-code-line gate.

Case (b) is the COUNTER-CONTROL. A "fix" that smooths a disagreement into
agreement passes (a) and fails (b) -- and rule 35 needs the disagreement
REPORTED, which is why (b) also asserts a full record still comes out.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network.envelope import MessageType
from pursuit.services.reporting.result_agreement import (
    AGREEMENT_CONTRADICTED,
    AGREEMENT_MATCHED,
    NO_PEER_CLAIM,
    AgreementField,
    build_agreement,
)
from tests.unit.result_agreement_fixtures import (
    VERDICT,
    agreement_ctx,
    capture_payload,
    claim,
)


def test_an_honest_agreeing_capture_records_agreed_true(
    tmp_path, default_params, network_params
):
    """(a) Both sides resolved the same capture; the thief received the cop's claim."""
    ctx = agreement_ctx(tmp_path, default_params, network_params, "a")
    claim(ctx, capture_payload(Outcome.CAPTURE.value))

    record = build_agreement(
        ctx.log_path, own_outcome=Outcome.CAPTURE, audit_verdict=VERDICT,
    )
    assert record.agreed is True
    assert record.reason == AGREEMENT_MATCHED
    assert record.own_outcome == Outcome.CAPTURE.value
    assert record.peer_outcome == Outcome.CAPTURE.value
    assert record.peer_claim_present is True
    assert record.audit_verdict == VERDICT


def test_a_fabricated_disagreement_is_reported_not_smoothed(
    tmp_path, default_params, network_params
):
    """(b) THE COUNTER-CONTROL. The peer claims a survival we resolved as a
    capture. `agreed` is False AND a complete record still comes out: rule 35
    disqualifies contradictory reports, so suppressing the contradiction is the
    fraud the rule exists to catch, not a way past it."""
    ctx = agreement_ctx(tmp_path, default_params, network_params, "b")
    claim(ctx, capture_payload(Outcome.SURVIVAL.value))

    record = build_agreement(
        ctx.log_path, own_outcome=Outcome.CAPTURE, audit_verdict=VERDICT,
    )
    assert record.agreed is False
    assert record.reason == AGREEMENT_CONTRADICTED
    assert record.own_outcome == Outcome.CAPTURE.value
    assert record.peer_outcome == Outcome.SURVIVAL.value
    assert sorted(record.to_dict()) == sorted(
        (
            AgreementField.AGREED, AgreementField.AUDIT_VERDICT, AgreementField.OWN_OUTCOME,
            AgreementField.PEER_CLAIM_PRESENT, AgreementField.PEER_OUTCOME, AgreementField.REASON,
        )
    )


def test_a_survival_game_with_no_peer_claim_is_null_and_never_true(
    tmp_path, default_params, network_params
):
    """(c) THE PLAN'S NAMED REVERT PROBE. No cop landed on the thief, so no
    Capture Claim exists on either side. An implementation that defaults
    `peer_outcome` to `own_outcome` writes `agreed: true` here."""
    ctx = agreement_ctx(tmp_path, default_params, network_params, "c")
    claim(ctx, {"text": "a hint, not a claim"}, kind=MessageType.HINT)

    record = build_agreement(
        ctx.log_path, own_outcome=Outcome.SURVIVAL, audit_verdict=VERDICT,
    )
    assert record.agreed is not True
    assert record.agreed is None
    assert record.reason == NO_PEER_CLAIM
    assert record.peer_outcome is None
    assert record.peer_claim_present is False
    assert record.own_outcome == Outcome.SURVIVAL.value


def test_a_missing_log_is_still_a_report_and_still_not_an_agreement(tmp_path):
    """A game that crashed before writing anything still yields a record --
    which is precisely when rule 32's per-game sanction would otherwise bite."""
    record = build_agreement(
        tmp_path / "absent.jsonl", own_outcome=Outcome.SURVIVAL, audit_verdict=None,
    )
    assert record.agreed is None
    assert record.reason == NO_PEER_CLAIM
    assert record.audit_verdict is None
