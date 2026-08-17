"""The live dashboard's entry point -- a standalone process (D-76).

    uv run python -m pursuit.gui.live_app --snapshot <path> --refresh-ms <N>

WHY A SEPARATE PROCESS, in one line each (the full three measurements are in
`sdk/view_publish.py`): `tk.mainloop()` blocks its calling thread and the
agent's freeze watchdog `os._exit`s the process 60 s after the last `touch()`
(the configured `watchdog_threshold`); Tk is not thread-safe, so a thread is
not an escape; and a process that never holds the true joint position turns
D-74's type-level firewall into a PROCESS-level one. This process has no turn
loop and no watchdog, so it may block on `mainloop()` freely.

**OQ-6 -- THE REFRESH INTERVAL HAS NO SOURCE, AND IS THEREFORE NOT WRITTEN
DOWN ANYWHERE IN `src/`.** `docs/PARAMETERS.md` Table 19 has no UI row, and
reusing the configured `watchdog_poll_seconds` would be one number serving
two purposes -- the practice `language_wiring.py:43-47` explicitly refuses.
So `--refresh-ms` is `required=True` with NO `default=`, and
`LiveDashboard.__init__` takes it as a REQUIRED keyword-only argument with no
default in source, exactly as `Watchdog.__init__` and `TokenBucket.__init__`
already do for their own config-supplied values (QUAL-11). The operator
states the number at launch; the repository states none. 07-10 records the
value used for the README screenshot.
"""

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path

from pursuit.gui.live_panels import LivePanels
from pursuit.gui.live_sidebar import LiveSidebar
from pursuit.gui.widgets import PANEL_PAD
from pursuit.sdk.view_snapshot import read_snapshot
from pursuit.sdk.view_text import WINDOW_TITLE

SNAPSHOT_HELP = "path to this seat's published view snapshot (<log-stem>.view.json)"
REFRESH_HELP = (
    "milliseconds between refreshes. REQUIRED and deliberately without a default: "
    "OQ-6 -- no document in this project states a UI refresh interval, so the "
    "operator states it and the repository does not."
)
ONCE_HELP = "build every widget, refresh once and exit 0 -- the scripted launch gate"


class LiveDashboard:
    """One window over one published snapshot. Owns its own Tk root."""

    def __init__(self, root: tk.Misc, snapshot: Path, *, refresh_ms: int) -> None:
        self.root = root
        self.snapshot = snapshot
        self.refresh_ms = refresh_ms
        self.panels = LivePanels(root)
        self.sidebar = LiveSidebar(root)
        self.panels.frame.pack(side=tk.LEFT, padx=PANEL_PAD, pady=PANEL_PAD, anchor="nw")
        self.sidebar.frame.pack(side=tk.LEFT, padx=PANEL_PAD, pady=PANEL_PAD, anchor="nw")

    def show(self) -> bool:
        """Draw the latest published frame. Returns whether one was read: an
        unreadable snapshot keeps the frame already on screen, because the
        writer runs in another process and the reader will sometimes arrive
        mid-rotation."""
        view = read_snapshot(self.snapshot)
        if view is None:
            return False
        self.panels.show(view)
        self.sidebar.show(view)
        return True

    def start(self) -> None:
        """Refresh, then re-arm on the Tk root's OWN timer."""
        self.show()
        self.root.after(self.refresh_ms, self.start)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pursuit.gui.live_app", description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True, help=SNAPSHOT_HELP)
    parser.add_argument("--refresh-ms", type=int, required=True, help=REFRESH_HELP)
    parser.add_argument("--once", action="store_true", help=ONCE_HELP)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    dashboard = LiveDashboard(root, args.snapshot, refresh_ms=args.refresh_ms)
    if args.once:
        dashboard.show()
        root.update()
        root.destroy()
        return 0
    dashboard.start()
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
