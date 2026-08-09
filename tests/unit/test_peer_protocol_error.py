"""06-06 item 3: a peer whose tool body REJECTS our call must not kill us.

`deadline.call_with_retry` re-raises `ToolError` on purpose -- an
application-level rejection is not a transport failure and must never be
retried -- but nothing above it used to catch it. The process died by
traceback with `{state, move, intent, nonce}` already in our ledger and no
FINAL_REVEAL sent, so WE became the side that published no nonces (rule 36)
because of one line in THEIR code.

The first test drives a REAL FastMCP round trip against a hostile server, so
this proves the exception genuinely escapes the retry ladder rather than
assuming it from a mock.
"""

from __future__ import annotations

import json

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from pursuit.constants import Outcome
from pursuit.network.deadline import call_with_retry
from pursuit.network.verdict import TechnicalWinReason, peer_protocol_verdict
from pursuit.shared.network_config import NetworkParams


async def test_a_hostile_tool_body_really_does_escape_the_retry_ladder():
    """The premise, proven against real FastMCP -- not assumed."""
    mcp = FastMCP("hostile-peer")

    @mcp.tool
    async def receive_commit(turn: int, sender: str, payload: dict) -> dict:
        raise ValueError("hostile peer tool body raises")

    async with Client(mcp) as client:
        async def _call() -> object:
            return await client.call_tool(
                "receive_commit", {"turn": 1, "sender": "police", "payload": {}},
            )

        with pytest.raises(ToolError):
            await call_with_retry(_call, timeout=0.5, retries=2, backoff=0.0)


def test_peer_protocol_verdict_measures_its_evidence():
    """Rules 16/22: a technical-win declaration must carry measured
    evidence, never fabricated. elapsed_seconds is real; the retry fields
    are structural because no ladder governs a non-retryable rejection."""
    import time

    started = time.monotonic() - 0.25
    verdict = peer_protocol_verdict(ToolError("peer said no"), started)

    assert verdict.reason is TechnicalWinReason.PEER_PROTOCOL_ERROR
    assert verdict.elapsed_seconds >= 0.25, "elapsed must be genuinely measured"
    assert verdict.attempts == 1
    assert verdict.timeout_seconds == 0.0
    assert verdict.backoff_seconds == 0.0
    assert "peer said no" in verdict.last_error
    assert verdict.as_evidence()["reason"] == "peer_protocol_error"


def test_peer_protocol_error_is_distinct_from_unresponsive():
    """A peer that rejects promptly is NOT unresponsive, and the log must
    not claim it was."""
    assert TechnicalWinReason.PEER_PROTOCOL_ERROR is not TechnicalWinReason.OPPONENT_UNRESPONSIVE
    assert TechnicalWinReason.PEER_PROTOCOL_ERROR.value == "peer_protocol_error"


async def test_run_turn_loop_converts_a_peer_tool_error_into_a_clean_ending(tmp_path, monkeypatch):
    """The fix itself: the loop ends through the normal terminal path --
    a technical_win record AND a game_over record -- instead of a traceback,
    so the caller still reaches the Final-Reveal audit that publishes our
    ledger."""
    import sys

    from pursuit.network import orchestrator
    from pursuit.network.state_machine import State, TurnStateMachine
    from tests.unit._fakes_agent import FakeReporter

    log_path = tmp_path / "game.jsonl"

    class _Ctx:
        role = "police"
        game_uid = "g"

        def __init__(self):
            self.log_path = log_path
            self.machine = TurnStateMachine(FakeReporter(), initial=State.MY_TURN)
            self.state = type("S", (), {"turn": 3})()

    ctx = _Ctx()

    async def _hostile(_ctx):
        raise ToolError("peer rejected receive_commit")

    # run_turn_loop resolves take_my_turn/await_opponent_turn by a deferred
    # import of the real module, so the fake has to sit in sys.modules;
    # monkeypatch restores the real entry afterwards.
    monkeypatch.setitem(
        sys.modules,
        "pursuit.network.turn_actions",
        type("M", (), {"take_my_turn": _hostile, "await_opponent_turn": _hostile}),
    )

    outcome = await orchestrator.run_turn_loop(ctx)

    assert outcome is Outcome.TECHNICAL_LOSS, "a peer fault must not propagate as an exception"
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    kinds = [e["event"] for e in events]
    assert "technical_win" in kinds, "the declaration must be recorded as evidence"
    assert "game_over" in kinds, "the game must still close with an outcome record"
    reasons = [e.get("reason") for e in events if e["event"] == "technical_win"]
    assert reasons == ["peer_protocol_error"]


def test_network_params_still_loadable():
    """Guard: verdict.py gained an import; nothing in the config path moved."""
    assert NetworkParams is not None
