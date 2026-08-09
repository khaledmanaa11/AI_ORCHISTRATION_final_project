"""Criterion-3 evidence: a live Step-0 mismatch -- a forged local step0
digest on one side -- proving `HandshakeOutcome.STEP0_MISMATCH` fires and
the detecting side's machine aborts to `State.ERROR` before move 1 is ever
reachable. Mirrors tests/unit/test_handshake_step0.py's own unit proof,
"live" here because both declarations are REAL `declare_step0`-collected
hardware declarations (git commit hash, psutil OS/CPU/RAM, best-effort
GPU) rather than a hand-built fixture, and the evaluating side's
machine/reporter are the SAME production `default_context`-built objects
a real game would use. Only the actual FastMCP round trip is skipped:
`respond_to_handshake` is called directly, exactly as `perform_handshake`
calls it internally once a reply arrives over the wire -- a synchronous,
in-process function call either way, never a network difference.

A Step-0 declaration is inherently per-agent (D-62): forging POLICE's
digest is detected by whichever side RECEIVES the forged claim, so this
measurement evaluates it from THIEF's own responder side.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from gate6_common import load_configs

from pursuit.network import agent_lifecycle
from pursuit.network.agent_audit_wiring import declare_step0
from pursuit.network.config_hash import config_digest
from pursuit.network.handshake import HandshakeOutcome, respond_to_handshake
from pursuit.network.handshake_wire import build_offer
from pursuit.network.state_machine import State

GAME_UID = "gate6-step0-mismatch"


def _forge(digest: str) -> str:
    """Flip the leading hex character -- still a well-formed 64-char hex
    string, just not the true hash of the genuine declaration content."""
    return ("1" if digest[0] == "0" else "0") + digest[1:]


async def measure_step0_mismatch() -> dict:
    cfg_a, cfg_b = load_configs()
    step0_digest_a, decl_a = await declare_step0(cfg_a)
    step0_digest_b, decl_b = await declare_step0(cfg_b)
    forged_digest_a = _forge(step0_digest_a)
    assert forged_digest_a != step0_digest_a

    with tempfile.TemporaryDirectory() as tmp:
        ctx_b = agent_lifecycle.default_context(
            cfg_b, game_uid=GAME_UID, log_path=Path(tmp) / "thief" / "b.jsonl",
            local_step0_digest=step0_digest_b, local_game_id=GAME_UID,
            local_step0_declaration=decl_b,
        )
        local_digest = config_digest(cfg_a.config_dir / "game_params.json")
        forged_offer = build_offer(
            local_digest, "police", local_step0_digest=forged_digest_a,
            local_game_id=GAME_UID, local_step0_declaration=decl_a,
        ).to_dict()

        _reply, result_b = respond_to_handshake(
            machine=ctx_b.machine, reporter=ctx_b.reporter, local_digest=local_digest,
            local_role=ctx_b.role, incoming=forged_offer,
            local_step0_digest=step0_digest_b, local_game_id=GAME_UID,
            local_step0_declaration=decl_b,
        )
        move_1_attempt = ctx_b.machine.attempt(State.MY_TURN)

        return {
            "forged_side": "police",
            "detecting_side": "thief",
            "outcome": result_b.outcome.value,
            "is_step0_mismatch": result_b.outcome is HandshakeOutcome.STEP0_MISMATCH,
            "aborted_to_error_state": result_b.aborted,
            "machine_state": ctx_b.machine.state.value,
            "detail": result_b.detail,
            "move_1_unreachable_after_abort": not move_1_attempt.accepted,
            "run_turn_loop_ever_called": False,
        }
