"""Phase-2 peer-to-peer network layer (FastMCP transport, state machine, resilience)."""

#: Sec14 professional packaging. This package imports nothing, so `__all__`
#: declares its SUBMODULE INVENTORY -- the documented meaning of `__all__` on a
#: package. Derived from the tracked tree and re-derived on every run by
#: `tests/unit/test_package_exports.py`, so a module added here without being
#: exported, or exported after being deleted, fails that test rather than
#: leaving a decorative list behind.
__all__ = (
    "agent_audit_exchange", "agent_audit_observed", "agent_audit_verdict",
    "agent_audit_wiring", "agent_context", "agent_entrypoint", "agent_lifecycle",
    "agent_step0_wiring", "agent_teardown", "agent_wiring", "brain_wiring",
    "capture_declaration", "commit_state", "config_hash", "deadline",
    "deadline_errors", "deadline_status", "deadline_wait", "envelope", "event_log",
    "final_reveal_buffer", "game_identity", "game_identity_validate", "handshake",
    "handshake_evaluate", "handshake_step0", "handshake_wire", "hint_payload",
    "language_wiring", "move_payload", "orchestrator", "peer_runtime",
    "secret_guard", "secret_wiring", "state_machine", "tools", "tunnel_manager",
    "tunnel_wiring", "turn_actions",  "turn_buffer", "turn_buffer_queue", "turn_commit",
    "turn_commit_ledger", "turn_commit_pull", "turn_commit_send",
    "turn_commit_wait", "turn_commit_wait_reveal", "turn_events",
    "turn_hint_buffer", "turn_hint_store", "turn_language", "turn_language_io",
    "turn_resolve", "verdict", "watchdog",
)
