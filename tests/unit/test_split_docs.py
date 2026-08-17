"""The rule-49 cross-link block a split repository's README carries (08-10).

THE CROSS-LINK URLS DO NOT EXIST YET. The two repositories are created and
pushed by a human at 08-12, so every test here asserts the ABSENCE of a
URL-shaped string as hard as it asserts the presence of the marker. A plausible
`https://github.com/<user>/<repo>` placeholder is the invented-value failure
(CLAUDE.md "never invent a numeric value", and rule 49 wants REAL links) wearing
its most reasonable disguise -- and unlike a missing link, a placeholder reads as
done. This is the discipline 08-04 used for `league.json`.

INJECTION RAISES WHEN IT CANNOT FIND ITS ANCHOR. A splitter that silently
returns the README unchanged ships a repository with no cross-link at all, and
the build would still report success.
"""

from __future__ import annotations

import pytest

from tests.unit.submission_gate_helpers import load

docs_mod = load("split_docs")

SHA = "0f6fbf3"
STAMP = "2026-08-17T00:00:00Z"
URL_SHAPES = ("http://", "https://", "github.com", "example.com", "<url>", "TODO")


@pytest.mark.parametrize("role", ["police", "thief"])
def test_the_banner_names_its_own_role_and_its_companion(role: str) -> None:
    text = docs_mod.banner(role, SHA, STAMP)
    other = docs_mod.COMPANION[role]
    assert f"`{role}`" in text
    assert f"`{other}`" in text
    assert SHA in text


@pytest.mark.parametrize("role", ["police", "thief"])
def test_the_banner_states_both_urls_absent_and_invents_neither(role: str) -> None:
    text = docs_mod.banner(role, SHA, STAMP)
    assert text.count(docs_mod.URL_ABSENT) == 2, text
    lowered = text.lower()
    for shape in URL_SHAPES:
        assert shape.lower() not in lowered, f"the banner carries a URL-shaped {shape!r}"


def test_the_two_banners_are_not_the_same_document() -> None:
    assert docs_mod.banner("police", SHA, STAMP) != docs_mod.banner("thief", SHA, STAMP)


def test_the_banner_carries_a_machine_checkable_marker() -> None:
    text = docs_mod.banner("police", SHA, STAMP)
    assert docs_mod.MARKER in text
    assert "role=police" in text


def test_injection_places_the_banner_after_the_first_heading() -> None:
    readme = "# Title\n\nintro line\n\n## Installation\n\nbody\n"
    out = docs_mod.inject(readme, docs_mod.banner("thief", SHA, STAMP))
    lines = out.splitlines()
    assert lines[0] == "# Title"
    assert docs_mod.MARKER in out
    assert out.index(docs_mod.MARKER) < out.index("## Installation")
    for original in ("intro line", "## Installation", "body"):
        assert original in out


def test_injection_refuses_a_readme_with_no_top_level_heading() -> None:
    with pytest.raises(docs_mod.MissingAnchorError):
        docs_mod.inject("no heading here\n", docs_mod.banner("police", SHA, STAMP))


def test_injection_refuses_to_run_twice() -> None:
    once = docs_mod.inject("# Title\n\nbody\n", docs_mod.banner("police", SHA, STAMP))
    with pytest.raises(docs_mod.MissingAnchorError):
        docs_mod.inject(once, docs_mod.banner("police", SHA, STAMP))


def test_the_provenance_document_reports_counts_not_adjectives() -> None:
    text = docs_mod.provenance("police", SHA, STAMP, included=907, excluded=(
        ("config/police/games_played.json", "D-77: live rule-37 counter"),
    ))
    assert "907" in text
    assert "config/police/games_played.json" in text
    assert "D-77" in text
    assert "core.hooksPath scripts/hooks" in text
    for shape in URL_SHAPES:
        assert shape.lower() not in text.lower()


def test_the_provenance_document_refuses_a_zero_file_build() -> None:
    with pytest.raises(docs_mod.EmptyBuildError):
        docs_mod.provenance("police", SHA, STAMP, included=0, excluded=())
