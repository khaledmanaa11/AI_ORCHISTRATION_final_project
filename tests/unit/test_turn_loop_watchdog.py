"""Deferred item #10: the TURN LOOP dies of the same wound the audit did --
and NET-07 must survive the fix, exactly as it survived 05-13's.

MEASURED BEFORE, at `0ea5388`, by running the three ladder cases below
against unmodified source. `next_protocol_message` touched the watchdog
only AFTER its whole `call_with_retry` ladder returned, and its 05-13
`on_attempt` hook defaulted to `None` -- which is what every turn-loop leg
took. `turn_buffer.await_move` and `turn_commit_send.push` had the same
post-ladder-only touch. So a ladder of `(retry_count + 1)` bounded attempts
plus backoffs -- 140 s on the injected clock at the shipped Table-19 values
-- ran entirely UNMARKED against `watchdog_threshold` = 60 s:

    config: response_timeout=30 retry_count=3 backoff=5 watchdog_threshold=60
    attempt cost (injected) = 35
    wait attempts=2 elapsed=70.0s touches=0 checks=[False, True] verdict=None
    push attempts=2 elapsed=70.0s touches=0 checks=[False, True] verdict=None
    move attempts=2 elapsed=70.0s touches=0 checks=[False, True] verdict=None

all three ending `fired=['freeze', 'exit']` at attempt 2 of 4, with
`touches=0` and NO verdict returned -- the D-13 ladder that would have
answered at t=140 s never got to speak. In production `exit_action` is
`os._exit(1)`, so that second poll is the end of the process: MID-GAME, with
our nonces ledgered and no FINAL_REVEAL sent, we become the side that
published nothing (rule 36 against US) while the peer records
`opponent_unresponsive`. `LethalWatchdog` below reproduces exactly that --
nothing downstream of a fired freeze runs -- so "no verdict" is a measured
fact here and not an inference from a boolean.

THE FIX IS THE TOUCH, NOT A WIDER THRESHOLD. Every case asserts BOTH that
the ladder outlives `watchdog_threshold` AND that no freeze fired; the two
are simultaneously satisfiable only by marking each bounded attempt. Moving
`watchdog_threshold` (Table 19, config -- CLAUDE.md rule 1) fails the first
assertion, and removing the touch fails the second.

Zero real sleeps: every second is charged to an injected clock and every
bound is read from `config/police/network.json` via the `network_params`
fixture, so no number is written down here.
"""

from __future__ import annotations

from pursuit.network import turn_buffer, turn_commit_send
from pursuit.network.envelope import MessageType
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_wait import H_COMMIT_KEY, wait_for_opponent_commit
from tests.unit._fakes_agent import FakeClient, make_ctx
from tests.unit._fakes_watchdog import (
    ArmedWatchdog,
    StalledClient,
    StalledQueue,
    attempt_cost,
    table19_overrides,
)


class ProcessKilledError(Exception):
    """What `os._exit(1)` actually means, as an exception a test can see."""


class LethalWatchdog(ArmedWatchdog):
    """An `ArmedWatchdog` whose freeze STOPS THE WORLD, as production's does.

    05-13's harness records `["freeze", "exit"]` and lets the ladder carry on,
    which is enough to see that NET-07 fired but NOT enough to see what it
    cost. Here the freeze ends the call, so "the verdict was never reached"
    is measured rather than inferred -- and a case that returns at all has
    proven the process would have survived."""

    def check(self) -> bool:
        if super().check():
            raise ProcessKilledError("NET-07 fired: os._exit(1) would have run here")
        return False


def _lethal(network_params) -> LethalWatchdog:
    return LethalWatchdog(
        threshold_seconds=network_params.watchdog_threshold,
        poll_seconds=network_params.watchdog_poll_seconds,
    )


def _turn_ctx(tmp_path, default_params, network_params, label, armed, client=None):
    """A WAIT_OPPONENT ctx running the REAL Table-19 ladder against the REAL
    watchdog -- the turn-loop twin of `test_audit_watchdog._audit_ctx`."""
    return make_ctx(
        tmp_path, default_params, network_params, role="police", label=label,
        initial_state=State.WAIT_OPPONENT, client=client or FakeClient(),
        watchdog=armed, net_overrides=table19_overrides(network_params),
    )


