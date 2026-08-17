"""Publish one `LocalView` snapshot beside the wire log -- best-effort, and
the only thing the agent process does for the live GUI (D-76).

D-76: THE LIVE GUI IS A SEPARATE PROCESS FED BY A PUBLISHED SNAPSHOT. The
alternative -- drive Tk with `after()` off the turn loop -- was rejected on
three measurements from this tree:

1. `tk.mainloop()` blocks its calling thread, and `network/watchdog.py` runs
   a daemon thread polling `clock() - _last_activity` against
   `watchdog_threshold` = 60 (`config/*/network.json`) whose action is
   `os._exit(WatchdogExit.FREEZE)`. Blocking the asyncio loop stops every
   `touch()` and kills the agent mid-game; the peer then declares us
   `opponent_unresponsive`.
2. Tk is not thread-safe, so "run the GUI in a thread" is not an escape --
   and a polling thread could additionally sample the pure 1.0/0.0 delta
   window between `observe_exact` and `predict` inside `decide()`.
3. A separate process CANNOT HOLD `ctx.state` AT ALL, which turns D-74's
   type-level firewall into a PROCESS-level one -- the strongest available
   answer to rule 9.

Cost: one snapshot file per agent. It is not shared runtime state (CLAUDE.md
rule 2): each process writes only its OWN view to its OWN path, and nothing
ever reads the other side's.

CONTAINMENT IS THE OTHER HALF, and it is copied from
`network/capture_declaration.send_capture_declaration` ("BEST-EFFORT and
returns nothing on purpose"). Since 06-05 a non-zero process exit code MEANS
an audit mismatch (`main.py:25-29`), so an exception escaping this publisher
would forge a technical-loss signal out of a failed cosmetic write. Nothing
here returns a verdict, touches `ctx.state`, or changes the turn loop's
return value.
"""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pursuit.sdk.view_builder import HintHistory, build_local_view
from pursuit.shared.durable_write import (
    DURABLE_WRITE_BACKOFF_SECONDS,
    DURABLE_WRITE_RETRIES,
    durable_write_json,
)

if TYPE_CHECKING:  # pragma: no cover -- annotation only, never imported at runtime
    from pursuit.network.agent_context import AgentContext

logger = logging.getLogger(__name__)

#: The sibling suffix, following `network/turn_commit_ledger.ledger_path_for`'s
#: `<log-file-stem>.<kind>` convention exactly: `logs/<role>/<uid>.jsonl` ->
#: `logs/<role>/<uid>.view.json`. No new config leaf, no env var, no invented
#: path. NOT folded onto one shared helper with `ledger_path_for`: that
#: function is on the D-64 nonce path 06-05 certified, and the D7-2/D7-4
#: precedent in this phase is to leave a certified path alone rather than
#: rename through it for a one-expression join. Filed as D7-15.
SNAPSHOT_SUFFIX = "view.json"

#: The live idle reading, when the injected watchdog exposes one. Read with
#: `getattr` rather than an isinstance check because `sdk/` may not import
#: `pursuit.network` (rules 8-9 gate, D-74) and several test doubles stand in
#: for `Watchdog`. A watchdog without the reading publishes `idle_seconds=None`
#: -- the honest "not measured", never a fabricated zero.
IDLE_READING = "idle_seconds"


def snapshot_path_for(log_path: Path) -> Path:
    """`logs/<role>/<uid>.jsonl` -> `logs/<role>/<uid>.view.json`."""
    return log_path.parent / f"{log_path.stem}.{SNAPSHOT_SUFFIX}"


def snapshot_payload(view: object) -> dict:
    """One `LocalView` as the plain tree `view_snapshot.read_snapshot` reads
    back. `dataclasses.asdict` and nothing else: whatever the closed field set
    carries is exactly what is published, so a field cannot be added to the
    view and quietly skipped here (or vice versa)."""
    return dataclasses.asdict(view)


def idle_reading(watchdog: object) -> float | None:
    """Seconds since the watchdog's last `touch()`, or None when the injected
    watchdog exposes no reading."""
    value = getattr(watchdog, IDLE_READING, None)
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def publish_view(ctx: AgentContext, history: HintHistory) -> None:
    """Write this peer's current `LocalView` to its snapshot path.

    NEVER RAISES. A dashboard that cannot be refreshed is a cosmetic loss; a
    turn loop that dies because a cosmetic write failed is a forfeited game,
    and since 06-05 it is a forfeit that looks like an audit mismatch. Every
    failure is logged and swallowed -- `BaseException` (so `CancelledError`
    and `KeyboardInterrupt`) is deliberately NOT caught.
    """
    try:
        view = build_local_view(ctx, history, idle_seconds=idle_reading(ctx.watchdog))
        durable_write_json(
            snapshot_path_for(ctx.log_path),
            snapshot_payload(view),
            retries=DURABLE_WRITE_RETRIES,
            backoff=DURABLE_WRITE_BACKOFF_SECONDS,
        )
    except Exception:
        logger.warning("live-view snapshot not published", exc_info=True)
