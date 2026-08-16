"""Inbound-HINT ingestion -- `record_hint`, split out of `turn_buffer.py`
at the 150-code-line gate (Segal Table 5). This is the SAME split
`turn_resolve.py` already made out of that same file for the same reason
(04-12): `turn_buffer.py` measured 146/150 and the receipt-logging this
module adds does not fit. `turn_buffer` re-exports the name, so
`turn_buffer.record_hint` still resolves for all three call sites
(`turn_buffer.await_move`, `turn_buffer.drain_trailing_hint`,
`turn_commit_wait.next_protocol_message`, which references it as
`turn_buffer.record_hint(...)`) and for any test that monkeypatches it
there.

Why the module exists beyond the line gate (05-UAT.md G3): HINT was the
only `MessageType` logged on SEND and never on RECEIVE. Machine A's
2026-08-13 remote-round log carries 5 `message_sent`+`hint` records and
ZERO `message_received`+`hint`, while its own `language_turn` records
carry the thief's verbatim hint texts with `outcome: evidence` -- the
hints demonstrably arrived and drove belief updates, with no durable
record that they ever crossed the wire (D-11/D-14, rule 20).

05-14 splits the buffers themselves into `turn_hint_store.py` at the same
gate (this file measured 141/150 once G8's replay guard landed). What is
left here is the INGESTION policy alone: log the receipt, then decide
whether the arrival may enter the buffers at all.
"""

from __future__ import annotations

from pursuit.network import turn_commit_send, turn_hint_store
from pursuit.network.agent_context import AgentContext
from pursuit.network.envelope import Envelope, MessageType

# How many turns of lookback the receive window keeps (05-06, G4).
# Recorded in docs/PARAMETERS.md ("Derived protocol constants"), 05-14.
#
# Derivation, not a tuning knob: a side emits its hint for turn N at the
# TAIL of turn N -- after REVEAL(N) has been sent AND an LLM compose has
# run -- so the hint is first pulled off the receiver's queue once that
# receiver's own `maybe_resolve` has already advanced it to N + 1. With
# zero lookback the guard `turn < ctx.state.turn` is therefore
# structurally UNSATISFIABLE for a responder: every correctly stamped
# inbound hint is discarded before it reaches `ctx.incoming_hints`.
#
# TWO unconfounded measurements carry that (05-14 restatement):
#   (1) SHAPE, not a statistic. `decode_turn_hint` emits `no_hint` on
#       exactly ONE branch -- the buffer pop returning nothing -- and
#       that branch sits UPSTREAM of every provider and key concern. A
#       key-starved decode takes the other branch and logs `no_evidence`
#       WITH the text (`llm/decode.py:66-67`, the TemplateProvider
#       neutral result). So the thief's 5-of-5 `no_hint` in the
#       2026-08-13 round says the BUFFER WAS EMPTY, whatever the key
#       situation was.
#   (2) The post-fix 2026-08-16 attempt-4 round: the responder's SIX
#       inbound hint records all sit at `record_turn == envelope_turn
#       + 1` -- 6 of 6, exactly ON this boundary, so zero lookback
#       drops every one of them -- while the initiator's five sit at
#       delta 0, inside the window either way.
#
# The `token_spend.calls = 0` sentence this comment used to carry is
# DELETED, not merely reworded (05-14). That same zero also covers the
# COMPOSE half, whose texts came from the template bank
# (`services/language_turn.py:76-81`), so it is equally consistent with
# "no key at all" and cannot distinguish the two readings it was cited
# to distinguish.
#
# ONE turn is the MINIMUM that makes the channel deliverable at all. A
# hint older than the window is genuinely stale and still drops, so the
# drop rule keeps real content.
#
# WHY THIS ONE IS PUBLISHED IN PARAMETERS.md WHILE 05-12's
# `_MAX_PEER_GAME_ID` IS NOT: the two are treated differently ON
# PURPOSE, and neither should be harmonised to the other. This is a
# PROTOCOL constant -- it describes a message ORDER that two
# independent implementations have to agree on, so a reader reconciling
# this codebase against the book goes looking for it in the one file
# that holds the project's numbers, and not finding it there is the
# Table-5 hardcoded-value risk 05-UAT.md flagged. `_MAX_PEER_GAME_ID`
# is a STRUCTURAL limit derived from a filesystem's 255-byte path
# component: nobody should ever want to tune it and no legal game's
# outcome depends on it, so it stays a source constant. Published is
# not the same as negotiable -- PARAMETERS.md records this as DERIVED
# with no Status column, and there is still no config leaf anywhere
# (CLAUDE.md rule 1).
_HINT_LOOKBACK_TURNS = 1


