"""The game-end hook on a REAL game: proofs (a) and (b).

(a) a normal game writes both artifacts and produces a `dry_run` send;
(b) a sink that ALWAYS fails leaves the outcome, the game's own log and this
    process's exit code untouched, and the report is still owed on the queue.

THE EXIT CODE IS THE POINT OF (b). Since 06-05 a non-zero exit MEANS an audit
mismatch (`main.py:25-29`), and `main()` derives it from ONE thing: whether
`run_agent`'s returned outcome is `TECHNICAL_LOSS`. So the exit code is proved
by proving the outcome object is unchanged, which is the fact the mapping
reads.
"""

from __future__ import annotations

import json

from pursuit.constants import Outcome
from pursuit.main import EXIT_TECHNICAL_LOSS
from pursuit.services.reporting.artifacts import log_filename, result_filename
from pursuit.services.reporting.chain import Refusal
from pursuit.services.reporting.end_of_game import report_game_end
from pursuit.services.reporting.end_of_game_chain import build_reporting_chain
from pursuit.services.reporting.message import report_filename
from pursuit.services.reporting.sink import EML_SUFFIX
from pursuit.shared.reporting_config import REPORTING_CONFIG_SOURCE, load_reporting_config
from tests.integration.end_of_game_harness import AlwaysFailingSink, no_wait, played_game

SUB_GAME = 1


def _exit_code(outcome) -> int:
    """`main.py:59`'s mapping, transcribed."""
    return EXIT_TECHNICAL_LOSS if outcome is Outcome.TECHNICAL_LOSS else 0


async def test_a_normal_game_writes_both_artifacts_and_sends_in_dry_run(
    tmp_path, monkeypatch
):
    uid = "endofgamea"
    cfg, ctx, outcome, envelope = await played_game(tmp_path, monkeypatch, uid)
    log_before, exit_before = ctx.log_path.read_bytes(), _exit_code(outcome)
    artifact_dir = tmp_path / "game_artifacts"

    report = await report_game_end(
        ctx, cfg, outcome=outcome, declaration_envelope=envelope, artifact_dir=artifact_dir,
    )

    assert report is not None
    assert report.send.sent is True and report.send.refusal is None
    assert report.pending == 0
    assert report.log_artifact.name == log_filename(uid, SUB_GAME)
    assert report.result_artifact.name == result_filename(uid)
    assert report.result_artifact.with_suffix(EML_SUFFIX).exists(), "the dry run wrote the message"
    assert ctx.log_path.read_bytes() == log_before, "reporting only READS the game's log"
    assert _exit_code(outcome) == exit_before == 0


async def test_a_sink_that_always_fails_changes_nothing_and_still_owes_the_report(
    tmp_path, monkeypatch
):
    """(b) The containment proof. Nothing about the game moves, and the report
    is held on the FIFO queue rather than lost (rules 28-29: queue, never
    crash; rule 32: the report is still owed)."""
    uid = "endofgamec"
    cfg, ctx, outcome, envelope = await played_game(tmp_path, monkeypatch, uid)
    log_before, exit_before = ctx.log_path.read_bytes(), _exit_code(outcome)
    last_game_over_before = _last_game_over(ctx)

    params = load_reporting_config(cfg.config_dir / REPORTING_CONFIG_SOURCE)
    failing = AlwaysFailingSink()
    chain = build_reporting_chain(
        params, watchdog=ctx.watchdog, artifact_dir=tmp_path / "game_artifacts",
        quota_dir=tmp_path, sink=failing, sleep=no_wait,
    )
    report = await report_game_end(
        ctx, cfg, outcome=outcome, declaration_envelope=envelope,
        artifact_dir=tmp_path / "game_artifacts", chain=chain,
    )

    assert failing.attempts == params.retries_before_failure + 1, "the whole ladder ran"
    assert report is not None, "a failed SEND is not a failed report build"
    assert report.send.sent is False
    assert report.send.refusal is Refusal.SEND_FAILED
    assert report.send.queued is True
    assert report.pending == 1 and chain.pending == 1

    assert report.log_artifact.exists() and report.result_artifact.exists()
    assert report.result_artifact.name == report_filename(
        json.loads(report.result_artifact.read_text(encoding="utf-8"))
    )
    assert ctx.log_path.read_bytes() == log_before
    assert _last_game_over(ctx) == last_game_over_before
    assert _exit_code(outcome) == exit_before == 0

    redrained = await chain.drain()
    assert len(redrained) == 1 and chain.pending == 1, "still owed, never dropped"


def _last_game_over(ctx) -> dict | None:
    records = [
        json.loads(line)
        for line in ctx.log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    overs = [r for r in records if r.get("event") == "game_over"]
    assert overs, "a finished game must leave a game_over record"
    return overs[-1]
