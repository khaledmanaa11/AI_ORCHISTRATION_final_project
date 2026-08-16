"""Deferred item #10, SEND side: the turn loop's four outgoing ladders.

Split from `test_turn_loop_watchdog.py` at the 150-code-line gate (Segal
Table 5) -- split, never compressed. That file keeps the WAIT legs and the
two NET-07 controls; this one keeps every leg that pushes.

WHY THE SEND LEGS ARE IN SCOPE AT ALL, and this is a measurement rather than
an argument. Deferred item #10 was written about the four `wait_for_*` legs.
But against a peer whose socket accepts TCP and never answers, OUR PUSH
STALLS FIRST -- `turn_commit_send.push` is what sends the COMMIT that the
wait leg is waiting for a reply to. Measured before the fix, on the same
injected clock as the wait legs:

    push attempts=2 elapsed=70.0s touches=0 checks=[False, True] verdict=None

So marking only the waits would have left the turn loop dying at exactly the
same t=60 s, one door earlier -- `os._exit(1)` mid-game, our nonces ledgered
and no FINAL_REVEAL sent (rule 36 against US). All four push legs carried the
identical post-ladder-only touch and all four are marked now.

`send_hint` and `send_capture_declaration` never return a verdict -- both are
best-effort by contract -- so what they owe here is only that the ladder ran
MARKED and the process survived it. `assert_ladder_survived` is the shared
five-fact block; see its docstring for which assertion refutes which wrong
fix.

Zero real sleeps; every bound is read from `config/police/network.json`.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import (
    capture_declaration,
    orchestrator,
    turn_buffer,
    turn_commit_send,
)
from pursuit.network.envelope import MessageType
from pursuit.network.hint_payload import Intent
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_wait import H_COMMIT_KEY
from tests.unit._fakes_watchdog import StalledClient, attempt_cost
from tests.unit._turn_loop_fixtures import assert_ladder_survived, lethal, turn_ctx


def _stalled(tmp_path, default_params, network_params, label):
    """A ctx whose peer accepts TCP and never answers, on the REAL ladder."""
    armed = lethal(network_params)
    client = StalledClient(armed, step=attempt_cost(network_params))
    ctx = turn_ctx(tmp_path, default_params, network_params, label, armed, client=client)
    return ctx, armed, client


async def test_a_stalled_peer_costs_the_commit_push_a_ladder_and_not_the_process(
    tmp_path, default_params, network_params,
):
    """`turn_commit_send.push` -- the COMMIT/ACK/REVEAL leg of D-58, and the
    FIRST thing a stalled peer stalls."""
    ctx, armed, client = _stalled(tmp_path, default_params, network_params, "t10-commit")

    verdict = await turn_commit_send.push(ctx, MessageType.COMMIT, 0, {H_COMMIT_KEY: "h"})

    assert_ladder_survived(armed, len(client.calls), network_params)
    assert verdict is not None, "no verdict -- the D-13 ladder never got to speak"


async def test_a_stalled_peer_costs_the_move_push_a_ladder_and_not_the_process(
    tmp_path, default_params, network_params,
):
    """`turn_commit_send.send_move_only` -- the toggle-off MOVE push, which
    turns an exhausted ladder into a recorded technical loss rather than a
    process death."""
    ctx, armed, client = _stalled(tmp_path, default_params, network_params, "t10-move-push")
    start = ctx.state.cop
    dest = orchestrator.first_legal_move(ctx.state, "cop", ctx.params)

    outcome = await turn_commit_send.send_move_only(ctx, State.MY_TURN, start, dest)

    assert_ladder_survived(armed, len(client.calls), network_params)
    assert outcome is Outcome.TECHNICAL_LOSS, "the exhausted ladder was never recorded"


async def test_a_stalled_peer_costs_the_hint_push_a_ladder_and_not_the_process(
    tmp_path, default_params, network_params,
):
    """`turn_buffer.send_hint` (D-47). Best-effort by contract -- a failed
    hint never ends the game -- so it returns nothing; what it owes is that
    its ladder is marked, because an UNMARKED best-effort ladder still gets
    `os._exit(1)` called on us."""
    ctx, armed, client = _stalled(tmp_path, default_params, network_params, "t10-hint")

    await turn_buffer.send_hint(ctx, 0, text="a hint", intent=Intent.TRUTH)

    assert_ladder_survived(armed, len(client.calls), network_params)
    assert ctx.log_path.exists() is False, "a failed push must not log message_sent"


async def test_a_stalled_peer_costs_the_capture_claim_a_ladder_and_not_the_process(
    tmp_path, default_params, network_params,
):
    """`capture_declaration.send_capture_declaration` (05-15, rule 21). It
    runs INSIDE `run_turn_loop`, where the watchdog stays armed until
    `agent_entrypoint:134` -- so an unmarked ladder here killed us BEFORE
    `run_final_audit` could publish our nonces (rule 36 against us)."""
    ctx, armed, client = _stalled(tmp_path, default_params, network_params, "t10-claim")

    await capture_declaration.send_capture_declaration(ctx, turn=0, outcome=Outcome.CAPTURE)

    assert_ladder_survived(armed, len(client.calls), network_params)
    assert ctx.log_path.exists() is False, "a failed push must not log message_sent"
