"""05-UAT.md G1 missing[4]: a late peer still completes with a matched
verdict against a peer that has already finished and torn down.

This is the test that would have caught the bug that cost the 2026-08-13
round: machine B declared machine A `opponent_unresponsive` while A had
already received and processed B's push, and B itself ended with no
verdict at all. The harness (`late_peer_harness.py`, split at the 150-line
gate) explains why a NEW harness was needed and what pairs with it to keep
it honest; read that file's docstring first.
"""

from __future__ import annotations

import json

import pytest

from pursuit.constants import Outcome
from tests.integration.late_peer_harness import late_peer_round


def _events(ctx) -> list[dict]:
    text = ctx.log_path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _of_kind(ctx, kind: str) -> list[dict]:
    return [event for event in _events(ctx) if event.get("event") == kind]


@pytest.fixture
def _no_llm_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


async def test_a_late_peer_still_completes_against_a_torn_down_peer(tmp_path, _no_llm_key):
    """The whole of G1, on real loopback sockets, in one sequence."""
    round_result = await late_peer_round(tmp_path, linger=True)
    ctx_a, ctx_b = round_result["ctx_a"], round_result["ctx_b"]
    assert round_result["peer_error"] is None, round_result["peer_error"]

    # 1. B ends with a matched audit_verdict -- not nothing at all, which
    #    is what the real round produced.
    verdicts_b = _of_kind(ctx_b, "audit_verdict")
    assert verdicts_b, "the late peer recorded no verdict at all -- the 2026-08-13 artifact"
    assert all(v["matched"] for v in verdicts_b)
    assert _of_kind(ctx_a, "audit_verdict"), "the early finisher recorded no verdict either"

    # 2. Neither side accuses the other of being unresponsive.
    for ctx in (ctx_a, ctx_b):
        reasons = [w.get("reason") for w in _of_kind(ctx, "technical_win")]
        assert "opponent_unresponsive" not in reasons, f"{ctx.role} falsely accused its peer"

    # A strengthening of assertion 1, and the part the LINGER specifically
    # buys: B's own push actually landed, so there is no audit_incomplete
    # evidence-about-us record either.
    assert not _of_kind(ctx_b, "audit_incomplete"), "the late peer's own push was cut off"

    # 3. The two verdicts AGREE, and each side's LAST game_over record
    #    matches the outcome that side returns (the 2026-08-13 round had
    #    B's log ending on game_over=capture while its process exited 1).
    assert round_result["final_a"] == round_result["final_b"]
    assert round_result["final_a"] is not Outcome.TECHNICAL_LOSS
    for ctx, final in ((ctx_a, round_result["final_a"]), (ctx_b, round_result["final_b"])):
        game_overs = _of_kind(ctx, "game_over")
        assert game_overs, f"{ctx.role} left no outcome-bearing record"
        assert game_overs[-1]["outcome"] == final.value


async def test_without_the_linger_the_late_peers_own_push_is_cut_off(tmp_path, _no_llm_key):
    """NON-VACUITY, pinned permanently rather than run once and discarded.

    The SAME sequence with `linger=False` -- the pre-05-04 teardown. What
    it reproduces is the 2026-08-13 shape exactly: A dequeues and processes
    B's push, completes a matched audit, and closes its listener before B's
    client is done with the session, so B's own push comes back a failure.

    The two branches differ by `linger_for_peer` ALONE. That is what makes
    this pair a real non-vacuity proof rather than two differently-shaped
    runs, and it is only true because the harness now HOLDS A's
    FINAL_REVEAL handler open (`late_peer_gate.py`) until A's teardown has
    committed its `task.cancel()`. "A's listener closed while B's push was
    in flight" is therefore a fact of PROGRAM ORDER, not of the scheduler:
    before 2026-08-17 it was a sub-tick coin flip on one event loop and
    this control failed roughly one run in three (deferred-items.md #4).

    Asserted as "B's own push did not land", NOT as "it raises
    ConnectError": deferred-items.md #1 is closed, so the measured shape
    here is now the contained, non-accusatory
    `audit_incomplete{reason: own_final_reveal_send_failed}` with
    `peer_error is None` -- which that item anticipated and this assertion
    was deliberately written to survive. If BOTH are ever absent, the
    linger has stopped being load-bearing and this file is testing nothing.
    """
    round_result = await late_peer_round(tmp_path, linger=False)
    ctx_b = round_result["ctx_b"]

    cut_off = round_result["peer_error"] is not None or bool(_of_kind(ctx_b, "audit_incomplete"))
    assert cut_off, "the late peer's push succeeded WITHOUT a linger -- harness proves nothing"
    # Whatever else happened, the sanction must not misfire: a peer that
    # was demonstrably alive is never declared unresponsive (rules 16/22).
    reasons = [w.get("reason") for w in _of_kind(ctx_b, "technical_win")]
    assert "opponent_unresponsive" not in reasons
