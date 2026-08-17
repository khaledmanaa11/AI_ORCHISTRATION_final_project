"""A REAL game writes a REAL `declaration_<game_id>.json`, and its keys are
checked against `docs/PARAMETERS.md:165` read out of the document.

THE DEFECT THIS FILE CLOSES. 08-01 re-derived at HEAD that
`build_declaration_artifact`, `write_declaration_artifact` and
`DeclarationContext` had ZERO production callers. `declaration_<game_id>.json`
is one of rule 50's four MANDATORY artifacts, so PARAMETERS' declaration
content had never been written by a game. Everything here therefore runs
against `played_game`'s real two-peer match and its real signed Step-0
envelope -- a synthetic context would prove the wrapper works, which was never
in doubt, and not that a game calls it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pursuit.services.reporting.artifacts import declaration_filename
from pursuit.services.reporting.end_of_game import report_game_end
from pursuit.shared.absent import is_stated_absent
from tests.integration.end_of_game_harness import played_game

PARAMETERS = Path(__file__).resolve().parents[2] / "docs/PARAMETERS.md"

#: The content words PARAMETERS:165 names, mapped to the artifact keys that
#: carry them. `identities`, `hardware spec` and `language model` are the
#: SIGNED Step-0 half and live inside `declarations`; the rest is D-71's
#: outside-the-signature content.
PARAMETERS_CONTENT = {
    "repo URLs": "repo_urls",
    "MCP server addresses": "mcp_server_addresses",
    "agreed token ceiling": "token_ceiling",
    "start/end times": ("start_time", "end_time"),
}


def _parameters_row() -> str:
    """The `declaration_<game_id>.json` row of PARAMETERS' artifact table."""
    match = re.search(r"\|\s*`declaration_<game_id>\.json`\s*\|([^|]*)\|", PARAMETERS.read_text(encoding="utf-8"))
    assert match is not None, "docs/PARAMETERS.md no longer has a declaration_ row"
    return match.group(1)


def test_the_parameters_row_still_asks_for_what_this_file_checks():
    """ANTI-VACUITY GUARD. Every key assertion below is worth nothing if the
    document stopped naming these; read the row and prove it still does."""
    row = _parameters_row()
    for phrase in PARAMETERS_CONTENT:
        assert phrase in row, f"docs/PARAMETERS.md:165 no longer names {phrase!r}"


async def _declaration_of_a_real_game(tmp_path, monkeypatch, uid):
    cfg, ctx, outcome, envelope = await played_game(tmp_path, monkeypatch, uid)
    artifact_dir = tmp_path / "game_artifacts"
    report = await report_game_end(
        ctx, cfg, outcome=outcome, declaration_envelope=envelope, artifact_dir=artifact_dir,
    )
    assert report is not None
    return report, artifact_dir / ctx.role / declaration_filename(uid)


async def test_a_real_game_writes_the_declaration_artifact_to_disk(tmp_path, monkeypatch):
    """THE TEST THAT MATTERS. Read off disk, not off the return value."""
    report, path = await _declaration_of_a_real_game(tmp_path, monkeypatch, "declarationa")
    assert report.declaration_artifact == path
    assert path.exists(), "the mandatory declaration artifact was not written"


async def test_the_written_keys_are_the_ones_parameters_165_names(tmp_path, monkeypatch):
    _report, path = await _declaration_of_a_real_game(tmp_path, monkeypatch, "declarationb")
    artifact = json.loads(path.read_text(encoding="utf-8"))
    for keys in PARAMETERS_CONTENT.values():
        for key in (keys,) if isinstance(keys, str) else keys:
            assert key in artifact, f"{key} missing from the declaration artifact"
    signed = artifact["declarations"]["own"]["declaration"]
    assert {"role", "team_code", "os", "cpu", "ram_gb", "gpu", "llm_name"} <= set(signed)


async def test_rule_49s_four_repo_links_are_carried_as_honest_absences(tmp_path, monkeypatch):
    """Rule 49 wants FOUR links in both teams' JSON. None exists until a human
    creates the repositories at 08-12, so each slot is a marker naming that
    plan -- never a `https://github.com/...` guess reading as a claim."""
    _report, path = await _declaration_of_a_real_game(tmp_path, monkeypatch, "declarationc")
    urls = json.loads(path.read_text(encoding="utf-8"))["repo_urls"]
    assert set(urls) == {"own_cop", "own_thief", "opponent_cop", "opponent_thief"}
    assert all(is_stated_absent(value) for value in urls.values())
    assert all("08-12" in value["detail"] for value in urls.values())


async def test_the_games_played_figure_is_left_unset_with_its_reason(tmp_path, monkeypatch):
    """Rule 38 is an ABSOLUTE disqualification. The signed envelope's raw
    counter is present because rule 37 puts it there; the artifact says so."""
    _report, path = await _declaration_of_a_real_game(tmp_path, monkeypatch, "declarationd")
    artifact = json.loads(path.read_text(encoding="utf-8"))
    declared = artifact["games_played_declared"]
    assert is_stated_absent(declared)
    assert "GAMES-PLAYED-RECONSTRUCTION.md" in declared["detail"]
    assert "games_played_so_far" in artifact["declarations"]["own"]["declaration"]


async def test_the_times_are_the_games_own_wire_log_timestamps(tmp_path, monkeypatch):
    """Measured, not stamped: both values must be timestamps this game really
    wrote, so a clock read at report time cannot pass."""
    cfg, ctx, outcome, envelope = await played_game(tmp_path, monkeypatch, "declaratione")
    stamps = [
        json.loads(line)["timestamp"]
        for line in ctx.log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = await report_game_end(
        ctx, cfg, outcome=outcome, declaration_envelope=envelope,
        artifact_dir=tmp_path / "game_artifacts",
    )
    artifact = json.loads(report.declaration_artifact.read_text(encoding="utf-8"))
    assert artifact["start_time"] == min(stamps)
    assert artifact["end_time"] == max(stamps)
