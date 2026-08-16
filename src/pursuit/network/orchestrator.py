"""Per-agent turn loop (D-01): the MY_TURN <-> WAIT_OPPONENT cycle.

Each process embeds exactly one `AgentContext` and drives it through this
loop -- there is no third referee process and no shared runtime object
between the cop and the thief (NET-01, NET-02, rule 2). Every live thing a
turn needs -- state machine, runtime, watchdog, log path, game_uid, the
GameState replica, the negotiated resolution rules, this turn's action
buffer -- hangs off the AgentContext INSTANCE handed in, never a
module-level global.

Joint turn (docs/phases/phase-3/RULES-RESOLUTION.md, supersedes D-12's
cop-then-thief order): both agents choose from the SAME pre-turn state; the
wire exchange only decides who SENDS first. Each half of the cycle records
its own or the opponent's action into the AgentContext buffer
(`turn_actions.py`); whichever half fills the second slot calls
`engine.resolve_turn` exactly once and stores the result.

Game logic is reached ONLY through `pursuit.sdk.engine` (QUAL-01): this
module never imports board/barrier/capture/outcome and computes no
legality, capture or score itself. The GameState replica kept on the context
includes the opponent's coordinate, but that value arrives only over the
wire in a received Envelope or as this agent's own move -- nothing here
reads the opponent's process, memory, config directory or log.

The two turn-cycle halves (`take_my_turn`, `await_opponent_turn`) live in
`turn_actions.py` -- split out at the 150-code-line gate -- and are
imported back below so this module still exports the full surface callers
expect. `turn_actions.py` imports the AgentContext shape FROM this module,
never the reverse; the import is deferred to call time so that
one-directional dependency holds regardless of import order.

`Coord`/`ChooseMove`/`AgentContext` themselves live in `agent_context.py`
(06-02, 150-line-gate room-making split -- this module was AT its ceiling)
and are re-exported below UNCHANGED so every existing
`from pursuit.network.orchestrator import AgentContext` call site keeps
working with zero edits.
"""

from __future__ import annotations

import time

from fastmcp.exceptions import ToolError

from pursuit.constants import Outcome
from pursuit.network import turn_events
from pursuit.network.agent_context import AgentContext, ChooseMove, Coord
from pursuit.network.event_log import append_event
from pursuit.network.state_machine import TERMINAL_STATES, State
from pursuit.network.verdict import peer_protocol_verdict
from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

__all__ = ("AgentContext", "ChooseMove", "Coord", "engine_agent", "first_legal_move", "run_turn_loop")


def engine_agent(role: str) -> str:
    """Bridge role.json's {"police","thief"} to the SDK's {"cop","thief"}
    (D-01) -- the one place this Phase-2 name mismatch is resolved."""
    if role == "police":
        return "cop"
    if role == "thief":
        return "thief"
    raise ValueError(f"unknown role {role!r}; expected 'police' or 'thief'")


def opponent_role(role: str) -> str:
    """The role this agent expects on every inbound envelope's `sender`
    (06-06). Lives here beside `engine_agent` because this module already
    owns the {"police","thief"} vocabulary -- adding the literals anywhere
    else would be a second, driftable copy."""
    if role == "police":
        return "thief"
    if role == "thief":
        return "police"
    raise ValueError(f"unknown role {role!r}; expected 'police' or 'thief'")


def first_legal_move(state: GameState, agent: str, params: GameParams) -> Coord:
    """Phase-2 placeholder: the first legal destination the SDK offers.
    Deterministic and algorithmic, replaced by the Phase-3 RL policy (D-01
    seam). No LLM is involved in move choice anywhere in this project
    (rule 25)."""
    return engine.legal_moves(state, agent, params)[0]


