"""D-64: the durable per-turn nonce ledger.

`CommitLedger` persists `{turn, h_commit, payload}` (nonce included, inside
`payload`) BEFORE any network send can occur in a caller's flow --
validate, serialize, write, flush, `os.fsync`, the identical durability
order `event_log.append_event` already uses, so a crash after commit still
leaves a recoverable local record.

This file is never read or written by anything on the wire path (D-64):
06-02's own integration test is what proves the wire-mirroring log stays
nonce-free. This module only proves it can durably hold and reproduce what
it is given -- it has no opinion about who calls it or when.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


class LedgerField:
    """JSONL key names for one ledger record."""

    TURN = "turn"
    H_COMMIT = "h_commit"
    PAYLOAD = "payload"


class CommitLedger:
    """A single JSONL file of per-turn commit records."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def append(self, *, turn: int, h_commit: str, payload: dict) -> None:
        """Append one record, durably.

        Order matters, mirroring `event_log.append_event`: validate and
        serialize BEFORE the file is opened, so a rejected record never
        creates or grows the ledger; write, flush and `os.fsync` before
        returning.
        """
        record = {
            LedgerField.TURN: turn,
            LedgerField.H_COMMIT: h_commit,
            LedgerField.PAYLOAD: payload,
        }
        line = json.dumps(record, sort_keys=True, separators=(",", ":"))

        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def read_all(self) -> list[dict]:
        """Parse every line in append order.

        A missing file returns `[]` -- a ledger with no commits yet is a
        legitimate pre-game-start state, not an error. A malformed existing
        line surfaces via `json.JSONDecodeError`, never a silent skip,
        matching the project's fail-loud house style.
        """
        if not self._path.exists():
            return []
        with self._path.open(encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
