"""Tests for the per-agent turn loop (pursuit.network.orchestrator).

House style: plain functions, hand-written fakes, no mock library (matching
test_state_machine.py). Shared fakes + the `make_ctx` assembly helper live in
tests/unit/_fakes_agent.py (QUAL-02 -- one copy, imported by every file that
needs them, including test_orchestrator_loop.py and test_agent_lifecycle*.py).

Timing rule (non-negotiable): every context built via make_ctx uses
response_timeout=0/retry_count=1/backoff_seconds=0/watchdog_threshold=0/
watchdog_poll_seconds=0, so every bounded wait in this suite resolves with
zero real wall-clock cost -- no test sleeps on a real threshold.
"""

import json
import re
from pathlib import Path

from pursuit.constants import Outcome
from pursuit.network import move_payload, orchestrator
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction
from tests.unit._fakes_agent import FakeClient, make_ctx

_ORCHESTRATOR_SRC = Path("src/pursuit/network/orchestrator.py").read_text(encoding="utf-8")


def test_first_legal_move_is_an_algorithm(default_params):
    """Deterministic, algorithmic, no randomness, no LLM (rule 25)."""
    state = engine.make_state(default_params)
    dest = orchestrator.first_legal_move(state, "cop", default_params)
    assert dest in engine.legal_moves(state, "cop", default_params)
    assert orchestrator.first_legal_move(state, "cop", default_params) == dest


async def test_take_my_turn_buffers_without_mutating_state_until_paired(
    tmp_path, default_params, network_params
):
    """QUAL-01, joint-turn edition (plan 03-14): replaces
    test_apply_role_move_dispatches_to_the_sdk_only -- apply_role_move is
    gone, and it applied a single side's move immediately, which is exactly
    the sequential defect RULES-RESOLUTION.md replaces. take_my_turn must
    buffer this agent's own move and push it over the wire, but MUST NOT
    apply it to ctx.state alone: state changes only once both sides' actions
    are known and engine.resolve_turn -- the sole authority (QUAL-01) -- has
    run."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="buffer")
    pre_state = ctx.state

    outcome = await orchestrator.take_my_turn(ctx)

    assert outcome is None
    assert ctx.state is pre_state  # nothing applied yet -- the pair is incomplete
    assert ctx.pending_cop_action is not None
    assert ctx.pending_thief_move is None


async def test_paired_turn_resolves_via_the_sdk_once(tmp_path, default_params, network_params):
    """Once both sides are buffered, the completing half applies both
    actions together through engine.resolve_turn -- the only place a joint
    turn is computed (QUAL-01) -- and the buffer is cleared for next turn."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="paired")
    thief_dest = engine.legal_moves(ctx.state, "thief", default_params)[0]
    incoming = Envelope(
        type=MessageType.MOVE, turn=1, sender="thief",
        payload={"x": thief_dest[0], "y": thief_dest[1]},
    )
    ctx.runtime.queue.put_nowait(incoming.to_dict())

    pre_state = ctx.state
    cop_dest = orchestrator.first_legal_move(pre_state, "cop", default_params)
    expected_state, expected_outcome = engine.resolve_turn(
        pre_state, CopAction(move=cop_dest), thief_dest, default_params, ctx.rules
    )

    await orchestrator.take_my_turn(ctx)
    outcome = await orchestrator.await_opponent_turn(ctx)

    assert ctx.state == expected_state
    assert outcome == expected_outcome
    assert ctx.pending_cop_action is None
    assert ctx.pending_thief_move is None


async def test_full_turn_cycle(tmp_path, default_params, network_params):
    """THE HAPPY PATH -- D-09 + D-07: HANDSHAKE -> MY_TURN -> WAIT_OPPONENT -> MY_TURN."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="happy")
    thief_dest = engine.legal_moves(ctx.state, "thief", default_params)[0]
    incoming = Envelope(
        type=MessageType.MOVE, turn=1, sender="thief",
        payload={"x": thief_dest[0], "y": thief_dest[1]},
    )
    ctx.runtime.queue.put_nowait(incoming.to_dict())

    await orchestrator.take_my_turn(ctx)
    assert ctx.machine.state is State.WAIT_OPPONENT

    await orchestrator.await_opponent_turn(ctx)
    assert ctx.machine.state is State.MY_TURN

    # Phase 4 (D-47): the move push plus the placeholder-hint push for the
    # same turn -- both calls really happened, the move first.
    assert len(ctx.runtime.client().calls) == 2
    name, args = ctx.runtime.client().calls[0]
    assert name == "receive_move"
    # receive_move's real wire signature carries no `type` key (the tool name
    # names the kind); rebuild it the same way agent_lifecycle's responder
    # does before decoding, per design note 12.
    rebuilt = {**args, "type": MessageType.MOVE.value}
    sent = Envelope.from_dict(rebuilt)
    assert sent.type is MessageType.MOVE
    # Phase 4 (D-53): the outgoing payload is a direction token, never a
    # coordinate (rule 27, LANG-02) -- move_payload.encode is the single
    # source of truth for that shape, never re-derived here.
    cop_start = engine.make_state(default_params).cop
    cop_dest = engine.legal_moves(engine.make_state(default_params), "cop", default_params)[0]
    assert sent.payload == move_payload.encode(cop_start, cop_dest, move_payload.ActionKind.MOVE)
    assert "x" not in sent.payload and "y" not in sent.payload

    hint_name, _hint_args = ctx.runtime.client().calls[1]
    assert hint_name == "receive_hint"

    assert ctx.state.thief == thief_dest
    assert ctx.watchdog.touches >= 2
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
    for line in lines:
        json.loads(line)


async def test_take_my_turn_reports_technical_loss_when_the_move_push_fails(
    tmp_path, default_params, network_params
):
    """Rules 16/22, D-13: the opponent never acking the move ends the game
    cleanly via Outcome.TECHNICAL_LOSS -- never raises, and the placeholder
    hint (D-47) is never attempted after a failed move push."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="push-fail",
        client=FakeClient(fail=True),
    )
    outcome = await orchestrator.take_my_turn(ctx)
    assert outcome is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER
    # retry_count=1 in make_ctx -> 2 failed move attempts, all "receive_move";
    # the hint push (D-47) is never attempted after the move push fails.
    assert all(name == "receive_move" for name, _args in ctx.runtime.client().calls)
    assert len(ctx.runtime.client().calls) == 2


def test_orchestrator_never_polls():
    """D-07 static guard: push-only, never a polling loop."""
    assert not re.search(r"while\s+True", _ORCHESTRATOR_SRC)
    for banned in ("def poll", "def check_opponent", "def has_moved"):
        assert banned not in _ORCHESTRATOR_SRC
