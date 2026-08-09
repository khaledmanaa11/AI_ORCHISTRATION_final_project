"""Fail-loud config loader for security.json -- the eleventh per-agent
config block (SEC-01/SEC-03/SEC-04, D-65).

SecurityKey lives HERE, not in pursuit.config_keys, extending the exact
precedent TunnelKey/ScentKey/LanguageKey/BeliefKey/DeceptionKey already set
(see tunnel_config.py's own docstring): config_keys.py is at its
150-code-line ceiling and every Phase-4/5/6 negotiated-block enum ships
beside the one loader that validates it.

security.json carries `commit_reveal` (the D-65 protocol toggle, default
ON) and `team_code` (the already-decided `khm-mn17`, rule 45) -- both
same-team, protocol-level facts shared by both agents, so the file is
byte-identical across config/police/ and config/thief/ (rule 11, the
game_params.json precedent). `require_bool` is imported from
`belief_toggle_config`, not reimplemented a fourth time (QUAL-02, 3rd
reuse after resolution.py's own `_require_bool` and belief_config.py).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pursuit.shared.belief_toggle_config import require_bool
from pursuit.shared.loader_helpers import require_str

SECURITY_CONFIG_SOURCE = "security.json"


class SecurityKey(str, Enum):
    """Field names in security.json. See module docstring for why this enum
    lives here instead of pursuit.config_keys."""

    VERSION = "version"
    COMMIT_REVEAL = "commit_reveal"
    TEAM_CODE = "team_code"

    def __str__(self) -> str:
        """Return the bare key string so json.dumps emits the field name."""
        return self.value


@dataclass(frozen=True)
class SecurityParams:
    """Structural security config -- constructed only by
    load_security_config()."""

    version: str
    commit_reveal: bool
    team_code: str


def load_security_config(path: Path | str) -> SecurityParams:
    """Load and validate a security.json file into a SecurityParams.

    Raises
    ------
    KeyError
        If a required key is absent.
    TypeError
        If a field carries the wrong type (`commit_reveal` as a non-bool,
        including an int like 1, is rejected -- bool is an int subtype).
    FileNotFoundError
        Propagates unchanged when path does not exist.
    """
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)

    return SecurityParams(
        version=require_str(data, SecurityKey.VERSION.value, source=SECURITY_CONFIG_SOURCE),
        commit_reveal=require_bool(
            data, SecurityKey.COMMIT_REVEAL.value, source=SECURITY_CONFIG_SOURCE
        ),
        team_code=require_str(data, SecurityKey.TEAM_CODE.value, source=SECURITY_CONFIG_SOURCE),
    )
