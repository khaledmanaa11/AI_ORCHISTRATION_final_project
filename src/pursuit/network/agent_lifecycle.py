"""Per-agent startup/wiring/shutdown (NET-01, NET-02, NET-04, NET-09, D-01).

This module builds a fully-wired `AgentContext` (`default_context`), starts
its FastMCP server (`start_server`) and tears it down (`shutdown_cleanly`).
Every collaborator is constructed fresh, per call, into a new `AgentContext`
instance -- there is no shared object between the cop and the thief (NET-02).

`run_agent` -- THE per-agent single entry point (load config, build the
context, handshake, play the turn loop, shut down) -- now lives in
`agent_entrypoint.py`, split out at the 150-code-line gate (it wraps its
whole body in `tunnel_wiring.run_with_tunnel`, CLOUD-01: the tunnel starts
BEFORE the runtime comes up and stops AFTER `shutdown_cleanly` returns when
tunnel.json's domain env var is set; a transparent no-op, the default for
every existing test/dev flow, when unset). `agent_entrypoint.py` imports
`default_context`/`start_server`/`shutdown_cleanly` FROM this module, so
`run_agent` is resolved back here lazily (PEP 562 `__getattr__`, the same
one-directional-dependency fix `orchestrator.py`/`turn_actions.py` already
uses) rather than an eager import that would be a genuine load-order
circular import. The small wiring closures (`RoleKey`, `load_role`,
`make_transition_reporter`, `make_freeze_handler`, `make_handshake_responder`)
live in `agent_wiring.py`; 04-12's mover/scent/language wiring lives in
`brain_wiring.py` -- both re-exported the same way.

The inbound handshake responder is bound at CONSTRUCTION time (design note
12): the responder must be handed to `PeerRuntime` before `start_server`
runs -- there is no later injection point. Skipping this is not a missing
nicety: the unwired tool answers with a generic ack that cannot decode
through `Envelope.from_dict`, aborting every real handshake before move 1.

`build_context` itself now lives in `agent_context.py` (06-02, 150-line-gate
room-making split -- this module was AT its ceiling) and is re-exported
below verbatim, so `agent_lifecycle.build_context` keeps working for every
caller (including the tests) exactly as if it were still defined here.
"""

from __future__ import annotations

import secrets
from pathlib import Path

# AgentConfig/load_agent_config/load_role/make_freeze_handler/
# make_handshake_responder/make_transition_reporter/engine_agent are
# re-exported verbatim so `agent_lifecycle.<name>` keeps working for every
# caller -- noqa: F401 on the re-export-only names.
from pursuit.network.agent_context import AgentContext, build_context  # noqa: F401
from pursuit.network.agent_wiring import (
    AgentConfig,  # noqa: F401
    load_agent_config,  # noqa: F401
    load_role,  # noqa: F401
    make_freeze_handler,
    make_handshake_responder,
    make_transition_reporter,
)
from pursuit.network.brain_wiring import build_turn_collaborators
from pursuit.network.config_hash import config_digest
from pursuit.network.orchestrator import engine_agent, opponent_role  # noqa: F401
from pursuit.network.peer_runtime import PeerRuntime
from pursuit.network.secret_wiring import resolve_shared_secret
from pursuit.network.state_machine import TurnStateMachine
from pursuit.network.watchdog import Watchdog
from pursuit.shared.scent_config import scent_digest


