"""07-10's one supervised live send -- the step the GAME path refuses to take.

WHY THIS FILE EXISTS. `end_of_game_chain.build_reporting_chain` raises
`LIVE_MODE_UNWIRED` when `reporting.mode` is `live` and no sink was injected,
and NOTHING in the agent path injects one -- every `GmailSink` built in this
repository before this file was built by a gate or a unit test around a FAKE
transport. `OAUTH-RUNBOOK.md` Sec4 step 4 nevertheless told the operator to flip
the config and run `dev_launch.py`, which is precisely the shape that refusal
exists to stop. Measured 2026-08-19: that procedure fails twice and sends
nothing. This is the missing half -- what the runbook meant by "07-10 constructs
GmailSink itself".

THE SHIPPED CONFIG IS NEVER EDITED. Flip-and-flip-back leaves a `live` config
in the working tree between two commands, one `git add -A` from being published,
and it turns five guard tests red while it sits there (all five observed, same
day). Here `dry_run` ON DISK IS A PRECONDITION: this refuses a config that is
already live, and lifts the copy it holds in memory (`dataclasses.replace`),
which is never written back.

IT DOES NOT PLAY A GAME AND IT DOES NOT READ THE LEAGUE CONFIG. It sends a
report a real game already produced. `load_league_config` refuses live mode
until all four rule-49 repo URLs are real -- including the OPPONENT'S TWO, which
do not exist until league day -- so routing this through the game path would
make the first real transmission of this project's life happen during a scored
game, with rule 35 zeroing BOTH teams if it went wrong. The guard stays exactly
as strict as it is for games. This is not a game.

WHAT IT PROVES AND WHAT IT DOES NOT. It proves the delivered half: a real
message, through the real chain, with the JSON attached. It proves nothing
about a game's outcome, and it writes no artifact -- the report it sends was
already written, by the run that produced it.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import replace
from pathlib import Path

from gate7_common import RecordingWatchdog

from pursuit.services.reporting.end_of_game import build_reporting_chain
from pursuit.services.reporting.gmail_sink import GmailSink, build_gmail_transport
from pursuit.shared.reporting_config import (
    ReportingMode,
    ReportingParams,
    load_reporting_config,
)

#: Refused rather than "helpfully" accepted: a live config on disk means the
#: flip-and-flip-back procedure is half-done, and finishing it silently here
#: would leave the operator with a live file and no reason to notice.
ALREADY_LIVE = (
    "the config on disk is already 'live'; this script needs the SHIPPED dry_run "
    "config and lifts it in memory. Restore it (git checkout config/<role>/"
    "reporting.json) and run again"
)
#: stdout is retained evidence for this step, the same channel the runbooks use.
SENT_LINE = "=== PURSUIT LIVE SEND: message accepted by Gmail, id={message_id} ==="
NOT_SENT_LINE = "=== PURSUIT LIVE SEND: NOT SENT ({refusal}); nothing was transmitted ==="


class _ReceiptCapturingSink:
    """Wrap the real sink so the id Gmail returned survives the chain.

    `ReportingChain` collapses a success to `SendOutcome(sent=True)` and drops
    the `SendReceipt`. That is right for the GAME path, which only needs to know
    whether it still owes a report -- and useless for THIS step, whose entire
    output is the message id a human checks the mailbox against. Captured by
    wrapping rather than by widening `chain.py`: the game path's return contract
    is not this script's to change.
    """

    def __init__(self, inner) -> None:
        self._inner = inner
        self.receipt = None

    async def send(self, report: dict):
        self.receipt = await self._inner.send(report)
        return self.receipt


def live_params(config_dir: Path | str) -> ReportingParams:
    """The shipped `dry_run` config, lifted to LIVE **in memory only**."""
    params = load_reporting_config(Path(config_dir) / "reporting.json")
    if params.mode is not ReportingMode.DRY_RUN:
        raise ValueError(ALREADY_LIVE)
    return replace(params, mode=ReportingMode.LIVE)


async def send_once(
    report: dict,
    params: ReportingParams,
    *,
    work_dir: Path | str,
    transport_builder=build_gmail_transport,
):
    """One report through the SHIPPED chain, with a real `GmailSink` on the end.

    Returns `(outcome, receipt)`. The receipt is `None` on refusal and carries
    the Gmail message id on success -- see `_ReceiptCapturingSink` for why it
    cannot simply be read off the outcome.

    `transport_builder` is the seam every test drives with a fake, mirroring
    `build_gmail_transport`'s own `credentials_loader`. `work_dir` holds only
    the quota ledger: no artifact is written here, because the report being
    sent was written by the game that produced it.
    """
    capturing = _ReceiptCapturingSink(
        GmailSink(transport=transport_builder(params), recipient=params.recipient)
    )
    chain = build_reporting_chain(
        params,
        watchdog=RecordingWatchdog(),
        artifact_dir=work_dir,
        quota_dir=work_dir,
        sink=capturing,
    )
    return await chain.send(report), capturing.receipt


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config-dir", required=True, help="config/police or config/thief")
    parser.add_argument("--result", required=True, help="a result_<game_id>.json to send")
    parser.add_argument(
        "--confirm-live-send",
        action="store_true",
        help="required: this transmits a real message to the mandatory recipient",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(sys.argv[1:] if argv is None else argv)
    if not args.confirm_live_send:
        print(
            "refusing: pass --confirm-live-send. This sends REAL mail to the "
            "mandatory recipient and cannot be undone (rule 35).",
            file=sys.stderr,
        )
        return 2
    report = json.loads(Path(args.result).read_text(encoding="utf-8"))
    params = live_params(args.config_dir)
    outcome, receipt = asyncio.run(
        send_once(report, params, work_dir=Path(args.result).parent)
    )
    if not outcome.sent:
        print(NOT_SENT_LINE.format(refusal=outcome.refusal), file=sys.stderr)
        return 1
    print(SENT_LINE.format(message_id=receipt.message_id))
    print(f"recipient={params.recipient}  report={Path(args.result).name}")
    print("NOW CHECK THE MAILBOX: rule 35 asks whether it ARRIVED, with the JSON attached.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
