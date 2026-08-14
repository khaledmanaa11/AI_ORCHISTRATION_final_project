"""D-61's game identity: the ONE id a whole match runs under, and the
mutable binding that lets construction-time wiring follow it.

05-UAT.md G2: before this module, the handshake-negotiated game id reached
exactly one artifact -- the Step-0 declaration FILENAME. `run_agent` minted
a process-local `secrets.token_hex(8)` and froze `log_path` (and, through
`turn_commit_ledger.ledger_path`, the D-64 ledger stem) around it BEFORE
the handshake ran, and `turn_commit_ledger.commit_own_action` sealed that
same un-negotiated id inside every hashed commit. The 2026-08-13 remote
round therefore produced four artifacts that cannot be joined: machine A's
log/ledger say `074fc2b16888899e`, machine B's say `d50ceb00be724b93`, and
both machines' declarations say `074fc2b16888899e`.

`GameIdentity` is the fix's load-bearing half. `agent_wiring`'s two JSONL
sink closures (`make_transition_reporter`, `make_freeze_handler`) are bound
at CONSTRUCTION time -- design note 12: they are handed to `TurnStateMachine`
and `Watchdog` before an `AgentContext` exists, so they cannot close over a
context and read `ctx.log_path` later. Handing them a mutable value object
instead lets them resolve the sink AT CALL TIME, so the one-off rename in
`adopt_negotiated_game_id` moves them too instead of leaving them writing to
the pre-negotiation path.

Both closures RELOCATED here from `agent_wiring.py` (148/150 -- no room) and
are re-exported from there, so `agent_lifecycle.make_transition_reporter`
and every existing importer and test resolve unchanged. Same
relocate-and-re-export move `secret_wiring.py` made for the same reason
(05-02).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pursuit.network import turn_events
from pursuit.network.event_log import append_event
from pursuit.network.state_machine import State, TransitionReporter, TransitionSeverity

if TYPE_CHECKING:  # typing only -- an eager import here would be a real cycle
    from pursuit.network.agent_context import AgentContext
    from pursuit.network.handshake_evaluate import HandshakeResult


@dataclass
class GameIdentity:
    """The MUTABLE `(game_uid, log_path)` binding a construction-time
    closure can follow across D-61's one-off rename. Deliberately NOT
    frozen and deliberately NOT a copy of any context field: one instance
    is shared by `default_context`'s two sinks and the live `AgentContext`,
    so `adopt_negotiated_game_id` rebinds all three by mutating this."""

    game_uid: str
    log_path: Path


def negotiated_game_id(role: str, own_uid: str, peer_game_id: str | None) -> str:
    """D-61's ONE policy definition (moved verbatim from the now-deleted
    `agent_audit_wiring._declared_game_id`, whose own docstring scoped it to
    the declaration filename): police keeps its own `game_uid`; the thief
    adopts the initiator's `peer_game_id`, falling back to its own when the
    peer published none.

    D-61 binds US, not them. `handshake_evaluate` reads `peer_game_id`
    unconditionally and nothing anywhere requires a peer to adopt ours or to
    keep its own -- see `security/audit.py`'s note on why the committed
    game_id is checked by MEMBERSHIP rather than equality."""
    if role == "police":
        return own_uid
    return peer_game_id or own_uid


def _sink(identity: GameIdentity | None, log_path: Path, game_uid: str) -> tuple[Path, str]:
    """Resolve `(log_path, game_uid)` AT CALL TIME. `identity is None` -- the
    default for every pre-existing caller -- returns the values frozen at
    construction, i.e. byte-identical behaviour to before this module. One
    definition, so the two sinks below cannot drift apart."""
    if identity is None:
        return log_path, game_uid
    return identity.log_path, identity.game_uid


def make_transition_reporter(
    log_path: Path, *, game_uid: str, role: str, identity: GameIdentity | None = None,
) -> TransitionReporter:
    """NET-05 sink: every illegal transition persists to the JSONL log (D-11)
    and echoes one console line. `turn=0` here is structural, not a game
    number: 02-03's TransitionReporter Protocol carries no turn field."""

    def _reporter(
        *, current: State, target: State, severity: TransitionSeverity, reason: str
    ) -> None:
        sink_path, sink_uid = _sink(identity, log_path, game_uid)
        record = turn_events.illegal_transition_record(
            game_uid=sink_uid, turn=0, sender=role, current=current, target=target,
            severity=severity, reason=reason,
        )
        append_event(sink_path, record, echo=print)

    return _reporter


