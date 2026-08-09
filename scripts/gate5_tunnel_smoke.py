#!/usr/bin/env python
"""GATE-5 smoke script (05-03): one command, run by a human with
NGROK_AUTHTOKEN / PURSUIT_NGROK_DOMAIN / PURSUIT_TUNNEL_SECRET set, that
starts one peer with the REAL TunnelManager (05-01) and SharedSecretMiddleware
(05-02) -- no parallel reimplementation of either -- round-trips a real HTTP
request through the PUBLIC url to that peer's own local FastMCP route,
asserts a request missing the shared-secret header dies with 403 THROUGH THE
TUNNEL (not just loopback), tears everything down, and writes a JSON
evidence file.

    uv run python scripts/gate5_tunnel_smoke.py [--config-dir config/police]

This is the SCRIPTABLE half of the book's Sec10.4 milestone-5 gate
(same-machine-via-public-URL, CLOUD-01). The genuine remote round (CLOUD-02
-- a second machine, a second operator) cannot be scripted from this repo
alone; see docs/phases/phase-5/GATE-5-MEASUREMENT.md.

It NEEDS a real ngrok account and is therefore a manual script, not a CI
test (must_haves) -- `preflight()` refuses to proceed, naming every missing
var, before touching pyngrok, PeerRuntime, or the network at all.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

# Guarded sys.path bootstrap (same idiom as scripts/measure_gate4.py):
# direct-path execution puts scripts/ on sys.path[0], not the repo root, so
# `pursuit` would not otherwise import.
if __package__ in (None, ""):
    _repo_root = str(Path(__file__).resolve().parent.parent)
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

from gate5_smoke_checks import (  # noqa: E402
    build_evidence,
    check_public_url,
    missing_env_vars,
    write_evidence,
)

from pursuit.network.peer_runtime import PeerRuntime  # noqa: E402
from pursuit.network.secret_guard import (  # noqa: E402
    NGROK_SKIP_WARNING_HEADER,
    NGROK_SKIP_WARNING_VALUE,
    client_headers,
)
from pursuit.network.secret_wiring import resolve_shared_secret  # noqa: E402
from pursuit.network.tunnel_manager import TunnelManager  # noqa: E402
from pursuit.shared.network_config import load_network_config  # noqa: E402
from pursuit.shared.tunnel_config import TunnelParams, load_tunnel_config  # noqa: E402

#: The nine D-05/D-58 tool names (tools.py) -- the "valid MCP-shaped
#: response" this script asserts arrived through the public tunnel.
EXPECTED_TOOL_NAMES = {
    "handshake", "receive_move", "receive_barrier", "game_over", "receive_hint",
    "receive_commit", "receive_ack", "receive_reveal", "receive_final_reveal",
}
_EVIDENCE_PATH = Path("docs/phases/phase-5/gate5_smoke_evidence.json")
_DEFAULT_CONFIG_DIR = Path("config/police")


def preflight(config_dir: Path, *, env: dict | None = None) -> TunnelParams:
    """Load tunnel.json and refuse -- by name -- to proceed if any of the
    three env vars it names are missing. Touches no network, no pyngrok, no
    PeerRuntime: this is the entire offline-safe half of `main()`, and the
    only part a test exercises directly.

    Raises
    ------
    SystemExit
        Naming every missing environment variable, if any are missing.
    """
    env = os.environ if env is None else env
    params = load_tunnel_config(Path(config_dir) / "tunnel.json")
    required = (params.authtoken_env, params.domain_env, params.secret_env)
    missing = missing_env_vars(required, env=env)
    if missing:
        raise SystemExit(
            "gate5_tunnel_smoke requires these environment variables, "
            f"missing: {', '.join(missing)}"
        )
    return params


async def run_smoke(config_dir: Path, tunnel_params: TunnelParams) -> dict:
    """The live half (reviewed logic, not unit-tested -- needs a real ngrok
    account): start one peer + its real tunnel, round-trip an authorized and
    an unauthorized request through the PUBLIC url, tear both down."""
    net = load_network_config(Path(config_dir) / "network.json")
    shared_secret = resolve_shared_secret(config_dir)
    runtime = PeerRuntime(net, "pursuit-gate5-smoke", shared_secret=shared_secret)
    tunnel = TunnelManager(tunnel_params, net)

    await runtime.start()
    try:
        tunnel.start()
        expected_domain = os.environ[tunnel_params.domain_env]
        url_ok = check_public_url(tunnel.public_url, expected_domain)
        mcp_url = f"{tunnel.public_url}/mcp"

        transport = StreamableHttpTransport(mcp_url, headers=client_headers(shared_secret))
        client = Client(transport, timeout=net.response_timeout)
        started = time.monotonic()
        async with client:
            tools = await client.list_tools()
        round_trip_seconds = time.monotonic() - started
        authorized_ok = {t.name for t in tools} == EXPECTED_TOOL_NAMES

        async with httpx.AsyncClient() as raw:
            response = await raw.post(
                mcp_url, json={}, headers={NGROK_SKIP_WARNING_HEADER: NGROK_SKIP_WARNING_VALUE}
            )
        unauthorized_rejected = response.status_code == 403
    finally:
        tunnel.stop()
        await runtime.stop()

    return build_evidence(
        public_url=tunnel.public_url or "",
        expected_domain=expected_domain,
        url_check_passed=url_ok,
        round_trip_seconds=round_trip_seconds,
        authorized_request_ok=authorized_ok,
        unauthorized_request_rejected=unauthorized_rejected,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. `--config-dir` selects which agent's config pair
    this run exposes (default config/police -- the gate is symmetric, either
    role's tunnel.json/network.json proves the same thing)."""
    args = sys.argv[1:] if argv is None else argv
    config_dir = _DEFAULT_CONFIG_DIR
    if "--config-dir" in args:
        idx = args.index("--config-dir")
        config_dir = Path(args[idx + 1])

    tunnel_params = preflight(config_dir)
    evidence = asyncio.run(run_smoke(config_dir, tunnel_params))
    written = write_evidence(_EVIDENCE_PATH, evidence)

    print(f"GATE-5 smoke -- verdict={evidence['verdict']}")
    print(f"  public_url={evidence['public_url']}")
    print(f"  round_trip_seconds={evidence['round_trip_seconds']:.3f}")
    print(f"Wrote {written}")
    return 0 if evidence["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
