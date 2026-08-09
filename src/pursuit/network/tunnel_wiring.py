"""Tunnel wiring for run_agent() -- decides tunnel-on/off, builds the
exchange block, and wraps a coroutine body with tunnel start/stop. Split
out of agent_lifecycle.py at the 150-code-line gate (mirrors
brain_wiring.py/language_wiring.py's own precedent, same docstring note).

Tunnel use is conditional, but tunnel.json carries no enable flag (D-55 --
that file is strings only): the static-domain env var's PRESENCE is the
opt-in signal. Every existing loopback test and dev flow never sets it, so
build_tunnel_manager() returns None and run_with_tunnel()'s wrapping is a
no-op -- the default stays tunnel-off exactly as it was before this plan.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeVar

from pursuit.network.tunnel_manager import TunnelManager
from pursuit.shared.network_config import NetworkParams
from pursuit.shared.tunnel_config import TunnelParams, load_tunnel_config

TUNNEL_CONFIG_FILE = "tunnel.json"

_T = TypeVar("_T")


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


async def run_with_tunnel(
    tunnel: TunnelManager | None, body: Callable[[], Awaitable[_T]]
) -> _T:
    """Wrap body() (the runtime+handshake+turn-loop) with tunnel start/stop,
    mirroring Watchdog's own start-before/stop-after shape. tunnel=None --
    the test/dev default -- runs body() exactly as it always has. A start
    failure raises BEFORE body() is invoked at all: a peer that would play
    unreachable must never begin the game (must_haves)."""
    if tunnel is None:
        return await body()
    tunnel.start()
    print(exchange_block(tunnel.public_url, tunnel.params))
    try:
        return await body()
    finally:
        tunnel.stop()
