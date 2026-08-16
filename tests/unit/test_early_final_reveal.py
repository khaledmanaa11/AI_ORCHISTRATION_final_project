"""We manufacture the silence we then punish (05-17).

THE DEFECT. The four turn-loop `wait_for_*` legs pull through
`turn_commit_wait.next_protocol_message`, which buffers an interleaved HINT
and hands everything else to the caller; each leg then DROPS whatever it was
not waiting for as tolerated jitter -- `turn_commit_wait.py:176` says so in
its own words. A peer's FINAL_REVEAL arriving in that window is therefore
consumed off our own queue and thrown away. Our audit's receive leg then
waits for an envelope that has already been delivered and destroyed, burns
its whole `(retry_count + 1) x response_timeout` ladder, and -- because our
OWN push landed -- takes the accusatory branch at `agent_audit_wiring.py:97`
and declares `OPPONENT_UNRESPONSIVE` against a peer that DEMONSTRABLY DID
PUSH. That is a false declaration (rules 16/22) and it costs us the
0-point technical loss as well.

THE PREMISE IS WHAT BREAKS, NOT THE INFERENCE. `agent_audit_wiring.py:90-93`
reasons that a push which LANDED proves the peer's server accepted our
envelope, so silence afterwards is the peer's own act. That is sound -- when
the silence is theirs. Here it is OURS. The fix restores the premise; it does
not soften rule 36, and
`test_a_genuinely_silent_peer_is_still_declared_unresponsive` is the control
that says so.

REACHABILITY, stated honestly. Two copies of THIS codebase serialise their
own pushes (each `await`s its tool call, and `tools._accept` enqueues before
answering), so a clean loopback game never reorders. The ordering needs a
perturbation -- and every one of them is ordinary league-day weather: a
league peer is a SECOND, INDEPENDENT implementation free to publish its
ledger the moment it resolves; and inside this codebase, one lost or
ladder-exhausted message makes the peer abort its turn loop and run its own
final audit while we are still waiting for the message it will now never
send (`test_the_buffered_reveal_survives_our_own_leg_timing_out`).
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network.agent_audit_wiring import run_final_audit
from pursuit.network.envelope import MessageType
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_wait import wait_for_reveal_capturing_early_ack
from tests.unit._early_reveal_fixtures import (
    ON,
    audit_verdicts,
    final_reveal,
    honest_peer_turn,
    in_game_reveal,
    kinds,
)
from tests.unit._fakes_agent import make_ctx

_OUR_H_COMMIT = "our-own-commit-hash"


async def test_a_peer_that_pushes_its_final_reveal_early_is_not_declared_unresponsive(
    tmp_path, default_params, network_params,
):
    """THE REPRODUCTION. The peer finishes its turn loop first and pushes its
    ledger; our still-running leg then gets the in-game REVEAL it was waiting
    for, so our own turn loop completes normally and a board outcome stands.
    Nothing anywhere went wrong, and pre-fix we declared the peer
    unresponsive anyway.

    Measured at HEAD (05-17 Task 1), verbatim:

        TURN LOOP LEG: queued=2 -> returned type='reveal' verdict=None
                       queue_left=0        <- the FINAL_REVEAL is GONE
        AUDIT: our push landed? 1 call(s) = ['receive_final_reveal']
        AUDIT OUTCOME: <Outcome.TECHNICAL_LOSS: 'technical_loss'>
        {"event": "technical_win", "reason": "opponent_unresponsive",
         "retries_attempted": 2, "timeout_seconds": 0.05, ...}
        {"event": "game_over", "outcome": "technical_loss", ...}
        audit_verdict: NEVER WRITTEN

    `retries_attempted: 2` is `make_ctx`'s fast test ladder; at the shipped
    Table-19 values the same exhaustion is 4 attempts and 135 s. The ladder
    LENGTH is not the defect and no number here is touched by the fix.

    Asserted as ONE TUPLE deliberately (05-15's shadowed-assertion finding):
    written as separate statements the outcome assertion fires first and the
    accusation count is never reached, so the half that names the false
    declaration could not fail."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="early-reveal",
        security=ON, initial_state=State.WAIT_OPPONENT,
    )
    peer_ledger = [honest_peer_turn(ctx)]
    ctx.runtime.queue.put_nowait(final_reveal(ctx, peer_ledger))
    ctx.runtime.queue.put_nowait(in_game_reveal(ctx))

    envelope, leg_verdict = await wait_for_reveal_capturing_early_ack(ctx, _OUR_H_COMMIT)
    assert (envelope.type, leg_verdict) == (MessageType.REVEAL, None), "the turn loop stalled"

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert (outcome, kinds(ctx).count("technical_win")) == (None, 0)
    # And the peer's ledger did not merely fail to trigger an accusation --
    # it was AUDITED, over the real hashes of the turn we watched it play.
    assert [(v["matched"], len(v["peer_audit"])) for v in audit_verdicts(ctx)] == [(True, 1)]
