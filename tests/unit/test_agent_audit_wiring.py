"""Coverage-closing tests (Rule 2) for agent_audit_wiring.py's own
technical-loss branches in run_final_audit: a failed FINAL_REVEAL push,
and a push that succeeds but nothing is ever received back.

Both cases below deliberately omit `board_outcome`, pinning the
`board_outcome is None` branch -- the "turn loop never resolved" case,
where a technical loss is still the right verdict. They are therefore NOT
the production shape: `agent_entrypoint.run_agent` always passes the turn
loop's own outcome (05-04), and `test_audit_send_failure.py` is the file
that covers it."""

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
    """No board_outcome: the turn loop never resolved, so nothing else
    stands and our own failed push is still a technical loss."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="final-audit-push-fail",
        security=_ON, client=FakeClient(fail=True), initial_state=State.GAME_OVER,
    )
    outcome = await run_final_audit(ctx)
    assert outcome is Outcome.TECHNICAL_LOSS


async def test_run_final_audit_is_technical_loss_when_the_opponent_never_answers(
    tmp_path, default_params, network_params,
):
    """Rule 36, unchanged by 05-04: a peer that never publishes its own
    nonces loses regardless of whether a board outcome stands."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="final-audit-recv-fail",
        security=_ON, initial_state=State.GAME_OVER,
    )
    outcome = await run_final_audit(ctx)
    assert outcome is Outcome.TECHNICAL_LOSS
