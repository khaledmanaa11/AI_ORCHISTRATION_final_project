"""Tests for TokenBucket -- docs/PARAMETERS.md Table 19's token-bucket law.

No ``time.sleep`` anywhere in this file -- every timing assertion advances a
``FakeClock`` instead (Task 2 verify criterion; ``network/watchdog.py``
precedent). ``FakeClock`` is exported for ``tests/unit/services/
test_gatekeeper.py`` to reuse (QUAL-02: no duplicated test fake).
"""

import pytest

from pursuit.services.llm.bucket import TokenBucket


class FakeClock:
    """A settable monotonic clock -- ``advance()`` moves it forward explicitly."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def advance(self, seconds: float) -> None:
        self._now += seconds

    def __call__(self) -> float:
        return self._now


def test_burst_of_capacity_is_admitted_then_next_call_refused() -> None:
    """A fresh bucket admits exactly C calls, then refuses call C+1."""
    bucket = TokenBucket(capacity=3, refill_rate=1.0, clock=FakeClock())
    assert [bucket.try_acquire() for _ in range(3)] == [True, True, True]
    assert bucket.try_acquire() is False


def test_one_more_admitted_after_exactly_one_over_rate_seconds() -> None:
    """After 1/r seconds, exactly one more call is admitted."""
    clock = FakeClock()
    bucket = TokenBucket(capacity=2, refill_rate=0.5, clock=clock)  # 1/r = 2s
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False
    clock.advance(2.0)
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False


def test_tokens_never_exceed_capacity_after_a_long_idle_gap() -> None:
    """The token count is clamped at C no matter how long the idle gap."""
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=10.0, clock=clock)
    for _ in range(5):
        bucket.try_acquire()
    clock.advance(10_000.0)
    assert bucket.tokens == 5


def test_try_acquire_decrements_by_exactly_one() -> None:
    bucket = TokenBucket(capacity=4, refill_rate=1.0, clock=FakeClock())
    bucket.try_acquire()
    assert bucket.tokens == 3


def test_time_until_available_is_zero_when_a_token_is_ready() -> None:
    bucket = TokenBucket(capacity=1, refill_rate=1.0, clock=FakeClock())
    assert bucket.time_until_available() == 0.0


def test_time_until_available_matches_the_refill_law_when_empty() -> None:
    clock = FakeClock()
    bucket = TokenBucket(capacity=1, refill_rate=0.25, clock=clock)  # 1/r = 4s
    bucket.try_acquire()
    assert bucket.time_until_available() == pytest.approx(4.0)


def test_partial_refill_is_fractional_not_all_or_nothing() -> None:
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=1.0, clock=clock)
    for _ in range(5):
        bucket.try_acquire()
    clock.advance(0.5)
    assert bucket.tokens == pytest.approx(0.5)
    assert bucket.try_acquire() is False


def test_default_clock_is_time_monotonic() -> None:
    """The clock argument is optional; the default lets a real bucket work."""
    bucket = TokenBucket(capacity=1, refill_rate=1.0)
    assert bucket.try_acquire() is True