async def run_turn_loop(ctx: AgentContext) -> Outcome | None:
    """Alternate MY_TURN/WAIT_OPPONENT (police sends first, design note 7)
    until an outcome or a terminal state ends the game (D-09); always closes
    with a persisted game_over record. This ordering only decides who SENDS
    first over the wire -- both sides still choose their action from the
    same pre-turn state (module docstring; RULES-RESOLUTION.md)."""
    # Deferred import (not module-level): turn_actions.py imports FROM this
    # module, so importing it back at module-load time would be a genuine
    # load-order-dependent circular import (verified: it broke when
    # turn_actions was the first of the pair ever imported). Deferring to
    # call time is safe -- by the time run_turn_loop actually runs, both
    # modules are always already fully loaded. Mirrors shared/state.py's
    # own local-import precedent for the identical reason.
    # 05-15 (G10) joins the same deferred-import discipline, for the same
    # reason: capture_declaration.py imports `engine_agent` FROM this module
    # (one-directional, at module level), so importing it back at load time
    # would be a genuine circular import.
    from pursuit.network.capture_declaration import send_capture_declaration  # noqa: PLC0415
    from pursuit.network.turn_actions import await_opponent_turn, take_my_turn  # noqa: PLC0415
    from pursuit.network.turn_commit_send import technical_loss  # noqa: PLC0415

    outcome: Outcome | None = None
    first, second = (
        (take_my_turn, await_opponent_turn)
        if ctx.role == "police"
        else (await_opponent_turn, take_my_turn)
    )
    started = time.monotonic()
    try:
        while ctx.machine.state not in TERMINAL_STATES:
            outcome = await first(ctx)
            if outcome is not None or ctx.machine.state in TERMINAL_STATES:
                break
            outcome = await second(ctx)
            if outcome is not None or ctx.machine.state in TERMINAL_STATES:
                break
    except ToolError as exc:
        # The opponent's tool body REJECTED one of our calls. deadline.py
        # re-raises ToolError on purpose (an application-level rejection is
        # not a transport failure and must never be retried) -- but nothing
        # above it used to catch it, so the process died by traceback with
        # our nonces already ledgered and no FINAL_REVEAL sent, making US
        # the side that published nothing (rule 36) on one line of their
        # code. Ending through the existing technical-loss pathway instead
        # keeps the terminal path -- and therefore the Final-Reveal audit
        # that publishes our ledger -- intact. See 06-06.
        outcome = technical_loss(ctx, peer_protocol_verdict(exc, started))

    if ctx.machine.state not in TERMINAL_STATES:
        ctx.machine.attempt(State.GAME_OVER)
    if outcome is not None:
        append_event(
            ctx.log_path,
            turn_events.game_over_record(
                game_uid=ctx.game_uid, turn=ctx.state.turn, sender=ctx.role, outcome=outcome,
            ),
        )
        # 05-15 (G10), rule 21 / book Sec3.5 p.22 Table 2: the cop's Capture
        # Claim. THE TWO STATEMENTS ARE DELIBERATELY ADJACENT AND SHARE ONE
        # `outcome` OBJECT AND ONE `ctx.state.turn` -- that is the whole
        # rule-22 argument, since a claim that cannot be computed separately
        # from the audited record cannot disagree with it. The ledger record
        # goes first because it is the durable evidence; the declaration is
        # best-effort by contract and cannot raise, return a verdict, or
        # change `outcome` (see capture_declaration.py). A no-op for the
        # thief and for every non-capture outcome.
        await send_capture_declaration(ctx, turn=ctx.state.turn, outcome=outcome)
    return outcome


def __getattr__(name: str):
    """PEP 562 lazy re-export: `take_my_turn`/`await_opponent_turn` are
    implemented in turn_actions.py (the 150-line split) and resolved here on
    first EXTERNAL access, so `orchestrator.take_my_turn` keeps working for
    every caller without a load-time circular import in either direction
    (verified: an eager module-level import here broke when turn_actions.py
    was the first of the pair ever imported)."""
    if name in ("take_my_turn", "await_opponent_turn"):
        from pursuit.network import turn_actions

        return getattr(turn_actions, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
