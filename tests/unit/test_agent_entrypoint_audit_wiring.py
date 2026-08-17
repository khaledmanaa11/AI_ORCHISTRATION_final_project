"""05-10: the `board_outcome=outcome` production wiring, pinned by a test.

05-VERIFICATION found `agent_entrypoint.py:110` correctly wired -- and pinned by NOTHING.
`test_agent_entrypoint.py`'s four cases run with `commit_reveal` OFF, so `run_final_audit` is
never called there at all and its kwarg is never asserted; `dev_launch.py` passes without it
too, because 05-04's linger prevents the failure locally. Deleting the argument would therefore
ship GREEN, silently re-introducing the exact regression 05-04 was written to prevent: without
it, a failed own final-reveal push accuses a peer that answered us (05-UAT.md G1, rules 16/22).

Sibling of `test_agent_entrypoint.py`, split at the 150-code-line gate (that file is at 145).
Its fakes are imported rather than re-derived, so the two files cannot drift on what `run_agent`
is being driven with. 07-00 moved those fakes on again, from `test_agent_entrypoint.py` into
`_agent_entrypoint_fixtures.py`; this file's import line is the only thing that changed.

The assertion is on VALUE IDENTITY, not on the kwarg's presence: `board_outcome` must be
`run_turn_loop`'s OWN return value, so the test fails against a version that passes the argument
but sources it from somewhere else, as well as against one that drops it.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import agent_entrypoint
from tests.unit._agent_entrypoint_fixtures import _FakeCtx, _FakeSecurity, _patch_common

_BOARD_OUTCOME = object()
"""A unique sentinel rather than a reused string, so `is` -- not `==` -- decides. Nothing else
in `run_agent` can produce this object, so only the real wiring can deliver it."""


def _patch_audit(monkeypatch, order, *, audit_returns=None):
    """Drive `run_agent` with `commit_reveal` ON and capture what `run_final_audit` was
    actually called with. Returns the capture dict."""
    _patch_common(monkeypatch, agreed=True, order=order)
    seen: dict = {}

    def _default_context(cfg_arg, **kwargs):
        order.append("default_context")
        ctx = _FakeCtx()
        ctx.security = _FakeSecurity(commit_reveal=True)
        return ctx

    async def _run_turn_loop(ctx):
        order.append("run_turn_loop")
        return _BOARD_OUTCOME

    async def _run_final_audit(ctx, *, board_outcome=None):
        order.append("run_final_audit")
        seen["board_outcome"] = board_outcome
        return audit_returns

    monkeypatch.setattr(agent_entrypoint, "default_context", _default_context)
    monkeypatch.setattr(agent_entrypoint, "run_turn_loop", _run_turn_loop)
    monkeypatch.setattr(agent_entrypoint, "run_final_audit", _run_final_audit)
    return seen


async def test_run_final_audit_receives_the_turn_loops_own_outcome_as_board_outcome(monkeypatch):
    """THE regression pin. Remove `board_outcome=outcome` from `agent_entrypoint.py` and this
    fails -- the revert probe is recorded in 05-10-SUMMARY.md. A test that passed without the
    wiring would be testing nothing."""
    order: list[str] = []
    seen = _patch_audit(monkeypatch, order)

    result = await agent_entrypoint.run_agent("config/police")

    assert "run_final_audit" in order, "the audit never ran -- the test proves nothing"
    assert seen["board_outcome"] is _BOARD_OUTCOME
    assert result is _BOARD_OUTCOME, "a None-returning audit must leave the board outcome standing"


async def test_the_audit_overrides_the_board_outcome_when_it_returns_one(monkeypatch):
    """The other half of the same wiring: a technical loss decided by the audit is what
    `run_agent` returns, so an audit verdict is never computed and then discarded."""
    order: list[str] = []
    seen = _patch_audit(monkeypatch, order, audit_returns=Outcome.TECHNICAL_LOSS)

    result = await agent_entrypoint.run_agent("config/police")

    assert seen["board_outcome"] is _BOARD_OUTCOME
    assert result is Outcome.TECHNICAL_LOSS
