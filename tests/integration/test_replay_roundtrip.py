"""A real two-peer game -> the `log_` artifact -> BOTH SOURCES DELETED ->
`Verified OK` on the screen's own value (07-08 Task 3, REPORT-09, rule 20).

Deleting the `.jsonl` and the `.ledger.jsonl` BEFORE verifying is the whole
point, and it is the promise 07-05 made this plan: a third party receives one
file and must be able to recompute every hash from it. A test that left the
sources on disk would prove nothing, because a reader could silently have
fallen back to them.

THE VERDICT ASSERTED HERE IS THE ONE THE BANNER RENDERS. Every assertion goes
through `open_replay(path).verdict`, which is exactly what
`gui/replay_app.main` calls -- never a parallel helper, which would be
evidence about the helper.
"""

from __future__ import annotations

import ast
import asyncio
import json
import pathlib

from pursuit.gui.replay_app import main as replay_app_main
from pursuit.network.agent_audit_wiring import run_final_audit
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.turn_commit_ledger import ledger_path_for
from pursuit.services.reporting.artifact_log import write_log_artifact
from pursuit.services.reporting.log_artifact_fields import LogArtifactField
from pursuit.services.reporting.log_turn_fields import TurnField
from pursuit.services.reporting.replay_verify import (
    VERIFIED_OK,
    ReplayExit,
    VerdictState,
    open_replay,
)
from tests.integration.two_peer_game import play_two_peer_game
from tests.unit.replay_fixtures import TAMPERERS, reseal

GAME_UID = "replayroundtrip"
GAME_ID = "replayround"
SUB_GAME_INDEX = 1
SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
VERIFY_MODULE = "pursuit.services.reporting.replay_verify"
#: The anti-vacuity floor for the production-caller scan, on
#: `test_log_artifact_reachability.py`'s precedent: an empty `src/` would
#: otherwise make the reacher list empty and the assertion meaningless.
MIN_SCANNED = 100


