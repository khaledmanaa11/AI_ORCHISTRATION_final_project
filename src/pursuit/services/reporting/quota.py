"""The Quota Manager -- stage 1 of the book's Figure-13 chain (rule 28, D-69).

OQ-1, RESOLVED AND CARRIED VERBATIM (07-PLAN-OUTLINE.md §5): the book's §9.3.1
names the stage "tracks the daily send ceiling", and docs/PARAMETERS.md Table
19 has NO daily row. docs/SEGAL_GUIDELINES.md:173-174 does supply real figures
for the generic API gatekeeper -- `requests_per_minute: 30`,
`requests_per_hour: 500`, `max_retries: 3` -- and those are sourced, so the
SOURCED HOURLY BOUND is what this manager enforces. No document anywhere gives
a daily figure, so none is written. If a daily bound is ever structurally
needed it is DERIVED as `24 x requests_per_hour` and labelled derived in both
config and source -- never presented as a book value. No engineering default
is used for the ceiling itself.

DURABLE ACROSS A PROCESS RESTART, and through the ONE persistence scheme this
project has (QUAL-02): `shared/durable_write.py`'s write -> fsync -> rotate to
`.prev` -> replace, read back through `load_json_with_fallback`. The same
scheme `step0_collect.record_game_played` and `QTable.save()` already use; no
second scheme is introduced.

THE WINDOW BOUNDARY COMES OFF AN INJECTED CLOCK, and it is a WALL clock
(`time.time`), not `time.monotonic`: a monotonic reading is meaningless across
the restart this counter is required to survive. Every test advances a fake.

EXHAUSTION IS A REFUSAL, NEVER AN EXCEPTION. `try_consume()` returns a bool
that the chain turns into a caller-handled `SendOutcome`; nothing here raises
into the turn loop (rules 28-29; docs/SEGAL_GUIDELINES.md:175-176 -- "On
overflow: FIFO queue, not rejection and not a crash").
"""

import time
from collections.abc import Callable
from enum import Enum
from pathlib import Path

from pursuit.shared.durable_write import (
    DURABLE_WRITE_BACKOFF_SECONDS,
    DURABLE_WRITE_RETRIES,
    durable_write_json,
    load_json_with_fallback,
)

#: Unit conversion, not a parameter: an hour is 3600 seconds. The CEILING is
#: SEGAL's `requests_per_hour`, read from reporting.json.
_SECONDS_PER_HOUR = 3600.0


class QuotaField(str, Enum):
    """The two fields the durable quota file carries."""

    WINDOW_START = "window_start"
    COUNT = "count"


class QuotaManager:
    """A durable, wall-clock hourly send counter.

    `ceiling_per_hour` is `ReportingParams.requests_per_hour`; `path` is the
    counter file, which must NOT live in the shipped `config/` tree (07-00 --
    `tests/_shipped_config_guard.py` makes that structural). All arguments are
    keyword-only and required except the injected `clock` (QUAL-11). One
    instance per process, never shared between the cop and thief
    (CLAUDE.md rule 2).
    """

    def __init__(
        self,
        *,
        ceiling_per_hour: int,
        path: "Path | str",
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._ceiling = ceiling_per_hour
        self._path = Path(path)
        self._clock = clock

    def _read(self) -> tuple[float, int]:
        """The persisted window, or a fresh one. Never raises: a missing or
        corrupt counter costs at most one window's accounting, exactly as
        `load_json_with_fallback`'s `.prev` generation is designed for."""
        try:
            data = load_json_with_fallback(self._path)
        except (OSError, ValueError):
            return self._clock(), 0
        if not isinstance(data, dict):
            return self._clock(), 0
        start = data.get(QuotaField.WINDOW_START.value)
        count = data.get(QuotaField.COUNT.value)
        if not isinstance(start, int | float) or not isinstance(count, int):
            return self._clock(), 0
        if isinstance(count, bool):
            return self._clock(), 0
        return float(start), count

    def _current_window(self) -> tuple[float, int]:
        """The live window, rolling it over if the persisted one has expired."""
        start, count = self._read()
        now = self._clock()
        if now - start >= _SECONDS_PER_HOUR or now < start:
            return now, 0
        return start, count

    def remaining(self) -> int:
        """Sends still permitted in the current window; never negative."""
        _start, count = self._current_window()
        return max(0, self._ceiling - count)

    def try_consume(self) -> bool:
        """Claim one send. True and the claim is persisted; False and nothing
        is written, because a refused send must not consume quota."""
        start, count = self._current_window()
        if count >= self._ceiling:
            return False
        durable_write_json(
            self._path,
            {QuotaField.WINDOW_START.value: start, QuotaField.COUNT.value: count + 1},
            retries=DURABLE_WRITE_RETRIES,
            backoff=DURABLE_WRITE_BACKOFF_SECONDS,
        )
        return True
