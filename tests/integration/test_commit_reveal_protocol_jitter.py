"""D-58 jitter tolerance: a duplicate ACK arriving after the real one must
be dropped (04-12's own jitter lesson), never a spurious technical loss.
Split from `test_commit_reveal_protocol.py` at the 150-code-line gate.

Hand-rolls the two-peer wiring `tests/integration/two_peer_game.py` itself
uses (rather than reusing `play_two_peer_game`) because the duplicate-ack
behavior must be installed on the CLIENT object `play_two_peer_game`
constructs internally and immediately overwrites `runtime.client` with --
there is no seam to wrap it after the fact through that helper's own
`wire=` hook, which runs BEFORE `runtime.client` is assigned.
"""

from __future__ import annotations

import asyncio

from fastmcp import Client

from pursuit.constants import Outcome
from pursuit.network import agent_lifecycle
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.config_hash import config_digest
from pursuit.network.handshake import make_client_caller, perform_handshake
from pursuit.network.orchestrator import run_turn_loop
from pursuit.shared.scent_config import scent_digest


class _DuplicateAckClient:
    """Wraps a real fastmcp `Client`: every `receive_ack` push is sent
    TWICE -- the second copy is the injected jitter this test proves gets
    tolerated (dropped), never raised into a technical loss."""

    def __init__(self, real_client):
        self._real = real_client

    async def __aenter__(self):
        await self._real.__aenter__()
        return self

    async def __aexit__(self, *exc_info):
        return await self._real.__aexit__(*exc_info)

    async def call_tool(self, name, args, **kwargs):
        result = await self._real.call_tool(name, args, **kwargs)
        if name == "receive_ack":
            await self._real.call_tool(name, args, **kwargs)
        return result


async def test_a_duplicate_ack_is_tolerated_never_a_technical_loss(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a = load_agent_config("config/police")
    cfg_b = load_agent_config("config/thief")
    ctx_a = agent_lifecycle.default_context(
        cfg_a, game_uid="commit-reveal-jitter", log_path=tmp_path / "a.jsonl",
    )
    ctx_b = agent_lifecycle.default_context(
        cfg_b, game_uid="commit-reveal-jitter", log_path=tmp_path / "b.jsonl",
    )
    # Police's own outgoing ACKs (acknowledging thief's COMMIT) are doubled.
    ctx_a.runtime.client = lambda: _DuplicateAckClient(Client(ctx_b.runtime.server))
    ctx_b.runtime.client = lambda: Client(ctx_a.runtime.server)

    local_digest = config_digest(cfg_a.config_dir / "game_params.json")
    local_scent_digest = scent_digest(cfg_a.scent)
    async with ctx_a.runtime.client() as client:
        result = await perform_handshake(
            machine=ctx_a.machine, reporter=ctx_a.reporter, local_digest=local_digest,
            local_role=ctx_a.role, call_peer=make_client_caller(client),
            local_scent_digest=local_scent_digest,
        )
    assert result.agreed, f"handshake failed: {result}"

    outcome_a, outcome_b = await asyncio.gather(run_turn_loop(ctx_a), run_turn_loop(ctx_b))

    assert outcome_a is not None and outcome_a == outcome_b
    assert outcome_a is not Outcome.TECHNICAL_LOSS, "a duplicate ACK must never end the game"
