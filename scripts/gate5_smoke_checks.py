"""Gate 5 smoke script -- the offline-testable half (05-03 must_haves: "a
unit-testable core: URL-pattern check and evidence-file writer are
importable and covered offline"). Split out of gate5_tunnel_smoke.py at the
gate4_* helper-module precedent (04-14): these functions touch no network,
no pyngrok, no filesystem beyond one write call, and are exercised directly
by tests/unit/test_gate5_smoke_checks.py with zero env vars set.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path

#: RESEARCH's own gate-script assertion list: "public_url is https and
#: matches the configured domain" -- a bare hostname match, no path/query
#: assumptions (pyngrok's own public_url never carries either).
_HTTPS_URL_PATTERN = re.compile(r"^https://([^/]+)/?$")


def missing_env_vars(names: Iterable[str], *, env: Mapping[str, str]) -> list[str]:
    """Names from `names`, in order, that are absent or blank in `env`.

    An empty list is the caller's signal to proceed. This is deliberately
    generic over `env` (never reads os.environ itself) so the script's own
    preflight is testable without mutating real process environment.
    """
    return [name for name in names if not env.get(name)]


def check_public_url(url: str, expected_domain: str) -> bool:
    """True iff `url` is exactly `https://<expected_domain>` -- the static
    domain claimed at NGROK_AUTHTOKEN setup (D-54), never a random ngrok
    subdomain and never plain http."""
    match = _HTTPS_URL_PATTERN.match(url)
    return bool(match) and match.group(1) == expected_domain


def build_evidence(
    *,
    public_url: str,
    expected_domain: str,
    url_check_passed: bool,
    round_trip_seconds: float,
    authorized_request_ok: bool,
    unauthorized_request_rejected: bool,
    generated_at: str | None = None,
) -> dict:
    """The JSON evidence shape GATE-5-MEASUREMENT.md links by path
    (must_haves: "writes a JSON evidence file ... into
    docs/phases/phase-5/"). `generated_at` is injectable so a test can
    assert an exact value instead of comparing against `datetime.now()`."""
    passed = url_check_passed and authorized_request_ok and unauthorized_request_rejected
    return {
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "public_url": public_url,
        "expected_domain": expected_domain,
        "url_is_https_and_matches_domain": url_check_passed,
        "round_trip_seconds": round_trip_seconds,
        "authorized_request_reached_mcp": authorized_request_ok,
        "unauthorized_request_rejected_403": unauthorized_request_rejected,
        "verdict": "PASS" if passed else "FAIL",
    }


def write_evidence(path: Path, evidence: dict) -> Path:
    """Write `evidence` as pretty, sorted JSON to `path`, creating parent
    directories. Returns `path` for the caller's own summary print."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
