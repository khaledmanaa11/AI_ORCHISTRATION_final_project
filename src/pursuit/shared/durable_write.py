"""Crash-safe write/read sequence shared by QTable (03-05), the future
training/checkpoint.py (03-08), 07-01's QuotaManager, 07-02's artifact spine
and 07-04's `.eml` -- lives under src/pursuit/shared/ because training/ must
never be imported by src/, so the shared home has to sit under src/ instead
(QUAL-02).

`durable_write_bytes` is the scheme; `durable_write_json` is that scheme over
`json.dumps`. Measured when the two were separated: the JSON bytes are
IDENTICAL either way (98 bytes for a payload carrying a newline, a tab and
Hebrew), because `json.dumps` escapes newlines and defaults to ASCII, so the
old text-mode write had nothing for Windows to translate.

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


def durable_write_bytes(
    path: "Path | str", data: bytes, *, retries: int, backoff: float
) -> None:
    """Write `data` to `path` crash-safely (D-15, D-24) -- THE write scheme.

    1. write to a temp file in the SAME directory, flush(), os.fsync(fd)
    2. rotate the existing target (if any) to its `.prev` generation
    3. os.replace(tmp, target), retried with linear backoff on
       PermissionError -- OneDrive, Defender, or an editor holding the
       destination open (WinError 32)

    Extracted from `durable_write_json` at its second payload shape (07-04's
    `.eml`), rather than copied: two write-and-rotate sequences would be two
    crash-safety schemes, and the one that is not the JSON one is the one that
    would stop being maintained (CLAUDE.md Table 5, no duplication). Binary
    mode is the primitive on purpose -- text mode on Windows translates "\\n"
    to "\\r\\n", which would silently rewrite an RFC 5322 message.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(target)

    with tmp_path.open("wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())

    if target.exists():
        os.replace(target, _prev_path(target))

    _replace_with_retry(tmp_path, target, retries=retries, backoff=backoff)


def durable_write_json(
    path: "Path | str", payload: object, *, retries: int, backoff: float
) -> None:
    """Write `payload` to `path` as JSON, crash-safely -- `durable_write_bytes`
    over `json.dumps`.

    The bytes are unchanged by the extraction: `json.dumps` defaults to
    `ensure_ascii=True` and emits no literal newline (a newline inside a string
    value is escaped as the two characters `\\n`), so the previous text-mode
    write had nothing for Windows' newline translation to act on.
    """
    durable_write_bytes(
        path, json.dumps(payload).encode("utf-8"), retries=retries, backoff=backoff
    )


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
