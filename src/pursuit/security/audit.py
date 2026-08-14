"""D-67: the Final-Reveal mutual audit.

Hash-verifying a revealed `{state,move,intent,nonce}` payload against
`H_commit` ALONE is bypassable: commit honestly to X, play Y in the
in-game REVEAL, present X at final reveal -- the hash matches and the
forgery survives. `audit_peer_records` closes this by ALSO cross-checking
the revealed composite action dict against the action THIS SIDE actually
observed in that turn's in-game REVEAL envelope (its own wire log).

Rule 36 coverage check: auditing only the entries the PEER chose to
include is itself bypassable -- an opponent sending `{"records": []}`
(the cheapest possible evasion) would otherwise pass vacuously.
`audit_peer_records` ALSO requires every turn THIS side watched fully
exchanged (committed AND revealed in-game) to be present in
`peer_records` at all; a missing one is a mismatch, not a silent skip.

A turn with an observed COMMIT but no observed REVEAL is a legitimately
TRAILING turn, not evidence of anything: `CommitLedger.append` runs
BEFORE the REVEAL send (turn_commit_wait.py), so an abnormal ending can
leave an honest peer with a committed-never-revealed entry in its own
final reveal. Such an entry is `matched=True` once its commit/hash check
out -- there is nothing played that turn to cross-check against.

D-60 committed-state binding (05-05, 05-UAT.md G2): `_audit_one` also reads
`payload.state` -- the peer's own committed record -- and rejects a replay
whose `turn`, `role` or `game_id` disagrees with local truth. That check and
ALL of its reasoning (why `game_id` is checked by MEMBERSHIP in this game's
candidate ids rather than by equality with one of them, and the THREE stated
limitations of that choice) live in the sibling `audit_state.py`, split out
at the 150-code-line gate the moment they landed here. Read that file before
changing the check: two equality shapes were tried and both false-accuse an
honest peer (rules 16/22).

Pure function, no network, no ctx (Task 3's own contract) -- Task 4 wires
this against real `observed_commits`/`observed_reveals`/`peer_records`
built from `ctx.log_path`'s own JSONL and this side's own `CommitLedger`.
The SAME function also audits THIS side's own ledger against what it
actually sent (CONTEXT, locked: symmetric honesty) -- only the caller's
sent/received direction differs; the coverage check applies identically
in both directions, no special-casing needed.
"""

from __future__ import annotations

from dataclasses import dataclass

from pursuit.security import commit_pack
from pursuit.security.audit_state import state_binding_detail


@dataclass(frozen=True)
class AuditRecord:
    """One turn's audit outcome."""

    turn: int
    matched: bool
    detail: str


