"""The hook's containment boundary, given REAL causes.

WHY THIS FILE EXISTS AT ALL. `test_end_of_game_reporting.py`'s failing-sink
case never reaches the `except` clause: the chain converts a refused send into
a `SendOutcome` and returns it (rules 28-29 -- queue, never crash). So without
these cases the containment is an untested branch, and a revert probe that
removes it would pass -- the exact vacuity 07-05 and 07-06 each found in their
own work.

WHAT AN ESCAPE WOULD COST. `agent_entrypoint.py` calls the hook inside the try
whose `finally` tears the runtime down, one line before `return outcome`. An
exception there propagates through `run_with_tunnel` and `run_agent` to
`main.py:58`'s `asyncio.run` and exits non-zero -- and since 06-05 a non-zero
exit MEANS an audit mismatch (`main.py:25-29`). A broken reporter would forge
a technical loss.
"""

from __future__ import annotations

from pursuit.services.reporting.artifact_declaration import ENVELOPE_DECLARATION_KEY
from pursuit.services.reporting.artifacts import IGNORED_RUN_DIR, result_filename
from pursuit.services.reporting.end_of_game import report_game_end
from tests.integration.end_of_game_harness import played_game


async def test_a_declaration_with_no_commit_hash_is_contained_not_raised(
    tmp_path, monkeypatch
):
    """Cause 1, BEFORE any artifact is written. `_commit_hash` raises `KeyError`
    -- PARAMETERS mandatory rule 5 means a report with no commit hash is not a
    report -- and the hook returns `None` instead of killing the process."""
    cfg, ctx, outcome, _envelope = await played_game(tmp_path, monkeypatch, "containa")

    report = await report_game_end(
        ctx, cfg, outcome=outcome,
        declaration_envelope={ENVELOPE_DECLARATION_KEY: {"role": "police"}},
        artifact_dir=tmp_path / "game_artifacts",
    )

    assert report is None
    assert outcome is not None, "the outcome object itself is untouched"


async def test_an_artifact_directory_under_logs_is_contained_not_raised(
    tmp_path, monkeypatch
):
    """Cause 2, INSIDE the artifact writer. D7-1: `write_artifact` refuses any
    path under `logs/`, which `.gitignore` excludes wholesale. That refusal is
    correct and must still not reach the exit code."""
    cfg, ctx, outcome, envelope = await played_game(tmp_path, monkeypatch, "containb")
    forbidden = tmp_path / IGNORED_RUN_DIR / "police"

    report = await report_game_end(
        ctx, cfg, outcome=outcome, declaration_envelope=envelope, artifact_dir=forbidden,
    )

    assert report is None
    assert not (forbidden / result_filename("containb")).exists()


async def test_a_game_that_produced_no_outcome_is_not_reported(tmp_path, monkeypatch):
    """The same definition of "completed" `record_completed_game` states beside
    this call site: a handshake that never became a game is not a game to
    report, and writing a `result_` for one would be a report about nothing."""
    cfg, ctx, _outcome, envelope = await played_game(tmp_path, monkeypatch, "containc")
    artifact_dir = tmp_path / "game_artifacts"

    report = await report_game_end(
        ctx, cfg, outcome=None, declaration_envelope=envelope, artifact_dir=artifact_dir,
    )

    assert report is None
    assert not artifact_dir.exists(), "nothing was written for a game that never resolved"
