"""05-05 Task 1 (D-61, 05-UAT.md G2): the two construction-time JSONL sinks
must be able to FOLLOW a game id that changes once, mid-process.

The hazard this file exists to catch is silent, not loud: a reporter bound
before the handshake keeps appending to the pre-negotiation path forever,
and nothing errors -- the round just ends with two logs that cannot be
joined. So every test here writes, MUTATES the identity, writes again, and
asserts on TWO distinct files.

The `identity=None` cases are the other half of the contract: every
pre-existing caller (`tests/unit/test_agent_lifecycle.py`,
`test_agent_lifecycle_resilience.py`, `tests/integration/test_turn_resilience.py`)
passes no identity and those files are UNMODIFIED by this plan, so the
default path is proven byte-identical here as well as by their own passing.
"""

from __future__ import annotations

import json

from pursuit.network.game_identity import (
    GameIdentity,
    make_freeze_handler,
    make_transition_reporter,
    negotiated_game_id,
)
from pursuit.network.state_machine import State, TransitionSeverity

_THRESHOLD = 60.0


def _lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _report(reporter):
    reporter(
        current=State.HANDSHAKE, target=State.HANDSHAKE,
        severity=TransitionSeverity.RECOVERABLE, reason="symmetric handshake",
    )


def test_the_reporter_follows_an_identity_mutated_after_construction(tmp_path):
    before, after = tmp_path / "old.jsonl", tmp_path / "new.jsonl"
    identity = GameIdentity(game_uid="old-uid", log_path=before)
    reporter = make_transition_reporter(before, game_uid="old-uid", role="thief", identity=identity)

    _report(reporter)
    identity.game_uid, identity.log_path = "new-uid", after
    _report(reporter)

    assert [r["game_uid"] for r in _lines(before)] == ["old-uid"]
    assert [r["game_uid"] for r in _lines(after)] == ["new-uid"]


def test_the_freeze_handler_follows_an_identity_mutated_after_construction(tmp_path):
    before, after = tmp_path / "old.jsonl", tmp_path / "new.jsonl"
    identity = GameIdentity(game_uid="old-uid", log_path=before)
    on_freeze = make_freeze_handler(
        before, game_uid="old-uid", role="police",
        threshold_seconds=_THRESHOLD, identity=identity,
    )

    on_freeze()
    identity.game_uid, identity.log_path = "new-uid", after
    on_freeze()

    assert [r["game_uid"] for r in _lines(before)] == ["old-uid"]
    assert [r["game_uid"] for r in _lines(after)] == ["new-uid"]


def test_without_an_identity_both_sinks_behave_exactly_as_before(tmp_path):
    """The default path: no identity supplied, so both closures keep using
    the values frozen at construction -- and a LATER-created GameIdentity
    naming a different file has no effect on them at all."""
    log = tmp_path / "frozen.jsonl"
    reporter = make_transition_reporter(log, game_uid="frozen-uid", role="thief")
    on_freeze = make_freeze_handler(
        log, game_uid="frozen-uid", role="thief", threshold_seconds=_THRESHOLD,
    )
    GameIdentity(game_uid="ignored", log_path=tmp_path / "ignored.jsonl")

    _report(reporter)
    on_freeze()

    records = _lines(log)
    assert [r["game_uid"] for r in records] == ["frozen-uid", "frozen-uid"]
    assert [r["event"] for r in records] == ["illegal_transition", "watchdog_incident"]
    assert not (tmp_path / "ignored.jsonl").exists()


def test_negotiated_game_id_is_the_one_d61_policy():
    """Police keeps its own; the thief adopts the initiator's, falling back
    to its own when the peer published none. This is the ONLY definition --
    `agent_audit_wiring._declared_game_id` was deleted, not copied."""
    assert negotiated_game_id("police", "ours", "theirs") == "ours"
    assert negotiated_game_id("police", "ours", None) == "ours"
    assert negotiated_game_id("thief", "ours", "theirs") == "theirs"
    assert negotiated_game_id("thief", "ours", None) == "ours"
