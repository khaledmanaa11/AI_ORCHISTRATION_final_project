"""Sec10.4 criterion 1 -- everything up to the send, and nothing beyond it.

The verdict is reported as TWO named fields, never one boolean:
`dry_run_verdict` (measured here) and `live_send_verdict` (PENDING, 07-10).
A game summary that was assembled, attached, scope-gated, rate-limited and
written to disk is not a game summary that was SENT BY MAIL, and a document
that collapsed the two would be the failure mode rule 38 exists for.

Every proof below runs against an INJECTED fake transport
(`tests/unit/gmail_fixtures.FakeGmailTransport`, which raises a REAL
`googleapiclient.errors.HttpError`), so nothing here opens a socket, reads a
credential or needs an environment variable.
"""

from __future__ import annotations

import json
import tempfile
from email import message_from_bytes
from email.policy import default as default_policy
from pathlib import Path

from gate7_common import REPO_ROOT, SHIPPED_REPORTING, RecordingWatchdog
from gate7_mail_live import measure_backoff_ladder, measure_queue_and_drain, measure_scope_gate

from pursuit.services.reporting.end_of_game import QUOTA_FILENAME, build_reporting_chain
from pursuit.services.reporting.message import BODY_TEXT
from pursuit.shared.reporting_config import (
    MANDATORY_REPORTING_ADDRESS,
    ReportingMode,
    load_reporting_config,
)

GAME_ID = "gate7mail"
#: RFC 5322's line separator, which `email.policy.SMTP` renders and which the
#: stdlib parser hands back verbatim. Structural, not a parameter.
CRLF = "\r\n"
#: A value that appears NOWHERE in the boilerplate body, so "the body carries
#: no report content" is a search for something distinctive rather than a hope.
DISTINCTIVE = "uid-gate7-distinctive-1a2b3c"
REPORT = {"game_uid": DISTINCTIVE, "game_id": GAME_ID, "outcome": "capture", "turns": 5}

LIVE_PENDING_REASON = (
    "no message has been delivered. The one live send needs a human at Google's "
    "OAuth consent screen and one config flipped to live; that is 07-10's work "
    "(docs/phases/phase-7/OAUTH-RUNBOOK.md). This script clears both credential "
    "environment variables at import, so it CANNOT have sent anything."
)
LIVE_EVIDENCE_REQUIRED = (
    "the Gmail message id returned by the API for the one supervised send",
    "a screenshot of the delivered message at the mandatory recipient showing the "
    "result_<game_id>.json ATTACHMENT (rules 33-34)",
    "the config diff proving reporting.mode was flipped to live and flipped BACK",
    "the games-played value decision (OQ-5) recorded in writing BEFORE the send",
)


def _shipped_modes() -> dict[str, str]:
    """Both shipped `reporting.json` modes, read off disk."""
    return {
        role: load_reporting_config(REPO_ROOT / "config" / role / "reporting.json").mode.value
        for role in ("police", "thief")
    }


def _attachment_evidence(message: object) -> dict:
    attachments = list(message.iter_attachments())
    first = attachments[0] if attachments else None
    payload = first.get_content() if first is not None else b""
    decoded = payload.decode("utf-8") if isinstance(payload, bytes) else str(payload)
    return {
        "attachment_count": len(attachments),
        "filename": first.get_filename() if first is not None else None,
        "content_type": first.get_content_type() if first is not None else None,
        "is_attachment": bool(first is not None and first.get_content_disposition() == "attachment"),
        "reparses_to_the_report": json.loads(decoded) == REPORT if decoded else False,
    }


def _body_evidence(message: object) -> dict:
    """The body as it came back off the RENDERED bytes.

    CRLF is normalised before the comparison and recorded as its own field:
    `render_message` renders under `email.policy.SMTP` deliberately, so that
    the `.eml` a dry run leaves on disk is byte-identical to what a live send
    would put on the wire. `tests/unit/test_mail_message.py:111` normalises the
    same way; a gate that compared raw would report a FAIL for the encoding
    being CORRECT.
    """
    body = message.get_body(preferencelist=("plain",))
    text = body.get_content() if body is not None else ""
    return {
        "line_ending_is_crlf": CRLF in text,
        "is_the_fixed_boilerplate": text.replace(CRLF, "\n") == BODY_TEXT,
        "carries_no_report_content": DISTINCTIVE not in text and GAME_ID not in text,
    }


async def _measure_dry_run(params: object) -> dict:
    """The whole production chain, composed by `build_reporting_chain`, with
    the sink it defaults to: `DryRunSink`, which transmits nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        watchdog = RecordingWatchdog()
        chain = build_reporting_chain(
            params, watchdog=watchdog, artifact_dir=directory, quota_dir=directory,
        )
        outcome = await chain.send(dict(REPORT))
        written = sorted(path.name for path in directory.iterdir())
        eml = directory / f"result_{GAME_ID}.eml"
        message = message_from_bytes(eml.read_bytes(), policy=default_policy)
        return {
            "mode": ReportingMode.DRY_RUN.value,
            "sent": outcome.sent,
            "refusal": outcome.refusal.value if outcome.refusal is not None else None,
            "pending_after_send": chain.pending,
            "watchdog_touches": watchdog.touches,
            "files_written": written,
            "quota_counter_written_beside_the_run": QUOTA_FILENAME in written,
            "to_header": message["To"],
            "subject_header": message["Subject"],
            "from_header_absent": message["From"] is None,
            "attachment": _attachment_evidence(message),
            "body": _body_evidence(message),
        }


async def measure_mail() -> dict:
    """Criterion 1's evidence: the dry-run half measured, the live half named."""
    params = load_reporting_config(SHIPPED_REPORTING)
    return {
        "shipped_modes": _shipped_modes(),
        "recipient": params.recipient,
        "recipient_is_the_mandatory_address": params.recipient == MANDATORY_REPORTING_ADDRESS,
        "dry_run_end_to_end": await _measure_dry_run(params),
        "backoff_ladder": await measure_backoff_ladder(params, dict(REPORT)),
        "scope_gate": measure_scope_gate(params),
        "queue_and_drain": await measure_queue_and_drain(params, dict(REPORT)),
        "live_send": {
            "verdict": "PENDING",
            "why": LIVE_PENDING_REASON,
            "evidence_07_10_must_attach": list(LIVE_EVIDENCE_REQUIRED),
        },
    }
