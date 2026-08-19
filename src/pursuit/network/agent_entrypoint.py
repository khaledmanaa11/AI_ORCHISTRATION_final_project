"""THE per-agent single entry point (NET-04, D-01, CLOUD-01) -- split out
of agent_lifecycle.py at the 150-code-line gate (same precedent as
brain_wiring.py/language_wiring.py/tunnel_wiring.py). agent_lifecycle.py
re-exports `run_agent` lazily (PEP 562 `__getattr__`, see that module's own
docstring) so `agent_lifecycle.run_agent` keeps working for every caller,
including `main.py`.

`run_agent` wraps its whole body in `run_with_tunnel` (tunnel_wiring.py):
when tunnel.json's domain env var is set, the tunnel starts BEFORE the
runtime comes up and stops AFTER the whole teardown returns -- including
the linger, since the teardown lives inside the wrapped body; when unset --
the default for every existing test and dev flow -- `run_with_tunnel` is a
transparent no-op, so `run_agent` behaves exactly as it did before that
plan.

05-04 (05-UAT.md G1): teardown is no longer one `shutdown_cleanly` call.
It is that function's two halves with a bounded, Table-19-sourced grace
window between them (`agent_teardown.linger_for_peer`), so a peer still
retrying its FINAL_REVEAL at us is not cut off by a socket we closed
milliseconds after our own audit matched.

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
import time
from contextlib import AsyncExitStack
from pathlib import Path

from fastmcp.exceptions import ToolError

from pursuit.constants import Outcome
from pursuit.network.agent_audit_exchange import record_technical_loss
from pursuit.network.agent_audit_wiring import declare_step0, run_final_audit, write_declaration
from pursuit.network.agent_lifecycle import (
    default_context,
    start_server,
    stop_runtime,
    stop_watchdog,
)
from pursuit.network.agent_step0_wiring import record_completed_game
from pursuit.network.agent_teardown import linger_for_peer
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.client_connect import NEVER_CONNECTED_LINE, enter_client_with_retry
from pursuit.network.config_hash import config_digest
from pursuit.network.game_identity import adopt_negotiated_game_id
from pursuit.network.handshake import make_client_caller, perform_handshake
from pursuit.network.orchestrator import run_turn_loop
from pursuit.network.secret_wiring import resolve_shared_secret
from pursuit.network.tunnel_wiring import build_tunnel_manager, run_with_tunnel
from pursuit.network.verdict import peer_protocol_verdict
from pursuit.services.reporting.end_of_game import report_game_end
from pursuit.shared.scent_config import scent_digest


async def run_agent(config_dir: Path | str, *, game_uid: str | None = None) -> Outcome | None:
    """One process, one orchestrator, one TurnStateMachine -- no referee, no
    shared state (NET-02)."""
    cfg = load_agent_config(config_dir)
    tunnel = build_tunnel_manager(cfg.config_dir, cfg.net)

    async def _play() -> Outcome | None:
        resolved_game_uid = game_uid or secrets.token_hex(8)
        step0_digest, declaration_envelope = await declare_step0(cfg)
        shared_secret = resolve_shared_secret(cfg.config_dir)
        shared_secret_value = shared_secret[1] if shared_secret is not None else None
        ctx = default_context(
            cfg, game_uid=resolved_game_uid,
            local_step0_digest=step0_digest, local_game_id=resolved_game_uid,
            local_step0_declaration=declaration_envelope,
        )
        ctx.watchdog.start()
        await start_server(ctx)
        try:
            local_digest = config_digest(cfg.config_dir / "game_params.json")
            local_scent_digest = scent_digest(cfg.scent)
            # The handshake enter rides the SAME D-13 ladder as every other
            # outgoing call (client_connect.py): a merely-late peer is
            # retried on a fresh client, and one that never comes up ends
            # this process with NO GAME and no verdict -- printing retained
            # evidence -- never the 2026-08-19 startup traceback.
            async with AsyncExitStack() as stack:
                connect = await enter_client_with_retry(stack, ctx.runtime.client, cfg.net)
                if not connect.succeeded:
                    print(NEVER_CONNECTED_LINE)
                    print(f"last_error={connect.verdict.last_error}")
                    return None
                result = await perform_handshake(
                    machine=ctx.machine, reporter=ctx.reporter, local_digest=local_digest,
                    local_role=ctx.role, call_peer=make_client_caller(connect.value),
                    local_scent_digest=local_scent_digest,
                    local_step0_digest=step0_digest, local_game_id=resolved_game_uid,
                    local_step0_declaration=declaration_envelope, shared_secret=shared_secret_value,
                )
            if not result.agreed:
                return None
            # 05-05 (D-61, 05-UAT.md G2) -- THE call-site ordering. It must
            # sit after `result.agreed` (there is no negotiated id without an
            # agreement) and BEFORE write_declaration/run_turn_loop: the turn
            # loop's first ledger append derives the D-64 ledger name from
            # ctx.log_path.stem and seals ctx.game_uid into every hashed
            # commit. Move this call below either of them and the four
            # criterion-2 artifacts stop joining again.
            adopt_negotiated_game_id(ctx, result)
            write_declaration(ctx, cfg, result, declaration_envelope)
            outcome = await run_turn_loop(ctx)
            if ctx.security.commit_reveal:
                # Same containment as run_turn_loop's own (06-06): a peer
                # that rejects our FINAL_REVEAL push must not kill this
                # process on the way out, after the game already resolved.
                audit_started = time.monotonic()
                try:
                    # board_outcome (05-04) is THE production wiring for
                    # 05-UAT.md G1: without this argument arriving from here,
                    # a failed own push still accuses a peer that answered.
                    audit_outcome = await run_final_audit(ctx, board_outcome=outcome)
                # This branch stays ACCUSATORY on purpose -- do not fold it
                # into the non-accusatory audit_incomplete path above.
                # `deadline.call_with_retry` re-raises ToolError unretried by
                # design: a peer whose tool body REJECTED our call performed
                # an act of its own (06-06's PEER_PROTOCOL_ERROR), which is a
                # different fact from our own send timing out, and the two
                # must not collapse into one verdict.
                except ToolError as exc:
                    audit_outcome = record_technical_loss(
                        ctx, peer_protocol_verdict(exc, audit_started),
                    )
                if audit_outcome is not None:
                    outcome = audit_outcome
            # 07-00, rules 37/38: THE game-end increment, and the ONLY one.
            # It sits here, not in write_declaration where it used to live,
            # because this is the single point at which the game's result
            # is known and final -- after the turn loop AND after an audit
            # that may override it. `record_completed_game` decides what
            # "completed" means and records why; a false games-played
            # declaration is an absolute disqualification (docs/RULES.md:79).
            record_completed_game(cfg, outcome)
            # 07-07, rules 32/35: THE game-end report, and it belongs HERE
            # rather than in the `finally` below for two reasons that are not
            # preferences. It needs the same definition of "completed" the
            # line above uses -- a handshake that never became a game is not
            # a game to report -- and it needs `ctx.language.gatekeeper` and
            # the armed watchdog still alive, both of which `stop_runtime`
            # and `stop_watchdog` end. Rule 32 disqualifies the points of any
            # game that goes unreported and rule 35 scores ZERO FOR BOTH
            # TEAMS when one side fails to report, so this is the most
            # submission-critical call site in the codebase -- and precisely
            # for that reason it is contained at its own boundary: it returns
            # a value nobody reads, never raises, and cannot touch `outcome`
            # or this process's exit code, which since 06-05 MEANS an audit
            # mismatch (main.py:25-29).
            # 08-04: `result.peer_step0_declaration` is threaded through
            # because `declaration_<game_id>.json` embeds BOTH sides' signed
            # envelopes (D-71) and this is the only place that holds the
            # peer's. It is None when the peer sent a digest and no content,
            # which the artifact records as an honest absence.
            await report_game_end(
                ctx, cfg, outcome=outcome, declaration_envelope=declaration_envelope,
                peer_declaration_envelope=result.peer_step0_declaration,
            )
            return outcome
        finally:
            # 05-04: shutdown_cleanly's two halves, with a bounded grace
            # window between them. The watchdog goes FIRST -- its freeze
            # action (os._exit(1)) would otherwise be live across the whole
            # linger (NET-07), which has no bounded attempt of its own to
            # touch on: it is a drain loop, not a retry ladder.
            #
            # 05-13 corrects this comment's original REASON, not its
            # conclusion. It used to read "touch() is called nowhere in the
            # audit path" -- true when 05-04 wrote it, and 05-04 protected
            # the linger while leaving the audit itself exposed to exactly
            # that fact (05-UAT.md G6). `run_final_audit` now touches once
            # per bounded attempt, so it survives its own 135 s ladder; the
            # linger still does not, so this ordering is unchanged.
            #
            # The try/finally is load-bearing, not decoration:
            # the linger awaits asyncio.wait_for, a cancellation point, and
            # CancelledError is a BaseException -- three bare statements
            # here would leak the server task and the bound port on Ctrl-C.
            stop_watchdog(ctx)
            try:
                await linger_for_peer(ctx)
            finally:
                await stop_runtime(ctx)

    return await run_with_tunnel(tunnel, _play)
