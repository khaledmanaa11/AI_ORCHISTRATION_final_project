"""QuotaManager -- the durable hourly ceiling (Figure 13 stage 1, OQ-1).

Every clock reading is a fake; no test sleeps. Every counter file is under
`tmp_path` -- 07-00's `tests/_shipped_config_guard.py` makes a write into the
shipped `config/` tree fail loudly, and this counter must never go near it.
"""

import json
from pathlib import Path

import pytest

from pursuit.services.reporting import QuotaField, QuotaManager

#: Test scaffolding, NOT a docs/ value: a ceiling of 3 is exhaustible in a
#: test. The SHIPPED ceiling is docs/SEGAL_GUIDELINES.md:173's 500, asserted
#: against the real files in tests/unit/test_reporting_config.py.
_TEST_CEILING = 3

#: The window length QuotaManager enforces -- one hour, in seconds.
_HOUR = 3600.0


class FakeWallClock:
    """A settable wall clock. Wall, not monotonic: this counter has to survive
    a process restart, and a monotonic reading does not."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self._now = start

    def advance(self, seconds: float) -> None:
        self._now += seconds

    def set(self, value: float) -> None:
        self._now = value

    def __call__(self) -> float:
        return self._now


def _manager(tmp_path: Path, clock: FakeWallClock, **kwargs: object) -> QuotaManager:
    return QuotaManager(
        ceiling_per_hour=kwargs.pop("ceiling_per_hour", _TEST_CEILING),
        path=tmp_path / "quota.json",
        clock=clock,
        **kwargs,
    )


def test_a_fresh_window_permits_exactly_the_ceiling_then_refuses(tmp_path: Path) -> None:
    quota = _manager(tmp_path, FakeWallClock())
    assert quota.remaining() == _TEST_CEILING
    assert [quota.try_consume() for _ in range(_TEST_CEILING)] == [True] * _TEST_CEILING
    assert quota.remaining() == 0
    assert quota.try_consume() is False


def test_a_refused_send_consumes_nothing(tmp_path: Path) -> None:
    """A refusal must not burn quota, or a caller that retries would dig itself
    permanently out of the window."""
    quota = _manager(tmp_path, FakeWallClock())
    for _ in range(_TEST_CEILING):
        quota.try_consume()
    before = (tmp_path / "quota.json").read_text(encoding="utf-8")
    assert quota.try_consume() is False
    assert (tmp_path / "quota.json").read_text(encoding="utf-8") == before


def test_the_count_survives_a_simulated_process_restart(tmp_path: Path) -> None:
    """Success criterion: a FRESH manager over the same path sees the count.
    This is the whole reason the write goes through durable_write_json."""
    clock = FakeWallClock()
    first = _manager(tmp_path, clock)
    assert first.try_consume() is True
    assert first.try_consume() is True

    restarted = _manager(tmp_path, FakeWallClock(clock()))
    assert restarted.remaining() == _TEST_CEILING - 2
    assert restarted.try_consume() is True
    assert restarted.try_consume() is False


def test_the_window_rolls_over_after_exactly_one_hour(tmp_path: Path) -> None:
    clock = FakeWallClock()
    quota = _manager(tmp_path, clock)
    for _ in range(_TEST_CEILING):
        quota.try_consume()
    clock.advance(_HOUR - 1)
    assert quota.try_consume() is False
    clock.advance(1)
    assert quota.remaining() == _TEST_CEILING
    assert quota.try_consume() is True


def test_a_backwards_system_clock_opens_a_fresh_window_instead_of_locking_out(
    tmp_path: Path,
) -> None:
    """An NTP correction or a DST-naive host must not strand the agent with a
    window that can never expire."""
    clock = FakeWallClock()
    quota = _manager(tmp_path, clock)
    for _ in range(_TEST_CEILING):
        quota.try_consume()
    clock.set(clock() - _HOUR * 2)
    assert quota.try_consume() is True


@pytest.mark.parametrize(
    "payload",
    [
        "not json at all",
        "[]",
        '{"window_start": "soon", "count": 1}',
        '{"window_start": 1000000.0, "count": true}',
        '{"count": 4}',
        "{}",
    ],
)
def test_a_malformed_counter_file_opens_a_fresh_window_and_never_raises(
    tmp_path: Path, payload: str
) -> None:
    (tmp_path / "quota.json").write_text(payload, encoding="utf-8")
    quota = _manager(tmp_path, FakeWallClock())
    assert quota.remaining() == _TEST_CEILING
    assert quota.try_consume() is True


def test_a_corrupt_target_falls_back_to_its_prev_generation(tmp_path: Path) -> None:
    """The durable_write_json contract, exercised on THIS counter rather than
    assumed from its own unit tests."""
    clock = FakeWallClock()
    quota = _manager(tmp_path, clock)
    quota.try_consume()
    quota.try_consume()  # the first write is now rotated into quota.prev.json
    assert (tmp_path / "quota.prev.json").is_file()
    (tmp_path / "quota.json").write_text("{corrupt", encoding="utf-8")
    assert quota.remaining() == _TEST_CEILING - 1


def test_the_persisted_shape_is_the_two_documented_fields(tmp_path: Path) -> None:
    clock = FakeWallClock()
    quota = _manager(tmp_path, clock)
    quota.try_consume()
    data = json.loads((tmp_path / "quota.json").read_text(encoding="utf-8"))
    assert data == {QuotaField.WINDOW_START.value: clock(), QuotaField.COUNT.value: 1}
