"""Instance SIX of the envelope-boundary class -- CLOSED and pinned (05-18, 08-05).

Split from `test_envelope_boundary_invariant.py` at the 150-code-line gate
(Segal Table 5) along a real seam: that file holds the CLASS guard -- the
invariant, enumerated from source across every pull site -- and this one holds
the single instance the guard found on its first run.

WHAT #19 WAS. `turn_buffer.await_move` is the commit-reveal TOGGLE-OFF wait,
and it had no type test of any kind: it buffered a HINT and returned everything
else to `await_opponent_turn`, which decoded it as a move. 05-18 measured it
across all nine `MessageType` members, police role:

    commit_reveal ON   0 of 9 unnamed reasons
    commit_reveal OFF  8 of 9 unnamed reasons, every one
                       'payload has neither direction nor x/y keys'

CLOSED BY 08-05: `await_move` now returns ONLY a MOVE, buffers a FINAL_REVEAL
on the way past, and keeps waiting through anything else. Re-measured at HEAD:

    commit_reveal ON   0 of 9
    commit_reveal OFF  1 of 9  -- and the one is MOVE itself, see below

THE BOOKMARK DID NOT FIRE, WHICH IS THE MOST USEFUL THING IN THIS FILE. The
previous version of this module asserted `counts["off"] > 0` over ALL NINE
types, so that whoever closed #19 would be failed and sent to the deferred
record. It did not fail, because the nine include MOVE -- the type this leg is
WAITING for -- and `envelope_of` builds it with a fixture payload that is not a
legal move, so the decoder rightly complains about it. That row was never part
of #19 and is not affected by its fix; it was inflating the count from 7 to 8
and would have kept the "still reproduces" assertion green forever.

So the accounting is done by NAME here, not by total. Nine members: HINT is
buffered, MOVE is awaited, and the remaining SEVEN are the foreign types #19
was about. All seven are closed; the MOVE row is a malformed MOVE being
rejected as a malformed MOVE, which is correct behaviour and is asserted as
such so nobody mistakes it for a regression or for an unfixed defect.
"""

from __future__ import annotations

import dataclasses

from pursuit.network import turn_actions
from pursuit.network.envelope import MessageType
from pursuit.network.state_machine import State
from pursuit.network.verdict import TechnicalWinReason
from tests.unit._early_reveal_fixtures import ON, accusations, envelope_of
from tests.unit._fakes_agent import make_ctx

_NAMED_REASONS = {reason.value for reason in TechnicalWinReason}
#: Buffered by this leg, and always was.
BUFFERED = MessageType.HINT
#: The type the leg is actually waiting for.
AWAITED = MessageType.MOVE
#: Everything else -- what #19 was about. Derived, never typed, so a new
#: MessageType member joins this set on the day it lands.
FOREIGN = tuple(m for m in MessageType if m not in (BUFFERED, AWAITED))


async def _unnamed_accusations(tmp_path, default_params, network_params, security, message_type):
    """Whether one well-formed arrival of *message_type* makes this side accuse
    the peer with a reason that is not a `TechnicalWinReason` member."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police",
        label=f"boundary-{security.commit_reveal}-{message_type.value}",
        security=security, initial_state=State.WAIT_OPPONENT,
    )
    ctx.runtime.queue.put_nowait(envelope_of(ctx, message_type))
    await turn_actions.await_opponent_turn(ctx)
    return [reason for reason in accusations(ctx) if reason not in _NAMED_REASONS]


def test_the_type_partition_covers_every_message_type() -> None:
    """ANTI-VACUITY. An emptied FOREIGN tuple would make the closure assertion
    below pass over nothing at all -- which is precisely how the previous
    version of this file managed to stay green through the fix."""
    assert len(FOREIGN) == len(list(MessageType)) - 2
    assert len(FOREIGN) >= 5, f"the foreign set collapsed: {FOREIGN}"
    assert BUFFERED not in FOREIGN and AWAITED not in FOREIGN


async def test_no_foreign_type_is_read_as_a_move_on_either_configuration(
    tmp_path, default_params, network_params,
):
    """#19, CLOSED. Asserted on BOTH toggle settings: the shipped path must
    never regress, and the toggle-off path is what this item was about."""
    off = dataclasses.replace(ON, commit_reveal=False)
    offenders = []
    for security, tag in ((ON, "on"), (off, "off")):
        for message_type in FOREIGN:
            unnamed = await _unnamed_accusations(
                tmp_path, default_params, network_params, security, message_type,
            )
            if unnamed:
                offenders.append(f"commit_reveal={tag} <- {message_type.value}: {unnamed}")
    assert not offenders, (
        "a legal envelope of a type we were not waiting for was read as a move "
        "and the peer was falsely accused (rules 16/22):\n" + "\n".join(offenders)
    )


async def test_a_buffered_hint_still_costs_the_peer_nothing(
    tmp_path, default_params, network_params,
):
    """The property that must not have been traded away for the type test."""
    off = dataclasses.replace(ON, commit_reveal=False)
    assert not await _unnamed_accusations(
        tmp_path, default_params, network_params, off, BUFFERED,
    )


async def test_a_malformed_move_is_still_rejected_as_a_malformed_move(
    tmp_path, default_params, network_params,
):
    """THE ROW THAT IS NOT #19, pinned so it is never mistaken for it.

    `envelope_of` builds a MOVE whose payload is not a legal move payload. The
    decoder complains, and complaining is right: the peer really did send a
    MOVE and it really was malformed. This row was inside 05-18's "8 of 9" and
    is the whole difference between that 8 and the 7 foreign types the fix
    addressed. Asserted positively so the count above can never be padded by
    it again."""
    off = dataclasses.replace(ON, commit_reveal=False)
    unnamed = await _unnamed_accusations(
        tmp_path, default_params, network_params, off, AWAITED,
    )
    assert unnamed, "a malformed MOVE stopped being rejected -- that IS a regression"