def _audit_one(
    entry: dict, observed_commits: dict[int, str], observed_reveals: dict[int, dict],
    *, candidate_game_ids: set[str] | None, forbidden_role: str | None,
) -> AuditRecord:
    """Per-entry checks, in order; the FIRST failing check's detail is
    reported -- never computed-but-hidden. See module docstring for why a
    trailing commit-without-reveal is `matched=True`, not a mismatch."""
    turn = entry["turn"]
    if turn not in observed_commits:
        return AuditRecord(turn=turn, matched=False, detail=f"turn {turn}: no observed commit")
    # `verify_reveal(h, **payload)` requires EXACTLY {state,move,intent,nonce}
    # with state/move dicts, so any other shape raises out of a function
    # running on PEER-SUPPLIED data -- and nothing upstream catches TypeError
    # (`agent_entrypoint`'s guard is `except ToolError`), so the process would
    # die before recording any verdict and WE would become the side that
    # published no nonces (rule 36). A malformed payload is evidence, so it
    # becomes a named mismatch here rather than an exception. This is the one
    # production call site that sees peer data (grep: the only other caller is
    # scripts/gate6_tamper.py, over records it built itself).
    try:
        rehash_ok = commit_pack.verify_reveal(observed_commits[turn], **entry["payload"])
    except (TypeError, KeyError) as exc:
        return AuditRecord(
            turn=turn, matched=False,
            detail=f"turn {turn}: malformed final-reveal payload -- {exc}",
        )
    if not rehash_ok:
        return AuditRecord(
            turn=turn, matched=False, detail=f"turn {turn}: re-hash does not match H_commit",
        )
    # PLACEMENT IS EXACT: after the re-hash and BEFORE the trailing-commit
    # early return below. Placed after it, a replayed record would take the
    # trailing-commit exemption -- matched=True -- and skip the state checks
    # entirely, which is the exact shape of the bug 06-05 already fixed once.
    state_detail = state_binding_detail(
        entry, candidate_game_ids=candidate_game_ids, forbidden_role=forbidden_role,
    )
    if state_detail is not None:
        return AuditRecord(turn=turn, matched=False, detail=state_detail)
    if turn not in observed_reveals:
        return AuditRecord(
            turn=turn, matched=True,
            detail=f"turn {turn}: trailing commit, no in-game reveal observed -- hash verified",
        )
    if entry["payload"]["move"] != observed_reveals[turn]:
        return AuditRecord(
            turn=turn, matched=False,
            detail=f"turn {turn}: revealed action does not match what was actually played (D-67)",
        )
    return AuditRecord(turn=turn, matched=True, detail=f"turn {turn}: matched")


def _missing_turns(
    observed_commits: dict[int, str], observed_reveals: dict[int, dict], peer_records: list[dict],
) -> list[AuditRecord]:
    """Rule 36 coverage check: a turn watched FULLY exchanged (committed
    AND revealed in-game) but simply absent from `peer_records` -- e.g.
    every turn, via an empty `{"records": []}` -- is itself a mismatch."""
    reported = {entry["turn"] for entry in peer_records}
    fully_exchanged = set(observed_commits) & set(observed_reveals)
    return [
        AuditRecord(
            turn=turn, matched=False,
            detail=f"turn {turn}: committed and revealed in-game but absent from final reveal",
        )
        for turn in sorted(fully_exchanged - reported)
    ]


def audit_peer_records(
    observed_commits: dict[int, str], observed_reveals: dict[int, dict], peer_records: list[dict],
    *, candidate_game_ids: set[str] | None = None, forbidden_role: str | None = None,
) -> list[AuditRecord]:
    """Audit every `peer_records` entry (`{"turn","h_commit","payload":
    {"state","move","intent","nonce"}}`) against what THIS side observed on
    the wire, PLUS the coverage check above. A genuinely turn-less game
    (nothing fully exchanged, nothing claimed) returns an empty list --
    vacuously matched, correctly (a game that died at handshake has
    nothing to audit).

    *candidate_game_ids* and *forbidden_role* (05-05) enable the two
    OPTIONAL halves of the committed-state binding; both default to None
    (that half skipped), so every pre-existing caller and fixture is
    untouched. `state.turn == entry["turn"]` needs no parameter and is
    ALWAYS enforced: `commit_own_action` passes ONE `turn` to both the
    record and the append, so it holds for every honest ledger by
    construction. `agent_audit_wiring.run_final_audit` is the production
    supplier -- the SAME `ctx.candidate_game_ids` set for both directions,
    passed through unchanged and never reconstructed, with `forbidden_role`
    the only per-direction difference."""
    records = [
        _audit_one(
            entry, observed_commits, observed_reveals,
            candidate_game_ids=candidate_game_ids, forbidden_role=forbidden_role,
        )
        for entry in peer_records
    ]
    records.extend(_missing_turns(observed_commits, observed_reveals, peer_records))
    records.sort(key=lambda record: record.turn)
    return records


def all_matched(records: list[AuditRecord]) -> bool:
    """True only when every record matched (vacuously True for an empty list)."""
    return all(record.matched for record in records)
