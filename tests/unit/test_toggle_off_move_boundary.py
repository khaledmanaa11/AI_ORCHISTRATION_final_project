"""Instance SIX of the envelope-boundary class, measured and scoped (05-18).

Split from `test_envelope_boundary_invariant.py` at the 150-code-line gate
(Segal Table 5) along a real seam: that file holds the CLASS guard -- the
invariant, enumerated from source across every pull site -- and this one holds
the single instance that guard found on its first run and that this plan
deliberately did NOT close. Split, never compressed; no assertion was
shortened to fit.

`turn_buffer.await_move` is the commit-reveal TOGGLE-OFF wait, and it has no
type test of any kind: it returns any non-HINT envelope to
`await_opponent_turn`, which decodes it as a move. Same shape as 05-09,
05-10, 05-15, 05-17 and deferred #18 -- an unexpected envelope type at a layer
boundary read as something it is not.

NOT FIXED HERE, for reasons that are recorded rather than assumed. Shipped
config is `commit_reveal: true`, so the exposed path is not the one a league
game runs; `turn_buffer.py` is not in 05-18's `files_modified` and sits at
146/150, so a repair needs its own split; and this is the last plan of phase
5, whose non-goals say anything further is recorded and carried. Latent on a
supported toggle is still a defect -- 05-14 (G8) fixed one of exactly this
shape -- which is why it is written down WITH ITS NUMBERS as deferred item
#19 instead of being forgotten the way instances one through five were.
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


async def test_instance_six_is_confined_to_the_commit_reveal_toggle_off_path(
    tmp_path, default_params, network_params,
):
    """MEASURED, all nine `MessageType` members, police role:

        commit_reveal ON   0 of 9 unnamed reasons   <- 05-18 Task 2's fix
        commit_reveal OFF  8 of 9 unnamed reasons, every one
                           'payload has neither direction nor x/y keys'

    This case asserts the SCOPE, never that the defect is correct. The first
    assertion is the one that must hold forever: the shipped path handles
    every type, and the exposure does not spread into it. The second is a
    LIVE BOOKMARK -- closing #19 drives the OFF count to 0 and fails it
    deliberately, so whoever fixes the defect is sent to the deferred record
    to close the entry rather than leaving a stale one behind. A test that
    silently kept passing after the fix would let the record rot, which is
    how a list of known issues stops being trusted.

    Reachability, stated honestly: with the toggle off this codebase never
    sends COMMIT/ACK/REVEAL/FINAL_REVEAL, so the reachable foreign types are
    HANDSHAKE and GAME_OVER -- and `game_over` is a registered tool on our
    published league surface, which is precisely the door 05-15 found a
    second implementation walking through."""
    off = dataclasses.replace(ON, commit_reveal=False)
    counts = {}

    for security, tag in ((ON, "on"), (off, "off")):
        unnamed = 0
        for message_type in MessageType:
            ctx = make_ctx(
                tmp_path, default_params, network_params, role="police",
                label=f"toggle-{tag}-{message_type.value}", security=security,
                initial_state=State.WAIT_OPPONENT,
            )
            ctx.runtime.queue.put_nowait(envelope_of(ctx, message_type))
            await turn_actions.await_opponent_turn(ctx)
            unnamed += any(reason not in _NAMED_REASONS for reason in accusations(ctx))
        counts[tag] = unnamed

    assert counts["on"] == 0, f"the SHIPPED path now mishandles a type: {counts}"
    assert counts["off"] > 0, "deferred item #19 no longer reproduces -- close it in the record"