async def _artifact_from_a_real_game(tmp_path, monkeypatch, uid: str) -> pathlib.Path:
    """One real recorded game on the shipped configs, then the final audit,
    then the artifact -- the order `agent_entrypoint.run_agent` uses. Returns
    the artifact path, with BOTH sources already deleted."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid=uid, log_dir=tmp_path,
    )
    assert outcome_a is not None and outcome_a == outcome_b
    await asyncio.gather(
        run_final_audit(ctx_a, board_outcome=outcome_a),
        run_final_audit(ctx_b, board_outcome=outcome_b),
    )
    path = write_log_artifact(
        tmp_path / "game_artifacts", ctx_a.log_path,
        game_uid=uid, game_id=uid, sub_game_index=SUB_GAME_INDEX,
    )
    ledger = ledger_path_for(ctx_a.log_path)
    assert ctx_a.log_path.exists() and ledger.exists()
    ctx_a.log_path.unlink()
    ledger.unlink()
    assert not ctx_a.log_path.exists() and not ledger.exists()
    return path


async def test_a_recorded_game_verifies_from_the_artifact_alone(tmp_path, monkeypatch):
    """Sec10.4 criterion 3, end to end, with the sources gone."""
    path = await _artifact_from_a_real_game(tmp_path, monkeypatch, GAME_UID)
    session = open_replay(path)
    assert session.verdict.banner == VERIFIED_OK
    assert session.verdict.state is VerdictState.OK
    assert session.verdict.committed > 0, "a zero-turn Verified OK proves nothing"
    assert session.verdict.verified == session.verdict.committed
    assert session.turn_count > session.verdict.committed, "the game-over turn is missing"
    # The screen can be stepped across every turn of the real game.
    for _ in range(session.turn_count):
        session.step()
    assert session.at_end is True and all(session.blocks())


async def test_a_single_field_tamper_in_the_artifact_names_the_turn_it_touched(
    tmp_path, monkeypatch
):
    """One legal direction swapped for another on ONE turn --
    `scripts/gate6_tamper.py`'s own mutation shape, reused rather than
    reinvented -- then resealed, so the verdict is earned by the per-turn
    re-hash rather than by the artifact seal."""
    path = await _artifact_from_a_real_game(tmp_path, monkeypatch, f"{GAME_UID}b")
    assert open_replay(path).verdict.banner == VERIFIED_OK, "the clean run is the control"

    body = json.loads(path.read_text(encoding="utf-8"))
    committed = [t for t in body[LogArtifactField.TURNS] if t[TurnField.HASH] is not None]
    assert len(committed) > 1, "a one-turn game cannot show that the RIGHT turn is named"
    target = committed[-1]
    target[TurnField.MOVE] = TAMPERERS[TurnField.MOVE](target[TurnField.MOVE])
    path.write_text(json.dumps(reseal(body)), encoding="utf-8")

    verdict = open_replay(path).verdict
    assert verdict.state is VerdictState.FAILED
    assert verdict.banner != VERIFIED_OK
    assert f"turn {target[TurnField.TURN]}" in verdict.banner, verdict.banner
    assert f"turn {committed[0][TurnField.TURN]}" not in verdict.banner, "it named turn 0"
    assert verdict.verified == verdict.committed - 1


def _bindings(relative: str) -> set[str]:
    tree = ast.parse((SRC / relative).read_text(encoding="utf-8"))
    return {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == VERIFY_MODULE
        for alias in node.names
    }


def _imports_the_verifier(path: pathlib.Path) -> bool:
    """By AST, never by substring: three of these modules discuss
    `replay_verify` in their docstrings, which a text scan would count."""
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module == VERIFY_MODULE:
            return True
        if isinstance(node, ast.Import) and any(a.name == VERIFY_MODULE for a in node.names):
            return True
    return False


def test_the_verdict_has_a_production_caller_and_it_is_the_shipped_screen():
    """D7-3's discipline: a verdict reachable only from tests proves nothing
    about what a grader sees. Every `src/` module reaching the verifier is
    NAMED, so a new one fails here rather than in a grader's inbox."""
    scanned = sorted(SRC.rglob("*.py"))
    assert len(scanned) > MIN_SCANNED, "the scan looked at almost nothing"
    reachers = sorted(p.relative_to(SRC).as_posix() for p in scanned if _imports_the_verifier(p))
    assert reachers == [
        "pursuit/gui/replay_app.py",
        "pursuit/gui/replay_panels.py",
        # run-3's 150-line split of the window class out of replay_app, plus
        # the board panel's frames -- both still THE shipped screen's path.
        "pursuit/gui/replay_viewer.py",
    ]
    assert {"open_replay", "board_colour_frames"} <= _bindings("pursuit/gui/replay_app.py")
    assert {"banner_colour", "SECTION_TITLES"} <= _bindings("pursuit/gui/replay_panels.py")
    assert "ReplaySession" in _bindings("pursuit/gui/replay_viewer.py")
    # And the verdict function is on that path: `open_replay` calls it.
    source = (SRC / "pursuit/services/reporting/replay_verify.py").read_text(encoding="utf-8")
    body = next(
        node for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "open_replay"
    )
    called = {n.func.id for n in ast.walk(body) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert {"load_artifact", "check_turns", "verdict_from"} <= called


def test_the_shipped_entry_point_refuses_a_live_log_without_opening_a_window(tmp_path, capsys):
    """`main()` verifies BEFORE it builds a Tk root, so this exercises the
    real production entry point with no display -- and proves a refused file
    can never produce a window whose empty banner a screenshot might flatter."""
    live = tmp_path / "521519a78f96c255.jsonl"
    live.write_text("{}\n", encoding="utf-8")
    argv = ["--artifact", str(live), "--step-ms", "400", "--once"]
    assert replay_app_main(argv) == ReplayExit.UNREADABLE
    out = capsys.readouterr().out
    assert "rule 18" in out and VERIFIED_OK not in out
