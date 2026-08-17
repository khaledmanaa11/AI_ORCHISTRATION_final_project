"""Crash-safe JSON write/read sequence shared by QTable (03-05) and the
future training/checkpoint.py (03-08) -- lives under src/pursuit/shared/
because training/ must never be imported by src/, so the shared home has
to sit under src/ instead (QUAL-02).

Why this is not just os.replace(): an overnight run checkpointing every
few thousand episodes WILL be interrupted eventually, and this repo sits
under a OneDrive-synced path where the sync client holds file handles open
and can dehydrate files (D-22). On Windows, os.replace() maps to
MoveFileEx(MOVEFILE_REPLACE_EXISTING), which is NOT guaranteed atomic and
can silently fall back to copy+delete, and directory fsync is unavailable
there (D-24). So the real protection is the rotated `.prev` generation, not
fsync alone: write -> flush -> fsync -> rotate old target to `.prev` ->
replace, with bounded retry-with-backoff on PermissionError (WinError 32).
"""

import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# The retry/backoff pair for a SMALL, LOCAL, crash-safe JSON write. An
# ENGINEERING DEFAULT under the D-18 discipline -- NOT a book value, and not a
# docs/PARAMETERS.md Table 19 row (those govern outgoing NETWORK requests; this
# is os.replace() losing a race with OneDrive or Defender). First measured by
# 03-05 for QTable.save() ("_SAVE_RETRIES=3/_SAVE_BACKOFF_SECONDS=0.1s"), then
# copied into security/step0_collect.py:29-34 for the games-played counter.
# 07-01's QuotaManager is the THIRD consumer, so the pair is extracted here, to
# the module that owns the write scheme (CLAUDE.md Table 5: extract at 2+
# copies). The two earlier copies still hold their own locals; folding them
# onto these names is logged in the phase's deferred-items.md rather than done
# as a drive-by edit to code 07-00 has just certified.
DURABLE_WRITE_RETRIES = 3
DURABLE_WRITE_BACKOFF_SECONDS = 0.1


def _tmp_path(target: Path) -> Path:
    return target.with_name(f"{target.stem}.tmp{target.suffix}")


def _prev_path(target: Path) -> Path:
    return target.with_name(f"{target.stem}.prev{target.suffix}")


def durable_write_json(
    path: "Path | str", payload: object, *, retries: int, backoff: float
) -> None:
    """Write `payload` to `path` as JSON, crash-safely (D-15, D-24).

    1. write to a temp file in the SAME directory, flush(), os.fsync(fd)
    2. rotate the existing target (if any) to its `.prev` generation
    3. os.replace(tmp, target), retried with linear backoff on
       PermissionError -- OneDrive, Defender, or an editor holding the
       destination open (WinError 32)
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(target)

    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh)
        fh.flush()
        os.fsync(fh.fileno())

    if target.exists():
        os.replace(target, _prev_path(target))

    _replace_with_retry(tmp_path, target, retries=retries, backoff=backoff)


def _replace_with_retry(tmp_path: Path, target: Path, *, retries: int, backoff: float) -> None:
    attempt = 0
    while True:
        try:
            os.replace(tmp_path, target)
            return
        except PermissionError:
            attempt += 1
            if attempt > retries:
                raise
            time.sleep(backoff * attempt)


def load_json_with_fallback(path: "Path | str") -> object:
    """Parse `path` as JSON; on failure, fall back to its `.prev` generation.

    Falls back on BOTH a missing target (a crash can land between the
    rotate-to-`.prev` and final-replace steps, leaving target briefly
    absent) and a malformed/corrupt target. The fallback is logged so a
    corrupt checkpoint costs one interval, never the whole overnight run
    (D-24). If `.prev` also fails to parse, the ORIGINAL error propagates --
    this never returns a partially populated result.
    """
    target = Path(path)
    try:
        return _read_json(target)
    except (FileNotFoundError, json.JSONDecodeError) as primary_error:
        prev = _prev_path(target)
        try:
            data = _read_json(prev)
        except (FileNotFoundError, json.JSONDecodeError):
            raise primary_error from None
        logger.warning("Falling back to %s after failing to load %s", prev, target)
        return data


def _read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)
