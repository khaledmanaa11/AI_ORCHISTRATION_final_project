"""`AgentContext` -> `LocalView` (D-74): the ONE module in this repository
permitted to read `ctx.state`, and the only place the rules 8-9 projection
happens.

Everything upstream of here legitimately holds the engine's true joint
position; everything downstream of here structurally cannot express it. That
is the whole design: `scripts/check_local_truth.py` enforces the downstream
half against `src/pursuit/gui/`, and `tests/unit/test_view_builder.py`
AST-scans `src/pursuit/sdk/` to prove this file is the only upstream reader.

Two deliberate shapes:

* **The belief and scent grids are densified.** `ScentField` keys its two
  dicts by coordinate; handing those to a view would put every cell on the
  board into it as a VALUE, the opponent's true cell among them. Both become
  positional row-major floats instead. `BeliefMap.posterior()` is already
  dense, and its `None` case is honest -- belief disabled this game yields
  `belief=None`, never a fabricated uniform grid, matching the convention
  `network/turn_language.belief_snapshot` already uses.
* **The hint history is an instance the caller owns and passes in.**
  `ctx.incoming_hints` holds only the LAST hint per sender and is never
  cleared (`agent_context.py:116`), so the turn-by-turn log has to be
  accumulated. It is NEVER a module-level global and NEVER a class
  attribute: two `AgentContext`s in one interpreter share no field (NET-02,
  rule 2), and a shared accumulator would break that for the GUI too. The
  live view must not read the wire log for it either -- that would put file
  I/O and replay coupling into what has to stay a thin shell.

Inbound payloads are hostile by 05-12's boundary rule: `tools.receive_hint`
validates them as nothing more than `isinstance(payload, dict)`. Nothing
below raises on one, and a field that cannot be trusted is DROPPED rather
than coerced into something plausible -- a dashboard that dies mid-game is
worse than one with a blank cell.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pursuit.sdk.local_view import BeliefView, Grid, HintView, LocalView, ScentView
from pursuit.shared.deception_types import Intent
from pursuit.shared.roles import COP, engine_agent
from pursuit.strategy.beliefadapter import BeliefAdapter

if TYPE_CHECKING:  # pragma: no cover -- annotation only, never imported at runtime
    from pursuit.network.agent_context import AgentContext

#: The sender label for a hint THIS peer sent. Not a wire role: the log is
#: one peer's own, and "self" cannot collide with "police"/"thief".
OWN_HINT_SENDER = "self"

_KNOWN_INTENTS = frozenset(intent.value for intent in Intent)


@dataclass
class HintHistory:
    """The caller-owned, append-only hint log. Never cleared, never shared."""

    entries: list[HintView] = field(default_factory=list)
    _latest: dict = field(default_factory=dict)

    def observe(self, ctx: AgentContext) -> None:
        """Fold `ctx.incoming_hints` in once. Idempotent per (sender, hint):
        a refresh loop re-reads the same buffered hint on every tick."""
        for sender, payload in sorted(ctx.incoming_hints.items(), key=lambda kv: str(kv[0])):
            hint = _incoming_hint(str(sender), payload)
            if hint is not None:
                self._append(hint)

    def record_outgoing(self, *, turn: int | None, text: str, intent: str | None) -> None:
        """Record a hint THIS peer sent. Its intent flag is our own, and is
        the one entry in the log that is a fact rather than a claim."""
        self._append(
            HintView(
                sender=OWN_HINT_SENDER, turn=_stamp(turn), text=text,
                claimed_intent=_intent(intent),
            )
        )

    def _append(self, hint: HintView) -> None:
        if self._latest.get(hint.sender) == hint:
            return
        self._latest[hint.sender] = hint
        self.entries.append(hint)


def build_local_view(
    ctx: AgentContext, history: HintHistory, *, idle_seconds: float | None = None
) -> LocalView:
    """Project one refresh tick of local truth. `idle_seconds` comes from
    the caller because `Watchdog` exposes no public idle reading and this
    plan does not edit `network/`."""
    history.observe(ctx)
    own_cell = ctx.state.cop if engine_agent(ctx.role) == COP else ctx.state.thief
    return LocalView(
        role=ctx.role,
        board_size=ctx.params.board_size,
        turn=ctx.state.turn,
        own_cell=own_cell,
        declared_barriers=tuple(sorted(ctx.state.barriers)),
        barriers_placed=ctx.state.barriers_placed,
        belief=_belief_view(ctx),
        scent=_scent_view(ctx),
        hints=tuple(history.entries),
        machine_state=ctx.machine.state.value,
        idle_seconds=idle_seconds,
        watchdog_threshold_seconds=float(ctx.net.watchdog_threshold),
    )


def _belief_view(ctx: AgentContext) -> BeliefView | None:
    if not isinstance(ctx.brain, BeliefAdapter):
        return None
    belief = ctx.brain.belief
    return BeliefView(
        rows=belief.posterior(), entropy=belief.entropy(),
        argmax=belief.argmax(), reliability=ctx.brain.reliability.value,
    )


def _scent_view(ctx: AgentContext) -> ScentView | None:
    scent = ctx.scent_field
    if scent is None:
        return None
    size = ctx.params.board_size
    return ScentView(own=_dense(scent.own, size), opponent=_dense(scent.opponent, size))


def _dense(cells: dict, board_size: int) -> Grid:
    """A coordinate-keyed grid as positional row-major floats."""
    return tuple(
        tuple(float(cells.get((row, col), 0.0)) for col in range(board_size))
        for row in range(board_size)
    )


def _incoming_hint(sender: str, payload) -> HintView | None:
    """One buffered inbound payload as a log entry, or None when it carries
    no text at all. Total over peer data -- it may be any object."""
    from pursuit.network.hint_payload import HintKey  # noqa: PLC0415

    if not isinstance(payload, dict):
        return None
    text = payload.get(HintKey.TEXT.value)
    if not isinstance(text, str):
        return None
    return HintView(
        sender=sender, turn=_stamp(payload.get(HintKey.TURN.value)), text=text,
        claimed_intent=_intent(payload.get(HintKey.INTENT.value)),
    )


def _stamp(value) -> int | None:
    """A turn stamp we are willing to show, else None. `bool` is an `int`
    subclass and would render as turn 1 -- `turn_hint_store.usable_stamp`
    rejects it for the same reason."""
    return None if isinstance(value, bool) or not isinstance(value, int) else value


def _intent(value) -> str | None:
    """A declared intent flag, or None. Never coerced: an unrecognised flag
    is 'the sender declared nothing we understand', not 'truth'."""
    return value if isinstance(value, str) and value in _KNOWN_INTENTS else None
