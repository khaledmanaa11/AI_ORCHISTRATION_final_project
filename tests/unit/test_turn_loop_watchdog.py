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

import pytest

from pursuit.network import turn_buffer
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_wait import H_COMMIT_KEY, wait_for_opponent_commit
from tests.unit._fakes_watchdog import armed_from
from tests.unit._turn_loop_fixtures import (
    ProcessKilledError,
    assert_ladder_survived,
    lethal,
    stall,
    turn_ctx,
)


async def test_a_stalled_peer_costs_the_wait_leg_a_ladder_and_not_the_process(
    tmp_path, default_params, network_params,
):
    """THE FIX, receive leg. `wait_for_opponent_commit` is one of the four
    D-58 waits that took `on_attempt=None`; the whole ladder now burns --
    longer than `watchdog_threshold` -- and still returns D-13's honest
    verdict instead of dying at t=60 s."""
    armed = lethal(network_params)
    ctx = turn_ctx(tmp_path, default_params, network_params, "t10-wait", armed)
    queue = stall(ctx, armed, network_params)

    opponent, verdict = await wait_for_opponent_commit(ctx, State.WAIT_OPPONENT, turn=0)

    assert_ladder_survived(armed, queue.pulls, network_params)
    assert opponent is None
    assert verdict is not None, "no verdict -- the D-13 ladder never got to speak"
    assert verdict.attempts == network_params.retry_count + 1


async def test_a_stalled_peer_costs_the_move_wait_a_ladder_and_not_the_process(
    tmp_path, default_params, network_params,
):
    """THE FIX, `turn_buffer.await_move` -- the fifth turn-loop wait leg,
    reached on the `commit_reveal=False` path (`turn_commit.await_opponent`)
    and carrying the identical post-ladder-only touch."""
    armed = lethal(network_params)
    ctx = turn_ctx(tmp_path, default_params, network_params, "t10-move", armed)
    queue = stall(ctx, armed, network_params)

    envelope, verdict = await turn_buffer.await_move(ctx)

    assert_ladder_survived(armed, queue.pulls, network_params)
    assert envelope is None
    assert verdict is not None, "no verdict -- the D-13 ladder never got to speak"


async def test_a_genuinely_frozen_turn_loop_is_still_killed(
    tmp_path, default_params, network_params,
):
    """NET-07 PRESERVED, and this is the assertion that says the fix is not a
    heartbeat. The touch marks an attempt STARTING, so one attempt that
    overruns `watchdog_threshold` on the wall clock -- only possible with the
    event loop wedged, since `bounded` would otherwise have cancelled it --
    still trips the freeze, and nothing after it runs."""
    armed = lethal(network_params)
    ctx = turn_ctx(tmp_path, default_params, network_params, "t10-frozen", armed)
    queue = stall(ctx, armed, network_params, step=network_params.watchdog_threshold + 1)

    with pytest.raises(ProcessKilledError):
        await wait_for_opponent_commit(ctx, State.WAIT_OPPONENT, turn=0)

    assert armed.checks[0] is True, "a frozen turn loop was NOT detected -- NET-07 traded away"
    assert armed.fired == ["freeze", "exit"], "the incident write must precede the exit"
    assert queue.pulls == 1, "the ladder ran on past the point os._exit(1) would have ended it"


async def test_the_turn_loop_never_disarms_the_watchdog(
    tmp_path, default_params, network_params,
):
    """THE CONTROL AGAINST THE WRONG FIX. A blanket `ctx.watchdog.stop()`
    across the turn loop turns every ladder case above green by DELETING
    NET-07. After a completely successful wait the watchdog must still be
    armed and still lethal: wedge the process afterwards -- no further
    attempt, so no further touch -- and the freeze fires."""
    armed = armed_from(network_params)
    ctx = turn_ctx(tmp_path, default_params, network_params, "t10-armed", armed)
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.COMMIT, turn=0, sender="thief", payload={H_COMMIT_KEY: "h"}),
    )

    opponent, verdict = await wait_for_opponent_commit(ctx, State.WAIT_OPPONENT, turn=0)

    assert (opponent, verdict) == ("h", None)
    assert armed.fired == [], "a clean turn must not look like a freeze"
    armed.clock.advance(network_params.watchdog_threshold + 1)
    assert armed.check() is True, "the turn loop left the watchdog disarmed"
    assert armed.fired == ["freeze", "exit"]
