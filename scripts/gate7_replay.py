"""Sec10.4 criterion 3 -- the replay app reconstructs a recorded round and
shows `Verified OK`. THREE verdicts, not one.

A run that can only ever show `Verified OK` proves nothing, so the same real
game feeds all three states: the clean artifact (OK), a single-field tamper on
ONE committed turn, resealed so the verdict is earned by the per-turn re-hash
rather than by the artifact seal (FAILED, naming that turn), and an artifact
with no committed turn at all (`Nothing to verify` -- the state that would read
`Verified OK` if the non-zero guard were dropped ahead of the aggregate).

BOTH SOURCES ARE DELETED BEFORE ANY VERDICT IS TAKEN. `<uid>.jsonl` and
`<uid>.ledger.jsonl` go off disk first, so a reader cannot silently have fallen
back to them -- the promise 07-05 made and 07-08 kept.

EVERY VERDICT IS TAKEN THROUGH `open_replay(path).verdict`, which is the value
`gui/replay_app.main` renders. There is deliberately no `verdict_for` wrapper
(07-08 removed it as test-only), and a measurement through a parallel helper
would be evidence about the helper.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from gate7_common import REPO_ROOT, outcome_name

from pursuit.network.turn_commit_ledger import ledger_path_for
from pursuit.services.reporting.artifact_log import write_log_artifact
from pursuit.services.reporting.log_artifact_fields import LogArtifactField
from pursuit.services.reporting.log_turn_fields import TurnField
from pursuit.services.reporting.replay_verify import ReplayExit, open_replay
from tests.unit.replay_fixtures import TAMPERERS, empty_artifact, reseal

REPLAY_APP_MODULE = "pursuit.gui.replay_app"
SUB_GAME_INDEX = 1
#: Stands in for the throwaway measurement directory -- see `_refusal`.
TMP_REDACTION = "<tmp>"

#: The interval THIS MEASUREMENT was taken with -- OQ-6 again: `--step-ms` is
#: required with no default anywhere in `src/`, so the operator states it.
GATE_STEP_MS = 400


def _verdict_fields(path: Path) -> dict:
    session = open_replay(path)
    verdict = session.verdict
    return {
        "banner": verdict.banner,
        "state": verdict.state.value,
        "detail": verdict.detail,
        "verified": verdict.verified,
        "committed": verdict.committed,
        "turn_count": session.turn_count,
    }


def _launch(argv: list[str]) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", REPLAY_APP_MODULE, *argv],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    return {
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-1:] or [],
    }


def _tampered(clean: Path, directory: Path) -> dict:
    """One committed turn's `move` swapped for another LEGAL direction --
    `scripts/gate6_tamper.py`'s own mutation shape -- then resealed."""
    body = json.loads(clean.read_text(encoding="utf-8"))
    committed = [t for t in body[LogArtifactField.TURNS] if t[TurnField.HASH] is not None]
    target = committed[-1]
    target[TurnField.MOVE] = TAMPERERS[TurnField.MOVE](target[TurnField.MOVE])
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / clean.name
    path.write_text(json.dumps(reseal(body)), encoding="utf-8")
    fields = _verdict_fields(path)
    return {
        **fields,
        "tampered_field": str(TurnField.MOVE),
        "tampered_turn": target[TurnField.TURN],
        "first_committed_turn": committed[0][TurnField.TURN],
        "banner_names_the_tampered_turn": f"turn {target[TurnField.TURN]}" in fields["banner"],
        "banner_does_not_name_turn_zero": (
            f"turn {committed[0][TurnField.TURN]}" not in fields["banner"]
        ),
    }


def _nothing_to_verify(directory: Path, clean_name: str) -> dict:
    """An artifact with no committed turn -- sealed, well formed, and empty."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / clean_name
    path.write_text(json.dumps(empty_artifact()), encoding="utf-8")
    return _verdict_fields(path)


def _refusal(tmp: Path) -> dict:
    """A live wire log by name: refused before any Tk root is built (rule 18).

    The throwaway directory is redacted OUT of the captured message, and the
    field says so. Two reasons, both declared rather than silent: the path is
    different on every run, which would make the evidence file differ between
    two runs that measured exactly the same thing; and an absolute temp path on
    a developer machine embeds a local username in a file destined for a PUBLIC
    submission repo (rule 49). Nothing about the REFUSAL is edited.
    """
    live = tmp / "gate7-live.jsonl"
    live.write_text("{}\n", encoding="utf-8")
    launched = _launch(["--artifact", str(live), "--step-ms", str(GATE_STEP_MS), "--once"])
    redacted = [line.replace(str(tmp), TMP_REDACTION) for line in launched.pop("stdout_tail")]
    return {
        **launched,
        "stdout_tail_tmp_dir_redacted": redacted,
        "expected_returncode": int(ReplayExit.UNREADABLE),
        "message_names_rule_18": any("rule 18" in line for line in redacted),
    }


def measure_replay(game: object, tmp: Path) -> dict:
    """Criterion 3's evidence, on the SAME real game criterion 2 measured."""
    ctx = game.ctx_police
    clean = write_log_artifact(
        tmp / "artifacts", ctx.log_path,
        game_uid=game.uid, game_id=game.uid, sub_game_index=SUB_GAME_INDEX,
    )
    ledger = ledger_path_for(ctx.log_path)
    sources_existed = ctx.log_path.exists() and ledger.exists()
    ctx.log_path.unlink()
    ledger.unlink()
    return {
        "game_uid": game.uid,
        "outcome_police": outcome_name(game.outcome_police),
        "outcome_thief": outcome_name(game.outcome_thief),
        "outcomes_agree": game.outcomes_agree,
        "artifact": clean.name,
        "sources_existed_before_deletion": sources_existed,
        "sources_deleted_before_verifying": {
            "wire_log": not ctx.log_path.exists(), "ledger": not ledger.exists(),
        },
        "verified_ok": _verdict_fields(clean),
        "failed": _tampered(clean, tmp / "tampered"),
        "nothing_to_verify": _nothing_to_verify(tmp / "empty", clean.name),
        "app_launch": {
            **_launch(["--artifact", str(clean), "--step-ms", str(GATE_STEP_MS), "--once"]),
            "step_ms": GATE_STEP_MS,
            "expected_returncode": int(ReplayExit.OK),
        },
        "live_log_refused_by_name": _refusal(tmp),
    }
