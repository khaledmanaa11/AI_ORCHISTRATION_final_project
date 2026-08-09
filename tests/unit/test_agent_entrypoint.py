"""Tests for run_agent (agent_entrypoint.py) -- CLOUD-01, NET-04, D-01.

Every collaborator is monkeypatched to a fake AT THE agent_entrypoint
MODULE's own namespace (the real functions are bound there by `from ...
import`, so patching agent_lifecycle/handshake/etc. directly would not
reach these call sites) -- zero real sockets, zero real handshake, matching
this codebase's DI-with-fakes house style.
"""

from pursuit.network import agent_entrypoint
from pursuit.shared.tunnel_config import load_tunnel_config

_TUNNEL_PARAMS = load_tunnel_config("config/police/tunnel.json")


class _FakeClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeSecurity:
    def __init__(self, commit_reveal: bool = False) -> None:
        self.commit_reveal = commit_reveal


class _FakeCtx:
    def __init__(self):
        self.runtime = type("R", (), {"client": lambda self: _FakeClient()})()
        self.watchdog = type("W", (), {"start": lambda self: None})()
        self.machine = object()
        self.reporter = object()
        self.role = "police"
        self.security = _FakeSecurity()  # commit_reveal off -- run_final_audit never fires


class _FakeTunnel:
    def __init__(self, order: list[str]) -> None:
        self._order = order
        self.public_url = "https://peer.ngrok-free.app"
        self.params = _TUNNEL_PARAMS

    def start(self) -> None:
        self._order.append("tunnel_start")

    def stop(self) -> None:
        self._order.append("tunnel_stop")


class _HandshakeResult:
    def __init__(self, agreed: bool) -> None:
        self.agreed = agreed


def _patch_common(monkeypatch, *, agreed: bool, order: list[str], tunnel=None):
    cfg = agent_entrypoint.load_agent_config("config/police")
    monkeypatch.setattr(agent_entrypoint, "load_agent_config", lambda config_dir: cfg)
    monkeypatch.setattr(agent_entrypoint, "build_tunnel_manager", lambda config_dir, net: tunnel)
    monkeypatch.setattr(agent_entrypoint, "make_client_caller", lambda client: object())

    def _default_context(cfg_arg, *, game_uid=None, local_step0_digest=None, local_game_id=None):
        order.append("default_context")
        return _FakeCtx()

    async def _start_server(ctx):
        order.append("start_server")

    async def _perform_handshake(**kwargs):
        order.append("perform_handshake")
        return _HandshakeResult(agreed)

    async def _run_turn_loop(ctx):
        order.append("run_turn_loop")
        return "OUTCOME"

    async def _shutdown_cleanly(ctx):
        order.append("shutdown_cleanly")

    async def _declare_step0(cfg_arg):
        order.append("declare_step0")
        return "fake-step0-digest", {"declaration": {}, "digest": "fake-step0-digest"}

    def _write_declaration(ctx, cfg_arg, result, envelope):
        order.append("write_declaration")

    async def _run_final_audit(ctx):
        order.append("run_final_audit")
        return None

    monkeypatch.setattr(agent_entrypoint, "default_context", _default_context)
    monkeypatch.setattr(agent_entrypoint, "start_server", _start_server)
    monkeypatch.setattr(agent_entrypoint, "perform_handshake", _perform_handshake)
    monkeypatch.setattr(agent_entrypoint, "run_turn_loop", _run_turn_loop)
    monkeypatch.setattr(agent_entrypoint, "shutdown_cleanly", _shutdown_cleanly)
    monkeypatch.setattr(agent_entrypoint, "declare_step0", _declare_step0)
    monkeypatch.setattr(agent_entrypoint, "write_declaration", _write_declaration)
    monkeypatch.setattr(agent_entrypoint, "run_final_audit", _run_final_audit)


async def test_run_agent_happy_path_returns_the_turn_loop_outcome(monkeypatch) -> None:
    order: list[str] = []
    _patch_common(monkeypatch, agreed=True, order=order)

    result = await agent_entrypoint.run_agent("config/police")

    assert result == "OUTCOME"
    assert order == [
        "declare_step0", "default_context", "start_server", "perform_handshake",
        "write_declaration", "run_turn_loop", "shutdown_cleanly",
    ]


async def test_run_agent_returns_none_when_handshake_does_not_agree(monkeypatch) -> None:
    """Error case: a disagreed handshake ends the game before the turn
    loop, but shutdown_cleanly ALWAYS still runs (finally)."""
    order: list[str] = []
    _patch_common(monkeypatch, agreed=False, order=order)

    result = await agent_entrypoint.run_agent("config/police")

    assert result is None
    assert "run_turn_loop" not in order
    assert order[-1] == "shutdown_cleanly"


async def test_run_agent_wraps_the_whole_play_in_the_tunnel(monkeypatch) -> None:
    """End-to-end through the real run_with_tunnel composition (not just
    the wiring helper in isolation): tunnel start precedes default_context,
    tunnel stop follows shutdown_cleanly."""
    order: list[str] = []
    tunnel = _FakeTunnel(order)
    _patch_common(monkeypatch, agreed=True, order=order, tunnel=tunnel)

    result = await agent_entrypoint.run_agent("config/police")

    assert result == "OUTCOME"
    assert order == [
        "tunnel_start", "declare_step0", "default_context", "start_server", "perform_handshake",
        "write_declaration", "run_turn_loop", "shutdown_cleanly", "tunnel_stop",
    ]