def _stall(ctx, armed, network_params) -> StalledQueue:
    queue = StalledQueue(armed, step=attempt_cost(network_params))
    ctx.runtime.queue = queue
    return queue


async def test_a_stalled_peer_costs_the_wait_leg_a_ladder_and_not_the_process(
    tmp_path, default_params, network_params,
):
    """THE FIX, receive leg. `wait_for_opponent_commit` is one of the four
    D-58 waits that took `on_attempt=None`; the whole ladder now burns --
    longer than `watchdog_threshold` -- and still returns D-13's honest
    verdict instead of dying at t=60 s."""
    armed = _lethal(network_params)
    ctx = _turn_ctx(tmp_path, default_params, network_params, "t10-wait", armed)
    queue = _stall(ctx, armed, network_params)

    opponent, verdict = await wait_for_opponent_commit(ctx, State.WAIT_OPPONENT, turn=0)

    assert queue.pulls == network_params.retry_count + 1, "the ladder was cut short"
    assert armed.clock.now > network_params.watchdog_threshold, (
        "the ladder no longer outlives watchdog_threshold -- a Table-19 NUMBER was moved"
    )
    assert armed.checks and not any(armed.checks), "NET-07 killed the turn loop mid-ladder"
    assert armed.fired == []
    assert armed.touches >= queue.pulls, "the ladder ran unmarked"
    assert opponent is None
    assert verdict is not None, "no verdict -- the D-13 ladder never got to speak"
    assert verdict.attempts == network_params.retry_count + 1


async def test_a_stalled_peer_costs_the_push_leg_a_ladder_and_not_the_process(
    tmp_path, default_params, network_params,
):
    """THE FIX, send leg. A peer whose socket accepts TCP and never answers
    stalls our COMMIT/ACK/REVEAL push first -- before any wait leg is ever
    reached -- so marking only the waits would have left the turn loop dying
    at the same t=60 s through the earlier door."""
    armed = _lethal(network_params)
    client = StalledClient(armed, step=attempt_cost(network_params))
    ctx = _turn_ctx(tmp_path, default_params, network_params, "t10-push", armed, client=client)

    verdict = await turn_commit_send.push(ctx, MessageType.COMMIT, 0, {H_COMMIT_KEY: "h"})

    assert len(client.calls) == network_params.retry_count + 1, "the ladder was cut short"
    assert armed.clock.now > network_params.watchdog_threshold, (
        "the ladder no longer outlives watchdog_threshold -- a Table-19 NUMBER was moved"
    )
    assert armed.checks and not any(armed.checks), "NET-07 killed the push leg mid-ladder"
    assert armed.touches >= len(client.calls), "the ladder ran unmarked"
    assert verdict is not None, "no verdict -- the D-13 ladder never got to speak"


async def test_a_stalled_peer_costs_the_move_wait_a_ladder_and_not_the_process(
    tmp_path, default_params, network_params,
):
    """THE FIX, `turn_buffer.await_move` -- the fifth turn-loop wait leg,
    reached on the `commit_reveal=False` path (`turn_commit.await_opponent`)
    and carrying the identical post-ladder-only touch."""
    armed = _lethal(network_params)
    ctx = _turn_ctx(tmp_path, default_params, network_params, "t10-move", armed)
    queue = _stall(ctx, armed, network_params)

    envelope, verdict = await turn_buffer.await_move(ctx)

    assert queue.pulls == network_params.retry_count + 1, "the ladder was cut short"
    assert armed.clock.now > network_params.watchdog_threshold, (
        "the ladder no longer outlives watchdog_threshold -- a Table-19 NUMBER was moved"
    )
    assert armed.checks and not any(armed.checks), "NET-07 killed the move wait mid-ladder"
    assert armed.touches >= queue.pulls, "the ladder ran unmarked"
    assert envelope is None
    assert verdict is not None, "no verdict -- the D-13 ladder never got to speak"
