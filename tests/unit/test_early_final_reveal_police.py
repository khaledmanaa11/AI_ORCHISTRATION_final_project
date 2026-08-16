"""The INITIATOR reads an honest peer's ledger as an illegal move (05-18).

Split from `test_early_final_reveal.py`, which sits at 133/150 with no room
for a third corridor -- split, never compressed, and both files share
`_early_reveal_fixtures.py`. That file holds the RESPONDER (thief) cases
05-17 fixed; this one holds the INITIATOR (police) branch it did not touch.

THE DEFECT (deferred item #18). `turn_commit.await_and_respond` branches on
role. The police branch called the pull primitive BARE -- `return await
next_protocol_message(ctx)` -- with no type test at all, and handed whatever
came back to `turn_actions.await_opponent_turn` as if it were the opponent's
REVEAL. The four `wait_for_*` legs each check a type; this one alone did not.

MEASURED AT HEAD (`da45b55`), police role, queue [FINAL_REVEAL, REVEAL],
verbatim:

    await_and_respond (police) returned type = final_reveal   verdict = None
    await_opponent_turn outcome              = Outcome.TECHNICAL_LOSS
    technical_win reasons                    = ['payload must be a dict, got NoneType']
    queue left = 1        <- the REVEAL we were waiting for was never read

`decode_revealed_action` looks for a `move` sub-key, the peer's ledger
payload is `{"records": [...]}`, and `payload.get("move")` is None -- so an
honest peer's PUBLISHED LEDGER becomes our own 0-point technical loss and a
false declaration under rules 16/22, reachable in a league game.

WHAT 05-17 DOES AND DOES NOT COVER. Its routing already puts the ledger
safely in `ctx.commit_state.early_final_reveal` on the way past, so the
AUDIT still matches (measured: `verdicts = [(True, 1)]` even at HEAD). This
is therefore about the GAME OUTCOME, not the audit: we lose a game we did
not lose. Reverting 05-17 changes neither the outcome nor the reason string.

NO `parametrize` in this file either -- an empty parameter set is a SILENT
pytest SKIP, and a control that skips is a control that cannot fail (the
sibling's own note).
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network.agent_audit_wiring import run_final_audit
from pursuit.network.state_machine import State
from pursuit.network.turn_actions import await_opponent_turn
from pursuit.network.turn_commit import await_and_respond
from pursuit.network.verdict import TechnicalWinReason
from tests.unit._early_reveal_fixtures import (
    ON,
    accusations,
    audit_verdicts,
    final_reveal,
    honest_peer_turn,
    in_game_reveal,
)
from tests.unit._fakes_agent import make_ctx
from tests.unit._turn_loop_fixtures import assert_ladder_survived, lethal, stall, turn_ctx

_UNRESPONSIVE = [TechnicalWinReason.OPPONENT_UNRESPONSIVE.value]


def _police(tmp_path, default_params, network_params, label):
    """The initiator mid-turn: it has already committed and revealed inside
    `turn_commit.initiate`, and only the opponent's REVEAL is left to await."""
    return make_ctx(
        tmp_path, default_params, network_params, role="police", label=label,
        security=ON, initial_state=State.WAIT_OPPONENT,
    )


def _matched(ctx) -> list[tuple]:
    """The audit's own verdict rows, over the REAL hashes `commit_pack` built.

    Never a bare "no accusation was written": `audit_peer_records([])` returns
    `[]` and `all_matched([])` is True, so a case asserting an empty
    accusation list alone passes over a ledger that never arrived (05-17's
    own vacuity finding, unchanged here)."""
    return [(v["matched"], len(v["peer_audit"])) for v in audit_verdicts(ctx)]


async def test_an_honest_peers_ledger_is_not_read_as_an_illegal_move(
    tmp_path, default_params, network_params,
):
    """THE REPRODUCTION, and the case deferred #18 measured. The peer
    finishes its own turn loop first and publishes its ledger; the REVEAL we
    are actually waiting for is right behind it on the same queue. Nothing
    anywhere went wrong -- and at HEAD we declared a technical loss against
    the peer with the reason string `'payload must be a dict, got NoneType'`.

    `outcome is None` is the whole point: the joint turn is not resolvable
    yet (the police half of this turn has not been recorded), so the correct
    result of this call is "carry on", not any verdict at all.

    Asserted as ONE TUPLE deliberately (05-15's shadowed-assertion finding):
    written as two statements the outcome assertion fires first and the
    reason string -- the half that names the false declaration -- is never
    reached."""
    ctx = _police(tmp_path, default_params, network_params, "police-initiator")
    peer_ledger = [honest_peer_turn(ctx)]
    ctx.runtime.queue.put_nowait(final_reveal(ctx, peer_ledger))
    ctx.runtime.queue.put_nowait(in_game_reveal(ctx))

    outcome = await await_opponent_turn(ctx)

    assert (outcome, accusations(ctx)) == (None, [])
    assert await run_final_audit(ctx, board_outcome=Outcome.CAPTURE) is None
    assert _matched(ctx) == [(True, 1)]


