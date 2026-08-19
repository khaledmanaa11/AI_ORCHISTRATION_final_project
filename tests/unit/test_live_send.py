"""The supervised live send's contract (07-10), driven with a FAKE transport.

No credential, no network, no browser: `live_send.send_once` takes its
transport builder as a seam, exactly as `build_gmail_transport` takes its
credentials loader. What is asserted here is the half a fake CAN prove -- that
the shipped chain is the one used, that the JSON arrives ATTACHED, and that the
two hazards this script exists to remove really are removed. The delivered
half stays a human's, and this file does not pretend otherwise.

THE TWO STRUCTURAL GUARDS ARE THE POINT. `test_the_shipped_config_is_never
_written` fires on the file's bytes, and the league-config guard reads the
module's own source: both encode a claim the docstring makes, so a later edit
that quietly reintroduces the flip-on-disk or routes this through
`report_game_end` fails here instead of on league day.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import live_send  # noqa: E402

from pursuit.shared.reporting_config import ReportingMode  # noqa: E402
from tests.unit.gmail_fixtures import (  # noqa: E402
    DEFAULT_MESSAGE_ID,
    OK_STATUS,
    FakeGmailTransport,
    sample_report,
)

SHIPPED_POLICE = REPO_ROOT / "config" / "police"


def _transport(statuses=(OK_STATUS,)):
    fake = FakeGmailTransport(statuses=list(statuses))
    return fake, (lambda _params: fake)


def test_the_shipped_config_is_read_and_lifted_to_live_in_memory():
    params = live_send.live_params(SHIPPED_POLICE)
    assert params.mode is ReportingMode.LIVE
    assert params.recipient == live_send.load_reporting_config(
        SHIPPED_POLICE / "reporting.json"
    ).recipient


def test_the_shipped_config_is_never_written():
    """The runbook's flip-and-flip-back hazard, asserted on the file's bytes."""
    before = (SHIPPED_POLICE / "reporting.json").read_bytes()
    live_send.live_params(SHIPPED_POLICE)
    assert (SHIPPED_POLICE / "reporting.json").read_bytes() == before
    assert b'"mode": "dry_run"' in before


def test_a_config_that_is_already_live_on_disk_is_refused(tmp_path):
    """Belt to the braces: if a flipped config IS lying around, refuse it."""
    source = json.loads((SHIPPED_POLICE / "reporting.json").read_text(encoding="utf-8"))
    source["reporting"]["mode"] = "live"
    (tmp_path / "reporting.json").write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="dry_run"):
        live_send.live_params(tmp_path)


async def test_the_report_is_sent_with_the_json_attached(tmp_path):
    fake, builder = _transport()
    report = sample_report()
    outcome, receipt = await live_send.send_once(
        report,
        live_send.live_params(SHIPPED_POLICE),
        work_dir=tmp_path,
        transport_builder=builder,
    )
    assert outcome.sent is True
    assert fake.attempts == 1
    assert receipt.mode is ReportingMode.LIVE
    assert receipt.message_id == DEFAULT_MESSAGE_ID, (
        "the id is this step's whole evidence; SendOutcome drops it"
    )
    attachment = next(
        part for part in fake.parsed_attempt(0).walk() if part.get_filename()
    )
    assert attachment.get_filename().endswith(".json")
    assert json.loads(attachment.get_payload(decode=True))["game_id"] == report["game_id"]


async def test_a_refusing_server_reports_not_sent_rather_than_raising(tmp_path):
    """The chain returns; it never raises. A failed send must SAY so."""
    fake, builder = _transport(statuses=[429])
    outcome, receipt = await live_send.send_once(
        sample_report(),
        replace(live_send.live_params(SHIPPED_POLICE), wait_after_error_seconds=0),
        work_dir=tmp_path,
        transport_builder=builder,
    )
    assert outcome.sent is False
    assert receipt is None, "no receipt may be reported for a message never accepted"
    assert fake.attempts > 1, "the gatekeeper's ladder should have retried"


def test_the_cli_refuses_without_the_confirmation_flag(tmp_path, capsys):
    artifact = tmp_path / "result_x.json"
    artifact.write_text(json.dumps(sample_report()), encoding="utf-8")
    code = live_send.main(
        ["--config-dir", str(SHIPPED_POLICE), "--result", str(artifact)]
    )
    assert code != 0
    assert "--confirm-live-send" in capsys.readouterr().err


def test_this_script_never_loads_the_league_config():
    """It is not a game, so rule 49's four-URL gate is neither met nor weakened.

    Asserted over the source: routing this through `report_game_end` would pull
    `load_league_config` back in, and that is the change this must catch.
    """
    source = Path(live_send.__file__).read_text(encoding="utf-8")
    body = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )
    _, _, code = body.partition('"""')[2].partition('"""')
    for forbidden in ("load_league_config", "report_game_end", "league.json"):
        assert forbidden not in code, f"{forbidden} reappeared in live_send.py"
    assert "build_reporting_chain" in code, "the control: the shipped chain IS used"
