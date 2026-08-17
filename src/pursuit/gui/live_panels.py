"""The four grid panels: board, belief heatmap, and both scent trails.

One `GridPanel` per entry in `view_render.PANEL_TITLES`, refreshed from
`view_render.panel_grids` in the same order and zipped with `strict=True`, so
a title added without a grid (or a grid without a title) raises rather than
drawing the wrong data under the wrong heading.

THIS MODULE MAKES NO DECISION ABOUT WHAT IS SHOWN. An absent belief map --
belief off this game, or 07-11's publication floor refusing a posterior that
would name a cell -- already arrives as a blank grid from `panel_grids`,
because a widget layer deciding for itself what to draw when a panel is
missing would be making a rules 8-9 decision in the one directory coverage
cannot see.
"""

from __future__ import annotations

import tkinter as tk

from pursuit.gui.widgets import PANEL_PAD, GridPanel
from pursuit.sdk.local_view import LocalView
from pursuit.sdk.view_render import PANEL_TITLES, panel_grids, panel_positions


class LivePanels:
    """Every grid panel for one seat's dashboard."""

    def __init__(self, parent: tk.Misc) -> None:
        self.frame = tk.Frame(parent)
        self.panels = tuple(GridPanel(self.frame, title=title) for title in PANEL_TITLES)
        for panel, (row, column) in zip(self.panels, panel_positions(), strict=True):
            panel.frame.grid(
                row=row, column=column, padx=PANEL_PAD, pady=PANEL_PAD, sticky="nw"
            )

    def show(self, view: LocalView) -> None:
        for panel, colours in zip(self.panels, panel_grids(view), strict=True):
            panel.paint(colours)
