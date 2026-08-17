"""WHAT the replay viewer is allowed to open -- and the live-game question.

Split out of `replay_verify.py` at the 150-code-line gate (Segal Table 5; the
combined module measured 183) along the seam it already had: this half answers
*which file may be read*, the other half answers *does it verify*. Split,
never compressed -- not one line of any docstring or body was shortened to
make room. `replay_verify.py` re-exports both public names below, so the Tk
layer keeps ONE import path.

A REPLAY VIEWER POINTED AT AN IN-PROGRESS GAME MUST NOT BECOME A LIVE ORACLE,
and that is decided here rather than left to chance. Rules 8-9 make displaying
the objective board state in the LIVE interface a project disqualification;
07-11 closed a confirmed leak of exactly that kind. A finished game's wire
record is legitimately public after the fact, but "after the fact" has to be
enforced, not assumed. Two independent reasons it holds:

1. **The artifact does not exist during play.** `log_<game_id>_g<NN>.json` is
   built at game end only -- D-64 keeps the nonce ledger off the wire path,
   rule 18 keeps every nonce secret while the game is live, and only SEC-04's
   end-of-game publication makes the ledger readable.
   `tests/unit/test_log_artifact_reachability.py` fails on every suite run if
   anything under `network/turn_*` or the orchestrator reaches the builder.

2. **The two LIVE files are refused by name.** An operator who points this app
   at `logs/<role>/<uid>.jsonl` or its `<uid>.ledger.jsonl` sibling gets a
   refusal naming rule 18, not a window. `load_artifact` checks the
   `docs/PARAMETERS.md:167` filename prefix that `artifact_names.log_filename`
   builds, and neither live file carries it.

So the answer to "what does it do if opened on a running game" is: it cannot
be. Refusing is the safe direction and the loud one -- a viewer that silently
opened a partial live log would be reading nonces mid-game.
"""

from __future__ import annotations

import json
from enum import IntEnum
from pathlib import Path

from pursuit.services.reporting.artifact_names import ArtifactPrefix

__all__ = ("ReplayExit", "load_artifact")


class ReplayExit(IntEnum):
    """Process exit codes -- structural, not game parameters (the
    `check_local_truth.ExitCode` / `watchdog.WatchdogExit` precedent for
    naming an exit code rather than writing the integer at the call site)."""

    OK = 0
    UNREADABLE = 2


def load_artifact(path: Path | str) -> dict:
    """Read a `log_` artifact, and REFUSE anything else.

    The refusal is the enforcement of the decision in the module docstring, at
    the one read site rather than as a convention every caller must remember
    -- `artifacts.write_artifact`'s D7-1 refusal is the precedent.

    Fail-loud: a wrong path is an operator error, and `gui/replay_app.main`
    reports it and exits `ReplayExit.UNREADABLE` rather than opening a window
    that says nothing. `json.JSONDecodeError` is a `ValueError`, so one
    `except` clause in the entry point covers both halves.
    """
    file_path = Path(path)
    if not file_path.name.startswith(ArtifactPrefix.LOG):
        raise ValueError(
            f"{file_path} is not a {ArtifactPrefix.LOG} artifact. The replay viewer reads the "
            "sealed end-of-game artifact only -- never a live wire log or nonce ledger (rule 18)."
        )
    artifact = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(artifact, dict):
        raise ValueError(f"{file_path} does not hold a JSON object")
    return artifact