async def test_a_peer_that_publishes_and_then_stops_is_accused_of_what_it_did(
    tmp_path, default_params, network_params,
):
    """The same arrival with NO REVEAL behind it -- the peer really did stop
    playing. NET-06's in-game sanction is not softened by this plan: the
    ladder runs, exhausts, and returns D-13's own measured verdict.

    What changes is the NAME. `opponent_unresponsive` is a declaration this
    side can defend at audit -- it is what `call_with_retry` actually
    measured. `'payload must be a dict, got NoneType'` accuses the peer of
    sending a malformed MOVE, which is a claim about an envelope it never
    sent, and that is the rules-16/22 exposure.

    The ledger is still audited MATCHED, so a legitimate in-game sanction
    never grows a SECOND, false accusation on top of it (the initiator twin
    of 05-17's `test_the_buffered_reveal_survives_our_own_leg_timing_out`)."""
    ctx = _police(tmp_path, default_params, network_params, "police-stopped")
    peer_ledger = [honest_peer_turn(ctx)]
    ctx.runtime.queue.put_nowait(final_reveal(ctx, peer_ledger))

    outcome = await await_opponent_turn(ctx)

    assert (outcome, accusations(ctx)) == (Outcome.TECHNICAL_LOSS, _UNRESPONSIVE)
    assert await run_final_audit(ctx, board_outcome=outcome) is None
    assert (_matched(ctx), accusations(ctx)) == ([(True, 1)], _UNRESPONSIVE)


async def test_a_genuinely_silent_peer_is_still_declared_unresponsive(
    tmp_path, default_params, network_params,
):
    """RULE 36's COUNTER-CONTROL on the INITIATOR branch, and the assertion
    that decides whether this plan fixed anything or just stopped enforcing
    something. Nothing arrives at all: no ledger is buffered, because none
    was published. The sanction must fire exactly as it did before, with the
    SAME reason string.

    A fix that spares this peer has broken the game. That is not
    hypothetical -- the shape of this change is "stop reading a ledger as a
    move", never "stop punishing silence"."""
    ctx = _police(tmp_path, default_params, network_params, "police-silent")
    honest_peer_turn(ctx)
    assert ctx.commit_state.early_final_reveal is None, "nothing may be buffered here"

    outcome = await await_opponent_turn(ctx)

    assert (outcome, accusations(ctx)) == (Outcome.TECHNICAL_LOSS, _UNRESPONSIVE)


async def test_the_initiators_own_wait_marks_its_ladder_like_every_other_leg(
    tmp_path, default_params, network_params,
):
    """THE SECOND HALF OF THE SAME OMISSION (deferred item #10 / 05-16).
    `turn_commit.py:103` was ALSO the last production caller of
    `next_protocol_message` still taking `on_attempt=None`: 05-16 marked the
    other five turn-loop ladders and this branch was skipped for the same
    reason the type test was -- it is the one wait that does not read like a
    wait leg. So the initiator's whole `(retry_count + 1) x response_timeout`
    ladder ran UNMARKED against `watchdog_threshold`.

    MEASURED pre-fix on the injected clock at the shipped Table-19 values:
    the freeze fires at attempt 2 of 4, t=70.0 s, `touches=0`, and
    `ProcessKilledError` ends the call -- so `os._exit(1)` runs MID-GAME and
    the D-13 verdict due at t=140 s is never spoken. Post-fix the same
    ladder burns its full length, outlives the threshold, and still returns
    the verdict.

    It lives here rather than in `test_turn_loop_watchdog.py` because that
    module is at 135/150 and this is the sixth leg of its own subject; the
    harness is shared, not copied. NET-07 is preserved, not traded: that
    module's own frozen-loop and never-disarmed controls are unchanged."""
    armed = lethal(network_params)
    ctx = turn_ctx(tmp_path, default_params, network_params, "police-ladder", armed, security=ON)
    queue = stall(ctx, armed, network_params)

    envelope, verdict = await await_and_respond(ctx)

    assert_ladder_survived(armed, queue.pulls, network_params)
    assert envelope is None
    assert verdict is not None, "no verdict -- the D-13 ladder never got to speak"
    assert verdict.attempts == network_params.retry_count + 1
