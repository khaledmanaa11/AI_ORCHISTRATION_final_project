"""Two REAL AgentContexts, wired in-memory, played to completion (04-12).

Deviation (Rule 3 - blocking): not in 04-12-PLAN.md's `files_modified`, but
needed by both `test_language_pipeline.py` and `test_llm_degradation.py`
(QUAL-02: one shared helper, not duplicated). Not `conftest.py` itself --
that module is already close to the 150-code-line gate.

Not a `test_*.py` module on purpose (mirrors `tests/unit/_fakes_agent.py`):
pytest never collects it as a test module.
"""

from __future__ import annotations

import asyncio
import pathlib
from collections.abc import Callable

from fastmcp import Client

from pursuit.network import agent_lifecycle
from pursuit.network.agent_wiring import AgentConfig
from pursuit.network.config_hash import config_digest
from pursuit.network.handshake import make_client_caller, perform_handshake
from pursuit.network.orchestrator import AgentContext, run_turn_loop
from pursuit.shared.scent_config import scent_digest


async def play_two_peer_game(
    cfg_a: AgentConfig, cfg_b: AgentConfig, *, game_uid: str, log_dir: pathlib.Path,
    wire: Callable[[AgentContext], None] | None = None,
) -> tuple[object, object, AgentContext, AgentContext]:
    """Build two REAL `AgentContext`s (`agent_lifecycle.default_context`),
    wire them to each other's real FastMCP server object in-memory
    (RESEARCH Pattern 5 -- no socket, no URL), perform one real handshake,
    then run BOTH turn loops concurrently to a finished game.

    `wire`, when supplied, is called once per context (BOTH `ctx_a` and
    `ctx_b`, in that order) right after construction and before the
    handshake -- the seam `test_llm_degradation.py` uses to swap in a
    failing provider, pre-load the token budget, or silence one side's
    hint channel entirely, without touching this module's own logic.

    Returns `(outcome_a, outcome_b, ctx_a, ctx_b)` -- both outcomes are the
    SAME game's result from each side's own perspective (rules 46-48: both
    sides score the ending identically).
    """
    ctx_a = agent_lifecycle.default_context(
        cfg_a, game_uid=game_uid, log_path=log_dir / "a.jsonl",
    )
    ctx_b = agent_lifecycle.default_context(
        cfg_b, game_uid=game_uid, log_path=log_dir / "b.jsonl",
    )
    if wire is not None:
        wire(ctx_a)
        wire(ctx_b)
    ctx_a.runtime.client = lambda: Client(ctx_b.runtime.server)
    ctx_b.runtime.client = lambda: Client(ctx_a.runtime.server)

    local_digest = config_digest(cfg_a.config_dir / "game_params.json")
    local_scent_digest = scent_digest(cfg_a.scent)
    async with ctx_a.runtime.client() as client:
        result = await perform_handshake(
            machine=ctx_a.machine, reporter=ctx_a.reporter, local_digest=local_digest,
            local_role=ctx_a.role, call_peer=make_client_caller(client),
            local_scent_digest=local_scent_digest,
        )
    assert result.agreed, f"two_peer_game: handshake failed: {result}"

    outcome_a, outcome_b = await asyncio.gather(run_turn_loop(ctx_a), run_turn_loop(ctx_b))
    return outcome_a, outcome_b, ctx_a, ctx_b
