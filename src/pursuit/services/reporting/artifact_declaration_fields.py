"""The declaration artifact's key names and its outside-the-signature content.

Split out of `artifact_declaration.py` at the 150-code-line gate (Segal
Table 5) -- the combined module measured 156 -- following the same
`reporting_config.py` / `reporting_config_fields.py` split 07-01 made, and
04-06's `language_config.py` / `language_model_config.py` before it: the KEY
NAMES and the validated CONTENT container here, the wrapping and the signature
re-verification there. `artifact_declaration.py` re-exports both names below,
so callers keep ONE import path.

Split, never compressed: no body or docstring was shortened to make room.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ("DeclarationArtifactField", "DeclarationContext")


class DeclarationArtifactField:
    """Key names for the declaration artifact -- structural, no magic strings.

    Every one of these sits at the artifact's TOP LEVEL, outside the signed
    envelopes. That is the whole of D-71: adding any of them inside the signed
    dict would change what `handshake_evaluate` verifies and abort every game.
    """

    DECLARATIONS = "declarations"
    PEER_STATUS = "peer_declaration_status"
    REPO_URLS = "repo_urls"
    MCP_SERVER_ADDRESSES = "mcp_server_addresses"
    TOKEN_CEILING = "token_ceiling"
    START_TIME = "start_time"
    END_TIME = "end_time"


@dataclass(frozen=True)
class DeclarationContext:
    """PARAMETERS' remaining declaration content (docs/PARAMETERS.md:165):
    repo URLs, MCP server addresses, agreed token ceiling, start/end times.

    Every field is required and NOTHING is defaulted, `token_ceiling` least of
    all: a caller with no agreed ceiling to hand over has found a gap to
    report, not a number to choose (CLAUDE.md: never invent a numeric value).
    `end_time` is `str | None` because a game that aborted has no end time and
    an honest null beats a fabricated timestamp.

    Frozen and constructed per call, never shared between the two agent
    processes (CLAUDE.md rule 2).
    """

    repo_urls: dict
    mcp_server_addresses: dict
    token_ceiling: int
    start_time: str
    end_time: str | None

    def __post_init__(self) -> None:
        """Fail loud on a malformed context rather than write a malformed
        artifact -- the house loader convention, and every message names the
        field it rejects."""
        for name in ("repo_urls", "mcp_server_addresses"):
            if not isinstance(getattr(self, name), dict):
                raise TypeError(f"{name} must be a dict")
        if isinstance(self.token_ceiling, bool) or not isinstance(self.token_ceiling, int):
            raise TypeError("token_ceiling must be an int")
        if self.token_ceiling <= 0:
            raise ValueError("token_ceiling must be positive")
        if not isinstance(self.start_time, str) or not self.start_time:
            raise ValueError("start_time must be a non-empty string")
        if self.end_time is not None and not isinstance(self.end_time, str):
            raise TypeError("end_time must be a string or None")
