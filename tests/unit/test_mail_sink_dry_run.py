"""What a disk write can honestly assert, and nothing more.

This file makes NO claim about 429, about the send-only scope, about backoff,
or about delivery. `DryRunSink` writes a file and returns success; it would do
so whether or not the live path works, so using it to assert REPORT-04 or
REPORT-05 would be the vacuity `sink.py`'s docstring names. Those belong to
`tests/unit/test_gmail_sink.py`, against `GmailSink`.
"""

import json
from email import message_from_bytes
from email.policy import default as default_policy

import pytest

from pursuit.services.reporting.artifacts import result_filename
from pursuit.services.reporting.message import build_report_message, render_message
from pursuit.services.reporting.sink import EML_SUFFIX, DryRunSink, MailSink, SendReceipt
from pursuit.shared.reporting_config import ReportingMode

RECIPIENT = "rmisegal+uoh26finalgame@gmail.com"
GAME_ID = "dryrun7"


def _report() -> dict:
    return {"game_uid": "uid-dry-1", "game_id": GAME_ID, "outcome": "timeout", "turns": 30}


async def _send(tmp_path, report: dict | None = None) -> SendReceipt:
    sink = DryRunSink(artifact_dir=tmp_path, recipient=RECIPIENT)
    return await sink.send(report if report is not None else _report())


async def test_both_files_are_written(tmp_path):
    receipt = await _send(tmp_path)
    assert [path.name for path in receipt.paths] == [
        result_filename(GAME_ID),
        f"result_{GAME_ID}{EML_SUFFIX}",
    ]
    assert all(path.exists() for path in receipt.paths)


async def test_the_json_file_equals_the_report(tmp_path):
    receipt = await _send(tmp_path)
    assert json.loads(receipt.paths[0].read_text(encoding="utf-8")) == _report()


async def test_the_eml_re_parses_to_the_message_the_builder_built(tmp_path):
    receipt = await _send(tmp_path)
    on_disk = message_from_bytes(receipt.paths[1].read_bytes(), policy=default_policy)
    expected = message_from_bytes(
        render_message(build_report_message(report=_report(), recipient=RECIPIENT)),
        policy=default_policy,
    )
    assert on_disk["To"] == expected["To"]
    assert on_disk["Subject"] == expected["Subject"]
    assert [part.get_filename() for part in on_disk.iter_attachments()] == [
        part.get_filename() for part in expected.iter_attachments()
    ]
    assert next(on_disk.iter_attachments()).get_payload(decode=True) == (
        next(expected.iter_attachments()).get_payload(decode=True)
    )


async def test_the_eml_bytes_are_not_newline_translated(tmp_path):
    """Written in binary through `durable_write_bytes`: a text-mode write on
    Windows would turn the CRLF `render_message` emits into CRCRLF."""
    receipt = await _send(tmp_path)
    assert b"\r\r\n" not in receipt.paths[1].read_bytes()


async def test_the_receipt_reports_dry_run_and_no_message_id(tmp_path):
    receipt = await _send(tmp_path)
    assert receipt.mode is ReportingMode.DRY_RUN
    assert receipt.message_id is None


async def test_a_second_send_rotates_rather_than_appends(tmp_path):
    """`durable_write_*` rotates the previous generation, so a re-sent series
    report (OQ-4 rewrites one `result_` file per sub-game) leaves the earlier
    one recoverable instead of clobbered."""
    await _send(tmp_path)
    await _send(tmp_path, {**_report(), "turns": 31})
    assert (tmp_path / f"result_{GAME_ID}.prev.json").exists()
    assert json.loads((tmp_path / result_filename(GAME_ID)).read_text())["turns"] == 31


async def test_the_dry_run_sink_satisfies_the_mail_sink_protocol():
    assert isinstance(DryRunSink(artifact_dir=".", recipient=RECIPIENT), MailSink)


async def test_a_logs_directory_is_refused_before_anything_is_written(tmp_path):
    """D7-1 is inherited from `write_artifact`, not re-implemented here."""
    sink = DryRunSink(artifact_dir=tmp_path / "logs" / "police", recipient=RECIPIENT)
    with pytest.raises(ValueError, match="D7-1"):
        await sink.send(_report())
    assert not (tmp_path / "logs").exists()


async def test_a_report_with_no_game_id_is_refused_rather_than_written(tmp_path):
    sink = DryRunSink(artifact_dir=tmp_path, recipient=RECIPIENT)
    with pytest.raises(KeyError, match="game_id"):
        await sink.send({"game_uid": "uid-dry-1"})
    assert list(tmp_path.iterdir()) == []
