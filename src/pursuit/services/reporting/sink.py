"""The `MailSink` contract and the sink that transmits nothing (REPORT-01).

`ReportingChain` (07-01) takes its sink as an injected callable with no
default, deliberately: the chain is the Figure-13 machinery and knows nothing
about transports. This module names the contract those transports satisfy and
supplies the one that writes to disk.

`DryRunSink` IS NOT EVIDENCE THAT THE LIVE PATH WORKS, AND MUST NEVER BE USED
AS ANY. A sink that writes a file and returns success makes every send test
green whether or not `GmailSink` is correct, which is this plan's central
vacuity risk. So the split is a hard rule, not a convention: the 429/backoff
test, the send-only-scope test and the retry-exhaustion/queue test all run
against `GmailSink` with an injected fake transport, and `DryRunSink`'s own
test asserts only what a disk write can honestly assert -- both files exist,
the `.eml` re-parses to the message `message.py` built, and the `.json` equals
the report. `tests/unit/test_mail_sink_dry_run.py` mentions neither 429 nor a
scope nor a backoff, and that absence is checked by
`tests/unit/test_gmail_sink.py`.

BOTH FILES GO THROUGH `artifacts.write_artifact*`, so the dry run inherits the
D7-1 refusal (nothing under `logs/`, which .gitignore excludes wholesale) and
the crash-safe write/rotate scheme, rather than opening a second write path
that no rule governs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from pursuit.services.reporting.artifacts import write_artifact, write_artifact_bytes
from pursuit.services.reporting.message import (
    build_report_message,
    render_message,
    report_filename,
)
from pursuit.shared.reporting_config import ReportingMode

__all__ = ("EML_SUFFIX", "DryRunSink", "MailSink", "SendReceipt")

#: The rendered RFC 5322 message keeps the artifact's stem and swaps only the
#: extension, so `result_<game_id>.json` and `result_<game_id>.eml` sit beside
#: each other and a reader never has to guess which report an `.eml` carries.
EML_SUFFIX = ".eml"


@dataclass(frozen=True)
class SendReceipt:
    """What one send produced. Never a bare bool: a dry run's evidence is the
    two paths it wrote, and a live send's is the id the API returned, and a
    caller that cannot tell them apart cannot report honestly."""

    mode: ReportingMode
    message_id: str | None = None
    paths: tuple[Path, ...] = field(default_factory=tuple)


@runtime_checkable
class MailSink(Protocol):
    """One outgoing report. Structural, so a fake transport in a test and the
    real `GmailSink` are interchangeable without either inheriting anything."""

    async def send(self, report: dict) -> SendReceipt:
        """Deliver `report`, or raise. Raising is how the gatekeeper's retry
        ladder is told to back off and try again (see `gmail_sink.py`); a sink
        that swallows a failure and returns a receipt anyway would report a
        delivery that never happened."""
        ...


class DryRunSink:
    """`reporting.mode = dry_run`: write the report and the message it would
    have been, and TRANSMIT NOTHING.

    This is what every config this repository ships selects, so that no
    development run can mail the lecturer (rules 31, 39-40). It opens no
    client, reads no credential and imports nothing from `google-*`.
    """

    def __init__(self, *, artifact_dir: Path | str, recipient: str) -> None:
        self._artifact_dir = artifact_dir
        self._recipient = recipient

    async def send(self, report: dict) -> SendReceipt:
        """Write `<artifact_dir>/result_<game_id>.json` and its `.eml`."""
        filename = report_filename(report)
        message = build_report_message(report=report, recipient=self._recipient)
        json_path = write_artifact(self._artifact_dir, filename, report)
        eml_path = write_artifact_bytes(
            self._artifact_dir,
            f"{Path(filename).stem}{EML_SUFFIX}",
            render_message(message),
        )
        return SendReceipt(mode=ReportingMode.DRY_RUN, paths=(json_path, eml_path))
