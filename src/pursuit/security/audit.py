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


@dataclass(frozen=True)
class AuditRecord:
    """One turn's audit outcome."""

    turn: int
    matched: bool
    detail: str


def _audit_one(
    entry: dict, observed_commits: dict[int, str], observed_reveals: dict[int, dict],
) -> AuditRecord:
    """Per-entry checks, in order; the FIRST failing check's detail is
    reported -- never computed-but-hidden. See module docstring for why a
    trailing commit-without-reveal is `matched=True`, not a mismatch."""
    turn = entry["turn"]
    if turn not in observed_commits:
        return AuditRecord(turn=turn, matched=False, detail=f"turn {turn}: no observed commit")
    if not commit_pack.verify_reveal(observed_commits[turn], **entry["payload"]):
        return AuditRecord(
            turn=turn, matched=False, detail=f"turn {turn}: re-hash does not match H_commit",
        )
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
) -> list[AuditRecord]:
    """Audit every `peer_records` entry (`{"turn","h_commit","payload":
    {"state","move","intent","nonce"}}`) against what THIS side observed on
    the wire, PLUS the coverage check above. A genuinely turn-less game
    (nothing fully exchanged, nothing claimed) returns an empty list --
    vacuously matched, correctly (a game that died at handshake has
    nothing to audit)."""
    records = [_audit_one(entry, observed_commits, observed_reveals) for entry in peer_records]
    records.extend(_missing_turns(observed_commits, observed_reveals, peer_records))
    records.sort(key=lambda record: record.turn)
    return records


def all_matched(records: list[AuditRecord]) -> bool:
    """True only when every record matched (vacuously True for an empty list)."""
    return all(record.matched for record in records)
