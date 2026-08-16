"""05-UAT.md G6: the final audit must survive long enough to be honest --
and NET-07 must survive the fix.

MEASURED BEFORE (HEAD `bcc04bf`). `run_agent` arms the freeze watchdog at
`agent_entrypoint.py:76` and stops it only at `:134`, spanning
`run_final_audit` at `:110`, while `grep -rn "watchdog.touch()" src/`
returned exactly five sites, ALL in the turn loop. So both audit ladders --
(retry_count+1) x response_timeout plus backoffs, 135 s at the shipped
Table-19 values -- ran entirely unmarked against a 60 s
`watchdog_threshold` whose freeze action is `os._exit(1)`. Against a peer
whose socket accepts TCP but never answers, the process died at t=60 s and
05-04's non-accusatory `record_audit_incomplete` at t~135 s NEVER RAN: the
log ended on `watchdog_incident` with no `audit_verdict`, and the peer then
declared US `opponent_unresponsive` -- the 2026-08-13 artifact through a
second door.

THE BALANCE. `test_the_audit_never_disarms_the_watchdog` is the control
that refutes the tempting wrong fix. Stopping the watchdog across the audit
would turn the first three cases green while DELETING NET-07; the audit
instead touches once per BOUNDED attempt, so a wedged event loop -- which
produces no further attempts -- is still killed
(`test_a_genuinely_frozen_audit_is_still_killed`).

Zero real sleeps: every second here is charged to an injected clock, and
every bound is read from `config/police/network.json` through the
`network_params` fixture (CLAUDE.md rule 1 -- no number is written down).
"""

from __future__ import annotations

import json

from pursuit.constants import Outcome
from pursuit.network.agent_audit_wiring import run_final_audit
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import FakeClient, make_ctx
from tests.unit._fakes_watchdog import ArmedWatchdog, StalledClient, StalledQueue

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")


def _kinds(ctx) -> list[str]:
    text = ctx.log_path.read_text(encoding="utf-8")
    return [json.loads(line)["event"] for line in text.splitlines() if line.strip()]


def _armed(network_params) -> ArmedWatchdog:
    return ArmedWatchdog(
        threshold_seconds=network_params.watchdog_threshold,
        poll_seconds=network_params.watchdog_poll_seconds,
    )


def _attempt_cost(network_params) -> float:
    """One bounded attempt plus its backoff, in Table-19 seconds."""
    return network_params.response_timeout + network_params.backoff_seconds


def _audit_ctx(tmp_path, default_params, network_params, label, armed, client):
    """A GAME_OVER ctx running the REAL Table-19 ladder against the REAL
    watchdog. `backoff_seconds=0` is the one real-time deviation and it is
    deliberate: `push_final_reveal` does not plumb `call_with_retry`'s
    injected `sleep` seam, so the production 5 s x 3 would be 15 s of wall
    clock. The backoff is charged to the INJECTED clock instead (see
    `_attempt_cost`), which is the only clock `Watchdog.check_once` reads --
    so the ladder is the full 135 s+ from NET-07's point of view."""
    return make_ctx(
        tmp_path, default_params, network_params, role="police", label=label,
        security=_ON, initial_state=State.GAME_OVER, client=client, watchdog=armed,
        net_overrides={
            "response_timeout": network_params.response_timeout,
            "retry_count": network_params.retry_count,
            "watchdog_threshold": network_params.watchdog_threshold,
            "watchdog_poll_seconds": network_params.watchdog_poll_seconds,
            "backoff_seconds": 0,
        },
    )


def _seed_final_reveal(ctx) -> None:
    ctx.runtime.queue.put_nowait(
        Envelope(
            type=MessageType.FINAL_REVEAL, turn=ctx.state.turn, sender="thief",
            payload={"records": []},
        ),
    )


