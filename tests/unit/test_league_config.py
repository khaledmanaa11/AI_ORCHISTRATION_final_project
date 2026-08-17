"""`shared/league_config.py` -- the loader's happy path, its refusals, and the
two SHIPPED files read off disk.

The shipped-file cases matter more than the synthetic ones: rule 49's four
links and PARAMETERS:165's declaration content have to be real in
`config/{police,thief}/league.json`, not merely representable.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from pursuit.shared.absent import is_stated_absent
from pursuit.shared.league_config import (
    MCP_ADDRESS_SLOTS,
    REPO_URL_SLOTS,
    load_league_config,
)
from pursuit.shared.reporting_config import ReportingMode
from tests.unit.league_config_fixtures import filled_body, shipped, write_league

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIPPED_FILES = (REPO_ROOT / "config/police/league.json", REPO_ROOT / "config/thief/league.json")

DRY = {"mode": ReportingMode.DRY_RUN}
LIVE = {"mode": ReportingMode.LIVE}


@pytest.mark.parametrize("path", SHIPPED_FILES, ids=lambda p: p.parent.name)
def test_the_shipped_file_loads_in_dry_run_with_every_slot_stated_absent(path):
    params = load_league_config(path, **DRY)
    assert set(params.repo_urls) == set(REPO_URL_SLOTS)
    assert set(params.mcp_server_addresses) == set(MCP_ADDRESS_SLOTS)
    assert len(params.absent_slots()) == len(REPO_URL_SLOTS) + len(MCP_ADDRESS_SLOTS)


@pytest.mark.parametrize("path", SHIPPED_FILES, ids=lambda p: p.parent.name)
def test_the_shipped_file_is_refused_in_live_mode(path):
    """The absences cannot survive into a scored game unnoticed (rule 49)."""
    with pytest.raises(ValueError, match="rule 49"):
        load_league_config(path, **LIVE)


@pytest.mark.parametrize("path", SHIPPED_FILES, ids=lambda p: p.parent.name)
def test_the_shipped_token_ceiling_is_the_table_18_row_4_figure(path):
    """docs/PARAMETERS.md:83 -- ~200,000, NEGOTIABLE. Read, never defaulted."""
    assert load_league_config(path, **DRY).token_ceiling == 200000


@pytest.mark.parametrize("path", SHIPPED_FILES, ids=lambda p: p.parent.name)
def test_the_shipped_file_carries_no_games_played_leaf(path):
    """Rule 38 is an ABSOLUTE disqualification and the value is a human's.
    A config leaf is the quiet place a chosen number would hide in."""
    raw = json.dumps(json.loads(path.read_text(encoding="utf-8"))["league"])
    assert "games_played" not in raw


@pytest.mark.parametrize("path", SHIPPED_FILES, ids=lambda p: p.parent.name)
def test_no_shipped_slot_holds_a_url_shaped_string(path):
    """The invented-value failure in its most reasonable disguise: a guessed
    `https://github.com/...` literal that reads as a claim in the artifact."""
    league = json.loads(path.read_text(encoding="utf-8"))["league"]
    values = list(league["repo_urls"].values()) + list(league["mcp_server_addresses"].values())
    assert values == [None] * len(values)


def test_absent_slots_are_rendered_as_markers_for_the_declaration(tmp_path):
    urls = load_league_config(shipped(tmp_path), **DRY).declaration_repo_urls()
    assert set(urls) == set(REPO_URL_SLOTS)
    assert all(is_stated_absent(value) for value in urls.values())
    assert all("08-12" in value["detail"] for value in urls.values())


def test_a_filled_file_loads_in_live_mode_and_reports_no_absences(tmp_path):
    params = load_league_config(write_league(tmp_path, filled_body()), **LIVE)
    assert params.absent_slots() == ()
    assert params.declaration_repo_urls()["own_cop"].startswith("https://github.com/")
    assert not any(is_stated_absent(v) for v in params.declaration_mcp_addresses().values())


def _mutate(tmp_path, group, slot, value):
    body = copy.deepcopy(filled_body())
    body["league"][group][slot] = value
    return write_league(tmp_path, body)


@pytest.mark.parametrize(
    "value",
    ["https://github.com/example/cop", "https://github.com/team/TODO", "https://<team>/cop"],
)
def test_a_placeholder_url_is_refused_in_live_mode(tmp_path, value):
    with pytest.raises(ValueError, match="placeholder"):
        load_league_config(_mutate(tmp_path, "repo_urls", "own_cop", value), **LIVE)


def test_a_placeholder_url_is_permitted_in_dry_run(tmp_path):
    """Dry-run play is not a submission; the refusal is scoped to `live`."""
    path = _mutate(tmp_path, "repo_urls", "own_cop", "https://github.com/example/cop")
    assert load_league_config(path, **DRY).repo_urls["own_cop"].endswith("example/cop")


@pytest.mark.parametrize("value", [7, "", "   ", []])
def test_a_non_url_slot_value_is_refused_in_both_modes(tmp_path, value):
    path = _mutate(tmp_path, "mcp_server_addresses", "own", value)
    with pytest.raises((TypeError, ValueError)):
        load_league_config(path, **DRY)
