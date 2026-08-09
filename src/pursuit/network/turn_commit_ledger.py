"""D-59/D-64: build the committed action payload, hash it, and durably
append the full `{state, move, intent, nonce}` record to THIS side's own
`CommitLedger` -- all before any network send.

Split out of `turn_commit_wait.py` at the 150-code-line gate (Segal
Table 5), pre-authorized by 06-05-PLAN.md, once the Gap-1 turn-binding
fix pushed that file to 156. The split is along the seam the file's own
docstring already described: the WAIT primitives stay in
`turn_commit_wait.py`, the commit+ledger mechanics live here -- the same
policy-vs-mechanism division `handshake.py`/`handshake_wire.py` and
`turn_commit.py`/`turn_commit_send.py` already follow.

`ledger_path` lands here as the ONE definition of D-64's
`<log-file-stem>.ledger.jsonl` convention. It previously existed as two
private copies (`turn_commit_wait._ledger_path` and
`agent_audit_wiring._ledger_path`); both now import this one, per the
no-duplication rule. The writer (`commit_own_action`, below) and the
reader (`agent_audit_wiring.run_final_audit`) can no longer drift apart
on where a game's nonces live.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.network import move_payload
from pursuit.network.agent_context import AgentContext, Coord
from pursuit.security import commit_pack
from pursuit.security.ledger import CommitLedger
from pursuit.security.state_record import build_state_record


def ledger_path(ctx: AgentContext) -> Path:
    """D-64's `<log-file-stem>.ledger.jsonl` sibling convention -- e.g.
    `logs/police/<uid>.jsonl` -> `logs/police/<uid>.ledger.jsonl`."""
    return ctx.log_path.parent / f"{ctx.log_path.stem}.ledger.jsonl"


def build_action_payload(pre_cell: Coord, dest: Coord, barrier: Coord | None) -> dict:
    """D-59/D-66's composite action dict. `move` is always present -- a
    real step, or a "stay" token (mirroring `CopAction.destination()`'s own
    "unchanged when placing") when a barrier is placed instead; `barrier`
    is present only then. Never both `move`-as-real-step AND `barrier` --
    matches `CopAction`'s own move-XOR-barrier invariant."""
    move_dest = pre_cell if barrier is not None else dest
    payload = {"move": move_payload.encode(pre_cell, move_dest, move_payload.ActionKind.MOVE), "barrier": None}
    if barrier is not None:
        payload["barrier"] = move_payload.encode(pre_cell, barrier, move_payload.ActionKind.BARRIER)
    return payload


def commit_own_action(
    ctx: AgentContext, *, pre_cell: Coord, dest: Coord, barrier: Coord | None,
    intent: str, turn: int,
) -> tuple[str, dict]:
    """Build + commit + durably ledger-append THIS side's own action for
    *turn*, all before any send. Returns `(h_commit, action_payload)` --
    `action_payload` is the exact dict this side later reveals verbatim.

    *turn* is this side's own pre-resolve turn, supplied by the caller --
    the SAME number the corresponding COMMIT/REVEAL envelopes are sent
    under and the SAME number the audit's evidence dicts are keyed on
    (06-05, Gap 1), so a game's ledger, its wire log, and its final reveal
    all agree on one turn numbering that no peer can influence."""
    action_payload = build_action_payload(pre_cell, dest, barrier)
    barriers_remaining = ctx.params.barrier_quota - ctx.state.barriers_placed
    state_record = build_state_record(
        game_id=ctx.game_uid, turn=turn, role=ctx.role,
        position=pre_cell, barriers_remaining=barriers_remaining,
    )
    h_commit, nonce = commit_pack.commit(state_record, action_payload, intent)
    payload = commit_pack.build_commit_payload(
        state=state_record, move=action_payload, intent=intent, nonce=nonce,
    )
    CommitLedger(ledger_path(ctx)).append(turn=turn, h_commit=h_commit, payload=payload)
    return h_commit, action_payload
