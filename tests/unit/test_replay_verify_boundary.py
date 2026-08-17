"""The boundary rule, on a file an adversary may have written.

`security/audit.py:56-124` lists SIX production defects from one pattern: an
unhandled exception on data we did not produce. A viewer that CRASHES on a
tampered artifact shows no verdict at all, which is strictly worse than
showing `FAILED` -- the grader sees a traceback and cannot tell a forgery from
a bug in our reader. Instance 5 of that list is exactly the shape below: a
`ValueError` from `build_commit_payload` on an intent outside {truth, lie},
which escaped a narrower `(TypeError, KeyError)` clause in production.

Also here: the seal, which covers what the per-turn hashes cannot; and the
refusal that keeps this viewer off a live game's files (rule 18).
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest

from pursuit.services.reporting.replay_verify import (
    VERIFIED_OK,
    VerdictState,
    check_turn,
    load_artifact,
    open_replay,
    seal_matches,
    verdict_for,
)
from tests.unit import replay_fixtures as fx

TAMPER_INDEX = 1
TAMPER_TURN = 1
LIVE_LOG_NAME = "521519a78f96c255.jsonl"
LIVE_LEDGER_NAME = "521519a78f96c255.ledger.jsonl"

REPORTING = pathlib.Path(__file__).parents[2] / "src" / "pursuit" / "services" / "reporting"
REPLAY_MODULES = ("replay_verdict", "replay_session", "replay_source", "replay_verify")
#: Names a READER must never bind. `write_log_artifact`/`build_log_artifact`
#: are the game-end builder (D-64, D7-14: `end_of_game.py` is its ONE
#: production caller); `join_game` and `CommitLedger` reach the live sources.
FORBIDDEN_BINDINGS = frozenset(
    {"write_log_artifact", "build_log_artifact", "join_game", "CommitLedger", "read_all"}
)


def _broken(field: str, value: object) -> dict:
    body = fx.artifact()
    body[fx.LogArtifactField.TURNS][TAMPER_INDEX][field] = value
    return fx.reseal(body)


def _assert_contained(verdict) -> None:
    assert verdict.state is VerdictState.FAILED
    assert verdict.banner != VERIFIED_OK
    assert f"turn {TAMPER_TURN}" in verdict.banner, verdict.banner


def test_an_intent_outside_truth_or_lie_is_a_named_failure_not_a_crash():
    """`ValueError` -- audit boundary-rule instance 5, verbatim."""
    _assert_contained(verdict_for(_broken(fx.TurnField.INTENT, "maybe")))


def test_a_state_that_is_not_an_object_is_a_named_failure_not_a_crash():
    """`TypeError` -- boundary-rule instance 3."""
    _assert_contained(verdict_for(_broken(fx.TurnField.STATE, "not-a-dict")))


def test_an_empty_nonce_is_a_named_failure_not_a_crash():
    """`ValueError` again, by the other half of instance 5."""
    _assert_contained(verdict_for(_broken(fx.TurnField.NONCE, "")))


def test_a_payload_key_removed_altogether_is_a_named_failure_not_a_crash():
    """`KeyError`. The artifact promises five top-level names per turn; a
    file that drops one is malformed, not unverifiable-and-therefore-fine."""
    body = fx.artifact()
    del body[fx.LogArtifactField.TURNS][TAMPER_INDEX][fx.TurnField.MOVE]
    _assert_contained(verdict_for(fx.reseal(body)))


def test_a_turn_record_that_is_not_an_object_cannot_read_as_ok():
    body = fx.artifact()
    body[fx.LogArtifactField.TURNS][TAMPER_INDEX] = "not-a-turn"
    verdict = verdict_for(fx.reseal(body))
    assert verdict.state is VerdictState.FAILED and verdict.banner != VERIFIED_OK


def test_a_turns_value_that_is_not_a_list_is_nothing_to_verify_never_ok():
    body = fx.artifact()
    body[fx.LogArtifactField.TURNS] = {"turn": 0}
    verdict = verdict_for(fx.reseal(body))
    assert verdict.state is VerdictState.NOTHING_TO_VERIFY
    assert verdict.banner != VERIFIED_OK


def test_the_contained_exception_is_reported_rather_than_swallowed():
    """The detail must carry the exception's own words, or a third party is
    told only that something went wrong."""
    check = check_turn({**fx.committed_turn(TAMPER_TURN), fx.TurnField.INTENT: "maybe"})
    assert check.committed is True and check.ok is False
    assert "maybe" in check.detail and "malformed" in check.detail


def test_a_field_outside_the_committed_payloads_still_fails_the_verdict():
    """`outcome` is inside `SEALED_FIELDS` and inside NO commit hash. Every
    turn still re-hashes, and the artifact is still FAILED."""
    body = fx.artifact()
    body[fx.LogArtifactField.OUTCOME] = {"outcome": "survival", fx.TurnField.TURN: 99}
    verdict = verdict_for(body)
    assert verdict.verified == verdict.committed == fx.COMMITTED_TURNS
    assert verdict.state is VerdictState.FAILED and verdict.banner != VERIFIED_OK
    assert "seal" in verdict.banner


def test_the_seal_check_is_not_a_no_op():
    """The counter-control: it says True for the clean artifact, and False
    for a digest of the wrong length, an absent digest and a non-str one."""
    assert seal_matches(fx.artifact()) is True
    for digest in ("00" * 32, None, 17):
        body = fx.artifact()
        body[fx.LogArtifactField.LOG_DIGEST] = digest
        assert seal_matches(body) is False, digest
    del body[fx.LogArtifactField.LOG_DIGEST]
    assert seal_matches(body) is False


def test_a_live_wire_log_and_its_nonce_ledger_are_both_refused_by_name(tmp_path):
    """Rule 18 keeps nonces secret while a game is live, so the replay viewer
    is not permitted to open the two files a live game writes."""
    for name in (LIVE_LOG_NAME, LIVE_LEDGER_NAME, "result_x.json", "declaration_x.json"):
        path = tmp_path / name
        path.write_text("{}\n", encoding="utf-8")
        with pytest.raises(ValueError, match="replay viewer"):
            load_artifact(path)


def test_the_refusal_is_not_a_blanket_one(tmp_path):
    """The counter-control for the refusal above -- the artifact this viewer
    exists for loads, from the same directory, in the same call."""
    path = fx.write(tmp_path, fx.artifact())
    assert load_artifact(path)[fx.LogArtifactField.ROLE] == fx.ROLE
    assert open_replay(path).verdict.banner == VERIFIED_OK


def test_a_log_artifact_that_is_not_a_json_object_is_refused(tmp_path):
    path = tmp_path / "log_x_g01.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_artifact(path)


def test_no_replay_module_can_build_write_or_reach_around_the_artifact():
    """The viewer READS. It may not build or write a `log_` artifact (D-64
    keeps that at game end, and D7-14 records `end_of_game.py` as its one
    production caller), and it may not open the live sources the artifact was
    joined from. Asserted on the SYNTAX, because these modules discuss those
    names in their docstrings -- which is the point."""
    assert len(REPLAY_MODULES) == 4, "a thinned module list would scan almost nothing"
    bound: set[str] = set()
    for name in REPLAY_MODULES:
        tree = ast.parse((REPORTING / f"{name}.py").read_text(encoding="utf-8"))
        bound |= {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
    assert bound & FORBIDDEN_BINDINGS == set(), sorted(bound & FORBIDDEN_BINDINGS)
    # The control: the scan DOES see the one name these modules must bind.
    assert "verify_reveal" in bound, "the binding scan is inert"
