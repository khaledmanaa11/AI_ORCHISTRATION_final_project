"""run_turn_loop-level tests -- split from test_orchestrator.py at the
150-code-line gate (Segal Table 5), not by test meaning. Shared fakes and the
`make_ctx` assembly helper live in tests/unit/_fakes_agent.py and are imported
here (QUAL-02): NET-05 illegal-transition severity handling, the NET-06
silent-opponent technical win, and a real-outcome clean exit.
"""

import asyncio
import json

from pursuit.constants import Outcome
from pursuit.network import orchestrator
from pursuit.network.state_machine import State, TransitionSeverity
from tests.unit._fakes_agent import make_ctx


async def test_illegal_transition_is_reported_and_handled_by_severity(
    tmp_path, default_params, network_params
):
    """THE NET-05 GATE: reported exactly once, severity decides the outcome."""
    recoverable_ctx = make_ctx(
        tmp_path, default_params, network_params,
        label="recoverable", initial_state=State.MY_TURN,
    )
    outcome = await orchestrator.take_my_turn(recoverable_ctx)
    assert outcome is None
    assert len(recoverable_ctx.reporter.calls) == 1
    assert recoverable_ctx.reporter.calls[0]["severity"] is TransitionSeverity.RECOVERABLE
    assert recoverable_ctx.machine.state is State.MY_TURN
    lines = recoverable_ctx.log_path.read_text(encoding="utf-8").splitlines()
    assert any(json.loads(line)["event"] == "illegal_transition" for line in lines)
    result = recoverable_ctx.machine.attempt(State.MY_TURN)
    assert result.continues is True

    violation_ctx = make_ctx(
        tmp_path, default_params, network_params,
        label="violation", initial_state=State.GAME_OVER,
    )
    outcome2 = await orchestrator.take_my_turn(violation_ctx)
    assert outcome2 is None
    assert len(violation_ctx.reporter.calls) == 1
    assert violation_ctx.reporter.calls[0]["severity"] is TransitionSeverity.PROTOCOL_VIOLATION
    assert violation_ctx.machine.state is State.ERROR
    lines2 = violation_ctx.log_path.read_text(encoding="utf-8").splitlines()
    assert any(json.loads(line)["event"] == "illegal_transition" for line in lines2)


async def test_silent_opponent_produces_a_technical_win(tmp_path, default_params, network_params):
    """THE NET-06 GATE: a silent opponent ends the game cleanly, never a hang."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="silent")
    outcome = await asyncio.wait_for(orchestrator.run_turn_loop(ctx), timeout=5)

    assert ctx.machine.state is State.GAME_OVER
    assert outcome is Outcome.TECHNICAL_LOSS
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    wins = [r for r in records if r["event"] == "technical_win"]
    assert len(wins) == 1
    assert wins[0]["retries_attempted"] == ctx.net.retry_count + 1
    assert wins[0]["timeout_seconds"] == ctx.net.response_timeout
    assert len(ctx.runtime.client().calls) == 1  # the one push; never asked to keep playing


async def test_loop_ends_cleanly_on_a_real_outcome(tmp_path, default_params, network_params):
    """A real SDK outcome (capture) ends the loop and persists game_over."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="capture")
    ctx.choose_move = lambda state, agent, params: state.thief  # cop lands on thief

    outcome = await asyncio.wait_for(orchestrator.run_turn_loop(ctx), timeout=5)

    assert outcome is Outcome.CAPTURE
    assert ctx.machine.state is State.GAME_OVER
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert any(r["event"] == "game_over" and r["outcome"] == Outcome.CAPTURE.value for r in records)
