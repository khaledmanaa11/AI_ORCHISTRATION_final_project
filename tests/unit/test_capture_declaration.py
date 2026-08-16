"""capture_declaration.py: rule 21's Capture Claim on the wire (05-15, G10).

The property under test is rule 22's, and it is a property of the WIRING,
not of a string: the declaration must fire on exactly the resolved capture
and on nothing else, and it must carry the same outcome the ledger record
carries. Every case here drives real code -- no mock of the module under
test. Receive-side cases live in test_agent_audit_exchange.py.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json

import pytest
from fastmcp.exceptions import ToolError

from pursuit.constants import Outcome
from pursuit.network import capture_declaration, orchestrator
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from tests.unit._fakes_agent import FakeClient, make_ctx


class _RejectingClient(FakeClient):
    """A peer whose `game_over` tool body REJECTS our declaration --
    `deadline.call_with_retry` re-raises ToolError unretried by design."""

    async def call_tool(self, name, args, **kwargs):
        self.calls.append((name, args))
        raise ToolError("peer rejected the declaration")


def _events(ctx) -> list[dict]:
    if not ctx.log_path.exists():
        return []
    text = ctx.log_path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


async def test_the_cop_declares_the_capture_through_the_existing_game_over_tool(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="declare")

    await capture_declaration.send_capture_declaration(ctx, turn=4, outcome=Outcome.CAPTURE)

    calls = ctx.runtime.client().calls
    assert len(calls) == 1
    name, args = calls[0]
    assert name == "game_over"  # the Phase-2 tool, not a new one
    assert args[EnvelopeKey.TURN] == 4
    assert args[EnvelopeKey.SENDER] == "police"
    assert args[EnvelopeKey.PAYLOAD][capture_declaration.OUTCOME_KEY] == Outcome.CAPTURE.value
    assert EnvelopeKey.TYPE not in args  # the tool name supplies the type


def test_the_declaration_is_the_shipped_envelope_and_decodes_as_one(
    tmp_path, default_params, network_params,
):
    """No new MessageType and no reshaped envelope: what we build must
    survive the peer's own `Envelope.from_dict` fail-loud decode."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="shape")
    envelope = capture_declaration.build_declaration(ctx, turn=2, outcome=Outcome.CAPTURE)

    assert envelope.type is MessageType.GAME_OVER
    assert Envelope.from_dict(envelope.to_dict()) == envelope


async def test_the_thief_never_declares_a_capture(tmp_path, default_params, network_params):
    """Book Sec3.5 p.22 Table 2 gives the Claim to the side that LANDS on
    the other. The thief has nothing to declare."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="thief", label="thief-quiet")

    await capture_declaration.send_capture_declaration(ctx, turn=4, outcome=Outcome.CAPTURE)

    assert ctx.runtime.client().calls == []
    assert not capture_declaration.declares_capture(ctx, Outcome.CAPTURE)


@pytest.mark.parametrize(
    "outcome", [Outcome.SURVIVAL, Outcome.TIE, Outcome.TECHNICAL_LOSS, None],
)
async def test_no_declaration_for_any_outcome_that_is_not_a_capture(
    tmp_path, default_params, network_params, outcome,
):
    """RULE 22, the disqualification rule: "Make a false capture
    declaration" -> immediate disqualification, zero score, no appeal. The
    cheapest way never to make one is to have exactly one branch that can
    send at all. The CAPTURE control lives in the first test above, so this
    parametrisation cannot pass by the sender being broken outright."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label=f"no-{outcome}")

    await capture_declaration.send_capture_declaration(ctx, turn=4, outcome=outcome)

    assert ctx.runtime.client().calls == []
    assert not capture_declaration.declares_capture(ctx, outcome)


async def test_a_silent_peer_costs_the_declaration_and_nothing_else(
    tmp_path, default_params, network_params,
):
    """Best-effort by contract: the capture is already resolved and already
    ledgered, so a declaration that cannot land must not accuse anyone. The
    log must also not CLAIM a declaration that never went out."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="silent-peer",
        client=FakeClient(fail=True),
    )

    result = await capture_declaration.send_capture_declaration(
        ctx, turn=4, outcome=Outcome.CAPTURE,
    )

    assert result is None
    assert not [e for e in _events(ctx) if e["event"] == "message_sent"]
    assert not [e for e in _events(ctx) if e["event"] == "technical_win"]


async def test_a_peer_that_rejects_the_declaration_never_ends_the_game(
    tmp_path, default_params, network_params,
):
    """A ToolError here must not convert a resolved capture into a loss --
    unlike the turn loop, there is nothing left to play for."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="rejecting",
        client=_RejectingClient(),
    )

    await capture_declaration.send_capture_declaration(ctx, turn=4, outcome=Outcome.CAPTURE)

    assert ctx.runtime.client().calls  # it really was attempted
    assert not [e for e in _events(ctx) if e["event"] == "message_sent"]


async def test_run_turn_loop_declares_the_very_outcome_it_ledgers(
    tmp_path, default_params, network_params,
):
    """THE rule-22 property, measured end to end on a real resolved capture
    (same scenario as test_orchestrator_loop's own capture case): the
    transmitted claim and the audited record are read off ONE `Outcome`
    object in two adjacent statements, so they cannot disagree."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="loop-capture")
    ctx.state = dataclasses.replace(ctx.state, cop=(2, 2), thief=(2, 3))
    ctx.choose_move = lambda state, agent, params: state.thief
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.MOVE, turn=1, sender="thief", payload={"x": 2, "y": 3}).to_dict()
    )

    outcome = await asyncio.wait_for(orchestrator.run_turn_loop(ctx), timeout=5)

    assert outcome is Outcome.CAPTURE
    declared = [c for c in ctx.runtime.client().calls if c[0] == "game_over"]
    assert len(declared) == 1
    ledgered = [e for e in _events(ctx) if e["event"] == "game_over"]
    assert len(ledgered) == 1
    claim = declared[0][1][EnvelopeKey.PAYLOAD][capture_declaration.OUTCOME_KEY]
    assert claim == ledgered[0]["outcome"] == outcome.value
    assert declared[0][1][EnvelopeKey.TURN] == ledgered[0]["turn"]


async def test_a_loop_that_ends_without_a_capture_declares_nothing(
    tmp_path, default_params, network_params,
):
    """The paired control for the case above: a silent opponent ends the
    same loop on TECHNICAL_LOSS, and no `game_over` envelope leaves."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="loop-silent")

    outcome = await asyncio.wait_for(orchestrator.run_turn_loop(ctx), timeout=5)

    assert outcome is Outcome.TECHNICAL_LOSS
    assert [c for c in ctx.runtime.client().calls if c[0] == "game_over"] == []
