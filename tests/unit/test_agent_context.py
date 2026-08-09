"""Tests for the 06-02 AgentContext split (agent_context.py): the new
`security`/`commit_state` fields, `PendingAction`/`CommitTurnState`'s idle
shape, and the re-export surface both origin modules (orchestrator.py,
agent_lifecycle.py) promise to keep unchanged.
"""

import pytest

from pursuit.network import agent_context, agent_lifecycle, orchestrator
from pursuit.network.agent_context import AgentContext, CommitTurnState, PendingAction
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import make_ctx


def test_agent_context_requires_security_no_default(tmp_path, default_params, network_params):
    """security has NO default -- every construction site must be explicit
    (06-02 must_haves)."""
    from pursuit.network.state_machine import TurnStateMachine
    from pursuit.sdk import engine
    from tests.unit._fakes_agent import FakeReporter, FakeRuntime, FakeWatchdog

    reporter = FakeReporter()
    with pytest.raises(TypeError):
        AgentContext(
            role="police", params=default_params, net=network_params,
            machine=TurnStateMachine(reporter), runtime=FakeRuntime(), watchdog=FakeWatchdog(),
            reporter=reporter, log_path=tmp_path / "x.jsonl", game_uid="g1",
            state=engine.make_state(default_params),
        )


def test_commit_state_defaults_idle_with_zero_explicit_construction(
    tmp_path, default_params, network_params,
):
    """ctx.commit_state defaults to an idle CommitTurnState() -- no
    pre-existing fixture needs an edit (make_ctx never sets it)."""
    ctx = make_ctx(tmp_path, default_params, network_params, label="idle")
    assert ctx.commit_state == CommitTurnState()
    assert ctx.commit_state.pending_action is None
    assert ctx.commit_state.own_ack_received is False
    assert ctx.commit_state.chosen_barrier is None


def test_pending_action_shape_carries_every_field_reveal_pending_needs():
    pending = PendingAction(
        move=(1, 1), barrier=None, plan=None, incoming_log={}, regime="B",
        action_payload={"move": {"kind": "move", "direction": "north"}, "barrier": None},
        h_commit="deadbeef", turn=3,
    )
    assert pending.move == (1, 1)
    assert pending.action_payload["barrier"] is None
    assert pending.h_commit == "deadbeef"
    assert pending.turn == 3


def test_orchestrator_reexports_agent_context_names_unchanged():
    """Every existing `from pursuit.network.orchestrator import AgentContext`
    call site keeps working with zero edits (06-02 must_haves)."""
    assert orchestrator.AgentContext is agent_context.AgentContext
    assert orchestrator.ChooseMove is agent_context.ChooseMove
    assert orchestrator.Coord is agent_context.Coord


def test_agent_lifecycle_reexports_build_context_unchanged():
    assert agent_lifecycle.build_context is agent_context.build_context
    assert agent_lifecycle.AgentContext is agent_context.AgentContext


def test_load_agent_config_populates_security_from_the_real_config():
    """The real shipped config/police/security.json flows through
    load_agent_config -> AgentConfig.security -> build_context ->
    AgentContext.security, matching D-65's default-true toggle."""
    cfg = agent_lifecycle.load_agent_config("config/police")
    assert isinstance(cfg.security, SecurityParams)
    assert cfg.security.commit_reveal is True
    assert cfg.security.team_code == "khm-mn17"
    assert cfg.security == agent_lifecycle.load_agent_config("config/police").security
