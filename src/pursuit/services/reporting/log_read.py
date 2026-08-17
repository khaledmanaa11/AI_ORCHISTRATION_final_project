"""Reading a possibly-interrupted JSONL file for the `log_` artifact.

Split out of `log_join.py` at the 150-code-line gate (Segal Table 5, the
combined module measured 175) along the seam its own docstring already named:
READING a crashed game's files and KEYING their records were two subjects in
one file. Split, never compressed. `log_join.py` re-exports both public names,
so callers keep one import path (the `artifacts.py`/`artifact_names.py`
precedent).

A TRUNCATED TAIL IS TOLERATED; MID-FILE CORRUPTION IS NOT.
`event_log.append_event` writes one line then `flush()` + `os.fsync()`, so an
interrupted process can leave a partial LAST line. `agent_audit_observed._read_log`
and `ledger.CommitLedger.read_all` both raise on it -- and `read_all`'s
docstring states that raise is deliberate fail-loud for the AUDIT path.

NEITHER CONTRACT IS WEAKENED. This module is a second reader, not a change to
either of those, because the two paths want opposite things: an audit that
cannot read its own evidence must stop, while a replay artifact that cannot be
produced from a crashed game is useless exactly when it is most needed. The two
failure modes stay distinguishable here as well -- a partial tail is dropped
and reported to the caller, and a malformed line anywhere else raises
`CorruptLogError`, because that is corruption rather than an interrupted write.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ("CorruptLogError", "read_tolerating_partial_tail")


class CorruptLogError(ValueError):
    """A malformed line that is NOT the file's last line.

    Distinct from a partial tail, and a distinct TYPE from
    `json.JSONDecodeError` (which is also a `ValueError`) so a test can assert
    the exact class rather than catching the decode error it was raised from.
    """


def read_tolerating_partial_tail(path: Path | str) -> tuple[list[dict], bool]:
    """Parse a JSONL file, dropping a partial LAST line and reporting it.

    Returns `(records, truncated_tail)`. A missing file is `([], False)` -- the
    same legitimate pre-game state `CommitLedger.read_all` already allows.
    """
    file_path = Path(path)
    if not file_path.exists():
        return [], False
    lines = [line for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records: list[dict] = []
    for index, line in enumerate(lines):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            if index == len(lines) - 1:
                return records, True
            raise CorruptLogError(
                f"{file_path}: malformed JSON on line {index + 1} of {len(lines)}; "
                "only a partial LAST line is an interrupted write"
            ) from exc
    return records, False
