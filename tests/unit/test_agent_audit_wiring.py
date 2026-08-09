"""Coverage-closing tests (Rule 2) for agent_audit_wiring.py's own
technical-loss branches in run_final_audit: a failed FINAL_REVEAL push,
and a push that succeeds but nothing is ever received back."""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network.agent_audit_wiring import run_final_audit
from pursuit.network.state_machine import State
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import FakeClient, make_ctx

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")


async def test_run_final_audit_is_technical_loss_when_the_push_fails(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="final-audit-push-fail",
        security=_ON, client=FakeClient(fail=True), initial_state=State.GAME_OVER,
    )
    outcome = await run_final_audit(ctx)
    assert outcome is Outcome.TECHNICAL_LOSS


async def test_run_final_audit_is_technical_loss_when_the_opponent_never_answers(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="final-audit-recv-fail",
        security=_ON, initial_state=State.GAME_OVER,
    )
    outcome = await run_final_audit(ctx)
    assert outcome is Outcome.TECHNICAL_LOSS
