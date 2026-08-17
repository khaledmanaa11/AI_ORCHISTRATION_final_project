"""Case (d) and the scanner's own control -- split out of
`test_result_agreement.py` at the 150-code-line gate (the combined file
measured 167).

CASE (d) IS THE PEER-CONTROLLED BOUNDARY. `security/audit.py` states the rule
once for the whole project: a value the peer sent that cannot be parsed becomes
a NAMED verdict, never an exception. Six separate Phase-5 defects came from the
opposite habit, so each shape gets its own input here rather than one
representative.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.services.reporting.result_agreement import (
    AGREEMENT_UNPARSEABLE,
    NO_OWN_OUTCOME,
    build_agreement,
    peer_outcome_claims,
)
from tests.unit.result_agreement_fixtures import agreement_ctx, capture_payload, claim


def test_an_unrecognised_outcome_string_is_a_named_non_agreement(
    tmp_path, default_params, network_params
):
    """`Outcome("we won on style")` raises `ValueError`; this must not."""
    ctx = agreement_ctx(tmp_path, default_params, network_params, "d1")
    claim(ctx, capture_payload("we won on style"))

    record = build_agreement(ctx.log_path, own_outcome=Outcome.CAPTURE, audit_verdict=None)
    assert record.agreed is False
    assert record.reason == AGREEMENT_UNPARSEABLE
    assert record.peer_claim_present is True
    assert record.peer_outcome is None


def test_a_non_string_outcome_and_a_non_dict_payload_are_both_evidence(
    tmp_path, default_params, network_params
):
    """The two other shapes a peer can send. Neither raises; both are present
    claims we could not read, which is a different fact from silence."""
    shapes = (("d2", capture_payload(42)), ("d3", None))
    assert len(shapes) == 2, "a thinned shape table would loop over nothing"
    for label, payload in shapes:
        ctx = agreement_ctx(tmp_path, default_params, network_params, label)
        claim(ctx, payload)
        record = build_agreement(ctx.log_path, own_outcome=Outcome.CAPTURE, audit_verdict=None)
        assert record.peer_claim_present is True, label
        assert record.peer_outcome is None, label
        assert record.agreed is False, label
        assert record.reason == AGREEMENT_UNPARSEABLE, label


def test_the_last_claim_wins_when_a_peer_sends_two(
    tmp_path, default_params, network_params
):
    """Append-only evidence: the peer's last word is its position. Ordered so
    that reading the FIRST claim would produce the opposite verdict."""
    ctx = agreement_ctx(tmp_path, default_params, network_params, "last")
    claim(ctx, capture_payload(Outcome.SURVIVAL.value), turn=4)
    claim(ctx, capture_payload(Outcome.CAPTURE.value), turn=5)

    record = build_agreement(ctx.log_path, own_outcome=Outcome.CAPTURE, audit_verdict=None)
    assert record.peer_outcome == Outcome.CAPTURE.value
    assert record.agreed is True


def test_a_game_with_no_own_outcome_agrees_with_nothing(
    tmp_path, default_params, network_params
):
    """A handshake that never became a game has nothing of ours to compare --
    and a peer claim on its own is still not an agreement."""
    ctx = agreement_ctx(tmp_path, default_params, network_params, "own")
    claim(ctx, capture_payload(Outcome.CAPTURE.value))

    record = build_agreement(ctx.log_path, own_outcome=None, audit_verdict=None)
    assert record.agreed is None
    assert record.reason == NO_OWN_OUTCOME
    assert record.own_outcome is None
    assert record.peer_outcome == Outcome.CAPTURE.value


def test_the_claim_scanner_ignores_records_that_are_not_inbound_claims():
    """The scanner's own control: it finds the one real claim among four
    records that each fail a different guard, so an empty result elsewhere is a
    measurement rather than a scanner that matches nothing."""
    records = [
        {"event": "message_sent", "envelope": {"type": "game_over", "payload": {"outcome": "x"}}},
        {"event": "message_received", "envelope": "not a dict"},
        {"event": "message_received", "envelope": {"type": "hint", "payload": {}}},
        {"event": "message_received",
         "envelope": {"type": "game_over", "payload": {"outcome": "capture"}}},
    ]
    assert peer_outcome_claims(records) == ["capture"]
    assert peer_outcome_claims(records[:3]) == []
