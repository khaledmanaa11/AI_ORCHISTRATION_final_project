"""The single API gatekeeper every external call in the project passes
through (D-34, QUAL-03). Provider-agnostic: ``submit()`` takes a generic
callable and a token estimate, never a vendor-specific request shape, so
Phase 7 hangs Gmail off this SAME class instead of writing a second
gatekeeper. No LLM-provider SDK import lives here -- see 04-06's
``provider.py`` for the (separate) module that owns that dependency.

``submit()``'s order, every number sourced from ``LanguageParams`` (Table 19,
floor-checked by ``shared/language_config.py``):

1. ``budget.reserve(estimated_tokens)`` -- the degrade level reflects every
   queued call immediately, not just completed ones (D-35).
2. Admit through a FIFO queue bounded at ``queue_depth`` (row 5); beyond the
   bound, raise ``GatekeeperOverflow`` immediately without touching any
   already-queued call (QUAL-05) -- the caller converts this into the
   deterministic fallback (D-33); it must never reach the turn loop unhandled.
3. Acquire the parallel-call semaphore (row 2) -- ``asyncio.Semaphore``
   serves waiters FIFO, which is what makes step 2's queue ordered.
4. Await the token bucket (``bucket.py``), one token per attempt -- every
   attempt, including a retry, is a real outgoing request.
5. Run ``fn`` under ``response_timeout_seconds`` (row 6); on ANY failure
   (including a timeout, which ``asyncio.wait_for`` raises as
   ``TimeoutError`` -- provider-agnostic, so this module cannot narrow the
   exception type further) back off ``wait_after_error_seconds`` (row 3) and
   retry, up to ``retries_before_failure`` times (row 4); the last failure
   then surfaces to the caller, same D-33 fallback contract as
   ``GatekeeperOverflow``.
6. Settle the budget with ``fn``'s observed usage and return its value.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pursuit.services.llm.bucket import TokenBucket
from pursuit.services.llm.budget import TokenBudget
from pursuit.shared.language_config import LanguageParams

_SECONDS_PER_MINUTE = 60.0


class GatekeeperOverflow(Exception):  # noqa: N818 -- name fixed by this plan's must_haves contract
    """The FIFO queue is already at ``queue_depth`` (Table 19 row 5, QUAL-05).

    Callers MUST catch this and apply the deterministic fallback (D-33) --
    it is not a crash and must never propagate unhandled into the turn loop.
    """


@dataclass(frozen=True)
class CallResult:
    """What every ``fn`` passed to ``Gatekeeper.submit()`` must return.

    ``value`` is opaque to this module -- an LLM provider's response, a
    Gmail send receipt, anything (D-34). ``input_tokens``/``output_tokens`` are
    the observed usage settled against the budget; a call with no concept
    of tokens (Phase 7 Gmail) passes 0 for both -- required, not defaulted,
    so every ``fn`` author states its usage explicitly (QUAL-11).
    """

    value: object
    input_tokens: int
    output_tokens: int


class Gatekeeper:
    """The one door to an external service (D-34). See module docstring.

    ``params`` is keyword-only and REQUIRED (QUAL-11); ``clock``/``sleep``
    are injected seams (default ``time.monotonic`` / ``asyncio.sleep``) so
    tests never wait on a real backoff. Construct a fresh instance per
    process -- never share one between the cop and thief processes
    (CLAUDE.md rule 2).
    """

    def __init__(
        self,
        *,
        params: LanguageParams,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._params = params
        self._sleep = sleep
        self._bucket = TokenBucket(
            capacity=params.requests_per_minute,
            refill_rate=params.requests_per_minute / _SECONDS_PER_MINUTE,
            clock=clock,
        )
        self.budget = TokenBudget(
            token_budget=params.token_budget_per_series,
            short_prompt_threshold=params.short_prompt_threshold_tokens,
            template_only_threshold=params.template_only_threshold_tokens,
        )
        self._semaphore = asyncio.Semaphore(params.parallel_requests)
        self._waiting = 0

    async def submit(
        self,
        fn: Callable[[], Awaitable[CallResult]],
        *,
        estimated_tokens: int,
    ) -> object:
        """Run ``fn`` through rate limit, parallel cap, queue and retry/backoff.

        Raises ``GatekeeperOverflow`` if the FIFO queue is already at
        ``queue_depth``, or ``fn``'s last exception once every retry is
        exhausted. See the module docstring for the full step order and the
        D-33 fallback contract both failure modes share.
        """
        self.budget.reserve(estimated_tokens)
        if self._waiting >= self._params.queue_depth:
            raise GatekeeperOverflow(
                f"queue depth {self._params.queue_depth} exceeded (Table 19 row 5)"
            )
        self._waiting += 1
        try:
            await self._semaphore.acquire()
        finally:
            self._waiting -= 1
        try:
            result = await self._call_with_retry(fn)
        finally:
            self._semaphore.release()
        self.budget.settle(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            estimated_tokens=estimated_tokens,
        )
        return result.value

    async def _call_with_retry(self, fn: Callable[[], Awaitable[CallResult]]) -> CallResult:
        """One rate-limited, timed-out, retried attempt ladder (steps 4-5).

        Every failure is retryable here -- this module is provider-agnostic
        and cannot narrow the exception type further than "fn's own async
        call, or its response_timeout_seconds deadline, failed."
        """
        total_attempts = self._params.retries_before_failure + 1
        last_exc: Exception | None = None
        for attempt in range(total_attempts):
            wait = self._bucket.time_until_available()
            if wait > 0:
                await self._sleep(wait)
            self._bucket.try_acquire()
            try:
                return await asyncio.wait_for(
                    fn(), timeout=self._params.response_timeout_seconds
                )
            except Exception as exc:
                last_exc = exc
                if attempt + 1 < total_attempts:
                    await self._sleep(self._params.wait_after_error_seconds)
        raise last_exc
