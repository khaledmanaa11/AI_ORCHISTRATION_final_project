"""Rule 35: TWO seats sharing one repository must produce TWO separate reports.

FOUND ON A REAL GAME, NOT REASONED ABOUT. One `scripts/dev_launch.py` run at
commit `4d68886` produced, for a SINGLE game:

    game_artifacts/log_1449bfdb473e0faa_g01.json   <- one seat
    game_artifacts/log_1449bfdb473e0faa_g02.json   <- the OTHER seat, as if a
                                                      second sub-game
    game_artifacts/result_1449bfdb473e0faa.json    <- role: police, carrying
                                                      BOTH seats' entries and
                                                      games_measured: 2

The thief's report was overwritten and gone. Rule 35 (`docs/RULES.md:76`):
"each team sends its own separate report ... Non-reporting ... by ONE team
disqualifies the game and scores 0 for both teams." Both processes share a
repository and therefore the configured `artifact_dir`, so this side's four
artifacts go to `<artifact_dir>/<role>/`.

The two seats are driven in the ORDER a real run produces -- one after the
other into the same root -- because a test that gave each seat its own root
would pass against the very bug this file exists to pin.
"""

from __future__ import annotations

import json

from pursuit.services.reporting.artifact_result import ResultArtifactField, TokensField
from pursuit.services.reporting.artifacts import log_filename, result_filename
from pursuit.services.reporting.end_of_game import report_game_end
from tests.integration.end_of_game_harness import played_seats

FIRST_SUB_GAME = 1


async def test_two_seats_sharing_one_artifact_root_write_two_separate_reports(
    tmp_path, monkeypatch
):
    seats = await played_seats(tmp_path, monkeypatch, "twoseats")
    assert len(seats) == 2
    root = tmp_path / "game_artifacts"

    reports = []
    for cfg, ctx, outcome, envelope in seats:
        report = await report_game_end(
            ctx, cfg, outcome=outcome, declaration_envelope=envelope, artifact_dir=root,
        )
        assert report is not None
        reports.append((ctx.role, report))

    roles = [role for role, _ in reports]
    assert roles == ["police", "thief"], "the two shipped roles, in run order"

    for role, report in reports:
        assert report.result_artifact.parent.name == role
        assert report.log_artifact.parent.name == role
        # BOTH seats are sub-game 01 of the same game: one game, two seats.
        assert report.log_artifact.name == log_filename("twoseats", FIRST_SUB_GAME)
        assert report.result_artifact.name == result_filename("twoseats")

        artifact = json.loads(report.result_artifact.read_text(encoding="utf-8"))
        assert artifact[ResultArtifactField.ROLE] == role
        assert len(artifact[ResultArtifactField.SUB_GAMES]) == 1, (
            "one game is ONE sub-game; the other seat is not a second one"
        )
        assert artifact[ResultArtifactField.SERIES_TOKENS][TokensField.GAMES_MEASURED] == 1

    police, thief = (report for _role, report in reports)
    assert police.result_artifact != thief.result_artifact
    assert police.log_artifact != thief.log_artifact


async def test_each_seat_reports_its_own_outcome_and_its_own_agreement(
    tmp_path, monkeypatch
):
    """The asymmetry rule 21 creates, carried honestly rather than smoothed:
    only the seat that RECEIVED a Capture Claim can record `agreed: true`, and
    the cop -- which sends the claim and receives none -- records `null` with a
    stated reason. Both still report."""
    seats = await played_seats(tmp_path, monkeypatch, "twoseatsb")
    root = tmp_path / "game_artifacts"
    agreements = {}

    for cfg, ctx, outcome, envelope in seats:
        report = await report_game_end(
            ctx, cfg, outcome=outcome, declaration_envelope=envelope, artifact_dir=root,
        )
        artifact = json.loads(report.result_artifact.read_text(encoding="utf-8"))
        agreements[ctx.role] = artifact[ResultArtifactField.SUB_GAMES][0]["agreement"]

    assert set(agreements) == {"police", "thief"}
    for role, agreement in agreements.items():
        assert agreement["own_outcome"] == "capture", role
        assert agreement["agreed"] is not False, f"{role} recorded a contradiction"
        assert agreement["reason"], f"{role} recorded no reason"
    assert agreements["thief"]["agreed"] is True
    assert agreements["thief"]["peer_outcome"] == "capture"
    assert agreements["police"]["agreed"] is None
    assert agreements["police"]["peer_claim_present"] is False
