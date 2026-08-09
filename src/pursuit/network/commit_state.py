"""D-58/D-66 per-turn commit-reveal scratch state -- split out of
agent_context.py at the 150-code-line gate (Segal Table 5): `AgentContext`
itself plus `build_context`'s NET-02 wiring concern already filled that
file; `PendingAction`/`CommitTurnState` are a separate concern (what the
responder's decide-now step stashes for its own later reveal) and have no
dependency on `AgentContext` itself, so they split cleanly.

Deviation (Rule 1 - bug prevention): `PendingAction` carries three fields
beyond 06-PLAN-OUTLINE.md's literal five-field sketch -- `action_payload`,
`h_commit`, `turn`. By the time `turn_commit.reveal_pending` runs,
`ctx.state` has already advanced past `engine.resolve_turn` (this plan's
own turn_actions.py ordering calls `maybe_resolve` BEFORE
`reveal_pending`, mirroring the initiator's existing position) -- so
`ctx.state`/`ctx.state.turn` no longer describe the pre-turn snapshot the
committed payload was built from. Re-deriving the composite action dict
at reveal time from a post-resolve `ctx.state` would (a) risk revealing a
payload that does not byte-match what was actually hashed and ledgered,
breaking D-59's audit chain outright, and (b) mis-tag the REVEAL
envelope's own turn number. Stashing the exact already-built dict, its
h_commit (for precise ACK matching) and its turn number is the minimal
fix that keeps REVEAL provably identical to what was committed.
"""

from __future__ import annotations

from dataclasses import dataclass

Coord = tuple[int, int]


@dataclass
class PendingAction:
    """The responder's fully-decided action for THIS turn (D-58), built
    once during `turn_commit.await_and_respond`'s decide-now step and
    consumed once by this role's own later `turn_commit.reveal_pending` --
    never rebuilt, so a stateful brain (BeliefAdapter's RNG/belief) is
    invoked exactly once per turn."""

    move: Coord
    barrier: Coord | None
    plan: object | None
    """DeceptionPlan | None -- typed `object` to avoid a shared/network
    import cycle here; the real type lives in deception_types.py."""
    incoming_log: dict
    regime: str
    action_payload: dict
    """The exact D-59/D-66 composite dict already committed+ledgered --
    `reveal_pending` sends THIS verbatim, never a re-derived one."""
    h_commit: str
    """This side's own commit hash for the turn -- lets `reveal_pending`
    match the specific ACK it is still waiting for, precisely."""
    turn: int
    """The turn this action was decided for -- captured before
    `maybe_resolve` can advance `ctx.state.turn` out from under it."""


@dataclass
class CommitTurnState:
    """Per-game mutable holder, one instance per AgentContext, never
    reconstructed mid-game. Every field returns to its idle default at
    turn resolution (D-58, D-66)."""

    pending_action: PendingAction | None = None
    own_ack_received: bool = False
    """Set when this side's own ACK arrives EARLY -- while
    `await_and_respond` is still waiting for the opponent's REVEAL, before
    this side's own later `reveal_pending` runs -- so `reveal_pending`
    never blocks on a message that already arrived and cannot arrive
    twice. Reset to False by `reveal_pending` once consumed."""
    chosen_barrier: Coord | None = None
    """The barrier companion to choose_destination's last return value
    (D-66) -- choose_destination stays a thin Coord-only wrapper (existing
    callers/tests need that), so its full Decision is stashed here as a
    side effect, read immediately after by whichever function just called
    it. Reset on every choose_destination call, never left stale across
    turns."""
