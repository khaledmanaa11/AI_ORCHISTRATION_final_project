"""D-67: the Final-Reveal mutual audit.

Hash-verifying a revealed `{state,move,intent,nonce}` payload against
`H_commit` ALONE is bypassable: commit honestly to X, play Y in the
in-game REVEAL, present X at final reveal -- the hash matches and the
forgery survives. `audit_peer_records` closes this by ALSO cross-checking
the revealed composite action dict against the action THIS SIDE actually
observed in that turn's in-game REVEAL envelope (its own wire log).

Pure function, no network, no ctx (Task 3's own contract) -- Task 4 wires
this against real `observed_commits`/`observed_reveals`/`peer_records`
built from `ctx.log_path`'s own JSONL and this side's own `CommitLedger`.
The SAME function also audits THIS side's own ledger against what it
actually sent (CONTEXT, locked: symmetric honesty) -- only the caller's
sent/received direction differs.
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
    """The three D-67 checks, in order; the FIRST failing check's detail is
    reported -- never computed-but-hidden."""
    turn = entry["turn"]
    if turn not in observed_commits:
        return AuditRecord(turn=turn, matched=False, detail=f"turn {turn}: no observed commit")
    if not commit_pack.verify_reveal(observed_commits[turn], **entry["payload"]):
        return AuditRecord(
            turn=turn, matched=False, detail=f"turn {turn}: re-hash does not match H_commit",
        )
    if turn not in observed_reveals:
        return AuditRecord(turn=turn, matched=False, detail=f"turn {turn}: no observed reveal")
    if entry["payload"]["move"] != observed_reveals[turn]:
        return AuditRecord(
            turn=turn, matched=False,
            detail=f"turn {turn}: revealed action does not match what was actually played (D-67)",
        )
    return AuditRecord(turn=turn, matched=True, detail=f"turn {turn}: matched")


def audit_peer_records(
    observed_commits: dict[int, str], observed_reveals: dict[int, dict], peer_records: list[dict],
) -> list[AuditRecord]:
    """Audit every `peer_records` entry (`{"turn","h_commit","payload":
    {"state","move","intent","nonce"}}`) against what THIS side observed on
    the wire. A turn present in `peer_records` but absent from
    `observed_commits`/`observed_reveals` is itself a mismatch, never
    silently skipped."""
    return [_audit_one(entry, observed_commits, observed_reveals) for entry in peer_records]


def all_matched(records: list[AuditRecord]) -> bool:
    """True only when every record matched (vacuously True for an empty list)."""
    return all(record.matched for record in records)
