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
"""

from __future__ import annotations

from pursuit.network import turn_commit_send
from pursuit.network.agent_context import AgentContext
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.hint_payload import HintKey

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


def _usable_stamp(buffer: dict, sender: str) -> int | None:
    """The turn stamp on the payload already buffered for *sender*, or
    None when there is no usable one (nothing buffered, or a stamp we
    refuse to trust).

    This reads PEER DATA and must never raise. `validate_hint_payload`
    runs only inside `build_hint`, on the SEND path -- `grep -rn
    validate_hint_payload src/` returns that one call site. The inbound
    path is `tools.receive_hint` -> `_accept` -> `Envelope.from_dict`,
    which validates the payload as nothing more than `isinstance(payload,
    dict)` on what its own docstring calls an attacker-controlled wire
    dict. So the stamp may be missing, None, `"3"`, a float, a list or a
    bool, and a bare `turn >= stored[...]` would raise `TypeError` inside
    `record_hint` -- caught by NO call site (`await_opponent_turn` catches
    only `HintProtocolError`), so it escapes `run_turn_loop` and ends the
    game. That is exactly the forfeit-caused-by-a-hint failure 04-12's
    deviation exists to prevent.

    Anything that is not a plain int is therefore "no usable stamp",
    bool included -- mirroring `envelope._require_non_bool_int`."""
    stored = buffer.get(sender)
    if not isinstance(stored, dict):
        return None
    stamp = stored.get(HintKey.TURN.value)
    if isinstance(stamp, bool) or not isinstance(stamp, int):
        return None
    return stamp


def _buffer_if_not_older(buffer: dict, sender: str, turn: int, payload: dict) -> None:
    """Overwrite only with a hint at least as new as the one already
    buffered for this sender. Unconditional overwrite was safe only while
    at most ONE turn was ever admissible; with lookback in play two hints
    from the same sender can both pass the window, and an out-of-order
    OLDER one would clobber a fresher one -- silently feeding stale
    evidence to the belief update.

    A payload with no usable stamp is simply replaced, so the existing
    same-turn-overwrite semantics (`{"text": ...}` with no turn key) are
    unchanged.

    Consequence, stated rather than discovered later: the stamp is
    peer-controlled, so a peer can make its own hint sticky by stamping a
    huge turn. Self-inflicted on a best-effort channel whose content is a
    CLAIM anyway, and the lookback window still expires it."""
    stamp = _usable_stamp(buffer, sender)
    if stamp is None or turn >= stamp:
        buffer[sender] = payload


# 05-14 (05-UAT.md Round 2, G8). `decode_turn_hint` POPS
# `ctx.incoming_hints` (`turn_language_io.py:59`) and `_buffer_if_not_older`
# above compares an arrival only against what is STILL buffered -- so a
# hint re-sent for turn N-1 after a pop sailed through the (correctly)
# widened window and was decoded a SECOND time, re-driving
# `observe_reliability` and the belief update on evidence already counted.
# Double-counted evidence corrupts the posterior, which is the one thing
# the strategy layer is entitled to trust. Before 05-06 widened the window
# the old `turn < ctx.state.turn` guard dropped the duplicate as a side
# effect; nothing did afterwards.
#
# `ctx.pending_hints` becomes the marker store, and that is a REPURPOSING,
# not a new field: it was declared (`agent_context.py:112`), cleared
# (`turn_resolve.py:96`) and written (below) with ZERO production readers,
# and `maybe_resolve` already clears it exactly once per resolved turn --
# which is precisely the right lifetime for a replay guard whose window is
# one turn wide. So `agent_context.py`, `turn_resolve.py` and
# `test_turn_buffer.py`'s four `pending_hints` assertions need no edit;
# those assertions stop being a write-only-buffer trap the moment the
# field is genuinely read.
#
# MARKER AND WINDOW DOVETAIL rather than overlap, and the window WIDTH is
# byte-unchanged: within one joint turn the marker refuses the repeat, and
# across the `maybe_resolve` that clears the marker our own turn counter
# has advanced, so the one-turn window refuses it instead. Residual, stated
# rather than discovered later: a peer that stamps a FUTURE turn can still
# get its own hint re-admitted after a resolve -- the same self-inflicted
# stickiness `_buffer_if_not_older` already documents, on a channel whose
# content is a CLAIM anyway.
def _is_replay(ctx: AgentContext, sender: str, turn: int) -> bool:
    """True when this arrival would be decoded a SECOND time.

    "Already decoded" is `incoming_hints[sender]` ABSENT while
    `pending_hints[sender]` is PRESENT -- the two are written together
    below, and only `incoming_hints` is popped, so that pair is what
    distinguishes *already decoded* from *never arrived*.

    Only a STRICTLY NEWER stamp re-enters. `_buffer_if_not_older`'s
    inclusive `>=` is right for an overwrite and WRONG here -- reusing it
    unexamined re-admits the exact repeat this guard exists to block. An
    arrival with no usable stamp cannot prove it is newer either, so it
    does not re-enter: the same "peer data proves nothing until it does"
    rule `_usable_stamp` keeps, and it never raises on peer input."""
    if sender in ctx.incoming_hints or sender not in ctx.pending_hints:
        return False
    stamp = _usable_stamp(ctx.pending_hints, sender)
    return stamp is None or turn <= stamp


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
    pops `incoming_hints`; `pending_hints` survives that pop and is read
    back by `_is_replay` as this turn's consumed marker (05-14).

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

    05-14 (G8): one inbound hint is decoded AT MOST ONCE -- `_is_replay`
    rejects a re-send of something already popped, WITHOUT narrowing the
    window (see that helper). Both guards sit after the log, for 05-06's
    reason: a hint we drop still crossed the wire."""
    turn_commit_send.log_received(
        ctx,
        Envelope(type=MessageType.HINT, turn=turn, sender=sender, payload=payload),
        state_from=ctx.machine.state,
        state_to=ctx.machine.state,
        local_turn=ctx.state.turn,
    )
    if turn < ctx.state.turn - _HINT_LOOKBACK_TURNS:
        return
    if _is_replay(ctx, sender, turn):
        return
    _buffer_if_not_older(ctx.pending_hints, sender, turn, payload)
    _buffer_if_not_older(ctx.incoming_hints, sender, turn, payload)