def make_freeze_handler(
    log_path: Path, *, game_uid: str, role: str, threshold_seconds: float,
    identity: GameIdentity | None = None,
) -> Callable[[], None]:
    """NET-07 sink (RESEARCH Pitfall 6): writes and fsyncs (via append_event)
    a watchdog_incident record BEFORE Watchdog's injected exit_action runs.
    `idle_seconds` is reported as the threshold itself -- the on_freeze seam
    is a zero-argument callable and carries no measured idle duration; the
    threshold is the one honest lower bound available at this call site."""

    def _on_freeze() -> None:
        sink_path, sink_uid = _sink(identity, log_path, game_uid)
        record = turn_events.watchdog_incident_record(
            game_uid=sink_uid, turn=0, sender=role,
            idle_seconds=threshold_seconds, threshold_seconds=threshold_seconds,
        )
        append_event(sink_path, record)

    return _on_freeze


def adopt_negotiated_game_id(ctx: AgentContext, result: HandshakeResult) -> None:
    """Make D-61's negotiated id the id THIS WHOLE GAME runs under.

    Called from `agent_entrypoint.run_agent` immediately after
    `if not result.agreed: return None` and BEFORE `write_declaration` /
    `run_turn_loop`. That position is a dependency, not a preference:

    - `turn_commit_ledger.ledger_path` derives the D-64 nonce ledger's name
      from `ctx.log_path.stem`, and its first writer
      (`turn_commit_ledger.commit_own_action`) runs INSIDE the turn loop --
      after this point -- so renaming the log here moves the ledger with it
      and there is no ledger file to rename. Reorder this call after
      `run_turn_loop` and that stops being true, loudly;
    - `commit_own_action` also seals `ctx.game_uid` into every hashed commit
      (`build_state_record(game_id=ctx.game_uid)`), which is how the
      2026-08-13 round ended up with the two sides committing DIFFERENT
      game_ids in the same match;
    - at this instant the log holds at most the benign symmetric-handshake
      `illegal_transition` record, verified against the retained evidence.

    Nothing here is an error case. The source file may not exist (no illegal
    transition was logged) and the resolved id may equal the current one
    (always true for police) -- both mean "no filesystem work", not a fault.
    """
    resolved = negotiated_game_id(ctx.role, ctx.game_uid, result.peer_game_id)
    ctx.negotiated_game_id = result.peer_game_id
    # ORDERING IS LOAD-BEARING -- see security/audit.py's own re-statement of
    # it. Capture the two ids that were on the table BEFORE the rebind below.
    # `ctx.game_uid` is about to become `resolved`, and on the thief that IS
    # `result.peer_game_id`, so a set built after this point holds ONE element
    # and the audit's membership check silently degenerates to equality --
    # which then accuses an honest peer that merely swapped conventions.
    ctx.candidate_game_ids = (
        {ctx.game_uid, result.peer_game_id} if result.peer_game_id is not None else None
    )
    if resolved == ctx.game_uid:
        return
    target = ctx.log_path.parent / f"{resolved}{ctx.log_path.suffix}"
    if ctx.log_path.exists() and ctx.log_path != target:
        ctx.log_path.replace(target)
    ctx.log_path = target
    ctx.game_uid = resolved
    if ctx.identity is not None:
        ctx.identity.log_path = target
        ctx.identity.game_uid = resolved
