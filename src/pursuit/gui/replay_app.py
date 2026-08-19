"""The replay verifier's entry point -- a standalone process (REPORT-09).

    uv run python -m pursuit.gui.replay_app --artifact <log_..._g01.json> \
        --step-ms <N>

Rule 20 (`docs/RULES.md:51`) makes a verifying replay viewer "a threshold
condition for approving and submitting the project", and Sec10.4 criterion 3
names the words on the screen. This file puts them there and computes nothing:
`services/reporting/replay_verify.open_replay` did the verification, the
stepping and the strings, where the coverage gate can see them.

`mainloop()` IS CORRECT HERE, AND THAT IS THE OPPOSITE OF THE LIVE DASHBOARD.
Say so, so a later reader does not "fix" this into the live app's shape. D-76
forced the live GUI into a separate process because `tk.mainloop()` blocks its
calling thread while `network/watchdog.py:48-57` runs a daemon thread whose
action after `watchdog_threshold` seconds of silence is `os._exit(FREEZE)` --
blocking the agent's asyncio loop kills the agent mid-game. THIS process has
no asyncio loop, no turn loop, no watchdog and no peer: it opens one finished
file and owns its own process, so it may block on `mainloop()` freely.

`--step-ms` FOLLOWS OQ-6, 07-06's precedent, for the same reason.
`docs/PARAMETERS.md` Table 19 has no UI row, so no interval is written down
anywhere in `src/`: the argument is `required=True` with NO `default=`, and
`ReplayViewer.__init__` takes it as a required keyword-only argument.

WHY THE IMPORT BELOW NAMES THE MODULE AND NOT THE PACKAGE.
`scripts/check_local_truth.py:80` allows a `gui/` module exactly ONE path into
`pursuit.services` -- `pursuit.services.reporting.replay_verify` -- so
`from pursuit.services.reporting import VERIFIED_OK` would be a reported
violation even though it resolves to the same object. One spelling, and the
gate is what keeps it that way.
"""

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path

from pursuit.gui.replay_viewer import ReplayViewer
from pursuit.services.reporting.replay_verify import (
    WINDOW_TITLE,
    ReplayExit,
    board_colour_frames,
    open_replay,
)

ARTIFACT_HELP = (
    "path to a sealed log_<game_id>_g<NN>.json artifact. A live wire log or "
    "nonce ledger is refused by name -- rule 18 keeps nonces secret while a "
    "game is running, and this artifact only exists once one has finished."
)
STEP_HELP = (
    "milliseconds between turns while playing. REQUIRED and deliberately "
    "without a default: OQ-6 -- no document in this project states a UI "
    "interval, so the operator states it and the repository does not."
)
ONCE_HELP = "build every widget, render one frame and exit 0 -- the scripted launch gate"
GAME_PARAMS_HELP = (
    "path to the game's byte-identical shared game_params.json (rule 11). "
    "Supplying it adds a reconstructed full-board panel -- legal only because "
    "this viewer opens sealed FINISHED games (rule 9 restricts the live view); "
    "the opponent's track integrates from their negotiated start plus their "
    "revealed moves. Omit it for the text-only verifier."
)
REFUSED = "replay_app: cannot open that file --"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pursuit.gui.replay_app", description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True, help=ARTIFACT_HELP)
    parser.add_argument("--step-ms", type=int, required=True, help=STEP_HELP)
    parser.add_argument("--once", action="store_true", help=ONCE_HELP)
    parser.add_argument("--game-params", type=Path, default=None, help=GAME_PARAMS_HELP)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Verify first, then draw. A file that cannot be opened, or that is not
    a `log_` artifact, is reported on stdout and exits `UNREADABLE` -- never a
    window with an empty banner, which a screenshot could not be told from a
    passing one. `json.JSONDecodeError` is a `ValueError`, so one clause
    covers the refusal and the malformed file alike."""
    args = build_parser().parse_args(argv)
    try:
        session = open_replay(args.artifact)
        frames = (
            board_colour_frames(session.artifact, args.game_params)
            if args.game_params
            else None
        )
    except (OSError, ValueError) as exc:
        print(REFUSED, exc)
        return ReplayExit.UNREADABLE
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    viewer = ReplayViewer(root, session, step_ms=args.step_ms, board_frames=frames)
    if args.once:
        viewer.show()
        root.update()
        root.destroy()
        return ReplayExit.OK
    viewer.start()
    root.mainloop()
    return ReplayExit.OK


if __name__ == "__main__":
    sys.exit(main())
