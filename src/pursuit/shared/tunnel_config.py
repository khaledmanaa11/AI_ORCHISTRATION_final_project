"""Fail-loud config loader for tunnel.json -- the tenth per-agent config
block (CLOUD-01, D-54, D-55).

TunnelKey lives HERE, not in pursuit.config_keys, extending the precedent
ScentKey/LanguageKey/BeliefKey/DeceptionKey already set (see scent_config.py's
own docstring): config_keys.py is at its 150-code-line ceiling and every
Phase-4/5 negotiated-block enum ships beside the one loader that validates it.

tunnel.json carries ONLY strings (D-55): a provider name, the shared-secret
header name, and the NAMES of three environment variables -- never their
values. NGROK_AUTHTOKEN, the static domain and the shared secret come from
os.environ.get() only, matching network_config.py's existing
PURSUIT_HOST/PURSUIT_PORT/PURSUIT_OPPONENT_URL convention. Reconnect bounds
and the liveness poll cadence are NOT config here at all: they are reused
directly from NetworkParams.retry_count/backoff_seconds/
watchdog_poll_seconds (Table 19 + the D-18 precedent) -- this loader
introduces zero new numeric parameters.

require_env() is the separate, explicit env-var resolution step
TunnelManager.start() calls to preflight NGROK_AUTHTOKEN and the static
domain BEFORE any pyngrok call -- "reported by NAME at startup, not
mid-connect" (must_haves). load_tunnel_config() itself never touches
os.environ: every existing loopback test/dev flow, none of which sets these
vars, loads tunnel.json exactly like any other config file.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pursuit.shared.loader_helpers import require_str

TUNNEL_CONFIG_SOURCE = "tunnel.json"


class TunnelKey(str, Enum):
    """Field names in tunnel.json (D-55). See module docstring for why this
    enum lives here instead of pursuit.config_keys."""

    VERSION = "version"
    PROVIDER = "provider"
    SECRET_HEADER = "secret_header"
    AUTHTOKEN_ENV = "authtoken_env"
    DOMAIN_ENV = "domain_env"
    SECRET_ENV = "secret_env"

    def __str__(self) -> str:
        """Return the bare key string so json.dumps emits the field name."""
        return self.value


@dataclass(frozen=True)
class TunnelParams:
    """Structural tunnel config -- every field a name or a label, never a
    secret or a number (D-55). Constructed only by load_tunnel_config()."""

    version: str
    provider: str
    secret_header: str
    authtoken_env: str
    domain_env: str
    secret_env: str


def load_tunnel_config(path: Path | str) -> TunnelParams:
    """Load and validate a tunnel.json file into a TunnelParams.

    Raises
    ------
    KeyError
        If a required key is absent.
    TypeError
        If a field carries the wrong type.
    """
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)

    return TunnelParams(
        version=require_str(data, TunnelKey.VERSION.value, source=TUNNEL_CONFIG_SOURCE),
        provider=require_str(data, TunnelKey.PROVIDER.value, source=TUNNEL_CONFIG_SOURCE),
        secret_header=require_str(
            data, TunnelKey.SECRET_HEADER.value, source=TUNNEL_CONFIG_SOURCE
        ),
        authtoken_env=require_str(
            data, TunnelKey.AUTHTOKEN_ENV.value, source=TUNNEL_CONFIG_SOURCE
        ),
        domain_env=require_str(data, TunnelKey.DOMAIN_ENV.value, source=TUNNEL_CONFIG_SOURCE),
        secret_env=require_str(data, TunnelKey.SECRET_ENV.value, source=TUNNEL_CONFIG_SOURCE),
    )


def require_env(var_name: str) -> str:
    """Resolve var_name from the environment; raise, naming it, if unset or
    blank. TunnelManager.start() calls this for NGROK_AUTHTOKEN and the
    static domain BEFORE calling pyngrok, so a missing var surfaces as one
    clear message instead of a cryptic mid-connect failure.

    Raises
    ------
    KeyError
        If var_name is unset or empty in os.environ.
    """
    value = os.environ.get(var_name)
    if not value:
        raise KeyError(f"Required environment variable {var_name!r} is not set")
    return value
