"""Durable run-state checkpoint I/O (D-22, D-24).

Generic JSON dict read/write -- this module carries no knowledge of what a
checkpoint payload contains (runstate.py owns that shape). It never
reimplements the crash-safe write sequence (write-temp -> flush -> fsync ->
rotate-to-.prev -> retrying replace); it reuses
pursuit.shared.durable_write, the exact module 03-05's qtable.py already
reuses for the same reason (QUAL-02). training/ imports from src/pursuit/,
never the reverse (D-17's import-direction guarantee extends here too).

retries/backoff are structural constants, not RL hyperparameters or game
values -- same exemption category as qtable.py's own
_SAVE_RETRIES/_SAVE_BACKOFF_SECONDS.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.shared.durable_write import durable_write_json, load_json_with_fallback

_CHECKPOINT_RETRIES = 3
_CHECKPOINT_BACKOFF_SECONDS = 0.1


def save_checkpoint(path: Path | str, payload: dict) -> None:
    """Write payload crash-safely to path (D-24)."""
    durable_write_json(
        path, payload, retries=_CHECKPOINT_RETRIES, backoff=_CHECKPOINT_BACKOFF_SECONDS
    )


def load_checkpoint(path: Path | str) -> dict | None:
    """Read a checkpoint payload; None means "no checkpoint yet, start fresh".

    A genuinely absent checkpoint (fresh run: neither the target nor its
    `.prev` generation exists) is not an error. A PRESENT-but-corrupt
    checkpoint still fails loud through load_json_with_fallback's own
    fallback-then-raise behaviour -- a bad checkpoint costs at most one
    interval (D-24), it never silently starts over.
    """
    target = Path(path)
    if not target.exists() and not _prev_path(target).exists():
        return None
    return load_json_with_fallback(target)


def _prev_path(target: Path) -> Path:
    """Mirrors durable_write's own private naming so existence-checking
    a `.prev` generation never re-derives the rotation rule itself."""
    return target.with_name(f"{target.stem}.prev{target.suffix}")
