"""league.json's key names, rule 49's FOUR repo slots, and the placeholder
refusal that keeps an invented URL out of a grader-facing artifact.

Split from `shared/league_config.py` at the 150-code-line gate (Segal Table 5)
on exactly the `reporting_config.py` / `reporting_config_fields.py` precedent
07-01 set: the KEY NAMES and per-slot validation here, the loader and its
params dataclass there. The dependency runs ONE way -- this module never
imports its loader -- and `league_config.py` re-exports every public name, so
callers keep one import path.

WHY THE URLS ARE CONFIG AND NOT LITERALS (D-81). `docs/RULES.md:98` (rule 49)
wants "four links in both teams' JSON": our cop repo, our thief repo, and the
opponent's two. None of the four exists yet -- the repositories are created by
a human at 08-12 and the opponent's are the opponent's -- so every slot ships
as JSON `null`, which the loader turns into a `shared/absent.py` marker naming
the plan that fills it. A guessed `https://github.com/...` literal would be
CLAUDE.md prohibition 1 wearing its most reasonable disguise, and it would ship
inside `declaration_<game_id>.json` reading as a claim.
"""

from __future__ import annotations

from enum import Enum

from pursuit.shared.absent import stated_absent

__all__ = (
    "LEAGUE_CONFIG_SOURCE",
    "MCP_ADDRESS_SLOTS",
    "REPO_URL_SLOTS",
    "LeagueKey",
    "absent_slot",
    "read_slots",
)

LEAGUE_CONFIG_SOURCE = "league.json"

#: docs/RULES.md:98, rule 49 -- "four links in both teams' JSON". The four are
#: named rather than counted, so a config carrying four copies of one link
#: cannot satisfy the rule by arithmetic.
REPO_URL_SLOTS = ("own_cop", "own_thief", "opponent_cop", "opponent_thief")

#: docs/PARAMETERS.md:165 -- "MCP server addresses", plural, both sides.
MCP_ADDRESS_SLOTS = ("own", "opponent")

#: Substrings that mark a value as a stand-in rather than a real address. Any
#: of them in `live` mode is refused: a placeholder that reaches the wire is
#: indistinguishable, to a grader, from a fabricated one.
PLACEHOLDER_TOKENS = ("example", "placeholder", "todo", "tbd", "your-", "changeme", "<", ">")

_ABSENT_DETAIL = (
    "not created yet. The two own-team repositories are cut and pushed BY A HUMAN at "
    "08-12 and the opponent's two are supplied by the opponent on league day; "
    "docs/RULES.md:98 (rule 49) requires all four. config/{{police,thief}}/league.json "
    "carries JSON null for slot '{slot}' until then, and shared/league_config.py "
    "REFUSES to load with reporting.mode = live while any slot is still null -- so "
    "this absence cannot survive into a scored game unnoticed"
)


class LeagueKey(str, Enum):
    """Field names for config/{police,thief}/league.json. Structural only."""

    VERSION = "version"
    GROUP_LEAGUE = "league"
    REPO_URLS = "repo_urls"
    MCP_SERVER_ADDRESSES = "mcp_server_addresses"
    TOKEN_CEILING = "token_ceiling"


def absent_slot(slot: str) -> dict:
    """The stated-absence marker for one unfilled slot, naming the owning plan."""
    return stated_absent(_ABSENT_DETAIL.format(slot=slot))


def _validate_slot(slot: str, value: object, *, group: str, live: bool) -> None:
    """One slot. `None` is a stated absence; a string must look like an address.

    `live` is the whole gate: dry-run play (every config this repo ships) may
    carry absences, and a live league game may not -- rule 49's links are part
    of what is submitted, not a detail of the run.
    """
    where = f"{LEAGUE_CONFIG_SOURCE} {group}.{slot}"
    if value is None:
        if live:
            raise ValueError(
                f"{where} is not set and reporting.mode is 'live'; rule 49 requires all "
                f"{len(REPO_URL_SLOTS)} repo links to be real before a scored game"
            )
        return
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{where} must be a non-empty string or null, got {value!r}")
    lowered = value.lower()
    if live and any(token in lowered for token in PLACEHOLDER_TOKENS):
        raise ValueError(f"{where} looks like a placeholder ({value!r}) and mode is 'live'")


def read_slots(group: object, slots: tuple[str, ...], *, name: str, live: bool) -> dict:
    """Validate one group of slots and return `{slot: url-or-None}`.

    Every named slot must be PRESENT as a key -- a missing key and a `null`
    value are different mistakes, and only the second one is a decision.
    Unknown keys are refused too: a typo'd slot name would otherwise sit in the
    file looking filled while the real slot stayed absent.
    """
    if not isinstance(group, dict):
        raise TypeError(f"{LEAGUE_CONFIG_SOURCE} '{name}' must be a JSON object")
    unknown = sorted(set(group) - set(slots))
    if unknown:
        raise ValueError(f"{LEAGUE_CONFIG_SOURCE} '{name}' has unknown slot(s): {unknown}")
    resolved: dict = {}
    for slot in slots:
        if slot not in group:
            raise KeyError(f"Required slot '{name}.{slot}' missing from {LEAGUE_CONFIG_SOURCE}")
        _validate_slot(slot, group[slot], group=name, live=live)
        resolved[slot] = group[slot]
    return resolved
