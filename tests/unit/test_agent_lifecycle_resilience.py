"""Resilience tests split from test_agent_lifecycle.py at the 150-code-line
gate (Segal Table 5): the freeze handler, config-sourced Watchdog
construction, and the RESEARCH Open Question 2 port-release proof.
"""

import contextlib
import dataclasses
import json
import socket
import time

from pursuit.network import agent_lifecycle
from pursuit.network.peer_runtime import PeerRuntime
from tests.unit._fakes_agent import FakeReporter, FakeWatchdog


def test_freeze_handler_writes_the_incident_before_exiting(tmp_path):
    """THE NET-07 GATE (RESEARCH Pitfall 6): readable from disk, no thread,
    no real exit."""
    log_path = tmp_path / "freeze.jsonl"
    handler = agent_lifecycle.make_freeze_handler(
        log_path, game_uid="g1", role="police", threshold_seconds=0
    )
    handler()
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["event"] == "watchdog_incident"


def test_watchdog_is_built_from_config_not_from_literals(tmp_path, monkeypatch):
    """QUAL-11 / D-18: threshold and poll interval come off NetworkParams,
    never a literal."""
    captured = {}
    real_watchdog = agent_lifecycle.Watchdog

    def _recording_watchdog(*, threshold_seconds, poll_seconds, on_freeze, **kwargs):
        captured["threshold_seconds"] = threshold_seconds
        captured["poll_seconds"] = poll_seconds
        return real_watchdog(
            threshold_seconds=threshold_seconds, poll_seconds=poll_seconds,
            on_freeze=on_freeze, **kwargs,
        )

    monkeypatch.setattr(agent_lifecycle, "Watchdog", _recording_watchdog)
    cfg = agent_lifecycle.load_agent_config("config/police")
    agent_lifecycle.default_context(cfg, game_uid="g1", log_path=tmp_path / "wd.jsonl")

    assert captured["threshold_seconds"] == cfg.net.watchdog_threshold
    assert captured["poll_seconds"] == cfg.net.watchdog_poll_seconds


async def test_game_over_releases_the_port(tmp_path, network_params):
    """RESEARCH OPEN QUESTION 2 -- verified, not assumed. Loopback only."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()

    net = dataclasses.replace(network_params, host="127.0.0.1", port=port)
    runtime = PeerRuntime(net, "pursuit-test-release")
    await runtime.start()

    deadline = time.monotonic() + 2.0
    bound = False
    while time.monotonic() < deadline and not bound:
        with contextlib.suppress(OSError), socket.create_connection(
            ("127.0.0.1", port), timeout=0.1
        ):
            bound = True
    assert bound, "server never accepted a connection within the bounded probe window"

    cfg = agent_lifecycle.load_agent_config("config/police")
    cfg = dataclasses.replace(cfg, net=net)
    ctx = agent_lifecycle.build_context(
        cfg, game_uid="g-port", log_path=tmp_path / "port.jsonl",
        runtime=runtime, watchdog=FakeWatchdog(), reporter=FakeReporter(),
    )
    await agent_lifecycle.shutdown_cleanly(ctx)

    fresh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    fresh.bind(("127.0.0.1", port))
    fresh.close()
