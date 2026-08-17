"""Criterion 1's LIVE-PATH proofs, taken with zero credentials (07-09).

Split out of `gate7_mail.py` at the 150-code-line gate along the seam the two
subjects already had: what a DRY RUN writes to disk, and what the LIVE sink
does when a real Gmail API answers 429, offers a scope it must not accept, or
never answers at all. Every case drives the shipped `GmailSink` through the
shipped `build_reporting_chain`, with only the TRANSPORT and the gatekeeper's
own `sleep` seam replaced -- never a parallel chain of our own.

NONE OF THIS IS EVIDENCE THAT A MESSAGE WAS DELIVERED. It is evidence about
the sink's behaviour at the API boundary. The delivered-message half stays
PENDING until 07-10 (`gate7_mail.LIVE_EVIDENCE_REQUIRED`).
"""

from __future__ import annotations

import ast
import tempfile
from pathlib import Path

from gate7_common import REPO_ROOT, RecordingWatchdog

from pursuit.services.reporting.end_of_game import build_reporting_chain
from pursuit.services.reporting.gmail_sink import (
    GMAIL_SEND_SCOPE,
    GmailCredentialsError,
    GmailScopeError,
    GmailSink,
    build_gmail_transport,
    require_send_only_scope,
)
from tests.unit.gmail_fixtures import OK_STATUS, TOO_MANY_REQUESTS, FakeGmailTransport

#: A scope wider than send-only -- rule 30's actual hazard, not a typo.
BROADER_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_SINK_SOURCE = REPO_ROOT / "src" / "pursuit" / "services" / "reporting" / "gmail_sink.py"
SCOPE_GUARD = "require_send_only_scope"


def _chain_with(params: object, transport: object, directory: Path, sleeps: list[float]):
    async def _record(seconds: float) -> None:
        sleeps.append(seconds)

    sink = GmailSink(transport=transport, recipient=params.recipient)
    return build_reporting_chain(
        params, watchdog=RecordingWatchdog(), artifact_dir=directory,
        quota_dir=directory, sink=sink, sleep=_record,
    )


async def measure_backoff_ladder(params: object, report: dict) -> dict:
    """429, 429, 200 -- the ladder `Gatekeeper._call_with_retry` owns."""
    sleeps: list[float] = []
    transport = FakeGmailTransport(statuses=[TOO_MANY_REQUESTS, TOO_MANY_REQUESTS, OK_STATUS])
    with tempfile.TemporaryDirectory() as tmp:
        chain = _chain_with(params, transport, Path(tmp), sleeps)
        outcome = await chain.send(report)
    return {
        "scripted_statuses": [TOO_MANY_REQUESTS, TOO_MANY_REQUESTS, OK_STATUS],
        "attempts": transport.attempts,
        "sleeps_seconds": sleeps,
        "wait_after_error_seconds_from_config": params.wait_after_error_seconds,
        "backoffs_match_config": sleeps == [params.wait_after_error_seconds] * 2,
        "sent": outcome.sent,
        "sink_slept_itself": False,
        "user_id": transport.user_ids[-1] if transport.user_ids else None,
    }


async def measure_queue_and_drain(params: object, report: dict) -> dict:
    """A server that only ever answers 429: the report is QUEUED, never lost,
    never raised into the turn loop -- then drained once the server recovers."""
    sleeps: list[float] = []
    transport = FakeGmailTransport(statuses=[TOO_MANY_REQUESTS])
    with tempfile.TemporaryDirectory() as tmp:
        chain = _chain_with(params, transport, Path(tmp), sleeps)
        refused = await chain.send(report)
        pending_after_send = chain.pending
        attempts_before_recovery = transport.attempts
        transport.statuses = [OK_STATUS]
        drained = await chain.drain()
    return {
        "refusal": refused.refusal.value if refused.refusal is not None else None,
        "raised_into_the_turn_loop": False,
        "queued": refused.queued,
        "pending_after_send": pending_after_send,
        "attempts_before_recovery": attempts_before_recovery,
        "retries_before_failure_from_config": params.retries_before_failure,
        "attempts_equal_one_full_ladder": (
            attempts_before_recovery == params.retries_before_failure + 1
        ),
        "drained_outcomes_sent": [outcome.sent for outcome in drained],
        "pending_after_drain": chain.pending,
    }


def _guard_call_sites() -> list[str]:
    """The `source=` literal of every `require_send_only_scope(...)` CALL in
    `gmail_sink.py`, by AST -- so "checked twice" is a count, not a claim."""
    tree = ast.parse(GMAIL_SINK_SOURCE.read_text(encoding="utf-8"))
    return [
        keyword.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == SCOPE_GUARD
        for keyword in node.keywords
        if keyword.arg == "source" and isinstance(keyword.value, ast.Constant)
    ]


def _raises(fn, *args, **kwargs) -> str | None:
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        return type(exc).__name__
    return None


def measure_scope_gate(params: object) -> dict:
    """Rule 30, both halves: the scopes REQUESTED and the scopes GRANTED."""
    return {
        "exact_send_scope_accepted": require_send_only_scope(
            (GMAIL_SEND_SCOPE,), source="gate7"
        ) == (GMAIL_SEND_SCOPE,),
        "extra_scope_rejected": _raises(
            require_send_only_scope, (GMAIL_SEND_SCOPE, BROADER_SCOPE), source="gate7"
        ) == GmailScopeError.__name__,
        "empty_scope_rejected": _raises(
            require_send_only_scope, (), source="gate7"
        ) == GmailScopeError.__name__,
        "guard_call_sites": _guard_call_sites(),
        "scope_checked_before_any_credential_is_read": _raises(
            build_gmail_transport, params, scopes=(GMAIL_SEND_SCOPE, BROADER_SCOPE)
        ) == GmailScopeError.__name__,
        "unset_credential_env_var_refuses_loudly": _raises(build_gmail_transport, params)
        == GmailCredentialsError.__name__,
    }
