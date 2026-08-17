"""The Figure-13 composition (D-69, rules 28-29, REPORT-02).

The book's order, unchanged: `QuotaManager` -> the token bucket -> the DOS
detector -> the sink. The bucket is NOT re-implemented here; it stays inside
`Gatekeeper.submit()` where it has been since Phase 4, and this module wraps
the ONE gatekeeper class rather than building a second one (D-68,
docs/SEGAL_GUIDELINES.md:179-182: "Build **one** gatekeeper satisfying both").
Quota is a pre-call gate; the detector is a pre-call gate AND a post-call
observer, which is the only place bucket readiness can be read per attempt.

NO REFUSAL IS A CRASH, AND NONE IS A BARE REJECTION. Every path returns a
`SendOutcome` (docs/SEGAL_GUIDELINES.md:175-176: "On overflow: FIFO queue, not
rejection and not a crash"; `GatekeeperOverflow`'s own docstring: "it is not a
crash and must never propagate unhandled into the turn loop"). A quota
exhaustion, a latched lock and a retry-exhausted send all enqueue onto a FIFO
bounded at `queue_depth` (Table 19 row 5, from reporting.json) and return.

THE DRAIN IS CALLER-DRIVEN. No thread, no background task, no timer: the
freeze watchdog (`network/watchdog.py`, `os._exit(1)`) is this process's only
liveness owner, and a second one racing it is how a game dies mid-turn.

THIS MODULE TRANSMITS NOTHING. `sink` is injected and has no default; 07-04
supplies `DryRunSink` (disk) and `GmailSink` (network).
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum

from pursuit.services.llm import CallResult, Gatekeeper
from pursuit.services.reporting.dos import DosDetector
from pursuit.services.reporting.quota import QuotaManager

#: A mail send has no concept of a token, so it estimates and reports zero --
#: `CallResult`'s own contract ("a call with no concept of tokens (Phase 7
#: Gmail) passes 0 for both"). Not a parameter.
_NO_TOKENS = 0

_log = logging.getLogger(__name__)


class Refusal(str, Enum):
    """Why a send did not go out. Every value is caller-handled, never raised."""

    QUOTA_EXHAUSTED = "quota_exhausted"
    DOS_LOCKED = "dos_locked"
    SEND_FAILED = "send_failed"
    QUEUE_FULL = "queue_full"


@dataclass(frozen=True)
class SendOutcome:
    """The result of one `send()` or one drained attempt.

    `sent` and `refusal` are exclusive: exactly one is set. `queued` says
    whether a refused report is still owed -- False on a full queue, which is
    the backpressure case SEGAL §4 asks to be alerted about, and it is logged
    at WARNING rather than swallowed.
    """

    sent: bool
    refusal: "Refusal | None" = None
    queued: bool = False


class ReportingChain:
    """Figure 13, composed around the shipped `Gatekeeper` (D-68/D-69)."""

    def __init__(
        self,
        *,
        gatekeeper: Gatekeeper,
        quota: QuotaManager,
        dos: DosDetector,
        sink: Callable[[dict], Awaitable[object]],
        queue_depth: int,
    ) -> None:
        self._gatekeeper = gatekeeper
        self._quota = quota
        self._dos = dos
        self._sink = sink
        self._queue_depth = queue_depth
        self._queue: list[dict] = []

    @property
    def pending(self) -> int:
        """Reports queued and still owed."""
        return len(self._queue)

    async def send(self, report: dict) -> SendOutcome:
        """One report through the whole chain. Returns; never raises."""
        if self._dos.locked:
            return self._enqueue(report, Refusal.DOS_LOCKED)
        if not self._quota.try_consume():
            return self._enqueue(report, Refusal.QUOTA_EXHAUSTED)
        return await self._through_gatekeeper(report)

    async def drain(self) -> list[SendOutcome]:
        """Re-attempt everything queued, oldest first, exactly once each.

        Explicit and caller-driven. The queue is taken in one slice before the
        first attempt, so a report that fails again is re-queued for the NEXT
        drain instead of being retried forever inside this one.
        """
        owed, self._queue = self._queue, []
        return [await self.send(report) for report in owed]

    async def _through_gatekeeper(self, report: dict) -> SendOutcome:
        """Stages 2-4: the bucket (inside `submit`), the observation, the sink."""

        async def _call() -> CallResult:
            return CallResult(
                value=await self._sink(report),
                input_tokens=_NO_TOKENS,
                output_tokens=_NO_TOKENS,
            )

        try:
            await self._gatekeeper.submit(_call, estimated_tokens=_NO_TOKENS)
        except Exception as exc:
            _log.warning("report send failed, queueing: %s", exc)
            return self._enqueue(report, Refusal.SEND_FAILED)
        finally:
            self._dos.observe(self._gatekeeper.bucket_ready)
        return SendOutcome(sent=True)

    def _enqueue(self, report: dict, refusal: Refusal) -> SendOutcome:
        """Hold a refused report for the next `drain()`, or alert if full."""
        if len(self._queue) >= self._queue_depth:
            _log.warning(
                "report send queue full at %d (Table 19 row 5); dropping the newest "
                "report after refusal %s", self._queue_depth, refusal.value,
            )
            return SendOutcome(sent=False, refusal=Refusal.QUEUE_FULL, queued=False)
        self._queue.append(report)
        return SendOutcome(sent=False, refusal=refusal, queued=True)
