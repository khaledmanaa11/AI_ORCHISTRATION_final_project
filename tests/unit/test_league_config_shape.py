"""`league.json`'s structural refusals -- the mistakes that would otherwise sit
in the file looking filled.

Split from `test_league_config.py` at the 150-code-line gate along the seam the
two subjects already had: what the loader ACCEPTS and how it renders it there,
what it REFUSES here.
"""

from __future__ import annotations

import copy
import json

import pytest

from pursuit.shared.league_config import LeagueKey, load_league_config
from pursuit.shared.reporting_config import ReportingMode
from tests.unit.league_config_fixtures import filled_body, write_league

DRY = {"mode": ReportingMode.DRY_RUN}


def _without(group: str, slot: str):
    body = copy.deepcopy(filled_body())
    del body["league"][group][slot]
    return body


@pytest.mark.parametrize(
    ("group", "slot"),
    [
        ("repo_urls", "opponent_thief"),
        ("repo_urls", "own_cop"),
        ("mcp_server_addresses", "opponent"),
    ],
)
def test_a_missing_slot_key_is_refused(tmp_path, group, slot):
    """A missing key and a `null` value are different mistakes, and only the
    second is a decision. Rule 49 wants four links; a file carrying three keys
    must not load as "one absent"."""
    with pytest.raises(KeyError, match=slot):
        load_league_config(write_league(tmp_path, _without(group, slot)), **DRY)


def test_an_unknown_slot_name_is_refused(tmp_path):
    """A typo'd slot would sit in the file looking filled while the real slot
    stayed absent -- and the loader would never mention either."""
    body = copy.deepcopy(filled_body())
    body["league"]["repo_urls"]["oppponent_cop"] = "https://github.com/x/y"
    with pytest.raises(ValueError, match="unknown slot"):
        load_league_config(write_league(tmp_path, body), **DRY)


@pytest.mark.parametrize("value", [0, -1, "200000", 1.5, True])
def test_a_bad_token_ceiling_is_refused_rather_than_defaulted(tmp_path, value):
    """`DeclarationContext.__post_init__` already refuses to default this field
    and that refusal is load-bearing; the loader must not undo it upstream."""
    body = copy.deepcopy(filled_body())
    body["league"][LeagueKey.TOKEN_CEILING.value] = value
    with pytest.raises((TypeError, ValueError)):
        load_league_config(write_league(tmp_path, body), **DRY)


def test_an_absent_token_ceiling_is_refused(tmp_path):
    body = copy.deepcopy(filled_body())
    del body["league"][LeagueKey.TOKEN_CEILING.value]
    with pytest.raises(KeyError, match=LeagueKey.TOKEN_CEILING.value):
        load_league_config(write_league(tmp_path, body), **DRY)


@pytest.mark.parametrize("key", ["version", "league"])
def test_a_missing_top_level_key_is_refused(tmp_path, key):
    body = copy.deepcopy(filled_body())
    del body[key]
    with pytest.raises(KeyError, match=key):
        load_league_config(write_league(tmp_path, body), **DRY)


@pytest.mark.parametrize("body", [[], "league", 3])
def test_a_non_object_file_is_refused(tmp_path, body):
    path = tmp_path / "league.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(TypeError, match="league.json"):
        load_league_config(path, **DRY)


@pytest.mark.parametrize("group", ["repo_urls", "mcp_server_addresses"])
def test_a_non_object_group_is_refused(tmp_path, group):
    body = copy.deepcopy(filled_body())
    body["league"][group] = ["https://github.com/x/y"]
    with pytest.raises(TypeError, match=group):
        load_league_config(write_league(tmp_path, body), **DRY)


def test_the_mode_argument_is_required(tmp_path):
    """A default would pick the lenient side silently, which is the whole
    thing this loader exists to prevent."""
    with pytest.raises(TypeError, match="mode"):
        load_league_config(write_league(tmp_path, filled_body()))
