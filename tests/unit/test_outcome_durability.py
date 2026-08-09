"""06-05 Gap 2: a caught mismatch must reach something durable.

`run_turn_loop` writes the only outcome-bearing record (`game_over`)
BEFORE the Final-Reveal audit runs, and `game_over` is the only event in
the log carrying an `outcome` field. So a verdict that lives only in
`run_agent`'s return value is invisible to any reader of the log -- and
`main.py` used to discard that return value too, exiting 0 either way.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pursuit.constants import Outcome
from pursuit.main import EXIT_TECHNICAL_LOSS, main
from pursuit.network.agent_audit_exchange import record_audit_verdict
from pursuit.security.audit import AuditRecord


class _FakeMachine:
    state = None


class _FakeState:
    turn = 4


class _Ctx:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.game_uid = "g"
        self.role = "police"
        self.state = _FakeState()
        self.machine = _FakeMachine()


def _events(log_path: Path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_a_mismatch_appends_a_corrected_game_over_record(tmp_path):
    ctx = _Ctx(tmp_path / "game.jsonl")
    mismatch = [AuditRecord(turn=1, matched=False, detail="turn 1: re-hash does not match H_commit")]

    outcome = record_audit_verdict(ctx, peer_audit=mismatch, self_audit=[], elapsed_seconds=0.0)

    assert outcome is Outcome.TECHNICAL_LOSS
    events = _events(ctx.log_path)
    game_overs = [e for e in events if e["event"] == "game_over"]
    assert game_overs, "a caught cheat must leave an outcome-bearing record"
    assert game_overs[-1]["outcome"] == Outcome.TECHNICAL_LOSS.value
    # Ordering matters: the corrected record must be the LAST word.
    assert events[-1]["event"] == "game_over"


def test_a_clean_audit_appends_no_game_over_record(tmp_path):
    """The board result stands on its own when nothing was caught -- the
    audit must not manufacture a second outcome for an honest game."""
    ctx = _Ctx(tmp_path / "game.jsonl")
    clean = [AuditRecord(turn=1, matched=True, detail="turn 1: matched")]

    outcome = record_audit_verdict(ctx, peer_audit=clean, self_audit=clean, elapsed_seconds=0.0)

    assert outcome is None
    events = _events(ctx.log_path)
    assert [e for e in events if e["event"] == "audit_verdict"]
    assert not [e for e in events if e["event"] == "game_over"]


@pytest.mark.parametrize(
    ("outcome", "expected_code"),
    [
        (Outcome.TECHNICAL_LOSS, EXIT_TECHNICAL_LOSS),
        (Outcome.CAPTURE, 0),
        (Outcome.SURVIVAL, 0),
        (None, 0),
    ],
)
def test_main_exit_code_follows_the_final_outcome(monkeypatch, outcome, expected_code):
    """main.py used to discard run_agent's return value entirely, so a
    caught cheat and a clean win were indistinguishable to the caller."""
    async def _fake_run_agent(config_dir):
        return outcome

    monkeypatch.setattr("pursuit.network.agent_lifecycle.run_agent", _fake_run_agent)
    monkeypatch.setattr(
        "pursuit.network.agent_lifecycle.load_agent_config", lambda config_dir: object(),
    )

    assert main(["--config-dir", "config/police"]) == expected_code
