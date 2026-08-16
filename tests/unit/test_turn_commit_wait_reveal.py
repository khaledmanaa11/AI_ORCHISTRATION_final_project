"""The shared tail leg's own ACK-capture contract (05-18).

The test module for `src/pursuit/network/turn_commit_wait_reveal.py`, which
05-18 split out of `turn_commit_wait.py` when the police branch of
`turn_commit.await_and_respond` was pointed at that leg instead of at a bare,
type-blind pull (deferred item #18). Its FINAL_REVEAL routing is pinned by
`test_early_reveal_routing.py`; what lives here is the half the signature
change touched -- `h_commit: str` became `h_commit: str | None`.

WRITTEN BECAUSE THE GUARD WAS UNPINNED, and that is the whole reason to keep
this file. `h_commit is not None` was added alongside the signature and
documented as load-bearing; deleting it left ALL 1538 tests green. A guard no
test defends is a guard the next refactor removes.
"""

from __future__ import annotations

from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.orchestrator import opponent_role
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_wait import H_COMMIT_KEY
from pursuit.network.turn_commit_wait_reveal import wait_for_reveal_capturing_early_ack
from tests.unit._early_reveal_fixtures import ON, in_game_reveal
from tests.unit._fakes_agent import make_ctx

_OUR_H_COMMIT = "our-own-commit-hash"
_TURN = 0


def _ack(ctx, payload: dict) -> Envelope:
    return Envelope(
        type=MessageType.ACK, turn=_TURN, sender=opponent_role(ctx.role), payload=payload,
    )


async def test_an_ack_that_names_nothing_is_never_read_as_naming_our_own_commit(
    tmp_path, default_params, network_params,
):
    """THE TRAP IS `dict.get` RETURNING None. Once the initiator passes
    `h_commit=None` -- it holds no outstanding commit, because `initiate`
    already collected this turn's ACK inside `wait_for_ack_and_commit` -- an
    ACK carrying NO `h_commit` key makes the comparison
    `envelope.payload.get(H_COMMIT_KEY) == h_commit` read `None == None`, i.e.
    True. A peer's contentless ACK would then set this side's
    `own_ack_received`.

    That flag is inert on the police role today, and that is precisely what
    makes the hole worth pinning rather than shrugging at: nothing anywhere
    would report it until some later change reads the flag on that path, at
    which point the cause is three plans in the past.

    BOTH directions, each asserted as one tuple so neither half shadows the
    other. The second is not decoration -- without it a guard hard-wired to
    False passes the first and pins nothing at all."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="ack-names-nothing",
        security=ON, initial_state=State.WAIT_OPPONENT,
    )
    ctx.runtime.queue.put_nowait(_ack(ctx, {}))
    ctx.runtime.queue.put_nowait(in_game_reveal(ctx))

    envelope, verdict = await wait_for_reveal_capturing_early_ack(ctx, None)

    assert (envelope.type, verdict, ctx.commit_state.own_ack_received) == (
        MessageType.REVEAL, None, False,
    )

    responder = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="ack-names-ours",
        security=ON, initial_state=State.WAIT_OPPONENT,
    )
    responder.runtime.queue.put_nowait(_ack(responder, {H_COMMIT_KEY: _OUR_H_COMMIT}))
    responder.runtime.queue.put_nowait(in_game_reveal(responder))

    envelope, verdict = await wait_for_reveal_capturing_early_ack(responder, _OUR_H_COMMIT)

    assert (envelope.type, verdict, responder.commit_state.own_ack_received) == (
        MessageType.REVEAL, None, True,
    )
