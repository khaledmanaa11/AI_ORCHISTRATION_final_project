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

from pursuit.network import orchestrator
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.sdk import engine
from tests.unit._fakes_agent import make_ctx

_ORCHESTRATOR_SRC = Path("src/pursuit/network/orchestrator.py").read_text(encoding="utf-8")


def test_first_legal_move_is_an_algorithm(default_params):
    """Deterministic, algorithmic, no randomness, no LLM (rule 25)."""
    state = engine.make_state(default_params)
    dest = orchestrator.first_legal_move(state, "cop", default_params)
    assert dest in engine.legal_moves(state, "cop", default_params)
    assert orchestrator.first_legal_move(state, "cop", default_params) == dest


def test_apply_role_move_dispatches_to_the_sdk_only(default_params):
    """Pins the dispatch: cop -> apply_cop_action (no turn tick), thief ->
    apply_thief_move (turn ticks) -- QUAL-01, nothing computed here."""
    state = engine.make_state(default_params)

    cop_dest = engine.legal_moves(state, "cop", default_params)[0]
    new_state, _outcome = orchestrator.apply_role_move(state, "police", cop_dest, default_params)
    assert new_state.cop == cop_dest
    assert new_state.turn == state.turn

    thief_dest = engine.legal_moves(state, "thief", default_params)[0]
    new_state2, _outcome2 = orchestrator.apply_role_move(
        state, "thief", thief_dest, default_params
    )
    assert new_state2.thief == thief_dest
    assert new_state2.turn == state.turn + 1


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

    assert len(ctx.runtime.client().calls) == 1
    name, args = ctx.runtime.client().calls[0]
    assert name == "receive_move"
    # receive_move's real wire signature carries no `type` key (the tool name
    # names the kind); rebuild it the same way agent_lifecycle's responder
    # does before decoding, per design note 12.
    rebuilt = {**args, "type": MessageType.MOVE.value}
    sent = Envelope.from_dict(rebuilt)
    assert sent.type is MessageType.MOVE
    cop_dest = engine.legal_moves(engine.make_state(default_params), "cop", default_params)[0]
    assert sent.payload == {"x": cop_dest[0], "y": cop_dest[1]}

    assert ctx.state.thief == thief_dest
    assert ctx.watchdog.touches >= 2
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
    for line in lines:
        json.loads(line)


def test_orchestrator_never_polls():
    """D-07 static guard: push-only, never a polling loop."""
    assert not re.search(r"while\s+True", _ORCHESTRATOR_SRC)
    for banned in ("def poll", "def check_opponent", "def has_moved"):
        assert banned not in _ORCHESTRATOR_SRC
