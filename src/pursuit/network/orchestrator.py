"""Per-agent turn loop (D-01): the MY_TURN <-> WAIT_OPPONENT cycle.

Each process embeds exactly one `AgentContext` and drives it through this
loop -- there is no third referee process and no shared runtime object
between the cop and the thief (NET-01, NET-02, rule 2). Every live thing a
turn needs -- state machine, runtime, watchdog, log path, game_uid, the
GameState replica -- hangs off the AgentContext INSTANCE handed in, never a
module-level global.

Game logic is reached ONLY through `pursuit.sdk.engine` (QUAL-01): this
module never imports board/barrier/capture/outcome and computes no
legality, capture or score itself. The GameState replica kept on the context
includes the opponent's coordinate, but that value arrives only over the
wire in a received Envelope or as this agent's own move -- nothing here
reads the opponent's process, memory, config directory or log (Phase 2 is
the book's open-coordinate stage; blindness arrives in Phase 4).

The two turn-cycle halves (`take_my_turn`, `await_opponent_turn`) are
implemented in `turn_actions.py` -- split out at the 150-code-line gate
(Segal Table 5) -- and imported back below so this module still exports the
full six-name surface the plan's artifacts require. `turn_actions.py`
imports the AgentContext shape and the SDK-dispatch helpers FROM this
module, never the reverse; the import below is deferred to the bottom of
this file so that one-directional dependency holds even though this module
also re-exports the two names.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pursuit.constants import Outcome
from pursuit.network import turn_events
from pursuit.network.event_log import append_event
from pursuit.network.peer_runtime import PeerRuntime
from pursuit.network.state_machine import (
    TERMINAL_STATES,
    State,
    TransitionReporter,
    TurnStateMachine,
)
from pursuit.network.watchdog import Watchdog
from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.network_config import NetworkParams
from pursuit.shared.state import GameState

ChooseMove = Callable[[GameState, str, GameParams], tuple[int, int]]
"""The Phase-3 replacement point (design note 5): a plain algorithm, never an
LLM (rule 25). Defaults to `first_legal_move` when unset on the context."""


@dataclass
class AgentContext:
    """Everything one process's turn loop needs -- an INSTANCE, never a
    module-level global (NET-02). Two contexts built in the same interpreter
    share no field: build a fresh one per process."""

    role: str
    params: GameParams
    net: NetworkParams
    machine: TurnStateMachine
    runtime: PeerRuntime
    watchdog: Watchdog
    reporter: TransitionReporter
    log_path: Path
    game_uid: str
    state: GameState
    choose_move: ChooseMove | None = None


def engine_agent(role: str) -> str:
    """Bridge role.json's {"police","thief"} to the SDK's {"cop","thief"}
    (D-01) -- the one place this Phase-2 name mismatch is resolved."""
    if role == "police":
        return "cop"
    if role == "thief":
        return "thief"
    raise ValueError(f"unknown role {role!r}; expected 'police' or 'thief'")


def first_legal_move(state: GameState, agent: str, params: GameParams) -> tuple[int, int]:
    """Phase-2 placeholder: the first legal destination the SDK offers.
    Deterministic and algorithmic, replaced by the Phase-3 RL policy (D-01
    seam). No LLM is involved in move choice anywhere in this project
    (rule 25)."""
    return engine.legal_moves(state, agent, params)[0]


def apply_role_move(
    state: GameState, role: str, dest: tuple[int, int], params: GameParams
) -> tuple[GameState, Outcome | None]:
    """Dispatch ONLY (QUAL-01): police -> apply_cop_action (no barrier in
    Phase 2, design note 6), thief -> apply_thief_move. No legality, capture
    or scoring is computed here."""
    if role == "police":
        return engine.apply_cop_action(state, dest, None, params)
    if role == "thief":
        return engine.apply_thief_move(state, dest, params)
    raise ValueError(f"unknown role {role!r}; expected 'police' or 'thief'")


async def run_turn_loop(ctx: AgentContext) -> Outcome | None:
    """Alternate MY_TURN/WAIT_OPPONENT per D-12 turn order (police first,
    design note 7) until an outcome or a terminal state ends the game
    (D-09); always closes with a persisted game_over record."""
    # Deferred import (not module-level): turn_actions.py imports FROM this
    # module, so importing it back at module-load time would be a genuine
    # load-order-dependent circular import (verified: it broke when
    # turn_actions was the first of the pair ever imported). Deferring to
    # call time is safe -- by the time run_turn_loop actually runs, both
    # modules are always already fully loaded. Mirrors shared/state.py's
    # own local-import precedent for the identical reason.
    from pursuit.network.turn_actions import await_opponent_turn, take_my_turn  # noqa: PLC0415

    outcome: Outcome | None = None
    first, second = (
        (take_my_turn, await_opponent_turn)
        if ctx.role == "police"
        else (await_opponent_turn, take_my_turn)
    )
    while ctx.machine.state not in TERMINAL_STATES:
        outcome = await first(ctx)
        if outcome is not None or ctx.machine.state in TERMINAL_STATES:
            break
        outcome = await second(ctx)
        if outcome is not None or ctx.machine.state in TERMINAL_STATES:
            break

    if ctx.machine.state not in TERMINAL_STATES:
        ctx.machine.attempt(State.GAME_OVER)
    if outcome is not None:
        append_event(
            ctx.log_path,
            turn_events.game_over_record(
                game_uid=ctx.game_uid, turn=ctx.state.turn, sender=ctx.role, outcome=outcome,
            ),
        )
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
