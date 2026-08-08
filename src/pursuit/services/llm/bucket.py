"""Token bucket rate limiter -- docs/PARAMETERS.md Table 19's law, verbatim.

``tokens <- min(C, tokens + r*dt)``, admit iff ``tokens >= 1``, decrementing by
one on admission (Table 19's formula box, beneath row 7). ``C`` ("capacity",
burst size) and ``r`` ("refill_rate", tokens/second, sustained rate) are
supplied by the caller -- this class is a generic, reusable primitive.
``Gatekeeper`` (gatekeeper.py) is the one place that derives both from
``LanguageParams.requests_per_minute`` (Table 19 row 1, a MINIMUM value,
floor-checked at load by ``shared/language_config.py``) and documents that
derivation, so this module carries no Table 19 number itself.

The clock is injected: ``time_until_available()`` lets the caller await
precisely rather than poll, and no test in this module's own test file ever
calls ``time.sleep`` (``network/watchdog.py`` precedent -- a real wait in the
turn path trips the watchdog).
"""

import time
from collections.abc import Callable


class TokenBucket:
    """A Table-19 token bucket: ``tokens <- min(C, tokens + r*dt)``.

    ``capacity`` and ``refill_rate`` are keyword-only and REQUIRED -- no
    default in source (QUAL-11) -- so a caller can never construct one
    without stating both numbers explicitly. ``clock`` is an injected seam
    (default ``time.monotonic``) so every timing assertion in tests advances
    a fake clock instead of sleeping.
    """

    def __init__(
        self,
        *,
        capacity: float,
        refill_rate: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._clock = clock
        self._tokens = capacity
        self._last_refill = clock()

    def _refill(self) -> None:
        """Apply ``tokens <- min(C, tokens + r*dt)`` for the elapsed time."""
        now = self._clock()
        elapsed = now - self._last_refill
        self._last_refill = now
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + self._refill_rate * elapsed)

    def try_acquire(self) -> bool:
        """Admit one call now iff a token is available, else refuse.

        Returns True and decrements the bucket by one on success; returns
        False and leaves the bucket unchanged otherwise. Never blocks and
        never raises.
        """
        self._refill()
        if self._tokens >= 1:
            self._tokens -= 1
            return True
        return False

    def time_until_available(self) -> float:
        """Seconds until ``try_acquire()`` would next succeed; 0.0 if ready now.

        Lets the caller ``await sleep(bucket.time_until_available())`` once,
        precisely, instead of polling ``try_acquire()`` in a loop.
        """
        self._refill()
        if self._tokens >= 1:
            return 0.0
        return (1 - self._tokens) / self._refill_rate

    @property
    def tokens(self) -> float:
        """Current token count, after applying any refill owed since the last call."""
        self._refill()
        return self._tokens
