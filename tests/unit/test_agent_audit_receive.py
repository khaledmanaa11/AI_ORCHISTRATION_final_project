"""agent_audit_exchange.receive_final_reveal: which envelope actually IS
the peer's Final Reveal (05-15, gap G10).

Split from `test_agent_audit_exchange.py` at the 150-code-line gate (Segal
Table 5) -- that file reached 152 once these four cases and their fixtures
landed. Split, never compressed, and along a real seam: the sibling holds
the coverage-closing branches of push/observed/record_technical_loss; this
file holds the receive leg's envelope-type contract.

THE DEFECT. `receive_final_reveal` used to read `records` off whatever
`next_protocol_message` returned first. Any other envelope arriving ahead
of the peer's FINAL_REVEAL therefore produced `records=[]` with
`verdict=None` -- byte-indistinguishable from the `{"records": []}` rule-36
evasion `security/audit.py` exists to punish -- so every played turn failed
`audit_state` as "absent from final reveal" and an HONEST peer was declared
a technical loss. That is a false accusation (rules 16/22). It was reachable
BEFORE 05-15 added a sender, because `game_over` is a registered tool on our
published league surface: any peer implementation calling it triggered it.
Measured pre-fix on a queue of [GAME_OVER, FINAL_REVEAL]: `records=[]`,
`verdict=None`, the peer's real ledger discarded.
"""

from __future__ import annotations

import json

from pursuit.constants import Outcome
from pursuit.network import agent_audit_exchange
from pursuit.network.envelope import Envelope, MessageType
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import make_ctx

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")

_PEER_LEDGER = [{"turn": 0, "role": "thief", "nonce": "abc", "h_commit": "deadbeef"}]


def _final_reveal() -> Envelope:
    return Envelope(
        type=MessageType.FINAL_REVEAL, turn=4, sender="thief",
        payload={"records": _PEER_LEDGER},
    )


def _capture_claim() -> Envelope:
    return Envelope(
        type=MessageType.GAME_OVER, turn=4, sender="thief",
        payload={"outcome": Outcome.CAPTURE.value, "reason": "declared"},
    )


async def test_a_capture_claim_ahead_of_the_final_reveal_does_not_swallow_it(
    tmp_path, default_params, network_params,
):
    """THE 05-15 case. Pre-fix this returned `([], None)` -- the peer's real
    ledger discarded, every played turn then failing `audit_state` as
    "absent from final reveal", and an honest peer accused of withholding
    its nonces (rule 36) on the strength of our OWN declaration arriving
    first.

    BOTH halves are asserted AS ONE TUPLE, and that is a self-audit
    correction, not a style choice. Written as two statements the `records`
    assertion fires first and SHADOWS the verdict one, so the verdict half
    was never actually exercised by either wrong fix -- it could not fail,
    which is the vacuous shape 05-13 and 05-14 each caught in their own
    controls. The verdict half is the one that refuses the *defensive*
    wrong fix (probe P8): return the peer's ledger correctly but attach an
    accusatory verdict because a stray envelope was seen on the way. That
    passes a records-only check and still loses the game to an honest peer
    through `run_final_audit`'s `recv_verdict is not None` branch."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="claim-first",
        security=_ON,
    )
    ctx.runtime.queue.put_nowait(_capture_claim())
    ctx.runtime.queue.put_nowait(_final_reveal())

    records, verdict = await agent_audit_exchange.receive_final_reveal(ctx)

    assert (records, verdict) == (_PEER_LEDGER, None)


async def test_the_peer_capture_claim_is_recorded_as_received_evidence(
    tmp_path, default_params, network_params,
):
    """Rule 21's declaration is only evidence if both sides' logs carry it."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="claim-logged",
        security=_ON,
    )
    ctx.runtime.queue.put_nowait(_capture_claim())
    ctx.runtime.queue.put_nowait(_final_reveal())

    await agent_audit_exchange.receive_final_reveal(ctx)

    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    received = [json.loads(line) for line in lines if line.strip()]
    claims = [
        r for r in received
        if r["event"] == "message_received"
        and r["envelope"]["type"] == MessageType.GAME_OVER.value
    ]
    assert len(claims) == 1
    assert claims[0]["envelope"]["payload"]["outcome"] == Outcome.CAPTURE.value


async def test_an_unexpected_non_declaration_envelope_is_still_dropped_as_jitter(
    tmp_path, default_params, network_params,
):
    """The drop POLICY is unchanged -- only the "what counts as the
    FINAL_REVEAL" question is. A stray ACK is skipped, logged nowhere, and
    costs nothing; the same tolerated-jitter rule the four `wait_for_*`
    legs in turn_commit_wait.py have always applied."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="stray-ack", security=_ON,
    )
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.ACK, turn=4, sender="thief", payload={"h_commit": "x"})
    )
    ctx.runtime.queue.put_nowait(_final_reveal())

    records, verdict = await agent_audit_exchange.receive_final_reveal(ctx)

    assert (records, verdict) == (_PEER_LEDGER, None)
    assert not ctx.log_path.exists()


async def test_a_final_reveal_arriving_first_is_unchanged(
    tmp_path, default_params, network_params,
):
    """The no-regression control: the ordinary path must be byte-equivalent
    to pre-05-15 -- one pull, records returned, nothing logged."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="normal", security=_ON,
    )
    ctx.runtime.queue.put_nowait(_final_reveal())

    records, verdict = await agent_audit_exchange.receive_final_reveal(ctx)

    assert (records, verdict) == (_PEER_LEDGER, None)
    assert not ctx.log_path.exists()
