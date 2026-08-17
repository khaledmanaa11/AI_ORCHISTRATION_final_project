"""A declaration that cannot be built must not cost the team the game.

WHY THIS IS THE CONTAINMENT THAT MATTERS. Rule 32 disqualifies the points of an
unreported game and rule 35 scores **zero for BOTH teams** when one side fails
to report. The declaration artifact is newly wired into the most
submission-critical call site in the codebase, so the failure mode this file
forbids is: a broken declaration writer takes the `result_` mail down with it
and both teams score nothing.

The other half is equally load-bearing and is asserted here too -- the failure
must be OBSERVABLE. A contained failure that logs and returns is how
`declaration_<game_id>.json` went unwritten for a whole phase in the first
place, so `EndOfGameReport.declaration_artifact` is `None` and a caller can see
it.
"""

from __future__ import annotations

import pytest

from pursuit.services.reporting import end_of_game_declaration
from pursuit.services.reporting.end_of_game import report_game_end
from tests.integration.end_of_game_harness import played_game


def _explode(*_args, **_kwargs):
    raise RuntimeError("simulated declaration failure")


async def test_a_broken_declaration_still_lets_the_result_mail_go(tmp_path, monkeypatch):
    cfg, ctx, outcome, envelope = await played_game(tmp_path, monkeypatch, "declcontain")
    monkeypatch.setattr(end_of_game_declaration, "build_game_declaration", _explode)

    report = await report_game_end(
        ctx, cfg, outcome=outcome, declaration_envelope=envelope,
        artifact_dir=tmp_path / "game_artifacts",
    )

    assert report is not None, "a failed declaration is not a failed report"
    assert report.send.sent is True and report.send.refusal is None
    assert report.log_artifact.exists() and report.result_artifact.exists()
    assert report.declaration_artifact is None, "the failure must be observable"


async def test_the_failure_is_logged_loudly_rather_than_swallowed(tmp_path, monkeypatch, caplog):
    cfg, ctx, outcome, envelope = await played_game(tmp_path, monkeypatch, "decllogged")
    monkeypatch.setattr(end_of_game_declaration, "build_game_declaration", _explode)

    with caplog.at_level("ERROR", logger=end_of_game_declaration.__name__):
        await report_game_end(
            ctx, cfg, outcome=outcome, declaration_envelope=envelope,
            artifact_dir=tmp_path / "game_artifacts",
        )

    messages = [record.getMessage() for record in caplog.records]
    assert any("declaration artifact could not be written" in message for message in messages)


async def test_a_log_with_no_timestamp_refuses_rather_than_inventing_a_start_time(tmp_path):
    """`DeclarationContext` requires a non-empty `start_time` and a fabricated
    one is worse than a missing artifact, so `game_window` raises."""
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="no timestamped wire-log record"):
        end_of_game_declaration.game_window(empty)


async def test_the_window_is_the_earliest_and_latest_stamp_not_the_first_two_lines(tmp_path):
    log = tmp_path / "out.jsonl"
    log.write_text(
        '{"timestamp": "2026-08-17T10:00:05+00:00"}\n'
        '{"timestamp": "2026-08-17T10:00:01+00:00"}\n'
        '{"no_timestamp": true}\n'
        '{"timestamp": "2026-08-17T10:00:09+00:00"}\n',
        encoding="utf-8",
    )
    assert end_of_game_declaration.game_window(log) == (
        "2026-08-17T10:00:01+00:00",
        "2026-08-17T10:00:09+00:00",
    )
