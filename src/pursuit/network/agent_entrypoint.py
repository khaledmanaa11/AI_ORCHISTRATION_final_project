"""THE per-agent single entry point (NET-04, D-01, CLOUD-01) -- split out
of agent_lifecycle.py at the 150-code-line gate (same precedent as
brain_wiring.py/language_wiring.py/tunnel_wiring.py). agent_lifecycle.py
re-exports `run_agent` lazily (PEP 562 `__getattr__`, see that module's own
docstring) so `agent_lifecycle.run_agent` keeps working for every caller,
including `main.py`.

`run_agent` wraps its whole body in `run_with_tunnel` (tunnel_wiring.py):
when tunnel.json's domain env var is set, the tunnel starts BEFORE the
runtime comes up and stops AFTER `shutdown_cleanly` returns; when unset --
the default for every existing test and dev flow -- `run_with_tunnel` is a
transparent no-op, so `run_agent` behaves exactly as it did before this
plan.

06-03 (D-61/D-62/D-63/D-67): Step-0 is declared+signed before the handshake
and rides its third payload digest; on a successful handshake the
declaration is written to disk under the negotiated game_id; after
`run_turn_loop` returns, the Final-Reveal mutual audit runs (when
`security.commit_reveal` is on) and can override the outcome to
`TECHNICAL_LOSS`. All of it lives behind `agent_audit_wiring.py` -- this
function stays a thin caller.
"""

from __future__ import annotations

import secrets
from pathlib import Path

from pursuit.constants import Outcome
from pursuit.network.agent_audit_wiring import declare_step0, run_final_audit, write_declaration
from pursuit.network.agent_lifecycle import default_context, shutdown_cleanly, start_server
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.config_hash import config_digest
from pursuit.network.handshake import make_client_caller, perform_handshake
from pursuit.network.orchestrator import run_turn_loop
from pursuit.network.tunnel_wiring import build_tunnel_manager, run_with_tunnel
from pursuit.shared.scent_config import scent_digest


async def run_agent(config_dir: Path | str, *, game_uid: str | None = None) -> Outcome | None:
    """One process, one orchestrator, one TurnStateMachine -- no referee, no
    shared state (NET-02)."""
    cfg = load_agent_config(config_dir)
    tunnel = build_tunnel_manager(cfg.config_dir, cfg.net)

    async def _play() -> Outcome | None:
        resolved_game_uid = game_uid or secrets.token_hex(8)
        step0_digest, declaration_envelope = await declare_step0(cfg)
        ctx = default_context(
            cfg, game_uid=resolved_game_uid,
            local_step0_digest=step0_digest, local_game_id=resolved_game_uid,
        )
        ctx.watchdog.start()
        await start_server(ctx)
        try:
            local_digest = config_digest(cfg.config_dir / "game_params.json")
            local_scent_digest = scent_digest(cfg.scent)
            async with ctx.runtime.client() as client:
                result = await perform_handshake(
                    machine=ctx.machine, reporter=ctx.reporter, local_digest=local_digest,
                    local_role=ctx.role, call_peer=make_client_caller(client),
                    local_scent_digest=local_scent_digest,
                    local_step0_digest=step0_digest, local_game_id=resolved_game_uid,
                )
            if not result.agreed:
                return None
            write_declaration(ctx, cfg, result, declaration_envelope)
            outcome = await run_turn_loop(ctx)
            if ctx.security.commit_reveal:
                audit_outcome = await run_final_audit(ctx)
                if audit_outcome is not None:
                    outcome = audit_outcome
            return outcome
        finally:
            await shutdown_cleanly(ctx)

    return await run_with_tunnel(tunnel, _play)
