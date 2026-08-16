"""monitor_tunnel()/run_with_tunnel() watch-task suite (05-11, CLOUD-01,
D-55). Sibling of test_tunnel_wiring.py, split per the
test_agent_entrypoint_audit_wiring.py precedent: a new fake-tunnel class
plus its cases, not a new concern.

The monitor's sleep and to_thread are INJECTED (house DI style) -- no real
thread runs and no cadence number is invented here: the cadence asserted is
NetworkParams.watchdog_poll_seconds, the D-55/D-18 reuse tunnel_config.py's
docstring declares. The run_with_tunnel lifecycle cases live in
test_tunnel_wiring_lifecycle.py -- split at the 150-code-line gate, not by
test meaning (this file measured 157 with them in).
"""

import asyncio

import pytest

from pursuit.network import tunnel_wiring
from pursuit.shared.network_config import load_network_config
from pursuit.shared.tunnel_config import load_tunnel_config

_TUNNEL_PARAMS = load_tunnel_config("config/police/tunnel.json")
_NETWORK_PARAMS = load_network_config("config/police/network.json")


class _InlineToThread:
    """to_thread stand-in: run the callable on the loop, synchronously,
    counting calls -- the count is what pins that the blocking probe and
    repair go through the to_thread seam at all (05-11)."""

    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, fn, *args):
        self.calls += 1
        return fn(*args)


class _CancelAfter:
    """Fake asyncio.sleep: asserts the D-55 cadence, then simulates the
    run_with_tunnel teardown by raising CancelledError after N ticks."""

    def __init__(self, ticks: int) -> None:
        self._remaining = ticks
        self.calls = 0

    async def __call__(self, seconds: float) -> None:
        assert seconds == _NETWORK_PARAMS.watchdog_poll_seconds
        self.calls += 1
        if self.calls > self._remaining:
            raise asyncio.CancelledError


class _WatchedTunnel:
    """Scripted healthy()/ensure_connected() answers, calls recorded."""

    params = _TUNNEL_PARAMS
    network_params = _NETWORK_PARAMS
    public_url = "https://peer.ngrok-free.app"

    def __init__(self, healthy_script, ensure_script=()) -> None:
        self._healthy_script = list(healthy_script)
        self._ensure_script = list(ensure_script)
        self.ensure_calls = 0

    def healthy(self):
        step = self._healthy_script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step

    def ensure_connected(self):
        self.ensure_calls += 1
        return self._ensure_script.pop(0)


async def test_monitor_stays_quiet_while_healthy() -> None:
    tunnel = _WatchedTunnel(healthy_script=[True, True])
    sleep = _CancelAfter(ticks=2)
    to_thread = _InlineToThread()

    with pytest.raises(asyncio.CancelledError):
        await tunnel_wiring.monitor_tunnel(tunnel, sleep=sleep, to_thread=to_thread)

    assert tunnel.ensure_calls == 0
    assert to_thread.calls == 2  # both probes went through the seam


async def test_monitor_repairs_a_drop_and_keeps_watching(capsys) -> None:
    tunnel = _WatchedTunnel(healthy_script=[False, True], ensure_script=[True])
    sleep = _CancelAfter(ticks=2)
    to_thread = _InlineToThread()

    with pytest.raises(asyncio.CancelledError):
        await tunnel_wiring.monitor_tunnel(tunnel, sleep=sleep, to_thread=to_thread)

    assert tunnel.ensure_calls == 1
    assert to_thread.calls == 3  # 2 probes + 1 repair, ALL through the seam
    out = capsys.readouterr().out
    assert tunnel_wiring.TUNNEL_DOWN_LINE in out
    assert tunnel_wiring.TUNNEL_RESTORED_LINE.format(url=tunnel.public_url) in out


async def test_monitor_gives_up_after_one_exhausted_repair(capsys) -> None:
    """D-55's bound stays per-drop: an exhausted ensure_connected() ends the
    watch -- it never becomes an unbounded retry loop."""
    tunnel = _WatchedTunnel(healthy_script=[False], ensure_script=[False])
    sleep = _CancelAfter(ticks=9)

    await tunnel_wiring.monitor_tunnel(tunnel, sleep=sleep, to_thread=_InlineToThread())

    assert tunnel.ensure_calls == 1
    assert sleep.calls == 1
    assert tunnel_wiring.TUNNEL_LOST_LINE in capsys.readouterr().out


async def test_monitor_treats_a_raising_probe_as_a_drop() -> None:
    """A dead agent process raises out of healthy() -- that must trigger the
    repair, not kill the watch task (05-11)."""
    tunnel = _WatchedTunnel(
        healthy_script=[RuntimeError("agent process terminated")], ensure_script=[False]
    )
    sleep = _CancelAfter(ticks=9)

    await tunnel_wiring.monitor_tunnel(tunnel, sleep=sleep, to_thread=_InlineToThread())

    assert tunnel.ensure_calls == 1
