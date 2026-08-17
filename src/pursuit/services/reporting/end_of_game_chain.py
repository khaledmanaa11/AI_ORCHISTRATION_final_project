"""The Figure-13 chain as the GAME-END path needs it: composed from
`reporting.json`, and touching the freeze watchdog once per bounded attempt.

Split out of `end_of_game.py` at the 150-code-line gate (Segal Table 5) along
the seam the two subjects already had: WHAT the hook does at game end, and HOW
the transport it uses is assembled. `end_of_game.py` re-exports both public
names, so callers keep ONE import path.

THE MAIL LADDER OUTLIVES THE FREEZE WATCHDOG, AND THE ARITHMETIC IS WHY.
`ctx.watchdog.start()` runs at `agent_entrypoint.py:77` and `stop_watchdog` at
`:153`; the game-end hook sits between them, so the watchdog is ARMED across
this whole path and its freeze action is `os._exit(1)`.

    watchdog_threshold                                     60 s
    response_timeout_seconds x (retries_before_failure + 1)
                                              30 x 4  =   120 s
    wait_after_error_seconds x retries_before_failure
                                              30 x 3  =    90 s
    -----------------------------------------------------------
    worst-case reporting window                            210 s
                                                      = 3.5x the threshold

This is 05-13's defect (05-UAT.md G6) arriving through a new door: that plan
found the audit ladder exposed to exactly this fact and fixed it by touching
once per bounded attempt, the shape `capture_declaration.py:116-118,132`
already uses inside the same armed window.

WHICH CONTAINMENT WAS CHOSEN, AND WHY IT IS THE TOUCH RATHER THAN A BOUND.
A total bound under 60 s would have to be a NEW number, and every figure above
is a docs/PARAMETERS.md Table 19 row read from `reporting.json` -- inventing a
shorter deadline to fit under the threshold is exactly the rule-1 violation
CLAUDE.md forbids, and it would also make the mail path give up sooner than
rule 32 wants. So: touch per bounded attempt, on ENTRY and again in a
`finally`. The largest gap between two touches is then whichever is larger of
one attempt's `response_timeout_seconds` and one backoff's
`wait_after_error_seconds` -- 30 s against a 60 s threshold, with the whole
210 s ladder still available to land the report.

The touch wraps the SINK, which is the one thing in the chain the game-end
path owns: `Gatekeeper._call_with_retry` invokes it exactly once per attempt
and sleeps the backoff between attempts, so wrapping it is per-attempt by
construction rather than by counting.

NET-07 IS NOT TRADED AWAY. The watchdog is touched, never stopped or
disarmed: an agent that genuinely freezes inside this window has no attempt in
flight, so nothing touches, and the freeze fires exactly as before. That
control is a test, not a claim.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

from pursuit.services.llm import Gatekeeper
from pursuit.services.reporting.chain import ReportingChain
from pursuit.services.reporting.dos import DosDetector
from pursuit.services.reporting.quota import QuotaManager
from pursuit.services.reporting.sink import DryRunSink, MailSink
from pursuit.shared.reporting_config import ReportingMode, ReportingParams

__all__ = ("QUOTA_FILENAME", "build_reporting_chain", "watchdog_touching")

#: The durable hourly send counter, beside this role's run output. NOT under
#: the shipped `config/` tree -- `tests/_shipped_config_guard.py` makes that
#: structural -- and not an artifact, so it does not belong in `artifact_dir`.
QUOTA_FILENAME = "reporting_quota.json"

LIVE_MODE_UNWIRED = (
    "reporting.mode is 'live' but no transport was injected. 07-10 owns the one "
    "supervised live send and constructs GmailSink itself; nothing in the game-end "
    "path may build a live transport on its own (rules 31, 39-40)"
)


def watchdog_touching(
    watchdog: object, sink: MailSink
) -> Callable[[dict], Awaitable[object]]:
    """Wrap `sink.send` so the freeze watchdog is marked per bounded attempt.

    Entry AND `finally`, so a failed attempt marks activity on its way out too
    -- otherwise the gap measured by the watchdog would be the attempt plus its
    backoff rather than the larger of the two (see the module docstring).
    """

    async def _send(report: dict) -> object:
        watchdog.touch()
        try:
            return await sink.send(report)
        finally:
            watchdog.touch()

    return _send


def build_reporting_chain(
    params: ReportingParams,
    *,
    watchdog: object,
    artifact_dir: Path | str,
    quota_dir: Path | str,
    sink: MailSink | None = None,
    sleep: Callable[[float], Awaitable[None]] | None = None,
) -> ReportingChain:
    """`QuotaManager -> Gatekeeper.submit -> DosDetector -> sink`, from config.

    `sink` is injected and defaults to `DryRunSink`, which transmits nothing.
    A `live` config with no injected transport is refused loudly rather than
    silently dry-run: 07-10 is the only step that may send.

    `sleep` is `Gatekeeper`'s own already-documented seam, forwarded rather
    than re-invented so a test can drive the full 210 s ladder against an
    injected clock without a single real backoff.
    """
    if sink is None and params.mode is not ReportingMode.DRY_RUN:
        raise ValueError(LIVE_MODE_UNWIRED)
    mail_sink = sink or DryRunSink(artifact_dir=artifact_dir, recipient=params.recipient)
    return ReportingChain(
        gatekeeper=Gatekeeper(params=params, sleep=sleep or asyncio.sleep),
        quota=QuotaManager(
            ceiling_per_hour=params.requests_per_hour,
            path=Path(quota_dir) / QUOTA_FILENAME,
        ),
        dos=DosDetector(retries_before_failure=params.retries_before_failure),
        sink=watchdog_touching(watchdog, mail_sink),
        queue_depth=params.queue_depth,
    )
