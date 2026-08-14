"""D-67 audit RESULT type: one turn's outcome, and "did every one of them match".

Split out of `audit.py` at the 150-code-line gate (Segal Table 5) when 05-10's
peer-shape guards took that file to exactly 150 -- the same relocate-and-
re-export move `audit_state.py` and `audit_shape.py` already made out of it, and
that `deadline_errors.py`, `game_identity.py`, `secret_wiring.py` and
`agent_audit_verdict.py` made elsewhere. `audit.py` re-exports both names, so
every existing importer (`agent_audit_verdict`, `agent_audit_wiring`, the test
suite, `scripts/gate6_tamper.py`) resolves unchanged.

Landing at exactly 150/150 would have left the next change with nowhere to go
and no warning -- deferred item #2's situation, one line worse. Splitting the
leaf is what this codebase does instead of compressing code to fit.

A dependency-free leaf on purpose: it imports nothing from `pursuit`, so the
result type never drags `commit_pack` or the state binding into a caller that
only wants to read a verdict.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditRecord:
    """One turn's audit outcome."""

    turn: int
    matched: bool
    detail: str


def all_matched(records: list[AuditRecord]) -> bool:
    """True only when every record matched (vacuously True for an empty list)."""
    return all(record.matched for record in records)
