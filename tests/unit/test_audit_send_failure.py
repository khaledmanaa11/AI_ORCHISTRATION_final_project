"""05-UAT.md G1: a failed OUTBOUND final-reveal push is evidence about US,
never an accusation against the peer (rules 16/22).

The 2026-08-13 two-machine round proved the point on real hardware: machine
B recorded `technical_win{opponent_unresponsive, retries_attempted: 4}` at
the very moment machine A had already received AND processed B's push --
A's own `audit_verdict.peer_audit` carries B's five ledger hashes
byte-for-byte. Our own send failing is not proof the peer was silent.

Case 1 is the fix. Cases 2-4 are the paired fairness controls this repo
requires whenever a sanction is relaxed (the established
`test_audit_turn_binding.py::test_an_honest_peer_is_still_matched`
pattern): every genuine sanction must still fire, unchanged.

Case 5 (05-13, G6) is case 1's MIRROR on the receive leg, and it is
deliberately filed here rather than beside the watchdog cases so that all
three controls sit in the same file as the relaxation they constrain --
case 3 in particular, which is exactly the discrimination case 5 owes.
"""

from __future__ import annotations

import json

from pursuit.constants import Outcome
from pursuit.network.agent_audit_wiring import run_final_audit
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.security import commit_pack
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import FakeClient, make_ctx

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")
_STATE = {"game_id": "g", "turn": 1, "role": "thief",
          "position": {"row": 2, "col": 3}, "barriers_remaining": 0}
_ACTION = {"move": {"kind": "move", "direction": "north"}, "barrier": None}


def _events(ctx) -> list[dict]:
    text = ctx.log_path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _kinds(ctx) -> list[str]:
    return [event["event"] for event in _events(ctx)]


def _seed_final_reveal(ctx, records: list[dict]) -> None:
    """Queue the opponent's own FINAL_REVEAL so the RECEIVE half succeeds --
    the point of case 1 is that a failed push no longer aborts the audit."""
    ctx.runtime.queue.put_nowait(
        Envelope(
            type=MessageType.FINAL_REVEAL, turn=ctx.state.turn, sender="thief",
            payload={"records": records},
        ),
    )


def _tampered_peer_turn(ctx) -> dict:
    """One honestly-committed turn we observed on the wire, plus the peer's
    own final-reveal entry for it with the payload MUTATED after the fact --
    D-67 tamper class (a), which must still fail the re-hash check."""
    h_commit, nonce = commit_pack.commit(_STATE, _ACTION, "truth")
    ctx.log_path.write_text(
        json.dumps({
            "game_uid": "g", "turn": 1, "event": "message_received", "sender": "thief",
            "timestamp": "t",
            "envelope": {"type": "commit", "turn": 1, "sender": "thief",
                         "payload": {"h_commit": h_commit}},
        }) + "\n",
        encoding="utf-8",
    )
    payload = commit_pack.build_commit_payload(
        state=_STATE, move=_ACTION, intent="lie", nonce=nonce,
    )
    return {"turn": 1, "h_commit": h_commit, "payload": payload}


async def test_a_failed_own_push_after_a_board_outcome_accuses_nobody(
    tmp_path, default_params, network_params,
):
    """THE FIX. Our push fails but the turn loop already produced a board
    outcome: record non-accusatory evidence about our own send, leave the
    board outcome standing, and STILL complete the audit."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="send-fail-with-outcome",
        security=_ON, client=FakeClient(fail=True), initial_state=State.GAME_OVER,
    )
    _seed_final_reveal(ctx, [])

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert outcome is not Outcome.TECHNICAL_LOSS
    kinds = _kinds(ctx)
    assert "audit_incomplete" in kinds
    assert "technical_win" not in kinds
    assert "game_over" not in kinds
    # The receive + audit steps still ran -- a failed own push no longer
    # aborts the audit, which is what left machine B with nothing at all.
    assert "audit_verdict" in kinds
    incomplete = next(e for e in _events(ctx) if e["event"] == "audit_incomplete")
    assert "own" in incomplete["reason"] and "opponent" not in incomplete["reason"]


async def test_a_failed_own_push_with_no_board_outcome_is_still_a_technical_loss(
    tmp_path, default_params, network_params,
):
    """CONTROL. No board outcome means the turn loop never resolved: there
    is nothing left standing, so the pre-existing sanction is correct."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="send-fail-no-outcome",
        security=_ON, client=FakeClient(fail=True), initial_state=State.GAME_OVER,
    )
    _seed_final_reveal(ctx, [])

    outcome = await run_final_audit(ctx, board_outcome=None)

    assert outcome is Outcome.TECHNICAL_LOSS
    assert "technical_win" in _kinds(ctx)


async def test_a_peer_that_withholds_its_own_nonces_is_still_a_technical_loss(
    tmp_path, default_params, network_params,
):
    """CONTROL, rule 36. Our push succeeds and the peer never publishes its
    nonces: that IS the peer's own act, and it still loses -- now with a
    corrected, durable game_over beside the verdict."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="recv-fail",
        security=_ON, initial_state=State.GAME_OVER,
    )

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert outcome is Outcome.TECHNICAL_LOSS
    assert "technical_win" in _kinds(ctx)
    assert _events(ctx)[-1]["event"] == "game_over"
    assert _events(ctx)[-1]["outcome"] == Outcome.TECHNICAL_LOSS.value


async def test_both_of_our_own_legs_failing_after_a_board_outcome_accuses_nobody(
    tmp_path, default_params, network_params,
):
    """CASE 5, the fix's MIRROR (05-13, 05-UAT.md G6). Our push failed AND
    our receive failed, with a board outcome standing: both of our own legs
    are demonstrably broken, so the peer may well have answered into a
    socket we could not reach. Contrast case 3, where the push LANDED --
    that is the whole discrimination, and it is why rule 36's sanction
    survives this relaxation."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="both-legs-fail",
        security=_ON, client=FakeClient(fail=True), initial_state=State.GAME_OVER,
    )

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert outcome is not Outcome.TECHNICAL_LOSS, "the board outcome did not stand"
    kinds = _kinds(ctx)
    assert "technical_win" not in kinds, "a peer that may have answered was accused"
    assert "game_over" not in kinds
    reasons = [e["reason"] for e in _events(ctx) if e["event"] == "audit_incomplete"]
    assert reasons == ["own_final_reveal_send_failed", "own_final_reveal_receive_failed"]
    # Both records name OUR OWN half of the exchange, never the peer's.
    assert all("own" in r and "opponent" not in r for r in reasons)
    # And it must NOT have fallen through to the audit: with peer_records
    # empty, every honest turn fails and TECHNICAL_LOSS re-enters through
    # the AUDIT_HASH_MISMATCH door.
    assert "audit_verdict" not in kinds


async def test_a_genuine_hash_mismatch_is_still_a_technical_loss(
    tmp_path, default_params, network_params,
):
    """CONTROL, D-67. A board outcome exists and our push succeeds, but the
    peer's revealed payload does not re-hash to the H_commit we watched it
    send: AUDIT_HASH_MISMATCH still wins, with a corrected game_over."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="hash-mismatch",
        security=_ON, initial_state=State.GAME_OVER,
    )
    _seed_final_reveal(ctx, [_tampered_peer_turn(ctx)])

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert outcome is Outcome.TECHNICAL_LOSS
    verdict = next(e for e in _events(ctx) if e["event"] == "technical_win")
    assert verdict["reason"] == "audit_hash_mismatch"
    assert _events(ctx)[-1]["event"] == "game_over"
    assert _events(ctx)[-1]["outcome"] == Outcome.TECHNICAL_LOSS.value
