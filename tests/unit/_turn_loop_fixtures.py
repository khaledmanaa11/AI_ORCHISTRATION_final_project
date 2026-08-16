"""The 05-16 turn-loop watchdog harness, split out of
`test_turn_loop_watchdog.py` at the 150-code-line gate (Segal Table 5) --
split, never compressed. Not a `test_*.py` file on purpose, so pytest never
collects it (the `_fakes_agent.py` / `_hint_decode_fixtures.py` precedent).

It sits ON TOP of 05-13's `_fakes_watchdog.py` rather than inside it: that
module owns the REAL `Watchdog` on an injected clock and the stalled peer,
which the audit path needs too, while everything here is about what a freeze
COSTS the turn loop -- and `_fakes_watchdog.py` is at 143/150 with no room
(deferred item #11).
"""

from __future__ import annotations

from pursuit.network.state_machine import State
from tests.unit._fakes_agent import FakeClient, make_ctx
from tests.unit._fakes_watchdog import (
    ArmedWatchdog,
    StalledQueue,
    attempt_cost,
    table19_overrides,
)


class ProcessKilledError(Exception):
    """What `os._exit(1)` actually means, as an exception a test can see."""


class LethalWatchdog(ArmedWatchdog):
    """An `ArmedWatchdog` whose freeze STOPS THE WORLD, as production's does.

    05-13's harness records `["freeze", "exit"]` and lets the ladder carry
    on, which is enough to see that NET-07 fired but NOT enough to see what
    it cost. Here the freeze ends the call, so "the verdict was never
    reached" is measured rather than inferred -- and a case that returns at
    all has proven the process would have survived.

    `super().check()` is called FIRST and unconditionally, so 05-13's own
    stop-flag gate still runs: a control against "disarm the watchdog across
    the turn loop" must not be able to pass against exactly that wrong fix
    (05-13 deviation 5, commit `da58bc2`).
    """

    def check(self) -> bool:
        if super().check():
            raise ProcessKilledError("NET-07 fired: os._exit(1) would have run here")
        return False


def lethal(network_params) -> LethalWatchdog:
    return LethalWatchdog(
        threshold_seconds=network_params.watchdog_threshold,
        poll_seconds=network_params.watchdog_poll_seconds,
    )


def turn_ctx(tmp_path, default_params, network_params, label, armed, client=None):
    """A WAIT_OPPONENT ctx running the REAL Table-19 ladder against the REAL
    watchdog -- the turn-loop twin of `test_audit_watchdog._audit_ctx`."""
    return make_ctx(
        tmp_path, default_params, network_params, role="police", label=label,
        initial_state=State.WAIT_OPPONENT, client=client or FakeClient(),
        watchdog=armed, net_overrides=table19_overrides(network_params),
    )


def assert_ladder_survived(armed, attempts, network_params) -> None:
    """The five facts a MARKED ladder shows, asserted in one place so no leg
    can drift into a weaker set (CLAUDE.md: extract at the second copy).

    The first assertion is the anti-vacuity guard -- a leg that never made an
    attempt would otherwise satisfy every other line. The second is the
    refutation of the tempting wrong fix: widening `watchdog_threshold` (a
    Table-19 config value, CLAUDE.md rule 1) makes the ladder no longer
    outlive it, so this assertion tells "you marked the attempts" apart from
    "you moved the number". The last is what the blanket-`stop()` wrong fix
    fails on.
    """
    assert attempts == network_params.retry_count + 1, "the ladder was cut short"
    assert armed.clock.now > network_params.watchdog_threshold, (
        "the ladder no longer outlives watchdog_threshold -- a Table-19 NUMBER was moved"
    )
    assert armed.checks and not any(armed.checks), "NET-07 killed the ladder mid-flight"
    assert armed.fired == []
    assert armed.touches >= attempts, "the ladder ran unmarked"


def stall(ctx, armed, network_params, *, step=None) -> StalledQueue:
    """Point *ctx* at a queue that never answers, each pull costing one
    bounded attempt (or *step* seconds) on the injected clock."""
    queue = StalledQueue(armed, step=attempt_cost(network_params) if step is None else step)
    ctx.runtime.queue = queue
    return queue
