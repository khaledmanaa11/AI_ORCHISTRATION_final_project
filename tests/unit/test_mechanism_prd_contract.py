"""§2.3's "critical requirement" — a PRD per mechanism — held to the tree (08-08).

`scripts/submission_mechanisms.py` already walks the packages and answers each
from `docs/mechanism-prd-map.json`. This file pins the three things that walk
cannot see, and that a document is free to get wrong quietly:

* a cited PRD must cite only paths that still exist — the drift that put a
  deleted command in the README and a withdrawn Q-learning agent in its
  opening paragraph;
* the register must never launder a **superseded** PRD into coverage, and the
  superseded banner it depends on must still be there and still point somewhere;
* `PRD_mcp_transport.md`'s tunnel exclusion is the whole reason `PRD_tunnel.md`
  exists, so the exclusion is asserted rather than remembered.
"""

from __future__ import annotations

import json

from tests.unit.doc_citation_helpers import cited_paths, unresolved_citations
from tests.unit.submission_gate_helpers import load

common = load("submission_common")
mechanisms = load("submission_mechanisms")

NEW_PRDS = ("docs/PRD_sdk.md", "docs/PRD_tunnel.md", "docs/PRD_gui.md")
SUPERSEDED = "docs/PRD_rl_strategy.md"
TRANSPORT = "docs/PRD_mcp_transport.md"


def _register() -> dict:
    return json.loads(common.read_tracked(mechanisms.REGISTER))["mechanisms"]


def test_every_package_the_walk_finds_is_answered_by_the_register():
    packages = mechanisms.discovered_packages()
    assert len(packages) >= 10, packages
    assert set(packages) <= set(_register()), sorted(set(packages) - set(_register()))


def test_every_register_entry_names_a_prd_or_a_reason():
    for package, entry in _register().items():
        assert entry.get("prds") or (entry.get("reason") or "").strip(), package


def test_the_register_answers_for_the_tree_and_nothing_else():
    stale = sorted(set(_register()) - set(mechanisms.discovered_packages()))
    assert stale == [], stale


def test_the_three_missing_prds_now_exist_and_are_cited():
    cited = {path for entry in _register().values() for path in entry.get("prds") or []}
    for prd in NEW_PRDS:
        assert common.is_tracked(prd), prd
    assert {"docs/PRD_sdk.md", "docs/PRD_gui.md"} <= cited, sorted(cited)


def test_no_cited_prd_is_superseded():
    """A DO-NOT-IMPLEMENT banner is not coverage; the resolver refuses it."""
    for entry in _register().values():
        for prd in entry.get("prds") or []:
            live, note = mechanisms._prd_is_live(prd)
            assert live, note


def test_the_superseded_banner_is_intact_and_still_points_somewhere():
    text = common.read_tracked(SUPERSEDED)
    assert "SUPERSEDED" in text
    assert "PRD_matrix_mover.md" in text
    assert common.is_tracked("docs/PRD_matrix_mover.md")


def test_the_transport_prd_still_excludes_the_tunnel():
    """The derivation `PRD_tunnel.md` rests on. If the transport PRD ever
    absorbs the tunnel, this fails instead of leaving two owners."""
    text = common.read_tracked(TRANSPORT)
    assert "Out of scope" in text
    assert "tunneling" in text


def test_the_tunnel_prd_is_the_one_that_names_the_tunnel_module():
    text = common.read_tracked("docs/PRD_tunnel.md")
    assert "src/pursuit/network/tunnel_manager.py" in text
    assert "src/pursuit/network/secret_guard.py" in text


def test_each_new_prd_cites_only_paths_that_exist():
    for prd in NEW_PRDS:
        assert unresolved_citations(prd) == [], prd


def test_the_citation_scan_over_the_new_prds_is_not_vacuous():
    """A PRD citing nothing would pass the test above having read nothing.

    Two floors, not one. `PRD_gui.md` (08-08's first, written before this
    contract existed) writes many of its references as bare module names --
    `turn_language.py:57` -- which the backtick-path scan cannot see and which
    this contract deliberately does not force a rewrite to satisfy. The two
    PRDs written against the contract carry the higher floor.
    """
    for prd in NEW_PRDS:
        assert len(cited_paths(prd)) >= 5, (prd, cited_paths(prd))
    for prd in ("docs/PRD_sdk.md", "docs/PRD_tunnel.md"):
        assert len(cited_paths(prd)) >= 15, (prd, cited_paths(prd))


def test_each_new_prd_traces_its_numbers_to_a_source():
    """§2.3 and CLAUDE.md rule 1: a number without a source is disqualifying."""
    for prd in ("docs/PRD_sdk.md", "docs/PRD_tunnel.md"):
        text = common.read_tracked(prd)
        assert "Parameters and their sources" in text, prd
        assert "docs/PARAMETERS.md" in text, prd
