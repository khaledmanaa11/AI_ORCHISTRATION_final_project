"""Fail-loud config loader for league.json -- the league-day IDENTITY values
`docs/PARAMETERS.md:165` puts inside `declaration_<game_id>.json` (D-81).

Follows `shared/reporting_config.py`'s convention exactly: a `*Key` str-Enum
beside its own loader, a frozen params dataclass, and KeyError/TypeError/
ValueError that name the offending key. The key names, rule 49's four repo
slots and the placeholder refusal live in `shared/league_config_fields.py` --
the same 150-line split -- and are re-exported here so callers have ONE import
path.

WHAT IS IN THIS FILE AND WHAT IS DELIBERATELY NOT.

IN: the two repo links per team that rule 49 (`docs/RULES.md:98`) requires in
both teams' JSON, both MCP server addresses, and the agreed token ceiling.
`docs/PARAMETERS.md:165` names exactly these as declaration content, and
before this loader existed the whole set was unrepresented anywhere in the
tree -- which is why `declaration_<game_id>.json`, one of rule 50's four
mandatory artifacts, had never been written by a real game.

NOT IN: the games-played value. It is rule 38 territory
(`docs/RULES.md:79`, ABSOLUTE disqualification), 07-00 fixed the counter
MECHANISM and left the VALUE to a human working from
`docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md`, and a config leaf is
exactly the kind of quiet place a chosen number would hide in. Nothing here
sets it, defaults it or infers it.

THE ONE NUMBER IS SOURCED, NOT CHOSEN. `token_ceiling` is
`docs/PARAMETERS.md:83` Table 18 row 4 -- "token budget per series", ~200,000,
status NEGOTIABLE -- and the file's `_sources` object carries that citation.
NEGOTIABLE means a lead team may agree a different figure on league day; the
shipped value is the book's, and the loader only refuses one that is absent,
non-integer or non-positive. It never supplies a default:
`DeclarationContext.__post_init__` already refuses to default this field and
that refusal is load-bearing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pursuit.shared.league_config_fields import (
    LEAGUE_CONFIG_SOURCE,
    MCP_ADDRESS_SLOTS,
    REPO_URL_SLOTS,
    LeagueKey,
    absent_slot,
    read_slots,
)
from pursuit.shared.loader_helpers import require_key, require_str
from pursuit.shared.reporting_config import ReportingMode

__all__ = (
    "LEAGUE_CONFIG_SOURCE",
    "MCP_ADDRESS_SLOTS",
    "REPO_URL_SLOTS",
    "LeagueKey",
    "LeagueParams",
    "absent_slot",
    "load_league_config",
)


@dataclass(frozen=True)
class LeagueParams:
    """Typed, immutable container for every value `load_league_config` reads.

    `repo_urls` and `mcp_server_addresses` map each named slot to its URL or to
    `None` for a stated absence. Constructed fresh per call, never shared
    between the police and thief processes (CLAUDE.md rule 2).
    """

    version: str
    repo_urls: dict
    mcp_server_addresses: dict
    token_ceiling: int

    def absent_slots(self) -> tuple[str, ...]:
        """Every still-unfilled slot, as `group.slot`. Empty is league-ready."""
        return tuple(
            f"{group}.{slot}"
            for group, mapping in (
                (LeagueKey.REPO_URLS.value, self.repo_urls),
                (LeagueKey.MCP_SERVER_ADDRESSES.value, self.mcp_server_addresses),
            )
            for slot, value in mapping.items()
            if value is None
        )

    def declaration_repo_urls(self) -> dict:
        """`repo_urls` as the artifact carries them: a real URL, or a marker
        that says why there is none. Never a placeholder string."""
        return _for_declaration(self.repo_urls)

    def declaration_mcp_addresses(self) -> dict:
        """`mcp_server_addresses` as the artifact carries them."""
        return _for_declaration(self.mcp_server_addresses)


def _for_declaration(mapping: dict) -> dict:
    return {slot: (absent_slot(slot) if url is None else url) for slot, url in mapping.items()}


def _require_ceiling(group: dict) -> int:
    """`token_ceiling`, refused rather than defaulted when it is unusable."""
    value = require_key(group, LeagueKey.TOKEN_CEILING.value, source=LEAGUE_CONFIG_SOURCE)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{LEAGUE_CONFIG_SOURCE} '{LeagueKey.TOKEN_CEILING.value}' must be an int")
    if value <= 0:
        raise ValueError(f"{LEAGUE_CONFIG_SOURCE} '{LeagueKey.TOKEN_CEILING.value}' must be > 0")
    return value


def load_league_config(path: Path | str, *, mode: ReportingMode) -> LeagueParams:
    """Load and validate config/{police,thief}/league.json.

    `mode` is `reporting.json`'s own mode and is REQUIRED, never defaulted: the
    whole point of this loader is that it is stricter for a live league game
    than for a dry run, and a default would pick the lenient side silently.

    Raises
    ------
    KeyError
        If any required key or named slot is absent.
    TypeError
        If a group is not an object, or a leaf carries the wrong type.
    ValueError
        If `token_ceiling` is not positive, or -- in `live` mode only -- if any
        slot is still `null` or holds a placeholder-looking value.
    """
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise TypeError(f"{LEAGUE_CONFIG_SOURCE} must be a JSON object")
    version = require_str(data, LeagueKey.VERSION.value, source=LEAGUE_CONFIG_SOURCE)
    group = require_key(data, LeagueKey.GROUP_LEAGUE.value, source=LEAGUE_CONFIG_SOURCE)
    if not isinstance(group, dict):
        raise TypeError(f"{LEAGUE_CONFIG_SOURCE} '{LeagueKey.GROUP_LEAGUE.value}' must be object")
    live = mode is not ReportingMode.DRY_RUN
    return LeagueParams(
        version=version,
        repo_urls=read_slots(
            require_key(group, LeagueKey.REPO_URLS.value, source=LEAGUE_CONFIG_SOURCE),
            REPO_URL_SLOTS, name=LeagueKey.REPO_URLS.value, live=live,
        ),
        mcp_server_addresses=read_slots(
            require_key(group, LeagueKey.MCP_SERVER_ADDRESSES.value, source=LEAGUE_CONFIG_SOURCE),
            MCP_ADDRESS_SLOTS, name=LeagueKey.MCP_SERVER_ADDRESSES.value, live=live,
        ),
        token_ceiling=_require_ceiling(group),
    )
