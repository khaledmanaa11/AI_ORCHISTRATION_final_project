"""How this side reads its OWN observed commit/reveal history back off its
wire log (D-67) -- split VERBATIM from `agent_audit_exchange.py` at the
150-code-line gate (Segal Table 5) when 05-15's receive-leg envelope-type
loop took that file to 153.

Split, never compressed, and split along the seam that module's own
docstring already named: it declared itself as holding "how to push/receive
one FINAL_REVEAL envelope" AND "how to read this side's own observed
commit/reveal history from its wire log". The second half is here now; the
first half stays there. Same precedent as `agent_audit_verdict.py` (06-05)
and `agent_step0_wiring.py` (05-13), and `observed` is re-exported from
`agent_audit_exchange` unchanged, so `agent_audit_wiring.py`, the gate
scripts and the test suite all resolve it exactly where they did before.

Not one character of the function body changed in the move.
"""

from __future__ import annotations

import json

from pursuit.network.agent_context import AgentContext
from pursuit.network.envelope import EnvelopeKey, MessageType
from pursuit.network.event_log import EventField
from pursuit.network.turn_commit_wait import H_COMMIT_KEY

__all__ = ["observed"]


def _read_log(ctx: AgentContext) -> list[dict]:
    if not ctx.log_path.exists():
        return []
    with ctx.log_path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def observed(ctx: AgentContext, *, direction: str) -> tuple[dict[int, str], dict[int, dict]]:
    """Build (observed_commits, observed_reveals) from ctx.log_path's own
    JSONL, filtered to *direction* ("message_sent" or "message_received").
    Sent = this side's own self-check evidence; received = what this side
    actually saw the opponent do (D-67).

    Both dicts are keyed on the RECORD's own top-level turn -- a number
    THIS side stamped (`turn_commit_send.log_received`'s `local_turn`,
    `turn_actions.await_opponent_turn`'s pre-resolve `observed_turn`, and
    our own `send_and_log` turn on the sent side) -- never on the nested
    `envelope`'s turn, which on the received side is whatever the peer
    chose to claim.

    That distinction is load-bearing, not cosmetic. Keying on the peer's
    own number let an adversary stamp its COMMIT and REVEAL envelopes with
    disjoint turns, which (1) emptied `audit.audit_peer_records`'s
    `set(commits) & set(reveals)` coverage intersection, re-opening the
    `{"records": []}` rule-36 evasion, and (2) sent every entry down the
    trailing-commit exemption, so the D-67 revealed-vs-played check never
    fired. Found at /gsd:verify-work 6 and reproduced with paired
    controls; see 06-UAT.md Gap 1 and tests/unit/test_audit_turn_binding.py.

    The nested envelope is still read for its type and payload, and is
    still stored verbatim, so the peer's claimed turn remains on record as
    evidence.

    05-15: a `message_received` GAME_OVER record (the peer's rule-21
    Capture Claim, logged by `capture_declaration.record_received_declaration`)
    is invisible here by construction -- only COMMIT and REVEAL envelope
    types are read, so the new record cannot perturb either audit direction.
    """
    commits: dict[int, str] = {}
    reveals: dict[int, dict] = {}
    for record in _read_log(ctx):
        if record.get(EventField.EVENT) != direction:
            continue
        envelope = record.get(EventField.ENVELOPE)
        if envelope is None:
            continue
        turn = record.get(EventField.TURN)
        payload = envelope.get(EnvelopeKey.PAYLOAD, {})
        if envelope.get(EnvelopeKey.TYPE) == MessageType.COMMIT.value:
            commits[turn] = payload.get(H_COMMIT_KEY)
        elif envelope.get(EnvelopeKey.TYPE) == MessageType.REVEAL.value:
            reveals[turn] = payload
    return commits, reveals
