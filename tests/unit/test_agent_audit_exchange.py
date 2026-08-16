"""Coverage-closing tests (Rule 2) for agent_audit_exchange.py's
technical-loss and edge-case branches: a failed FINAL_REVEAL push/receive,
observed() skipping a record with no envelope, an absent wire log, and
record_technical_loss's own append+return shape.

The receive leg's ENVELOPE-TYPE contract (05-15, G10) lives in the sibling
`test_agent_audit_receive.py`, split off at the 150-code-line gate. The
silent-peer case below stays here and is BYTE-UNEDITED: it is the fairness
control for that split -- rule 36's sanction against a peer that really
does publish nothing must keep firing exactly as it did."""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import agent_audit_exchange
from pursuit.network.verdict import TechnicalWin, TechnicalWinReason
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import FakeClient, make_ctx

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")


async def test_push_final_reveal_returns_a_verdict_when_the_opponent_never_answers(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="audit-push-fail",
        security=_ON, client=FakeClient(fail=True),
    )
    verdict = await agent_audit_exchange.push_final_reveal(ctx, [])
    assert isinstance(verdict, TechnicalWin)
    assert verdict.reason is TechnicalWinReason.OPPONENT_UNRESPONSIVE


async def test_receive_final_reveal_returns_a_verdict_and_no_records_on_silence(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="audit-recv-fail",
        security=_ON,
    )
    records, verdict = await agent_audit_exchange.receive_final_reveal(ctx)
    assert records == []
    assert isinstance(verdict, TechnicalWin)


def test_observed_on_a_missing_log_file_returns_empty_dicts(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="audit-no-log")
    commits, reveals = agent_audit_exchange.observed(ctx, direction="message_sent")
    assert commits == {} and reveals == {}


def test_observed_skips_a_record_with_no_envelope(tmp_path, default_params, network_params):
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="audit-no-env")
    ctx.log_path.write_text(
        '{"game_uid":"g","turn":0,"event":"message_sent","sender":"police","timestamp":"t"}\n',
        encoding="utf-8",
    )
    commits, reveals = agent_audit_exchange.observed(ctx, direction="message_sent")
    assert commits == {} and reveals == {}


def test_record_technical_loss_appends_a_technical_win_event_and_returns_the_outcome(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="audit-tl")
    verdict = TechnicalWin(
        reason=TechnicalWinReason.OPPONENT_UNRESPONSIVE, attempts=2, timeout_seconds=1.0,
        backoff_seconds=0.0, elapsed_seconds=2.0, last_error="simulated",
    )

    outcome = agent_audit_exchange.record_technical_loss(ctx, verdict)

    assert outcome is Outcome.TECHNICAL_LOSS
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    assert any('"technical_win"' in line for line in lines)