async def test_a_push_ladder_outliving_the_threshold_still_reaches_audit_incomplete(
    tmp_path, default_params, network_params,
):
    """THE FIX, send leg. The whole push ladder burns -- longer than
    `watchdog_threshold` -- and the audit still gets to be honest."""
    armed = _armed(network_params)
    client = StalledClient(armed, step=_attempt_cost(network_params))
    ctx = _audit_ctx(tmp_path, default_params, network_params, "g6-send", armed, client)
    _seed_final_reveal(ctx)

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert len(client.calls) == network_params.retry_count + 1, "the ladder was cut short"
    assert armed.clock.now > network_params.watchdog_threshold, "ladder shorter than the threshold"
    assert armed.checks and not any(armed.checks), "NET-07 killed the audit mid-ladder"
    assert armed.fired == []
    assert armed.touches >= len(client.calls), "the ladder ran unmarked"
    kinds = _kinds(ctx)
    assert "audit_incomplete" in kinds
    assert "audit_verdict" in kinds, "the audit never reached its verdict -- machine B's shape"
    assert "technical_win" not in kinds
    assert outcome is not Outcome.TECHNICAL_LOSS


async def test_a_receive_ladder_outliving_the_threshold_still_records_its_verdict(
    tmp_path, default_params, network_params,
):
    """THE FIX, receive leg -- and simultaneously the paired control for
    05-13's discrimination. Our push LANDS, so the channel demonstrably
    worked and a peer that then publishes no nonces still loses (rule 36).
    What changes is that the sanction is REACHED at all: before, the process
    died partway down this ladder with nothing written."""
    armed = _armed(network_params)
    ctx = _audit_ctx(
        tmp_path, default_params, network_params, "g6-recv", armed, FakeClient(),
    )
    queue = StalledQueue(armed, step=_attempt_cost(network_params))
    ctx.runtime.queue = queue

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert queue.pulls == network_params.retry_count + 1
    assert armed.clock.now > network_params.watchdog_threshold
    assert armed.checks and not any(armed.checks), "NET-07 killed the receive leg"
    assert outcome is Outcome.TECHNICAL_LOSS, "rule 36's sanction was softened"
    assert "technical_win" in _kinds(ctx)


async def test_a_genuinely_frozen_audit_is_still_killed(
    tmp_path, default_params, network_params,
):
    """NET-07 PRESERVED. The touch marks an attempt STARTING, never a
    heartbeat: one attempt that overruns `watchdog_threshold` on the wall
    clock (only possible with the event loop wedged, since `bounded` would
    otherwise have cancelled it) still trips the freeze. In production
    `exit_action` is `os._exit(1)`, so there is no second attempt; here it
    is injected, which is the only reason the ladder keeps running."""
    armed = _armed(network_params)
    client = StalledClient(armed, step=network_params.watchdog_threshold + 1)
    ctx = _audit_ctx(tmp_path, default_params, network_params, "g6-frozen", armed, client)
    _seed_final_reveal(ctx)

    await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert armed.checks[0] is True, "a frozen audit was NOT detected -- NET-07 was traded away"
    assert armed.fired[:2] == ["freeze", "exit"], "the incident write must precede the exit"


async def test_the_audit_never_disarms_the_watchdog(
    tmp_path, default_params, network_params,
):
    """THE CONTROL AGAINST THE WRONG FIX. Stopping the watchdog for the
    duration of the audit would turn every case above green while deleting
    NET-07 outright. After a COMPLETELY SUCCESSFUL audit the watchdog is
    still armed and still lethal: wedge the process afterwards -- no further
    attempt, so no further touch -- and the freeze fires."""
    armed = _armed(network_params)
    ctx = _audit_ctx(
        tmp_path, default_params, network_params, "g6-armed", armed, FakeClient(),
    )
    _seed_final_reveal(ctx)

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert outcome is not Outcome.TECHNICAL_LOSS
    assert armed.fired == [], "a clean audit must not look like a freeze"
    armed.clock.advance(network_params.watchdog_threshold + 1)
    assert armed.check() is True, "the audit left the watchdog disarmed"
    assert armed.fired == ["freeze", "exit"]
