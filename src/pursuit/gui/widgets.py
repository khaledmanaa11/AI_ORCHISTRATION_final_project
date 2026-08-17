"""Shared chrome for the live dashboard -- extracted at the SECOND copy, not
the third (SEGAL Sec3:152-154, CLAUDE.md Table 5).

Two widgets, both deliberately dumb. `GridPanel` hands each pre-computed
rectangle straight to `create_rectangle`; `TextPanel` hands a pre-joined
block straight to a label. Neither computes a coordinate, a colour, a size or
a string: `pursuit.sdk.view_render` and `pursuit.sdk.view_text` did all of
that where the coverage gate can see it.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pursuit.sdk.view_render import OUTLINE_COLOUR, cell_rectangles, grid_extent

#: Widget chrome. Presentation only -- no game parameter is expressible here.
PANEL_PAD = 4
TEXT_WRAP_PIXELS = 320
TEXT_FONT = ("TkFixedFont",)


class GridPanel:
    """A titled canvas that paints one dense grid of colours."""

    def __init__(self, parent: tk.Misc, *, title: str) -> None:
        self.frame = ttk.LabelFrame(parent, text=title)
        self.canvas = tk.Canvas(self.frame, highlightthickness=0, borderwidth=0)
        self.canvas.pack(padx=PANEL_PAD, pady=PANEL_PAD)

    def paint(self, colours: tuple[tuple[str, ...], ...]) -> None:
        extent = grid_extent(colours)
        self.canvas.configure(width=extent, height=extent)
        self.canvas.delete("all")
        for x0, y0, x1, y1, fill in cell_rectangles(colours):
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline=OUTLINE_COLOUR)


class TextPanel:
    """A titled label showing one pre-joined block of text."""

    def __init__(self, parent: tk.Misc, *, title: str) -> None:
        self.frame = ttk.LabelFrame(parent, text=title)
        self.label = ttk.Label(
            self.frame, justify=tk.LEFT, anchor="nw",
            wraplength=TEXT_WRAP_PIXELS, font=TEXT_FONT,
        )
        self.label.pack(padx=PANEL_PAD, pady=PANEL_PAD, fill=tk.BOTH, expand=True)

    def show(self, block: str) -> None:
        self.label.configure(text=block)
