"""The shared `run_agent` driver: every collaborator `agent_entrypoint`
binds by `from ... import` is faked AT THAT MODULE's own namespace (patching
`agent_lifecycle`/`handshake`/etc. directly would not reach these call
sites) -- zero real sockets, zero real handshake, matching this codebase's
DI-with-fakes house style.

Split out of `test_agent_entrypoint.py` (07-00) at the 150-code-line gate:
that file stood at 148/150 and 07-00 needs a SECOND consumer of the same
driver -- `test_games_played_counter.py`, which drives the real `run_agent`
against a THROWAWAY config directory to measure what the games-played
counter does at each of the three exits. Split, never compressed: every
fake below is byte-identical to the version that lived in
`test_agent_entrypoint.py`, and the only addition is the `config_dir`
parameter.

`config_dir=None` -- what every pre-existing case passes -- keeps the real
`config/police` AgentConfig those cases have always used, so their behaviour
is unchanged. A caller that supplies one gets the same config object with
`config_dir` replaced, which is the only way to exercise a production path
that WRITES into `cfg.config_dir` without touching the shipped tree
(`tests/_shipped_config_guard.py` explains why that matters, rules 37/38).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from pursuit.network import agent_entrypoint
from pursuit.shared.network_config import load_network_config
from pursuit.shared.tunnel_config import load_tunnel_config

_TUNNEL_PARAMS = load_tunnel_config("config/police/tunnel.json")
_NETWORK_PARAMS = load_network_config("config/police/network.json")


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
        self.network_params = _NETWORK_PARAMS  # the 05-11 watch reads its cadence

    def start(self) -> None:
        self._order.append("tunnel_start")

    def stop(self) -> None:
        self._order.append("tunnel_stop")


class _HandshakeResult:
    def __init__(self, agreed: bool) -> None:
        self.agreed = agreed


def _patch_common(
    monkeypatch, *, agreed: bool, order: list[str], tunnel=None, config_dir: Path | None = None,
):
    cfg = agent_entrypoint.load_agent_config("config/police")
    if config_dir is not None:
        cfg = dataclasses.replace(cfg, config_dir=Path(config_dir))
    monkeypatch.setattr(agent_entrypoint, "load_agent_config", lambda config_dir: cfg)
    monkeypatch.setattr(agent_entrypoint, "build_tunnel_manager", lambda config_dir, net: tunnel)
    monkeypatch.setattr(agent_entrypoint, "make_client_caller", lambda client: object())

    def _default_context(
        cfg_arg, *, game_uid=None, local_step0_digest=None, local_game_id=None,
        local_step0_declaration=None,
    ):
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

    # 05-04: teardown is three named steps, not one shutdown_cleanly call.
    # They are module-level helpers precisely so they stay patchable HERE
    # (a `ctx.watchdog.stop()` method call could not be), which also lets
    # this order list and test_late_peer_teardown.py's harness assert the
    # SAME named sequence rather than two parallel descriptions of it.
    def _stop_watchdog(ctx):
        order.append("stop_watchdog")

    async def _linger_for_peer(ctx):
        order.append("linger_for_peer")

    async def _stop_runtime(ctx):
        order.append("stop_runtime")

    async def _declare_step0(cfg_arg):
        order.append("declare_step0")
        return "fake-step0-digest", {"declaration": {}, "digest": "fake-step0-digest"}

    # 05-05: adoption sits between the handshake and write_declaration --
    # the D-64 ledger stem and every hashed commit derive from what it sets.
    def _adopt_negotiated_game_id(ctx, result):
        order.append("adopt_negotiated_game_id")

    def _write_declaration(ctx, cfg_arg, result, envelope):
        order.append("write_declaration")

    async def _run_final_audit(ctx):
        order.append("run_final_audit")
        return None

    # 07-00 (rules 37/38): `run_agent` now advances
    # `cfg.config_dir/games_played.json` on its way out. Every case that
    # takes `config_dir=None` drives it against the REAL `config/police`,
    # so an unfaked call would advance the shipped, league-facing counter on
    # every `pytest` run -- the exact defect 07-00 removes. Recording the
    # step by name instead STRENGTHENS the order assertions, which now pin
    # WHERE in the sequence a game gets counted; the real file effect is
    # measured against `tmp_path` in `test_games_played_counter.py`, which
    # restores this function deliberately after supplying a throwaway dir.
    def _record_completed_game(cfg_arg, outcome):
        order.append("record_completed_game")

    monkeypatch.setattr(agent_entrypoint, "default_context", _default_context)
    monkeypatch.setattr(agent_entrypoint, "start_server", _start_server)
    monkeypatch.setattr(agent_entrypoint, "perform_handshake", _perform_handshake)
    monkeypatch.setattr(agent_entrypoint, "run_turn_loop", _run_turn_loop)
    monkeypatch.setattr(agent_entrypoint, "stop_watchdog", _stop_watchdog)
    monkeypatch.setattr(agent_entrypoint, "linger_for_peer", _linger_for_peer)
    monkeypatch.setattr(agent_entrypoint, "stop_runtime", _stop_runtime)
    monkeypatch.setattr(agent_entrypoint, "adopt_negotiated_game_id", _adopt_negotiated_game_id)
    monkeypatch.setattr(agent_entrypoint, "declare_step0", _declare_step0)
    monkeypatch.setattr(agent_entrypoint, "write_declaration", _write_declaration)
    monkeypatch.setattr(agent_entrypoint, "run_final_audit", _run_final_audit)
    monkeypatch.setattr(agent_entrypoint, "record_completed_game", _record_completed_game)
    return cfg
