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

import ast
import importlib
import json
import os
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


def test_importing_this_script_does_not_disarm_the_credential_environment():
    """THE BUG THIS FILE EXISTS TO NEVER REPEAT (2026-08-19).

    `gate7_common` POPS the two Gmail env vars out of `os.environ` at IMPORT
    time -- correct for a gate that must never let a grader's shell become a
    live send. `live_send` imported it for a six-line watchdog and thereby
    disarmed itself: three real runs died on "environment variable
    PURSUIT_GMAIL_CREDENTIALS_PATH ... is unset" with the variable set in the
    calling shell. A fake transport never touches the environment, so NO test
    above this one could have caught it. This one imports for real.
    """
    for name in ("PURSUIT_GMAIL_CREDENTIALS_PATH", "PURSUIT_GMAIL_TOKEN_PATH"):
        os.environ[name] = f"sentinel-for-{name}"
    importlib.reload(live_send)
    for name in ("PURSUIT_GMAIL_CREDENTIALS_PATH", "PURSUIT_GMAIL_TOKEN_PATH"):
        assert os.environ.get(name) == f"sentinel-for-{name}", (
            f"importing live_send cleared {name}; a live send is impossible"
        )
        del os.environ[name]


def test_this_script_neither_imports_nor_calls_the_paths_that_would_break_it():
    """Two claims the docstrings make, asserted over the PARSED module.

    `ast`, not a substring scan: the first draft of this guard read the raw
    source and failed on the `_SendWatchdog` docstring, which NAMES
    `gate7_common` precisely to explain why it must not be imported. Prose
    about a hazard is not the hazard.

    `gate7_common` would disarm the credential environment at import;
    `report_game_end` / `load_league_config` would drag rule 49's four-URL gate
    back in and make this impossible before league day.
    """
    tree = ast.parse(Path(live_send.__file__).read_text(encoding="utf-8"))
    imported, referenced = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Name):
            referenced.add(node.id)
        elif isinstance(node, ast.Attribute):
            referenced.add(node.attr)
    for forbidden in ("gate7_common", "load_league_config", "report_game_end"):
        assert forbidden not in imported | referenced, f"{forbidden} reappeared"
    assert "build_reporting_chain" in imported, "the control: the shipped chain IS used"


def test_the_ast_guard_can_actually_fire():
    """An all-clear from a scanner that matches nothing is not an all-clear."""
    tree = ast.parse("from gate7_common import RecordingWatchdog")
    modules = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert "gate7_common" in modules