def record_hint(ctx: AgentContext, sender: str, turn: int, payload: dict) -> None:
    """Log, then buffer, one inbound hint. A missing hint is simply never
    passed here, and never blocks resolution.

    Deviation (Rule 1 - bug, 04-12): TWO of 04-04's original rules --
    "late" and "duplicate" both raising `HintProtocolError` -- are
    replaced with silent drop / overwrite. The move and the hint are two
    INDEPENDENT network round-trips, each with its own (now real,
    variable-latency) decode/compose work between them; a genuine
    two-peer game measurably hits both timing patterns. Raising in either
    case turned ordinary jitter into a spurious `Outcome.TECHNICAL_LOSS`
    -- exactly the "forfeit caused by a hint" ruled out by 04-12's and
    05-06's must_haves alike. Only `await_move`'s SEPARATE "two
    consecutive hints, no move" cap still raises -- that one guards
    liveness, not hint timing.

    Also caches `payload` into `ctx.incoming_hints[sender]` (04-12) --
    UNLIKE `pending_hints`, this survives `maybe_resolve`'s clear, so
    whichever side's `take_my_turn` runs after the buffer already cleared
    (design note 7's "police sends first") can still decode the hint that
    arrived alongside the opponent's last revealed move. `decode_turn_hint`
    consumes `incoming_hints`; `pending_hints` is left holding what was
    consumed, as `turn_hint_store.is_replay`'s marker (05-14).

    05-06 (G3): the receipt is logged FIRST, ahead of the drop guard, on
    purpose -- a hint we DROP is still a thing that crossed the wire, and
    rule 20's replay evidence must show it.

    The Envelope is rebuilt locally instead of being threaded down from
    the caller, and nothing is lost by that: all three call sites have
    already established `envelope.type is MessageType.HINT` before
    calling, and each passes that same envelope's own `sender`/`turn`/
    `payload` verbatim. Keeping the `(ctx, sender, turn, payload)`
    signature leaves those three call sites and their tests
    byte-unmodified.

    Turn binding follows `turn_commit_send.log_received` exactly: the
    record's own top-level turn is OUR `ctx.state.turn`, while the nested
    envelope keeps the peer's declared `turn` verbatim as evidence. A
    hint record must never become an attacker-controllable audit join key
    (06-UAT.md Gap 1). Receiving a hint changes no state, so `state_from`
    and `state_to` are both the current one -- said explicitly rather
    than left implied.

    05-06 (G4): the drop window carries `_HINT_LOOKBACK_TURNS` of
    lookback -- see that constant for the derivation -- and the buffers
    keep the freshest hint per sender rather than the last one to
    arrive.

    05-14 (G8): one inbound hint is decoded AT MOST ONCE --
    `turn_hint_store.is_replay` rejects a re-send of something already
    consumed, WITHOUT narrowing the window (see that module for why the
    marker is written at consumption and not at arrival). Both guards sit
    after the log, for 05-06's reason: a hint we drop still crossed the
    wire."""
    turn_commit_send.log_received(
        ctx,
        Envelope(type=MessageType.HINT, turn=turn, sender=sender, payload=payload),
        state_from=ctx.machine.state,
        state_to=ctx.machine.state,
        local_turn=ctx.state.turn,
    )
    if turn < ctx.state.turn - _HINT_LOOKBACK_TURNS:
        return
    if turn_hint_store.is_replay(ctx, sender, turn):
        return
    turn_hint_store.buffer_if_not_older(ctx.pending_hints, sender, turn, payload)
    turn_hint_store.buffer_if_not_older(ctx.incoming_hints, sender, turn, payload)