def default_context(
    cfg: AgentConfig, *, game_uid: str | None = None, log_path: Path | None = None,
    local_step0_digest: str | None = None, local_game_id: str | None = None,
    local_step0_declaration: dict | None = None,
) -> AgentContext:
    """Build the REAL collaborators. THE ORDER IS LOAD-BEARING (design
    note 12): the reporter and machine must exist before the responder
    closure is built, and the responder must be handed to the PeerRuntime AT
    CONSTRUCTION -- there is no later injection point. 04-12: also builds
    the real mover, scent field and `LanguageRuntime` -- every real game
    plays the full Figure-7 pipeline; only bespoke fixtures skip this.
    06-03 (D-61/D-62): `local_step0_digest`/`local_game_id`/
    `local_step0_declaration` thread into the responder the SAME way
    `local_scent_digest` already does -- default None so every pre-existing
    caller stays byte-unmodified; `agent_entrypoint.run_agent` is the one
    real caller that supplies all three. The SAME resolved shared-secret
    tuple this function already builds for `PeerRuntime` (D-56) is reused
    for the responder's OWN Step-0 content verification -- one resolution,
    two consumers, never a second `resolve_shared_secret` call here."""
    game_uid = game_uid or secrets.token_hex(8)
    if log_path is None:
        log_path = Path("logs") / cfg.role / f"{game_uid}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    reporter = make_transition_reporter(log_path, game_uid=game_uid, role=cfg.role)
    machine = TurnStateMachine(reporter)
    local_digest = config_digest(cfg.config_dir / "game_params.json")
    local_scent_digest = scent_digest(cfg.scent)
    shared_secret_pair = resolve_shared_secret(cfg.config_dir)
    shared_secret_value = shared_secret_pair[1] if shared_secret_pair is not None else None
    responder = make_handshake_responder(
        machine=machine, reporter=reporter, local_digest=local_digest, local_role=cfg.role,
        local_scent_digest=local_scent_digest,
        local_step0_digest=local_step0_digest, local_game_id=local_game_id,
        local_step0_declaration=local_step0_declaration, shared_secret=shared_secret_value,
    )
    # D-56: shared_secret resolved from THIS agent's config_dir (tunnel.json's
    # secret_header + os.environ[secret_env]) -- None (every existing
    # test/dev flow) installs no middleware and sends no header.
    # expected_sender (06-06): in live play the only legitimate sender on a
    # game message is the opponent's role. Supplied HERE because this is the
    # one place that knows cfg.role for a real match; every other caller
    # leaves it None and keeps the pre-06-06 accept-anything behaviour.
    runtime = PeerRuntime(
        cfg.net, f"pursuit-{cfg.role}", handshake_handler=responder,
        shared_secret=shared_secret_pair, expected_sender=opponent_role(cfg.role),
    )
    watchdog = Watchdog(
        threshold_seconds=cfg.net.watchdog_threshold,
        poll_seconds=cfg.net.watchdog_poll_seconds,
        on_freeze=make_freeze_handler(
            log_path, game_uid=game_uid, role=cfg.role,
            threshold_seconds=cfg.net.watchdog_threshold,
        ),
    )
    brain, scent_field, language = build_turn_collaborators(cfg)
    return build_context(
        cfg, game_uid=game_uid, log_path=log_path, runtime=runtime, watchdog=watchdog,
        reporter=reporter, machine=machine, brain=brain, scent_field=scent_field, language=language,
    )


async def start_server(ctx: AgentContext) -> None:
    """Background this agent's FastMCP server on THIS process's event loop
    (Pitfall 3). PeerRuntime.start() owns its own asyncio.Task internally."""
    await ctx.runtime.start()


def stop_watchdog(ctx: AgentContext) -> None:
    """Teardown half one: stop the freeze-detector's daemon thread.
    Idempotent. Split out (05-04) so `agent_entrypoint.run_agent` can stop
    it BEFORE its bounded post-audit linger and the runtime AFTER --
    `Watchdog.touch()` is called nowhere in the audit path, and a watchdog
    left running past GAME_OVER treats a clean shutdown as a freeze, whose
    action is `os._exit(1)` (NET-07)."""
    ctx.watchdog.stop()


async def stop_runtime(ctx: AgentContext) -> None:
    """Teardown half two: ask the runtime to cancel its server task and
    release its listening socket. Idempotent, and deliberately unchanged --
    the linger, never a gentler stop, is what leaves a peer still
    mid-exchange a live listener."""
    await ctx.runtime.stop()


async def shutdown_cleanly(ctx: AgentContext) -> None:
    """GAME_OVER teardown, as the COMPOSITION of the two halves above --
    never a third copy of the same two statements, or this wrapper and
    `run_agent` would silently drift apart. Idempotent.

    Since 05-04 its only remaining callers are tests: `run_agent`
    interleaves a bounded `agent_teardown.linger_for_peer` window BETWEEN
    the halves, so a peer still retrying its FINAL_REVEAL finds a live
    listener instead of a socket closed milliseconds after our own audit
    matched (05-UAT.md G1)."""
    stop_watchdog(ctx)
    await stop_runtime(ctx)


def __getattr__(name: str):
    """PEP 562 lazy re-export: `run_agent` is implemented in
    `agent_entrypoint.py` (the 150-line split) and resolved here on first
    EXTERNAL access, so `agent_lifecycle.run_agent` keeps working for every
    caller (including `main.py`) without a load-time circular import --
    `agent_entrypoint.py` imports `default_context`/`start_server`/
    `shutdown_cleanly` FROM this module, so an eager import back here would
    invert that one-directional dependency (same fix as
    `orchestrator.py`/`turn_actions.py`)."""
    if name == "run_agent":
        from pursuit.network import agent_entrypoint

        return agent_entrypoint.run_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
