"""Offline test for gate5_tunnel_smoke.py's env preflight (05-03
must_haves: "the script refuses to run with the env vars missing, naming
them"). Only `preflight()` is exercised here -- it is deliberately
synchronous and touches no pyngrok/PeerRuntime/network, unlike `run_smoke()`
(the live half this plan's must_haves calls "reviewed logic", not
unit-tested, since it needs a real ngrok account).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from gate5_tunnel_smoke import preflight  # noqa: E402

_TUNNEL_JSON = (
    '{"version": "1.00", "provider": "ngrok", "secret_header": "X-Test",'
    ' "authtoken_env": "TEST_AUTHTOKEN", "domain_env": "TEST_DOMAIN",'
    ' "secret_env": "TEST_SECRET"}'
)


def test_preflight_raises_naming_every_missing_var(tmp_path):
    (tmp_path / "tunnel.json").write_text(_TUNNEL_JSON, encoding="utf-8")

    with pytest.raises(SystemExit, match="TEST_AUTHTOKEN.*TEST_DOMAIN.*TEST_SECRET"):
        preflight(tmp_path, env={})


def test_preflight_names_only_the_vars_actually_missing(tmp_path):
    (tmp_path / "tunnel.json").write_text(_TUNNEL_JSON, encoding="utf-8")
    env = {"TEST_AUTHTOKEN": "t", "TEST_DOMAIN": "", "TEST_SECRET": "s"}

    with pytest.raises(SystemExit) as excinfo:
        preflight(tmp_path, env=env)
    message = str(excinfo.value)
    assert "TEST_DOMAIN" in message
    assert "TEST_AUTHTOKEN" not in message
    assert "TEST_SECRET" not in message


def test_preflight_returns_params_when_every_var_is_set(tmp_path):
    (tmp_path / "tunnel.json").write_text(_TUNNEL_JSON, encoding="utf-8")
    env = {"TEST_AUTHTOKEN": "t", "TEST_DOMAIN": "d", "TEST_SECRET": "s"}

    params = preflight(tmp_path, env=env)

    assert params.authtoken_env == "TEST_AUTHTOKEN"
    assert params.domain_env == "TEST_DOMAIN"
    assert params.secret_env == "TEST_SECRET"
