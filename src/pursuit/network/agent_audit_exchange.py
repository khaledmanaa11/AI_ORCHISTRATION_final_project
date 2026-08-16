"""D-67 wire mechanics for the Final-Reveal mutual audit -- split from
agent_audit_wiring.py at the 150-code-line gate (pre-authorized: this
plan's own must_haves anticipated agent_audit_wiring.py needing further
splitting, mirroring the handshake.py/turn_commit.py precedent). Holds
"how to push/receive one FINAL_REVEAL envelope" and "how to read this
side's own observed commit/reveal history from its wire log" --
agent_audit_wiring.py keeps only the two public entry points and policy
(declare_step0/write_declaration/run_final_audit).

"How to record an audit verdict" moved to the sibling
`agent_audit_verdict.py` when 06-05's Gap-2 fix took this file to 159 code
lines; both of its public names are re-exported below, so importers that
already reach for them here are unaffected.
"""

from __future__ import annotations

import json

from pursuit.network.agent_audit_verdict import (
    record_audit_incomplete,
    record_audit_verdict,
    record_technical_loss,
)
from pursuit.network.agent_context import AgentContext
from pursuit.network.deadline import call_with_retry
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.event_log import EventField
from pursuit.network.turn_commit_wait import H_COMMIT_KEY, next_protocol_message
from pursuit.network.verdict import TechnicalWin

_FINAL_REVEAL_TOOL = "receive_final_reveal"
_RECORDS_KEY = "records"

__all__ = [
    "observed",
    "push_final_reveal",
    "receive_final_reveal",
    "record_audit_incomplete",
    "record_audit_verdict",
    "record_technical_loss",
]


async def push_final_reveal(ctx: AgentContext, records: list[dict]) -> TechnicalWin | None:
    """Send THIS side's own ledger as one FINAL_REVEAL envelope, via the
    SAME call_with_retry ladder every other push uses (D-17, no new number).

    05-13 (05-UAT.md G6) -- the audit now touches the freeze watchdog once
    at the START of each BOUNDED attempt. Before this, `Watchdog.touch()`
    was called NOWHERE in the audit path: all five call sites were in the
    turn loop, and `agent_entrypoint.run_agent` arms the watchdog before
    `start_server` and stops it only in the teardown `finally`, so this
    ladder -- (retry_count+1) x response_timeout plus backoffs, 135 s at
    the shipped Table-19 values -- ran entirely unmarked against a 60 s
    `watchdog_threshold` whose freeze action is `os._exit(1)`. Against a
    peer whose socket accepts TCP but never answers (a stalled tunnel edge,
    exactly the drop 05-11 exists for) the process died at t=60 s, so
    `run_final_audit`'s non-accusatory `record_audit_incomplete` at
    t~135 s NEVER RAN: our log ended on `watchdog_incident` with no
    `audit_verdict`, and the peer then declared US `opponent_unresponsive`.

    NET-07 is PRESERVED, not traded away, and the placement is the whole
    reason. The touch marks a real attempt STARTING -- the shape
    `turn_commit_send.push` already uses around this same ladder -- never a
    heartbeat on a dead loop. Every attempt is itself bounded by
    `response_timeout`, so the widest possible gap between two touches is
    response_timeout + backoff_seconds (35 s) < watchdog_threshold (60 s),
    while a genuinely wedged event loop stops producing attempts at all and
    is still killed. Stopping the watchdog across the audit would have made
    the same test pass by deleting the requirement.
    """
    envelope = Envelope(
        type=MessageType.FINAL_REVEAL, turn=ctx.state.turn, sender=ctx.role,
        payload={_RECORDS_KEY: records},
    )
    args = {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}

    async def _call() -> object:
        ctx.watchdog.touch()
        async with ctx.runtime.client() as client:
            return await client.call_tool(_FINAL_REVEAL_TOOL, args)

    call_outcome = await call_with_retry(
        _call, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
        backoff=ctx.net.backoff_seconds,
    )
    return None if call_outcome.succeeded else call_outcome.verdict


async def receive_final_reveal(ctx: AgentContext) -> tuple[list[dict], TechnicalWin | None]:
    """Block for the opponent's own FINAL_REVEAL -- the SAME bounded-wait
    primitive turn_commit.py's own waits use (tolerant of a stray HINT).

    The receive leg carries the IDENTICAL 135 s-against-60 s exposure the
    push leg does -- `next_protocol_message`'s only touch is AFTER its whole
    ladder -- and it is the leg that runs LAST, so a freeze here kills the
    process with the peer's records already in hand and no `audit_verdict`
    written. `on_attempt` is therefore passed here and nowhere else: the
    turn-loop callers keep the pre-05-13 behaviour byte for byte."""
    envelope, verdict = await next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)
    if verdict is not None:
        return [], verdict
    return envelope.payload.get(_RECORDS_KEY, []), None


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
    evidence."""
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
