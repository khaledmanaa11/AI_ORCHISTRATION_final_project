"""D-56 -- resolve the shared-secret tuple `PeerRuntime` needs, from one
per-agent config directory. Split out beside `tunnel_wiring.py` (same
150-code-line-gate precedent that plan 05-01 already established for
`tunnel_wiring.py`/`agent_entrypoint.py`): `agent_wiring.py` was already at
135 of its 150 code lines, with no room left to absorb this without pushing
it over; `secret_guard.py`'s own scope (Task 1) is the middleware and the
header factories, not config/env resolution.

`resolve_shared_secret` is the factory-function seam `agent_lifecycle.
default_context` calls, matching `make_handshake_responder`'s own
injection style (agent_wiring.py) -- a function call, not a wider
`AgentConfig` dataclass, since only the one `PeerRuntime(...)` construction
site needs this value.
"""

from __future__ import annotations

import os
from pathlib import Path

from pursuit.shared.tunnel_config import TUNNEL_CONFIG_SOURCE, load_tunnel_config


def resolve_shared_secret(config_dir: Path | str) -> tuple[str, str] | None:
    """`(header_name, secret_value)` for `PeerRuntime`'s `shared_secret`
    kwarg, or `None` when tunnel.json is absent or its `secret_env` is
    unset -- every existing loopback test/dev flow, none of which sets it.
    Secret-on is opt-in per environment, not a hardcoded league switch
    (must_haves), and is independent of whether the tunnel itself
    (`tunnel_wiring.build_tunnel_manager`) is active -- a direct LAN
    connection can carry the header with no ngrok process running at all.
    """
    path = Path(config_dir) / TUNNEL_CONFIG_SOURCE
    if not path.exists():
        return None
    params = load_tunnel_config(path)
    secret_value = os.environ.get(params.secret_env)
    if not secret_value:
        return None
    return params.secret_header, secret_value
