"""A real two-peer game -> `log_<game_id>_g<NN>.json` -> 100% re-hash WITH BOTH
SOURCES DELETED (07-05 Task 2, REPORT-06/09, rule 20).

Deleting the `.jsonl` and the `.ledger.jsonl` before verifying is the whole
point: a test that leaves them on disk proves nothing about self-containment,
and self-containment is what 07-08's replay viewer depends on.
"""

from __future__ import annotations

import asyncio
import json

from pursuit.network.agent_audit_wiring import run_final_audit
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.turn_commit_ledger import ledger_path_for
from pursuit.services.reporting.artifact_log import (
    LogArtifactField,
    verify_log_artifact,
    verify_log_turns,
    write_log_artifact,
)
from pursuit.services.reporting.artifacts import log_filename
from pursuit.services.reporting.log_join import GAME_OVER_EVENT, LANGUAGE_TURN_EVENT
from pursuit.services.reporting.log_turn_fields import (
    LANGUAGE_INTERNAL_FIELDS,
    TurnField,
    WireSide,
)
from tests.integration.two_peer_game import play_two_peer_game

GAME_UID = "logartifactroundtrip"
GAME_ID = "logroundtrip"
SUB_GAME_INDEX = 1


async def _play(tmp_path, monkeypatch, uid):
    """One real recorded game on the shipped configs, THEN the final audit --
    the order `agent_entrypoint.run_agent` uses (turn loop, audit, and only
    then the artifact). Without the audit leg there is no `audit_verdict`
    record to carry, which is the whole reason this builder runs at game end.
    Returns the police context."""
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
    return ctx_a


async def test_the_artifact_verifies_with_both_sources_deleted(tmp_path, monkeypatch):
    """The plan's five steps, in this order and no other."""
    ctx = await _play(tmp_path, monkeypatch, GAME_UID)
    events = [json.loads(line) for line in ctx.log_path.read_text(encoding="utf-8").splitlines()]
    assert {LANGUAGE_TURN_EVENT, GAME_OVER_EVENT} <= {e["event"] for e in events}

    path = write_log_artifact(
        tmp_path / "game_artifacts", ctx.log_path,
        game_uid=GAME_UID, game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX,
    )
    assert path.name == log_filename(GAME_ID, SUB_GAME_INDEX)

    ledger = ledger_path_for(ctx.log_path)
    assert ctx.log_path.exists() and ledger.exists()
    ctx.log_path.unlink()
    ledger.unlink()
    assert not ctx.log_path.exists() and not ledger.exists()

    assert verify_log_artifact(path)
    artifact = json.loads(path.read_text(encoding="utf-8"))
    verified, committed = verify_log_turns(artifact)
    # Step 5's guard, and it is not decoration: `all(...)` over an empty
    # sequence is True, and `audit_record.all_matched([])` returning True is
    # this repository's own canonical instance of that trap.
    assert committed > 0, "an artifact with no committed turn cannot prove anything"
    assert verified == committed
    # The ledger is the only source of a committed turn, so this is also the
    # check that the join found every one of them rather than a convenient few.
    assert committed == len(artifact[LogArtifactField.TURNS]) - 1


async def test_the_artifact_carries_hints_verdict_and_no_internal_state(tmp_path, monkeypatch):
    """The hint (with its rule-25 intent flag), the game's `audit_verdict`, and
    the rules 8-9 absence scan -- on a REAL game rather than a fixture."""
    ctx = await _play(tmp_path, monkeypatch, f"{GAME_UID}b")
    path = write_log_artifact(
        tmp_path / "game_artifacts", ctx.log_path,
        game_uid=f"{GAME_UID}b", game_id=f"{GAME_ID}b", sub_game_index=SUB_GAME_INDEX,
    )
    artifact = json.loads(path.read_text(encoding="utf-8"))

    hints = [t[TurnField.HINT][WireSide.OUTGOING] for t in artifact[LogArtifactField.TURNS]]
    present = [h for h in hints if h is not None]
    assert len(present) > 0
    assert all(sorted(h) == ["intent", "text"] for h in present)
    assert any(h["intent"] in {"truth", "lie"} for h in present)

    assert artifact[LogArtifactField.AUDIT_VERDICT] is not None
    assert artifact[LogArtifactField.AUDIT_VERDICT]["matched"] is True
    assert artifact[LogArtifactField.OUTCOME] is not None
    assert artifact[LogArtifactField.TRUNCATED_TAIL] == {"log": False, "ledger": False}

    serialized = path.read_text(encoding="utf-8")
    assert len(LANGUAGE_INTERNAL_FIELDS) == 6
    leaked = sorted(name for name in LANGUAGE_INTERNAL_FIELDS if name in serialized)
    assert leaked == [], f"rules 8-9: internal state in the artifact: {leaked}"
    # The counter-control: the same scan over a payload that DOES carry the
    # field finds it, so the empty result above is a measurement.
    assert "belief_argmax" in json.dumps({"belief_argmax": [5, 3]})


async def test_the_peers_claimed_turns_are_carried_verbatim_from_a_real_game(
    tmp_path, monkeypatch
):
    """The peer's stamped envelope turn survives into the artifact unaltered,
    for every received envelope of a real game -- so a third party can see what
    the peer claimed as well as where this side filed it.

    Recomputed independently from the raw events rather than asserted against a
    shape, and floored on a non-zero count so a builder that recorded nothing
    fails instead of passing on an empty comparison.
    """
    ctx = await _play(tmp_path, monkeypatch, f"{GAME_UID}c")
    events = [json.loads(line) for line in ctx.log_path.read_text(encoding="utf-8").splitlines()]
    expected: dict = {}
    for event in events:
        if event["event"] == "message_received" and "envelope" in event:
            expected.setdefault(event["turn"], {})[event["envelope"]["type"]] = (
                event["envelope"]["turn"]
            )
    assert sum(len(kinds) for kinds in expected.values()) > 0

    path = write_log_artifact(
        tmp_path / "game_artifacts", ctx.log_path,
        game_uid=f"{GAME_UID}c", game_id=f"{GAME_ID}c", sub_game_index=SUB_GAME_INDEX,
    )
    artifact = json.loads(path.read_text(encoding="utf-8"))
    claimed = {
        turn[TurnField.TURN]: turn[TurnField.PEER_CLAIMED_TURNS]
        for turn in artifact[LogArtifactField.TURNS]
        if turn[TurnField.PEER_CLAIMED_TURNS]
    }
    assert claimed == expected
