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

from pursuit.shared.absent import stated_absent

__all__ = ("DECLARED_GAMES_PLAYED_UNSET", "DeclarationArtifactField", "DeclarationContext")

#: 08-04. The embedded Step-0 envelope carries `games_played_so_far` because
#: rule 37 puts it there, and its value is today's RAW per-role counter --
#: which 07-00 measured advancing +14 across one `pytest` run for zero games,
#: leaving the two shipped files disagreeing by seven. Left unmarked, a grader
#: reads that number as this team's declaration. So the artifact's top level
#: says what it is and what it is not. There is no parameter for this field and
#: no caller may set it: rule 38 (`docs/RULES.md:79`) makes a false
#: games-played declaration an ABSOLUTE disqualification, so the value is not
#: representable here until a human chooses it.
DECLARED_GAMES_PLAYED_UNSET = stated_absent(
    "deliberately unset. The `games_played_so_far` inside the signed Step-0 "
    "envelope below is the RAW per-role counter and is NOT this team's declared "
    "figure: 07-00 measured one `pytest` run advancing it by +14 for zero games. "
    "The declared value is a human's decision from docs/phases/phase-7/"
    "GAMES-PLAYED-RECONSTRUCTION.md, taken at 08-14, and rule 38 "
    "(docs/RULES.md:79) makes declaring it falsely an ABSOLUTE disqualification. "
    "The per-game audit trail it will be derived from is the league ledger "
    "(services/reporting/league_ledger.py)"
)


class DeclarationArtifactField:
    """Key names for the declaration artifact -- structural, no magic strings.

    Every one of these sits at the artifact's TOP LEVEL, outside the signed
    envelopes. That is the whole of D-71: adding any of them inside the signed
    dict would change what `handshake_evaluate` verifies and abort every game.
    """

    DECLARATIONS = "declarations"
    PEER_STATUS = "peer_declaration_status"
    GAMES_PLAYED_DECLARED = "games_played_declared"
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
