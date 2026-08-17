"""The replay window's contents: the verdict banner, and one turn's record.

THE BANNER IS THE DELIVERABLE. Sec10.4 criterion 3 is satisfied by what this
label says, and the screenshot of it is a README asset, so it is deliberately
the largest thing on screen. It is also the thing this module is least
entitled to decide: the words come from `replay_verify` and so does the
colour, because `pyproject.toml:38` omits `*/gui/*` from coverage and a
literal defined here would be untested AND invisible to the `fail_under = 85`
gate.

Reuses 07-06's `widgets.TextPanel` rather than drawing its own labelled box
(SEGAL Sec3:152-154 -- extract at the second copy, do not write it twice).

NO DERIVATION HAPPENS HERE. No arithmetic, no string building, no decision
about what to show; `test_gui_structural.py` enforces all three structurally
and fails on the first `BinOp` or f-string.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pursuit.gui.widgets import PANEL_PAD, TextPanel
from pursuit.services.reporting.replay_verify import (
    SECTION_TITLES,
    ReplaySession,
    banner_colour,
)

#: Presentation only -- no game parameter is expressible as a font size, and
#: these are named rather than inline per CLAUDE.md's hardcoded-value rule.
BANNER_FONT = ("TkDefaultFont", 22, "bold")
DETAIL_FONT = ("TkDefaultFont", 11)


class ReplayPanels:
    """The banner, the counts beneath it, and one text panel per section."""

    def __init__(self, parent: tk.Misc) -> None:
        self.frame = tk.Frame(parent)
        self.banner = ttk.Label(self.frame, font=BANNER_FONT, anchor=tk.CENTER)
        self.banner.pack(padx=PANEL_PAD, pady=PANEL_PAD, fill=tk.X)
        self.detail = ttk.Label(self.frame, font=DETAIL_FONT, anchor=tk.CENTER)
        self.detail.pack(padx=PANEL_PAD, pady=PANEL_PAD, fill=tk.X)
        self.panels = tuple(TextPanel(self.frame, title=title) for title in SECTION_TITLES)
        for panel in self.panels:
            panel.frame.pack(padx=PANEL_PAD, pady=PANEL_PAD, fill=tk.BOTH, expand=True)

    def show(self, session: ReplaySession) -> None:
        """Render the verdict and the turn under the cursor.

        The banner is re-read from the session every frame rather than set
        once at construction: it is one value computed once by
        `replay_verify`, and re-reading it means the screen cannot hold a
        verdict the verifier no longer stands behind.
        """
        self.banner.configure(
            text=session.verdict.banner, foreground=banner_colour(session.verdict.state)
        )
        self.detail.configure(text=session.verdict.detail)
        for panel, block in zip(self.panels, session.blocks(), strict=True):
            panel.show(block)
