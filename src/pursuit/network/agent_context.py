"""AgentContext -- split out of orchestrator.py/agent_lifecycle.py at the
150-code-line gate (Segal Table 5), not by responsibility: both origin
files were AT their ceiling before this plan, so `security`/`commit_state`
had no room to land in place. `Coord`, `ChooseMove`, `AgentContext` (moved
verbatim from orchestrator.py) and `build_context` (moved verbatim from
agent_lifecycle.py) live here; both origins re-export every name so no
existing `from pursuit.network.orchestrator import AgentContext` /
`from pursuit.network.agent_lifecycle import build_context` call site
needs to change. `default_context` itself STAYS in agent_lifecycle.py
(unmoved) and now imports `build_context` from here instead of defining
it in place.

`PendingAction`/`CommitTurnState` (D-58/D-66 scratch state) live in the
sibling `commit_state.py`, split out at the SAME 150-line gate once this
file's own content plus theirs exceeded it -- re-imported and re-exported
here so `agent_context.CommitTurnState`/`agent_context.PendingAction`
still resolve, and `AgentContext.commit_state` still types against them.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from pursuit.network.commit_state import CommitTurnState, Coord, PendingAction  # noqa: F401
from pursuit.network.language_wiring import LanguageRuntime
from pursuit.network.peer_runtime import PeerRuntime
from pursuit.network.state_machine import TransitionReporter, TurnStateMachine
from pursuit.network.watchdog import Watchdog
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction
from pursuit.shared.config import GameParams
from pursuit.shared.network_config import NetworkParams
from pursuit.shared.resolution import BOOK_ONLY, ResolutionRules
from pursuit.shared.security_config import SecurityParams
from pursuit.shared.state import GameState
from pursuit.strategy.base import BrainBase
from pursuit.strategy.beliefadapter import BeliefAdapter
from pursuit.strategy.scentfield import ScentField

if TYPE_CHECKING:
    from pursuit.network.agent_wiring import AgentConfig

ChooseMove = Callable[[GameState, str, GameParams], Coord]
"""The Phase-3 replacement point (design note 5): a plain algorithm, never an
LLM (rule 25). Defaults to `first_legal_move` when unset on the context."""


@dataclass
class AgentContext:
    """Everything one process's turn loop needs -- an INSTANCE, never a
    module-level global (NET-02). Two contexts built in the same interpreter
    share no field: build a fresh one per process.

    `rules` are the negotiated terminal predicates (RULES-RESOLUTION.md
    Sec5); BOOK_ONLY is the safe default until agent_lifecycle.py loads a
    real per-agent resolution.json onto a live context.
    `pending_cop_action`/`pending_thief_move` buffer this turn's actions
    until both are known (turn_actions.py), then resolve_turn runs exactly
    once and both slots are cleared. `pending_hints` (Phase 4, D-47)
    buffers this turn's hint(s) by sender the same way, cleared alongside
    the action slots when the turn resolves (turn_buffer.py).

    Phase 4 (04-12) adds four OPTIONAL fields, defaulting to None/empty so
    a pre-existing fixture that never sets them is unaffected: `brain` (the
    registry-built mover), `scent_field` (this role's trail, held for the
    game), `language` (the gatekeeper/provider/hint-bank runtime), and
    `incoming_hints` (the LAST hint per sender -- unlike `pending_hints`,
    NOT cleared at resolve, so `take_my_turn` decodes it one call later;
    see turn_language.py).

    Phase 6 (06-02) adds `security` (SecurityParams, REQUIRED -- no
    default, so every construction site must be explicit about the
    commit-reveal toggle) and `commit_state` (CommitTurnState, D-58/D-66
    scratch state, defaulted so no pre-existing fixture needs an edit)."""

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
    security: SecurityParams
    choose_move: ChooseMove | None = None
    rules: ResolutionRules = BOOK_ONLY
    pending_cop_action: CopAction | None = None
    pending_thief_move: Coord | None = None
    pending_hints: dict[str, dict] = field(default_factory=dict)
    brain: BrainBase | BeliefAdapter | None = None
    scent_field: ScentField | None = None
    language: LanguageRuntime | None = None
    incoming_hints: dict[str, dict] = field(default_factory=dict)
    commit_state: CommitTurnState = field(default_factory=CommitTurnState)


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
    brain: BrainBase | BeliefAdapter | None = None,
    scent_field: ScentField | None = None,
    language: LanguageRuntime | None = None,
) -> AgentContext:
    """PURE WIRING: every collaborator is injected, nothing is constructed
    implicitly. The seam the NET-02 isolation tests and every fake-driven
    test use. `brain`/`scent_field`/`language` are the Phase-4 (04-12)
    additions; `security` (Phase 6) comes straight off `cfg.security`."""
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
        security=cfg.security,
        choose_move=choose_move,
        rules=cfg.rules,
        brain=brain,
        scent_field=scent_field,
        language=language,
    )
