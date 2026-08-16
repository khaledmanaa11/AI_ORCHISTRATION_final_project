"""Where the early FINAL_REVEAL goes, and what it costs (05-17).

Split from `test_early_final_reveal.py` at the 150-code-line gate (Segal
Table 5) along a real seam: that file holds the two ACCUSATION-shaped cases
-- the reproduction and rule 36's counter-control -- and this one holds the
routing mechanism they both stand on. Split, never compressed; no assertion
was shortened to fit, and both files share `_early_reveal_fixtures.py`.

Each case here refutes a specific wrong fix by construction, and each of
those wrong fixes was RUN rather than reasoned about (05-13/05-14/05-15 each
recorded the same lesson). The counts are in 05-17-SUMMARY.md.

No `parametrize` here either -- see the sibling's note on the silent-SKIP
trap.
"""

from __future__ import annotations

from pursuit.network.agent_audit_exchange import receive_final_reveal
from pursuit.network.envelope import MessageType
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_wait import (
    wait_for_opponent_commit,
    wait_for_reveal_capturing_early_ack,
)
from pursuit.network.verdict import TechnicalWinReason
from tests.unit._early_reveal_fixtures import (
    ON,
    CountingQueue,
    final_reveal,
    honest_peer_turn,
    in_game_reveal,
    peer_commit,
)
from tests.unit._fakes_agent import make_ctx

_OUR_H_COMMIT = "our-own-commit-hash"
_PEER_H_COMMIT = "peer-commit-hash"
_TURN = 0


async def test_a_duplicate_final_reveal_neither_double_counts_nor_re_drives_the_audit(
    tmp_path, default_params, network_params,
):
    """(c). The two copies carry DIFFERENT ledgers ON PURPOSE: sending the
    same bytes twice cannot tell first-wins from last-wins, so a probe
    built that way would pass against either rule and pin neither.

    First-wins is the rule. A re-send is either a transport retry (identical
    -- nothing to prefer) or a peer revising what it published after seeing
    ours, and rule 36 is about what a peer published. The second call to the
    receive leg is the "no re-drive" half: one published ledger drives AT
    MOST ONE audit, which is what `take_final_reveal` consuming rather than
    peeking buys."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="duplicate",
        security=ON, initial_state=State.WAIT_OPPONENT,
    )
    peer_ledger = [honest_peer_turn(ctx)]
    ctx.runtime.queue.put_nowait(final_reveal(ctx, peer_ledger))
    ctx.runtime.queue.put_nowait(final_reveal(ctx, []))
    ctx.runtime.queue.put_nowait(in_game_reveal(ctx))

    await wait_for_reveal_capturing_early_ack(ctx, _OUR_H_COMMIT)
    records, verdict = await receive_final_reveal(ctx)

    assert (records, verdict) == (peer_ledger, None)
    again_records, again_verdict = await receive_final_reveal(ctx)
    assert (again_records, again_verdict.reason) == (
        [], TechnicalWinReason.OPPONENT_UNRESPONSIVE,
    )


async def test_every_wait_leg_buffers_it_because_the_pull_primitive_does(
    tmp_path, default_params, network_params,
):
    """The routing lives in ONE place -- `next_protocol_message`, which all
    four `wait_for_*` legs pull through -- so it is pinned here on a SECOND
    leg, and deliberately on `wait_for_opponent_commit`: that is the leg
    whose own source comment ("a duplicate/unexpected arrival here is
    tolerated jitter -- dropped") named the drop this plan is about.

    A fix applied leg-by-leg instead of at the primitive passes the
    reproduction and fails here."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="second-leg",
        security=ON, initial_state=State.WAIT_OPPONENT,
    )
    peer_ledger = [honest_peer_turn(ctx)]
    ctx.runtime.queue.put_nowait(final_reveal(ctx, peer_ledger))
    ctx.runtime.queue.put_nowait(peer_commit(ctx, _PEER_H_COMMIT))

    opponent_h, verdict = await wait_for_opponent_commit(ctx, State.WAIT_OPPONENT, _TURN)

    buffered = ctx.commit_state.early_final_reveal
    assert (opponent_h, verdict, getattr(buffered, "type", None)) == (
        _PEER_H_COMMIT, None, MessageType.FINAL_REVEAL,
    )


async def test_an_early_ledger_short_circuits_the_ladder_instead_of_waiting_it_out(
    tmp_path, default_params, network_params,
):
    """The wrong fix this one exists to refute: buffer the reveal, but
    consult the buffer only AFTER the receive ladder has run. That returns
    the same records, accuses nobody, and passes every other assertion in
    this corridor -- while costing the audit its whole
    `(retry_count + 1) x response_timeout`. At the shipped Table-19 values
    that is 135 s against a 60 s `watchdog_threshold`, which is deferred
    item #10's arithmetic and a real risk of dying before the verdict is
    written.

    Zero pulls is the whole difference, and it is only visible by counting
    them. The count is taken as a DELTA across the audit alone, so the turn
    loop's own pulls -- which must happen -- cannot mask a regression."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="short-circuit",
        security=ON, initial_state=State.WAIT_OPPONENT,
    )
    ctx.runtime.queue = CountingQueue()
    peer_ledger = [honest_peer_turn(ctx)]
    ctx.runtime.queue.put_nowait(final_reveal(ctx, peer_ledger))
    ctx.runtime.queue.put_nowait(in_game_reveal(ctx))

    await wait_for_reveal_capturing_early_ack(ctx, _OUR_H_COMMIT)
    pulls_before_audit = ctx.runtime.queue.gets
    records, verdict = await receive_final_reveal(ctx)

    assert (records, verdict, ctx.runtime.queue.gets - pulls_before_audit) == (
        peer_ledger, None, 0,
    )
    assert pulls_before_audit > 0, "the turn loop pulled nothing -- the counter is not wired"
