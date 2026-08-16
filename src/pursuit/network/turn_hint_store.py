"""The two per-sender inbound-hint buffers and the rules that govern them
-- split out of `turn_hint_buffer.py` at the 150-code-line gate (Segal
Table 5), 05-14. That file measured 141/150 once G8's replay guard landed
and `consume_hint` did not fit; split, never compressed (CLAUDE.md). It is
the third split this `turn_buffer.py` family has taken for the same reason
(`turn_resolve.py` 04-12, `turn_hint_buffer.py` itself 05-06).

The seam is real and not merely arithmetic. `turn_hint_buffer.record_hint`
owns the INGESTION policy -- log the receipt first, then apply the drop
window -- while this module owns the two buffers themselves: what counts
as a usable peer stamp, which of two arrivals wins, what "already decoded"
means, and the consumption that writes that marker. `decode_turn_hint`
(`turn_language_io.py`) is the other half of the same contract and calls
`consume_hint` here rather than popping a dict it does not own.

Nothing here logs, sends, or raises. Every function is TOTAL over peer
data (05-12's boundary rule): the stamps read below arrive through
`tools.receive_hint` -> `_accept` -> `Envelope.from_dict`, which validates
a payload as nothing more than `isinstance(payload, dict)`.
"""

from __future__ import annotations

from pursuit.network.agent_context import AgentContext
from pursuit.network.hint_payload import HintKey


def usable_stamp(buffer: dict, sender: str) -> int | None:
    """The turn stamp on the payload already buffered for *sender*, or
    None when there is no usable one (nothing buffered, or a stamp we
    refuse to trust).

    This reads PEER DATA and must never raise. `validate_hint_payload`
    runs only inside `build_hint`, on the SEND path -- `grep -rn
    validate_hint_payload src/` returns that one call site. The inbound
    path validates the payload as nothing more than `isinstance(payload,
    dict)` on what `_accept`'s own docstring calls an attacker-controlled
    wire dict. So the stamp may be missing, None, `"3"`, a float, a list
    or a bool, and a bare `turn >= stored[...]` would raise `TypeError`
    inside `record_hint` -- caught by NO call site (`await_opponent_turn`
    catches only `HintProtocolError`), so it escapes `run_turn_loop` and
    ends the game. That is exactly the forfeit-caused-by-a-hint failure
    04-12's deviation exists to prevent.

    Anything that is not a plain int is therefore "no usable stamp",
    bool included -- mirroring `envelope._require_non_bool_int`."""
    stored = buffer.get(sender)
    if not isinstance(stored, dict):
        return None
    stamp = stored.get(HintKey.TURN.value)
    if isinstance(stamp, bool) or not isinstance(stamp, int):
        return None
    return stamp


def buffer_if_not_older(buffer: dict, sender: str, turn: int, payload: dict) -> None:
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
    stamp = usable_stamp(buffer, sender)
    if stamp is None or turn >= stamp:
        buffer[sender] = payload


def is_replay(ctx: AgentContext, sender: str, turn: int) -> bool:
    """True when this arrival would be decoded a SECOND time (05-14, G8).

    "Already decoded" is `incoming_hints[sender]` ABSENT while
    `pending_hints[sender]` is PRESENT. `consume_hint` below establishes
    exactly that pair, which is what distinguishes *already decoded* from
    *never arrived*.

    Only a STRICTLY NEWER stamp re-enters. `buffer_if_not_older`'s
    inclusive `>=` is right for an overwrite and WRONG here -- reusing it
    unexamined re-admits the exact repeat this guard exists to block. An
    arrival with no usable stamp cannot prove it is newer either, so it
    does not re-enter: the same "peer data proves nothing until it does"
    rule `usable_stamp` keeps, and it never raises on peer input."""
    if sender in ctx.incoming_hints or sender not in ctx.pending_hints:
        return False
    stamp = usable_stamp(ctx.pending_hints, sender)
    return stamp is None or turn <= stamp


# WHY THE MARKER IS WRITTEN HERE, AT CONSUMPTION, AND NOT LEFT TO
# `record_hint`'s own arrival-time write into `pending_hints`. 05-14's plan
# proposed the latter, reasoning that `maybe_resolve` already clears
# `pending_hints` once per resolved turn and that this is the marker's
# right lifetime. MEASURED, that is half right -- right for the RESPONDER
# and wrong for the INITIATOR, and both halves are on the record:
#
#   * RESPONDER (attempt-4 machine B, 6 of 6 inbound records at
#     `record_turn == envelope_turn + 1`): the hint arrives AFTER its
#     receiver has resolved, so arrival and decode fall inside the same
#     clear-interval and the arrival-time write is still there at decode.
#   * INITIATOR (attempt-4 machine A, 5 of 5 at delta 0, both games): the
#     hint arrives DURING the turn, is buffered into both dicts, and then
#     `maybe_resolve` CLEARS `pending_hints` before `take_my_turn` decodes
#     it one turn later. The arrival-time marker is destroyed before the
#     consumption it was supposed to mark. Probed directly: with the
#     marker left at arrival the initiator's re-sent hint is decoded
#     TWICE (`decodes=2`, second outcome `no_evidence`) while the
#     responder's is decoded once.
#
# Writing it at consumption fixes both, because the marker's lifetime then
# starts when the evidence is actually spent. MARKER AND WINDOW DOVETAIL
# and the window WIDTH is byte-unchanged: inside one joint turn the marker
# refuses the repeat, and across the `maybe_resolve` that clears the
# marker our own turn counter has advanced past the stamp, so the one-turn
# window refuses it instead.
#
# Residual, stated rather than discovered later: a peer that stamps a
# FUTURE turn can still get its own hint re-admitted after a resolve --
# the same self-inflicted stickiness `buffer_if_not_older` documents, on a
# channel whose content is a CLAIM anyway.
def consume_hint(ctx: AgentContext, sender: str) -> dict | None:
    """Take *sender*'s buffered hint for decoding, and leave the consumed
    marker `is_replay` reads.

    `incoming_hints` is popped -- that half is `decode_turn_hint`'s
    pre-05-14 behaviour, byte for byte. What is new is that the payload is
    left in `pending_hints` on the way out, so the fact that this evidence
    has been spent survives the pop. Nothing is written when there was
    nothing to consume: an untouched `pending_hints` is what keeps an
    older marker alive for the rest of its turn."""
    payload = ctx.incoming_hints.pop(sender, None)
    if payload is not None:
        ctx.pending_hints[sender] = payload
    return payload
