"""The replay window itself: panels, optional board, transport controls.

Split from `replay_app.py` at the 150-code-line gate (Segal Table 5), the
same precedent as `tunnel_wiring.py`'s split from `agent_lifecycle.py`;
`replay_app.py` keeps the argument surface and the process boundary, this
module keeps the widgets. NO DERIVATION HAPPENS HERE (`test_gui_structural`):
the board frames arrive fully painted from `replay_board` via the one
permitted `replay_verify` import path, and this class only indexes them with
the session's own cursor.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pursuit.gui.replay_panels import ReplayPanels
from pursuit.gui.widgets import PANEL_PAD, GridPanel
from pursuit.services.reporting.replay_verify import ReplaySession

BACK_LABEL = "back"
STEP_LABEL = "step"
PLAY_LABEL = "play"
PAUSE_LABEL = "pause"
BOARD_TITLE = "board (reconstructed)"


class ReplayViewer:
    """One window over one verified artifact. Owns its own Tk root."""

    def __init__(
        self,
        root: tk.Misc,
        session: ReplaySession,
        *,
        step_ms: int,
        board_frames: tuple | None = None,
    ) -> None:
        self.root = root
        self.session = session
        self.step_ms = step_ms
        self.board_frames = board_frames
        self.content = tk.Frame(root)
        self.board = None
        if board_frames:
            self.board = GridPanel(self.content, title=BOARD_TITLE)
            self.board.frame.pack(side=tk.LEFT, anchor=tk.N, padx=PANEL_PAD, pady=PANEL_PAD)
        self.panels = ReplayPanels(self.content)
        self.controls = tk.Frame(root)
        self.buttons = tuple(
            ttk.Button(self.controls, text=label, command=command)
            for label, command in (
                (BACK_LABEL, self.back),
                (STEP_LABEL, self.step),
                (PLAY_LABEL, self.play),
                (PAUSE_LABEL, self.pause),
            )
        )
        for button in self.buttons:
            button.pack(side=tk.LEFT, padx=PANEL_PAD, pady=PANEL_PAD)
        self.panels.frame.pack(
            side=tk.LEFT, padx=PANEL_PAD, pady=PANEL_PAD, fill=tk.BOTH, expand=True
        )
        self.content.pack(padx=PANEL_PAD, pady=PANEL_PAD, fill=tk.BOTH, expand=True)
        self.controls.pack(padx=PANEL_PAD, pady=PANEL_PAD)

    def show(self) -> None:
        self.panels.show(self.session)
        if self.board is not None and self.session.index < len(self.board_frames):
            self.board.paint(self.board_frames[self.session.index])

    def back(self) -> None:
        self.session.back()
        self.show()

    def step(self) -> None:
        self.session.step()
        self.show()

    def play(self) -> None:
        self.session.play()
        self.show()

    def pause(self) -> None:
        self.session.pause()
        self.show()

    def tick(self) -> None:
        """One transport frame, then re-arm on the Tk root's OWN timer. The
        session decides whether a step happens and pauses itself at the end."""
        if self.session.playing:
            self.step()
        self.root.after(self.step_ms, self.tick)

    def start(self) -> None:
        self.show()
        self.root.after(self.step_ms, self.tick)
