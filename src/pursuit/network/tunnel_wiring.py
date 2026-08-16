"""Tunnel wiring for run_agent() -- decides tunnel-on/off, builds the
exchange block, and wraps a coroutine body with tunnel start/stop. Split
out of agent_lifecycle.py at the 150-code-line gate (mirrors
brain_wiring.py/language_wiring.py's own precedent, same docstring note).

Tunnel use is conditional, but tunnel.json carries no enable flag (D-55 --
that file is strings only): the static-domain env var's PRESENCE is the
opt-in signal. Every existing loopback test and dev flow never sets it, so
build_tunnel_manager() returns None and run_with_tunnel()'s wrapping is a
no-op -- the default stays tunnel-off exactly as it was before this plan.

05-11 adds monitor_tunnel(): the watch task that finally gives
TunnelManager.ensure_connected() its production caller. Remote-round
attempt 2 (2026-08-16, game 5efbc5811fabfac4) is the motivating evidence:
machine A's ingress died mid-game and the designed, tested, documented
bounded reconnect (D-55) never ran, because nothing called it.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeVar

from pursuit.network.tunnel_manager import TunnelManager
from pursuit.shared.network_config import NetworkParams
from pursuit.shared.tunnel_config import TunnelParams, load_tunnel_config

TUNNEL_CONFIG_FILE = "tunnel.json"

# Watch-task evidence lines: stdout is part of the retained round evidence
# (REMOTE-ROUND-RUNBOOK.md keeps consoles), same channel as exchange_block.
TUNNEL_DOWN_LINE = "=== PURSUIT TUNNEL DOWN -- bounded reconnect starting ==="
TUNNEL_RESTORED_LINE = "=== PURSUIT TUNNEL RESTORED at {url} ==="
TUNNEL_LOST_LINE = "=== PURSUIT TUNNEL REPAIR EXHAUSTED -- ingress stays down ==="
TUNNEL_WATCH_ERROR_LINE = "=== PURSUIT TUNNEL WATCH DIED -- game result unaffected ==="

_T = TypeVar("_T")

AsyncSleepFn = Callable[[float], Awaitable[None]]
ToThreadFn = Callable[..., Awaitable[bool]]
MonitorFn = Callable[[TunnelManager], Awaitable[None]]


def build_tunnel_manager(config_dir: Path | str, net: NetworkParams) -> TunnelManager | None:
    """None when tunnel.json is absent or its domain env var is unset (the
    tunnel-off default). Otherwise a real, production-bound TunnelManager
    -- its own constructor defaults already supply the real pyngrok calls,
    so this function passes nothing beyond params."""
    path = Path(config_dir) / TUNNEL_CONFIG_FILE
    if not path.exists():
        return None
    params = load_tunnel_config(path)
    if not os.environ.get(params.domain_env):
        return None
    return TunnelManager(params, net)


def exchange_block(public_url: str, params: TunnelParams) -> str:
    """The one league-day artifact a human copy-pastes to the opponent team:
    the public URL and WHICH env var they set for the shared secret --
    never the secret value itself (must_haves)."""
    return (
        "=== PURSUIT TUNNEL READY ===\n"
        f"public_url={public_url}\n"
        f"shared_secret_header={params.secret_header}\n"
        f"opponent_sets_env={params.secret_env}\n"
        "=============================="
    )


def _probe(tunnel: TunnelManager) -> bool:
    """healthy() with any raise contained as 'unhealthy' -- a dead agent
    process must trigger the repair, not kill the watch (05-11)."""
    try:
        return tunnel.healthy()
    except Exception:  # same containment ensure_connected() applies (05-11)
        return False


async def monitor_tunnel(
    tunnel: TunnelManager,
    *,
    sleep: AsyncSleepFn = asyncio.sleep,
    to_thread: ToThreadFn = asyncio.to_thread,
) -> None:
    """Watch the tunnel for the whole game; repair a drop with the EXISTING
    bounded reconnect. The poll cadence is NetworkParams.watchdog_poll_seconds
    -- the exact reuse tunnel_config.py's docstring declares under D-55/D-18;
    zero new numeric parameters (CLAUDE.md rule 1).

    ensure_connected() is synchronous and sleeps (time.sleep, Table 19
    backoff) -- worst case ~retry_count*backoff_seconds plus real connect
    round-trips. Both it and the probe run through to_thread so the event
    loop keeps serving the peer's inbound calls during a repair; a 15-20 s
    loop stall would itself feed the peer's OPPONENT_UNRESPONSIVE ladder.

    One exhausted repair ends the watch (printed, honest): D-55's bound is
    per-drop and this task never turns it into an unbounded retry loop.
    Detection is only as wide as TunnelManager.healthy()'s stated envelope
    (agent-process/local-API death) -- see that docstring before assuming a
    live-process session blip would be caught here.
    """
    poll_seconds = tunnel.network_params.watchdog_poll_seconds
    while True:
        await sleep(poll_seconds)
        if await to_thread(_probe, tunnel):
            continue
        print(TUNNEL_DOWN_LINE)
        if await to_thread(tunnel.ensure_connected):
            print(TUNNEL_RESTORED_LINE.format(url=tunnel.public_url))
            continue
        print(TUNNEL_LOST_LINE)
        return


async def run_with_tunnel(
    tunnel: TunnelManager | None,
    body: Callable[[], Awaitable[_T]],
    *,
    monitor: MonitorFn = monitor_tunnel,
) -> _T:
    """Wrap body() (the runtime+handshake+turn-loop) with tunnel start/stop,
    mirroring Watchdog's own start-before/stop-after shape. tunnel=None --
    the test/dev default -- runs body() exactly as it always has: no task,
    no behaviour change. A start failure raises BEFORE body() is invoked at
    all: a peer that would play unreachable must never begin the game
    (must_haves). The watch task (05-11) lives exactly as long as body(),
    cancelled in finally BEFORE tunnel.stop(). Cancellation cannot interrupt
    a repair already inside a worker thread -- ensure_connected's own
    _stopped guard turns such a straggler into a no-op, not a resurrection.
    A watch that DIED raising must never eat a resolved game or skip the
    teardown (agent_entrypoint's own on-the-way-out discipline): any
    non-cancellation exception is contained to a printed line, and
    tunnel.stop() runs unconditionally."""
    if tunnel is None:
        return await body()
    tunnel.start()
    print(exchange_block(tunnel.public_url, tunnel.params))
    watch = asyncio.create_task(monitor(tunnel))
    try:
        return await body()
    finally:
        watch.cancel()
        try:
            with contextlib.suppress(asyncio.CancelledError):
                await watch
        except Exception:  # a watch bug must never mask the game (05-11)
            print(TUNNEL_WATCH_ERROR_LINE)
        finally:
            tunnel.stop()
