"""What the report CONTAINS, and what actually leaves in the message.

Split out of `test_end_of_game_reporting.py` at the 150-code-line gate. That
file proves the hook RAN and changed nothing; this one opens the file it
produced and checks its contents against three independent sources -- the
`log_` artifact's own verdict, `git rev-parse HEAD`, and the signed Step-0
declaration -- and then re-parses the rendered RFC 5322 bytes.
"""

from __future__ import annotations

import json
import subprocess
from email import message_from_bytes
from email.policy import SMTP

from pursuit.security.step0_collect import DeclarationField
from pursuit.services.reporting.artifact_declaration import ENVELOPE_DECLARATION_KEY
from pursuit.services.reporting.artifact_log import LogArtifactField
from pursuit.services.reporting.artifact_result import (
    ResultArtifactField,
    SubGameField,
    TokensField,
)
from pursuit.services.reporting.end_of_game import report_game_end
from pursuit.services.reporting.result_agreement import AgreementField
from pursuit.services.reporting.sink import EML_SUFFIX
from tests.integration.end_of_game_harness import played_game


async def _reported(tmp_path, monkeypatch, uid):
    cfg, ctx, outcome, envelope = await played_game(tmp_path, monkeypatch, uid)
    report = await report_game_end(
        ctx, cfg, outcome=outcome, declaration_envelope=envelope,
        artifact_dir=tmp_path / "game_artifacts",
    )
    assert report is not None
    return report, outcome, envelope


async def test_the_report_carries_the_verdict_the_commit_and_both_token_totals(
    tmp_path, monkeypatch
):
    report, outcome, envelope = await _reported(tmp_path, monkeypatch, "messagea")
    artifact = json.loads(report.result_artifact.read_text(encoding="utf-8"))
    log_artifact = json.loads(report.log_artifact.read_text(encoding="utf-8"))
    sub_game = artifact[ResultArtifactField.SUB_GAMES][0]
    agreement = sub_game[SubGameField.AGREEMENT]

    assert agreement[AgreementField.OWN_OUTCOME] == outcome.value
    assert agreement[AgreementField.AUDIT_VERDICT] == log_artifact[LogArtifactField.AUDIT_VERDICT]
    assert agreement[AgreementField.AUDIT_VERDICT]["matched"] is True

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
    ).stdout.strip()
    declared = envelope[ENVELOPE_DECLARATION_KEY][DeclarationField.COMMIT_HASH]
    assert artifact[ResultArtifactField.COMMIT_HASH] == declared == head

    tokens = sub_game[SubGameField.TOKENS]
    series = artifact[ResultArtifactField.SERIES_TOKENS]
    assert tokens[TokensField.PRESENT] is True, "this game ran the language layer"
    assert series[TokensField.GAMES_MEASURED] == 1
    assert series[TokensField.TOTAL_TOKENS] == tokens[TokensField.TOTAL_TOKENS]


async def test_what_is_emailed_is_byte_for_byte_what_is_committed(tmp_path, monkeypatch):
    """`DryRunSink` names its `.json` with `report_filename`, which is
    `result_<game_id>.json` -- the SAME path the hook already wrote through
    `write_result_artifact`. So in `dry_run` the file is written twice, with
    identical bytes, and `.prev` holds that identical generation after one game
    rather than a previous sub-game.

    Recorded as a deliberate property rather than left as a surprise, because
    it is worth something: the attachment a grader receives is provably the
    artifact rule 50 has us commit. The `.prev` GENERATION still does its
    crash-safety job -- a crash in the rotate/replace window leaves a readable
    copy either way -- and the per-sub-game history lives in `sub_games`.
    """
    report, _outcome, _envelope = await _reported(tmp_path, monkeypatch, "messageb")
    committed = json.loads(report.result_artifact.read_text(encoding="utf-8"))

    message = message_from_bytes(
        report.result_artifact.with_suffix(EML_SUFFIX).read_bytes(), policy=SMTP,
    )
    attachments = [part for part in message.walk() if part.get_filename()]
    assert len(attachments) == 1
    assert attachments[0].get_content_type() == "application/json", "rule 34"
    assert json.loads(attachments[0].get_payload(decode=True).decode()) == committed

    prev = report.result_artifact.with_name(
        f"{report.result_artifact.stem}.prev{report.result_artifact.suffix}"
    )
    assert prev.read_bytes() == report.result_artifact.read_bytes()
