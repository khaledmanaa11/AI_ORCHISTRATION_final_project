"""The sidebar: this peer's status and freeze timer, the published belief's
caption, and the hint log with each sender's SELF-DECLARED intent flag.

One `TextPanel` per entry in `view_text.SIDEBAR_TITLES`, filled from
`view_text.sidebar_blocks` in the same order and zipped with `strict=True`.
Every string -- including the newline join -- is built in `sdk/`; this module
calls `configure(text=...)` and nothing else.

The hint log is the panel most likely to tempt someone into "just showing the
real position next to the claim". It cannot: this process is fed a published
`LocalView` and has no access to the objective board state at all (D-76), and
`scripts/check_local_truth.py` fails the build if a module here reaches for
it.
"""

from __future__ import annotations

import tkinter as tk

from pursuit.gui.widgets import PANEL_PAD, TextPanel
from pursuit.sdk.local_view import LocalView
from pursuit.sdk.view_text import SIDEBAR_TITLES, sidebar_blocks


class LiveSidebar:
    """Every text panel for one seat's dashboard."""

    def __init__(self, parent: tk.Misc) -> None:
        self.frame = tk.Frame(parent)
        self.panels = tuple(TextPanel(self.frame, title=title) for title in SIDEBAR_TITLES)
        for panel in self.panels:
            panel.frame.pack(padx=PANEL_PAD, pady=PANEL_PAD, fill=tk.BOTH, expand=True)

    def show(self, view: LocalView) -> None:
        for panel, block in zip(self.panels, sidebar_blocks(view), strict=True):
            panel.show(block)
