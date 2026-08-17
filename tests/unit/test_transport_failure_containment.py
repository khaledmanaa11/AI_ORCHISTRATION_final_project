"""05-09: a transport failure ends in a RECORDED VERDICT, never an uncaught exception -- and
the accusation lands only where a peer really is unreachable.

Pre-05-09, `httpx.ConnectError` matched neither `except` clause in `call_with_retry`: it
escaped the ladder, propagated out of `run_agent` through `main.py`, and terminated the agent.
Consequence when it fired: WE became the side that published no nonces (rule 36), with no
verdict at all in our own log -- the exact artifact machine B produced on 2026-08-13, measured
4/4 runs by 05-04 (deferred-items.md #1). It was never teardown-only either: `call_with_retry`
carries EVERY outgoing envelope, so a transient drop mid-game over a real tunnel forfeited the
game.

Cases 1-2 are the two boundaries and the two DIFFERENT verdicts they earn; both FAIL against
the pre-05-09 tuple (revert probe recorded in 05-09-SUMMARY.md). Cases 3-5 are controls, all
green pre-fix by construction -- they encode PRESERVED behaviour and the two SUBTRACTIONS that
keep the widening honest, so their discrimination is against the design alternatives (case 4
fails if written with `httpx.HTTPError`; case 5 fails against a tuple-only 05-09).

Helpers are imported from `test_audit_send_failure.py` rather than re-derived (QUAL-02, and the
`test_step0_and_audit_tamper.py` sibling-import precedent).
"""

from __future__ import annotations

import httpx
import pytest

from pursuit.constants import Outcome
from pursuit.network import turn_commit
from pursuit.network.agent_audit_wiring import run_final_audit
from pursuit.network.state_machine import State
from pursuit.sdk import engine
from tests.unit._fakes_agent import FakeClient, make_ctx
from tests.unit.test_audit_send_failure import (
    _ON,
    _events,
    _kinds,
    _seed_final_reveal,
    _tampered_peer_turn,
)

_CONNECT_ERROR_TEXT = "All connection attempts failed"


class RaisingClient(FakeClient):
    """Raises a freshly-built exception on every `call_tool` -- the transport shapes
    `_fakes_agent.FakeClient`'s single `McpError` does not cover."""

    def __init__(self, build_exception):
        super().__init__()
        self._build_exception = build_exception

    async def call_tool(self, name, args, **kwargs):
        self.calls.append((name, args))
        raise self._build_exception()


def _connect_error() -> httpx.ConnectError:
    return httpx.ConnectError(_CONNECT_ERROR_TEXT)


def _forbidden() -> httpx.HTTPStatusError:
    """The wrong-shared-secret shape: a real 403 from 05-02's `SharedSecretMiddleware`."""
    request = httpx.Request("POST", "http://127.0.0.1:9/mcp")
    return httpx.HTTPStatusError(
        "Client error '403 Forbidden'", request=request, response=httpx.Response(403, request=request),
    )


def _accusations(ctx) -> list[dict]:
    """Every technical_win record in this side's own log. A raise-first class fails before
    anything is appended at all, so a MISSING log file is the strongest form of "no
    accusation", not an error -- `_kinds` cannot express that."""
    if not ctx.log_path.exists():
        return []
    return [event for event in _events(ctx) if event["event"] == "technical_win"]


def _in_game_ctx(tmp_path, default_params, network_params, label, build_exception):
    return make_ctx(
        tmp_path, default_params, network_params, role="police", label=label, security=_ON,
        client=RaisingClient(build_exception), initial_state=State.MY_TURN,
    )


async def _take_one_turn(ctx, default_params):
    """The real in-game initiator path: commit, then push the COMMIT envelope."""
    dest = engine.legal_moves(ctx.state, "cop", default_params)[0]
    return await turn_commit.initiate(ctx, ctx.machine.state, ctx.state.cop, dest, None, None, played_turn=ctx.state.turn)


async def test_in_game_a_dropped_connection_is_a_recorded_technical_win_not_a_crash(
    tmp_path, default_params, network_params,
):
    """CASE 1 -- IN-GAME. The COMMIT push fails on every attempt, so the peer is unreachable
    for the WHOLE ladder and the accusation is CORRECT here: this is the one place it is. What
    matters is that it is a RETURNED verdict recorded in our own log, not an exception that
    ends the process before any verdict exists."""
    ctx = _in_game_ctx(tmp_path, default_params, network_params, "in-game-drop", _connect_error)

    outcome = await _take_one_turn(ctx, default_params)

    assert outcome is Outcome.TECHNICAL_LOSS
    assert ctx.runtime.client().calls, "no attempt was made at all"
    verdict = next(e for e in _events(ctx) if e["event"] == "technical_win")
    assert verdict["reason"] == "opponent_unresponsive"
    assert verdict["retries_attempted"] == ctx.net.retry_count + 1


