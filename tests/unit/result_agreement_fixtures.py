"""Shared scaffolding for the rule-35 agreement cases.

Not a `test_*.py` module on purpose (the `_fakes_agent.py` / `artifact_log_
fixtures.py` precedent): pytest never collects it, so the two case files below
share ONE copy of the writer instead of two (Segal Table 5, no duplication).

EVERY LOG IN THOSE FILES IS WRITTEN BY THE PRODUCTION WRITER.
`capture_declaration.record_received_declaration` is the only function that
files a peer's Capture Claim, so `claim()` drives it rather than hand-rolling
records: a reader tested against a shape its writer does not produce measures
the test author's memory, not the pair.
"""

from __future__ import annotations

from pursuit.network.capture_declaration import (
    CAPTURE_REASON,
    OUTCOME_KEY,
    REASON_KEY,
    record_received_declaration,
)
from pursuit.network.envelope import Envelope, MessageType
from tests.unit._fakes_agent import make_ctx

VERDICT = {"matched": True, "turn": 5}
"""A stand-in for `log_join`'s `{matched, turn}` summary -- passed THROUGH the
agreement builder verbatim, never re-derived by it."""


def agreement_ctx(tmp_path, default_params, network_params, label="agree"):
    """The thief's seat: the only one that receives a Capture Claim."""
    return make_ctx(tmp_path, default_params, network_params, role="thief", label=label)


def claim(ctx, payload, *, kind=MessageType.GAME_OVER, turn=4) -> None:
    """File one inbound envelope through the production receiver."""
    record_received_declaration(
        ctx, Envelope(type=kind, turn=turn, sender="police", payload=payload),
    )


def capture_payload(outcome: object) -> dict:
    """The exact two-key payload `capture_declaration.build_declaration` sends."""
    return {OUTCOME_KEY: outcome, REASON_KEY: CAPTURE_REASON}
