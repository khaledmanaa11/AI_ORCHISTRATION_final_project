"""ONE invariant, held across EVERY queue-pull site in the codebase (05-18).

THE CLASS, not the fifth instance of it. 05-09, 05-10, 05-15, 05-17 and
deferred item #18 are the same defect five times over: peer-supplied data at a
boundary is mishandled -- dropped, or misread as something else. Every one was
found by grepping outward after the previous fix, never by review, and every
fix bought exactly one defect. This module is the standing guard instead.

SCOPE, stated precisely because an earlier draft of this docstring over-claimed
it (corrected at verify-work, 2026-08-17): this guard covers the QUEUE-PULL
sites, which is where 05-15, 05-17 and #18 live -- three of the five, not all
five. 05-09 was an OUTBOUND exception-taxonomy defect in `call_with_retry`
(`deadline.py`) and 05-10 was in `security/audit.py`; both are the same family
but structurally outside any pull-site enumeration, and neither would be caught
here. What this guard IS complete for, it is genuinely complete for: no queue
read exists anywhere under `src/` outside the discovered set (re-measured at
verify-work). Do not read a green run here as cover for the outbound half.

THE INVARIANT. Every site that pulls an envelope either HANDLES its type,
BUFFERS it for the layer that wants it, or SKIPS it -- and no site ever passes
a non-move envelope into move handling. Concretely, asserted three ways:

  no traceback        an unexpected type is never an exception
  named reasons only  every accusation a pull site writes is a
                      `TechnicalWinReason` member, never a decoder's message.
                      This is the sharp one: `opponent_unresponsive` is a
                      claim we measured, `'payload must be a dict, got
                      NoneType'` accuses a peer of sending a malformed MOVE
                      it never sent -- a false declaration under rules 16/22,
                      and the exact shape of instance five.
  the ledger survives a peer's FINAL_REVEAL is returned, buffered or left
                      queued -- never consumed and destroyed

The sites are read OUT OF THE SOURCE (`_pull_site_discovery`), so a pull added
next month is covered the day it lands and cannot silently opt out. What a
hand-written list buys is a snapshot; that is how this class kept regenerating.

FOUND BY THIS MODULE ON ITS FIRST RUN, which is the argument for it: INSTANCE
SIX, on the commit-reveal toggle-off path. `turn_buffer.await_move` has no
type test of any kind, so eight of the nine `MessageType` members reach move
handling and come back as `'payload has neither direction nor x/y keys'`.
Recorded as deferred item #19 and scoped in the sibling
`test_toggle_off_move_boundary.py` -- shipped config is `commit_reveal: true`,
`turn_buffer.py` is not in this plan's `files_modified`, and phase 5 ends
here. That sibling is a split at the 150-code-line gate along a real seam:
this file holds the CLASS guard, that one holds the single instance the guard
found and this plan deliberately did not close.

NO `parametrize`: an empty parameter set is a SILENT pytest SKIP, so the
enumeration is a plain loop and `pull_sites()` RAISES on an empty result.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import turn_actions
from pursuit.network.envelope import MessageType
from pursuit.network.state_machine import State
from pursuit.network.verdict import TechnicalWinReason
from tests.unit._early_reveal_fixtures import ON, accusations, honest_peer_turn
from tests.unit._fakes_agent import make_ctx
from tests.unit._pull_site_discovery import pull_sites
from tests.unit._pull_site_drivers import DRIVERS, probe

_NAMED_REASONS = {reason.value for reason in TechnicalWinReason}

_LEDGER_EXEMPT = {
    # Deferred item #17, OPEN with its own measurement: the post-audit linger
    # drains through a plain `queue.get()` rather than through
    # `next_protocol_message`, so 05-17's buffer does not cover that window
    # and a FINAL_REVEAL arriving there is consumed unaudited. Named here
    # rather than silently tolerated, and asserted below to be a REAL
    # discovered site -- an exemption for a function that no longer exists
    # would quietly widen this test's blind spot.
    "linger_for_peer",
}


def test_the_pull_sites_are_enumerated_from_source_and_every_one_is_driven():
    """THE ANTI-VACUITY GATE, and the property that makes this a class fix.

    Both directions are checked. A DISCOVERED site with no driver fails --
    that is a new pull landing in `src/pursuit/network/` and being covered on
    the day it lands, instead of joining the queue of instances six, seven and
    eight. A DRIVER naming nothing discovered fails too -- that is a probe
    that has quietly stopped exercising anything, which is how a green suite
    stops meaning something.

    `pull_sites()` itself raises on an empty result, so this cannot pass by
    finding nothing."""
    sites = pull_sites()

    assert len(sites) >= len(_LEDGER_EXEMPT) + 1, f"enumeration collapsed: {sites}"
    assert sorted(sites) == sorted(DRIVERS), (
        f"undriven sites {sorted(set(sites) - set(DRIVERS))}, "
        f"stale drivers {sorted(set(DRIVERS) - set(sites))}"
    )
    assert set(sites) >= _LEDGER_EXEMPT, "an exemption names a site that no longer pulls anything"


async def test_no_pull_site_mishandles_any_envelope_type(
    tmp_path, default_params, network_params,
):
    """THE INVARIANT, over every discovered site x every `MessageType`, on the
    SHIPPED configuration (police, commit-reveal ON -- what a league game
    runs).

    Each arrival is WELL-FORMED. A site rejecting garbage proves nothing about
    how it treats a legitimate envelope of a type it was not waiting for, and
    that -- not garbage -- is the class. The FINAL_REVEAL rows carry a real
    ledger hashed through `commit_pack`, never `{"records": []}`, which is
    byte-indistinguishable from the rule-36 evasion and passes vacuously
    through `all_matched([])`.

    Every failure is collected and reported together rather than fired one at
    a time: a matrix that stops at the first bad cell hides how far the defect
    reaches, and reach is exactly what tells one instance apart from a class."""
    sites = pull_sites()
    breaches, ledgers_kept = [], 0

    for site in sorted(sites):
        for message_type in MessageType:
            found = await probe(tmp_path, default_params, network_params, site, message_type)
            where = f"{site}({sites[site]}) <- {message_type.value}"
            if found["raised"] is not None:
                breaches.append(f"{where}: raised {found['raised']}")
            unnamed = [a for a in found["accusations"] if a not in _NAMED_REASONS]
            if unnamed:
                breaches.append(f"{where}: accused with an unnamed reason {unnamed}")
            if message_type is not MessageType.FINAL_REVEAL:
                continue
            ledgers_kept += found["kept"]
            if not found["kept"] and site not in _LEDGER_EXEMPT:
                breaches.append(f"{where}: the peer's published ledger was destroyed")

    assert not breaches, "\n".join(breaches)
    # POSITIVE evidence, not the absence of a complaint. `not breaches` is
    # satisfied by a matrix that never ran, by a `kept` flag wired to a
    # constant True, and by an exemption set that swallowed everything -- an
    # exact count is satisfied by none of them.
    assert ledgers_kept == len(sites) - len(_LEDGER_EXEMPT), (
        f"{ledgers_kept} sites kept the ledger, expected "
        f"{len(sites)} discovered minus {len(_LEDGER_EXEMPT)} exempt"
    )


async def test_a_genuinely_silent_peer_is_still_declared_unresponsive(
    tmp_path, default_params, network_params,
):
    """THE COUNTER-CONTROL, carried here UNCHANGED from 05-17 because a
    class-level guard is exactly the shape of change that can pass by
    disabling the thing it claims to protect.

    Rule 36's sanction is not softened by any of the above. Nothing arrives,
    nothing is buffered, and the peer is still accused -- with the same named
    reason. A version of this codebase that stops accusing silent peers would
    turn the whole matrix above green and would have broken the game."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="boundary-silent",
        security=ON, initial_state=State.WAIT_OPPONENT,
    )
    honest_peer_turn(ctx)
    assert ctx.commit_state.early_final_reveal is None, "nothing may be buffered here"

    outcome = await turn_actions.await_opponent_turn(ctx)

    assert (outcome, accusations(ctx)) == (
        Outcome.TECHNICAL_LOSS, [TechnicalWinReason.OPPONENT_UNRESPONSIVE.value],
    )


