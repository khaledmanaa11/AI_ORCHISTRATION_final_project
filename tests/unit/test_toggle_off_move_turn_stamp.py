"""Deferred item #13: the toggle-off MOVE envelope's turn stamp (08-05).

THE DEFECT, as 05-14 measured it on a full 16-turn `commit_reveal=False` game:

    police (first mover):  moves=[0..15]  hints=[0..15]
    thief  (second mover): moves=[1..16]  hints=[0..14]

Turn 16 was never played by anybody. `turn_commit_send.send_move_only` read
`ctx.state.turn`, and on the SECOND mover `take_my_turn`'s own
`record_action` + `maybe_resolve` had already advanced N -> N+1 by the time
that read happened -- so the MOVE envelope claimed a turn one into the future
(rule 20 evidence integrity). 05-14 fixed the identical defect for the HINT
channel one line away, and deliberately left this door open because the repair
changes a public entry point's signature.

WHY IT IS DRIVEN THROUGH `take_my_turn` AND NOT THROUGH `send_move_only`.
The bug is not in the sender; the sender faithfully reports the number it is
given. It is in WHICH number reaches it, and that is decided by the ordering
of `record_action`/`maybe_resolve` against the send. A test that called
`send_move_only` directly would pass both before and after the fix.
"""

from __future__ import annotations

from pursuit.network import turn_actions
from pursuit.network.envelope import EnvelopeKey, MessageType
from pursuit.network.state_machine import State
from tests.unit._fakes_agent import make_ctx

#: The joint turn this test plays. Any value works; naming it stops the
#: assertion from being read off whatever the code happened to produce.
PLAYED_TURN = 0


def move_pushes(ctx) -> list[dict]:
    """Every MOVE envelope this side actually put on the wire."""
    return [
        args for name, args in ctx.runtime.client().calls
        if name == "receive_move"
    ]


async def _play_one_second_mover_turn(tmp_path, default_params, network_params):
    """Drive ONE toggle-off turn in which THIS side moves second.

    "Second" is expressed the way production expresses it: the opponent's
    action is already in the joint-turn buffer when `take_my_turn` runs, so
    this side's own `record_action` fills the second slot and `maybe_resolve`
    fires inside the same call -- exactly the ordering 05-14 described.
    """
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police",
        label="toggle-off-stamp", initial_state=State.MY_TURN,
    )
    assert not ctx.security.commit_reveal, "this case is about the toggle-OFF path"
    assert ctx.state.turn == PLAYED_TURN
    ctx.pending_thief_move = ctx.state.thief  # the opponent has already acted
    await turn_actions.take_my_turn(ctx)
    return ctx


async def test_the_second_movers_move_is_stamped_with_the_turn_it_played(
    tmp_path, default_params, network_params,
):
    ctx = await _play_one_second_mover_turn(tmp_path, default_params, network_params)
    pushes = move_pushes(ctx)
    assert len(pushes) == 1, f"expected exactly one MOVE push, got {pushes}"
    assert pushes[0][EnvelopeKey.TURN] == PLAYED_TURN, (
        f"the MOVE envelope claims turn {pushes[0][EnvelopeKey.TURN]} for the action "
        f"played on turn {PLAYED_TURN} -- deferred item #13"
    )


async def test_the_joint_turn_really_did_resolve_inside_that_call(
    tmp_path, default_params, network_params,
):
    """ANTI-VACUITY. If `maybe_resolve` did not fire, `ctx.state.turn` never
    advanced, the buggy read and the correct one coincide, and the assertion
    above would pass against the unfixed code. This case proves the two values
    genuinely differ in the window under test."""
    ctx = await _play_one_second_mover_turn(tmp_path, default_params, network_params)
    assert ctx.state.turn == PLAYED_TURN + 1, (
        "the joint turn did not resolve, so this test is not exercising the defect"
    )


async def test_the_logged_move_record_carries_the_same_turn_as_the_wire(
    tmp_path, default_params, network_params,
):
    """The log record and the envelope must not disagree with each other: the
    replay viewer joins on the record's turn and re-hashes the envelope."""
    import json

    ctx = await _play_one_second_mover_turn(tmp_path, default_params, network_params)
    sent = [
        json.loads(line) for line in ctx.log_path.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("event") == "message_sent"
    ]
    moves = [
        record for record in sent
        if record["envelope"][EnvelopeKey.TYPE] == MessageType.MOVE.value
    ]
    assert len(moves) == 1, f"expected one logged MOVE, got {moves}"
    assert moves[0]["turn"] == PLAYED_TURN
    assert moves[0]["envelope"][EnvelopeKey.TURN] == PLAYED_TURN
