"""One valid `league.json` body, and a writer that perturbs it.

Not a `test_*.py` module on purpose (the `artifact_declaration_fixtures.py`
precedent): pytest never collects it, so the dry-run cases and the live-mode
refusal cases share ONE copy of the setup.
"""

from __future__ import annotations

import json
from pathlib import Path

REAL_URLS = {
    "own_cop": "https://github.com/khm-mn17/pursuit-cop",
    "own_thief": "https://github.com/khm-mn17/pursuit-thief",
    "opponent_cop": "https://github.com/other-team/cop",
    "opponent_thief": "https://github.com/other-team/thief",
}
REAL_ADDRESSES = {"own": "https://own.example-tunnel/mcp", "opponent": "https://opp.tunnel/mcp"}

#: What config/{police,thief}/league.json ships: every slot a stated absence.
SHIPPED_BODY = {
    "version": "1.00",
    "league": {
        "repo_urls": dict.fromkeys(REAL_URLS),
        "mcp_server_addresses": dict.fromkeys(REAL_ADDRESSES),
        "token_ceiling": 200000,
    },
}


def filled_body() -> dict:
    """A league-ready file: all four rule-49 links and both addresses real."""
    return {
        "version": "1.00",
        "league": {
            "repo_urls": dict(REAL_URLS),
            "mcp_server_addresses": {"own": "https://own.tunnel/mcp", "opponent": REAL_ADDRESSES["opponent"]},
            "token_ceiling": 200000,
        },
    }


def write_league(tmp_path: Path, body: dict) -> Path:
    path = tmp_path / "league.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    return path


def shipped(tmp_path: Path) -> Path:
    return write_league(tmp_path, SHIPPED_BODY)
