"""One driver per discovered pull site, plus the probe that runs it (05-18).

Not a `test_*.py` file on purpose (the `_fakes_agent.py` precedent).

THE DRIVERS ARE HAND-WRITTEN AND THE SITE LIST IS NOT, and the split matters.
`_pull_site_discovery.pull_sites()` reads the sites out of the source, so it
cannot go stale; a driver is per-signature work that no AST walk can invent.
The test module joins the two and FAILS on either mismatch -- a discovered
site with no driver (a new pull silently opting out, the way this defect
class kept regenerating) and a driver naming nothing discovered (a probe
pinning a function that no longer pulls anything).

Every site runs on the police role with commit-reveal ON: that is the SHIPPED
configuration (`config/*/security.json`), the one a league game runs, and the
one deferred item #18 was found on.
"""

from __future__ import annotations

import dataclasses

from pursuit.network import agent_teardown, turn_actions, turn_buffer, turn_commit
from pursuit.network.agent_audit_exchange import receive_final_reveal
from pursuit.network.deadline import wait_for_opponent
from pursuit.network.envelope import MessageType
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_pull import next_protocol_message
from pursuit.network.turn_commit_wait import (
    wait_for_ack_and_commit,
    wait_for_matching_ack,
    wait_for_opponent_commit,
)
from pursuit.network.turn_commit_wait_reveal import wait_for_reveal_capturing_early_ack
from tests.unit._early_reveal_fixtures import (
    ON,
    RECORDS_KEY,
    accusations,
    envelope_of,
    final_reveal,
    honest_peer_turn,
)
from tests.unit._fakes_agent import make_ctx

_OUR_H_COMMIT = "our-own-commit-hash"
_TURN = 0


class _SteppingClock:
    """Zero until the linger's drain has actually run once, then past its
    total cap. Without it the drain never executes (`backoff_seconds` is 0
    on the fast test ladder, so its inner wait is cancelled before it can
    pull) and deferred item #17's exemption below would be VACUOUS -- it
    would exempt a drain that never happened."""

    def __init__(self, cap: float) -> None:
        self._cap, self._calls = cap, 0

    def __call__(self) -> float:
        self._calls += 1
        return 0.0 if self._calls <= 2 else self._cap * 2


async def _wait_for_opponent(ctx):
    return await wait_for_opponent(ctx.runtime.queue, timeout=ctx.net.response_timeout)


async def _next_protocol_message(ctx):
    return await next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)


async def _await_move(ctx):
    return await turn_buffer.await_move(ctx)


async def _drain_trailing_hint(ctx):
    return turn_buffer.drain_trailing_hint(ctx)


async def _linger_for_peer(ctx):
    ctx.net = dataclasses.replace(ctx.net, backoff_seconds=ctx.net.response_timeout)
    return await agent_teardown.linger_for_peer(ctx, clock=_SteppingClock(ctx.net.response_timeout))


async def _wait_for_ack_and_commit(ctx):
    return await wait_for_ack_and_commit(ctx, _OUR_H_COMMIT, _TURN, State.WAIT_OPPONENT)


async def _wait_for_reveal_capturing_early_ack(ctx):
    return await wait_for_reveal_capturing_early_ack(ctx, _OUR_H_COMMIT)


async def _wait_for_opponent_commit(ctx):
    return await wait_for_opponent_commit(ctx, State.WAIT_OPPONENT, _TURN)


async def _wait_for_matching_ack(ctx):
    return await wait_for_matching_ack(ctx, _OUR_H_COMMIT)


async def _await_and_respond(ctx):
    return await turn_commit.await_and_respond(ctx)


async def _await_opponent_turn(ctx):
    return await turn_actions.await_opponent_turn(ctx)


async def _receive_final_reveal(ctx):
    return await receive_final_reveal(ctx)


DRIVERS = {
    "await_and_respond": _await_and_respond,
    "await_move": _await_move,
    "await_opponent_turn": _await_opponent_turn,
    "drain_trailing_hint": _drain_trailing_hint,
    "linger_for_peer": _linger_for_peer,
    "next_protocol_message": _next_protocol_message,
    "receive_final_reveal": _receive_final_reveal,
    "wait_for_ack_and_commit": _wait_for_ack_and_commit,
    "wait_for_matching_ack": _wait_for_matching_ack,
    "wait_for_opponent": _wait_for_opponent,
    "wait_for_opponent_commit": _wait_for_opponent_commit,
    "wait_for_reveal_capturing_early_ack": _wait_for_reveal_capturing_early_ack,
}


def _carries(value, arrival, records) -> bool:
    """True when a site's own RETURN VALUE hands the arrival back.

    Checked recursively because the sites return four different shapes --
    a bare Envelope, `(Envelope, verdict)`, `(records, verdict)`, or an
    Outcome -- and "handed it to the caller" is one fact across all of them.
    Without this, a site that correctly RETURNS a FINAL_REVEAL (the raw
    primitive, and the audit's own receive leg) reads as having destroyed
    it, and the invariant would be asserting the opposite of the truth."""
    if value is arrival or (records is not None and value == records):
        return True
    if isinstance(value, tuple | list):
        return any(_carries(item, arrival, records) for item in value)
    return False


async def probe(tmp_path, default_params, network_params, site, message_type) -> dict:
    """Run one pull site against ONE well-formed arrival of *message_type*
    and report what became of it. Never asserts -- the caller owns the
    invariant, so one measurement serves every one of them.

    A FINAL_REVEAL carries a REAL ledger hashed through `commit_pack`, never
    `{"records": []}`: an empty ledger is byte-indistinguishable from the
    rule-36 evasion `security/audit.py` exists to punish, and `all_matched([])`
    is True, so "the ledger survived" would pass over a ledger that never
    was (05-17's vacuity finding)."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police",
        label=f"{site}-{message_type.value}", security=ON,
        initial_state=State.WAIT_OPPONENT,
    )
    if message_type is MessageType.FINAL_REVEAL:
        records = [honest_peer_turn(ctx)]
        arrival = final_reveal(ctx, records)
    else:
        records, arrival = None, envelope_of(ctx, message_type)
    ctx.runtime.queue.put_nowait(arrival)

    raised, result = None, None
    try:
        result = await DRIVERS[site](ctx)
    except BaseException as exc:  # noqa: BLE001 -- measuring, never handling
        raised = f"{type(exc).__name__}: {exc}"

    buffered = ctx.commit_state.early_final_reveal
    return {
        "site": site, "type": message_type, "raised": raised,
        "accusations": accusations(ctx),
        # HANDLED, BUFFERED or SKIPPED-but-put-back -- the three the
        # invariant permits. False means the arrival was CONSUMED AND
        # DESTROYED, which is the fourth and is what this test forbids.
        "kept": (
            _carries(result, arrival, records)
            or (buffered is not None and buffered.payload.get(RECORDS_KEY) == records)
            or ctx.runtime.queue.qsize() > 0
        ),
    }
