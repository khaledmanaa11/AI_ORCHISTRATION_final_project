"""Per-agent startup/wiring/shutdown (NET-01, NET-02, NET-04, NET-09, D-01).

`run_agent` is THE single per-agent entry point: load this agent's own config,
build a fully-wired AgentContext, start its own FastMCP server, perform the
outbound handshake, play the turn loop, then shut down cleanly. Every
collaborator is constructed fresh, per call, into a new `AgentContext`
instance -- there is no shared object between the cop and the thief (NET-02).

The small wiring closures and the config-dir readers (`RoleKey`, `load_role`,
`make_transition_reporter`, `make_freeze_handler`, `make_handshake_responder`)
live in `agent_wiring.py`, split out at the 150-code-line gate (Segal Table
5), and are imported back below so each stays reachable as
`agent_lifecycle.<name>` for every caller, including the tests.

The inbound handshake responder is bound at CONSTRUCTION time (design note
12): 02-06's `register_tools` closes the tool bodies over whatever it is
given when the server is built, so `default_context` builds the reporter and
machine FIRST, wraps 02-08's `respond_to_handshake` in an `async def`
closure, and passes it as `handshake_handler=` into the `PeerRuntime` before
`start_server` ever runs -- there is no later injection point. Skipping this
is not a missing nicety: the unwired tool answers with a generic ack that
cannot decode through `Envelope.from_dict`, aborting every real handshake to
`State.ERROR` before move 1.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from pathlib import Path

from pursuit.constants import Outcome

# load_role/make_freeze_handler/make_handshake_responder/make_transition_reporter and
# engine_agent below are re-exported verbatim (this file's own body never calls them
# directly except where shown) so `agent_lifecycle.<name>` keeps working for every
# caller, per this module's required export surface -- noqa: F401 on the re-export-only
# names.
from pursuit.network.agent_wiring import (
    load_role,  # noqa: F401
    make_freeze_handler,
    make_handshake_responder,
    make_transition_reporter,
)
from pursuit.network.config_hash import config_digest
from pursuit.network.handshake import make_client_caller, perform_handshake
from pursuit.network.orchestrator import (
    AgentContext,
    ChooseMove,
    engine_agent,  # noqa: F401
    run_turn_loop,
)
from pursuit.network.peer_runtime import PeerRuntime
from pursuit.network.state_machine import TransitionReporter, TurnStateMachine
from pursuit.network.watchdog import Watchdog
from pursuit.sdk import engine
from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.network_config import NetworkParams, load_network_config


@dataclass(frozen=True)
class AgentConfig:
    """The three per-agent config files, loaded once and handed to build_context."""

    config_dir: Path
    role: str
    params: GameParams
    net: NetworkParams


def load_agent_config(config_dir: Path | str) -> AgentConfig:
    """Load role.json + network.json + game_params.json from ONE per-agent
    directory -- the only source for this process's identity (NET-01)."""
    directory = Path(config_dir)
    role = load_role(directory)
    net = load_network_config(directory / "network.json")
    params = load_game_params(directory / "game_params.json")
    return AgentConfig(config_dir=directory, role=role, params=params, net=net)


def build_context(
    cfg: AgentConfig,
    *,
    game_uid: str,
    log_path: Path,
    runtime: PeerRuntime,
    watchdog: Watchdog,
    reporter: TransitionReporter,
    machine: TurnStateMachine | None = None,
    choose_move: ChooseMove | None = None,
) -> AgentContext:
    """PURE WIRING: every collaborator is injected, nothing is constructed
    implicitly. The seam the NET-02 isolation tests and every fake-driven
    test use."""
    return AgentContext(
        role=cfg.role,
        params=cfg.params,
        net=cfg.net,
        machine=machine or TurnStateMachine(reporter),
        runtime=runtime,
        watchdog=watchdog,
        reporter=reporter,
        log_path=log_path,
        game_uid=game_uid,
        state=engine.make_state(cfg.params),
        choose_move=choose_move,
    )


def default_context(
    cfg: AgentConfig, *, game_uid: str | None = None, log_path: Path | None = None
) -> AgentContext:
    """Build the REAL collaborators. THE ORDER IS LOAD-BEARING (design
    note 12): the reporter and machine must exist before the responder
    closure is built, and the responder must be handed to the PeerRuntime AT
    CONSTRUCTION -- there is no later injection point."""
    game_uid = game_uid or secrets.token_hex(8)
    if log_path is None:
        log_path = Path("logs") / cfg.role / f"{game_uid}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    reporter = make_transition_reporter(log_path, game_uid=game_uid, role=cfg.role)
    machine = TurnStateMachine(reporter)
    local_digest = config_digest(cfg.config_dir / "game_params.json")
    responder = make_handshake_responder(
        machine=machine, reporter=reporter, local_digest=local_digest, local_role=cfg.role,
    )
    runtime = PeerRuntime(cfg.net, f"pursuit-{cfg.role}", handshake_handler=responder)
    watchdog = Watchdog(
        threshold_seconds=cfg.net.watchdog_threshold,
        poll_seconds=cfg.net.watchdog_poll_seconds,
        on_freeze=make_freeze_handler(
            log_path, game_uid=game_uid, role=cfg.role,
            threshold_seconds=cfg.net.watchdog_threshold,
        ),
    )
    return build_context(
        cfg, game_uid=game_uid, log_path=log_path, runtime=runtime, watchdog=watchdog,
        reporter=reporter, machine=machine,
    )


async def start_server(ctx: AgentContext) -> None:
    """Background this agent's FastMCP server on THIS process's event loop
    (Pitfall 3). PeerRuntime.start() owns its own asyncio.Task internally."""
    await ctx.runtime.start()


async def shutdown_cleanly(ctx: AgentContext) -> None:
    """GAME_OVER teardown: stop the watchdog daemon thread, then ask the
    runtime to cancel its server task and release its listening socket.
    Idempotent -- both Watchdog.stop() and PeerRuntime.stop() are safe to
    call twice. Stopping the watchdog here matters: left running past
    GAME_OVER, its daemon thread would eventually see no further touch()
    calls and treat a clean shutdown as a freeze (Rule 1)."""
    ctx.watchdog.stop()
    await ctx.runtime.stop()


async def run_agent(config_dir: Path | str, *, game_uid: str | None = None) -> Outcome | None:
    """THE per-agent single entry point (NET-04, D-01): one process, one
    orchestrator, one TurnStateMachine -- no referee, no shared state."""
    cfg = load_agent_config(config_dir)
    ctx = default_context(cfg, game_uid=game_uid)
    ctx.watchdog.start()
    await start_server(ctx)
    try:
        local_digest = config_digest(cfg.config_dir / "game_params.json")
        async with ctx.runtime.client() as client:
            result = await perform_handshake(
                machine=ctx.machine, reporter=ctx.reporter, local_digest=local_digest,
                local_role=ctx.role, call_peer=make_client_caller(client),
            )
        if not result.agreed:
            return None
        return await run_turn_loop(ctx)
    finally:
        await shutdown_cleanly(ctx)