async def test_at_the_audit_boundary_a_dropped_push_accuses_nobody(
    tmp_path, default_params, network_params,
):
    """CASE 2 -- AUDIT BOUNDARY, with a board outcome already standing. Failing to CONNECT to a
    peer that has already torn down is evidence about the connection, not about the peer's
    honesty, so it takes 05-04's non-accusatory `record_audit_incomplete` path, leaves the board
    outcome standing, and STILL falls through to the receive + audit steps."""
    ctx = _in_game_ctx(tmp_path, default_params, network_params, "audit-drop", _connect_error)
    _seed_final_reveal(ctx, [])

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert outcome is not Outcome.TECHNICAL_LOSS
    kinds = _kinds(ctx)
    assert "audit_incomplete" in kinds
    assert "technical_win" not in kinds, "a torn-down peer was accused of being unresponsive"
    assert "audit_verdict" in kinds, "the audit aborted -- machine B's 2026-08-13 shape"
    incomplete = next(e for e in _events(ctx) if e["event"] == "audit_incomplete")
    assert "ConnectError" in incomplete["last_error"]


async def test_a_genuine_hash_mismatch_is_still_a_technical_loss(
    tmp_path, default_params, network_params,
):
    """CASE 3 -- CONTROL, D-67. The widened tuple must not have softened a real sanction.
    PRESERVED behaviour, so this is green pre-fix as well as post-fix."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="still-mismatch",
        security=_ON, initial_state=State.GAME_OVER,
    )
    _seed_final_reveal(ctx, [_tampered_peer_turn(ctx)])

    outcome = await run_final_audit(ctx, board_outcome=Outcome.CAPTURE)

    assert outcome is Outcome.TECHNICAL_LOSS
    verdict = next(e for e in _events(ctx) if e["event"] == "technical_win")
    assert verdict["reason"] == "audit_hash_mismatch"


async def test_a_403_about_our_own_secret_never_becomes_an_accusation(
    tmp_path, default_params, network_params,
):
    """CASE 4 -- CONTROL. A 403 is an application-level answer about OUR OWN shared secret. It
    is not retried and it produces no verdict against the peer. Also green pre-fix: its real
    discrimination is against the DESIGN ALTERNATIVE -- written with `httpx.HTTPError` in place
    of `httpx.TransportError` this test FAILS, because `HTTPStatusError` is a sibling under
    `HTTPError`. An always-green control is not the same as a vacuous one."""
    ctx = _in_game_ctx(tmp_path, default_params, network_params, "wrong-secret", _forbidden)

    with pytest.raises(httpx.HTTPStatusError, match="403"):
        await _take_one_turn(ctx, default_params)

    assert len(ctx.runtime.client().calls) == 1, "our own wrong secret burned the retry budget"
    assert _accusations(ctx) == []


async def test_our_own_deterministic_fault_is_raised_immediately(
    tmp_path, default_params, network_params,
):
    """CASE 5 -- CONTROL, the B1 case, in BOTH its shapes. Both classes ARE
    `httpx.TransportError` subclasses, so a tuple-only 05-09 would retry them: four identical
    failures, 3 x backoff_seconds burned, and a DURABLE TechnicalWin against a peer that never
    received a valid request (rules 16/22). A scheme-less `PURSUIT_OPPONENT_URL` is an ordinary
    league-day slip -- REMOTE-ROUND-RUNBOOK.md has the operator paste it by hand -- and must
    fail instantly and obviously, never as a false accusation ~135 s later."""
    shapes = {
        "local": lambda: httpx.LocalProtocolError("malformed request"),
        "scheme": lambda: httpx.UnsupportedProtocol(
            "Request URL is missing an 'http://' or 'https://' protocol."
        ),
    }
    for label, build_exception in shapes.items():
        ctx = _in_game_ctx(tmp_path, default_params, network_params, label, build_exception)

        with pytest.raises(httpx.TransportError):
            await _take_one_turn(ctx, default_params)

        assert len(ctx.runtime.client().calls) == 1, f"{label}: backoff burned on our own fault"
        assert _accusations(ctx) == [], f"{label}: our own malformed request accused the peer"
