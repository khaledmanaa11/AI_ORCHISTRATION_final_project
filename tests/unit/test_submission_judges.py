"""The Sec17 audit's individual judges, and the shortcuts each one refuses
(08-01).

Every test here pins a way the audit could have been written that would report
a pass it had not earned:

* a mermaid GREP would count `docs/phases/phase-8/TODO.md`, whose table cell
  quotes the command; a rendered block has to own its whole line;
* Table 5's aggregation over a cited row that does not exist would fold an empty
  list into a pass;
* the superseded-mechanism derivation would go green the moment a banner is
  deleted, so an empty derivation is UNJUDGED and not PASS;
* an allowlist entry must never suppress a provider-issued key shape.
"""

from __future__ import annotations

from tests.unit.submission_gate_helpers import load

common = load("submission_common")
docs = load("submission_docs")
honesty = load("submission_readme_honesty")
scan = load("submission_scan")
table5 = load("submission_table5")

GROUP = common.GROUP_1
_FENCE = docs._FENCE


def test_a_quoted_mermaid_string_is_not_a_rendered_block():
    """The exact shape `docs/phases/phase-8/TODO.md` carries today.

    `.match` alone would refuse this line whatever the pattern said, so the
    assertion that carries weight is the `.search` one: a judge written with
    `search` -- or with `'```mermaid' in text` -- counts the quoted command as a
    diagram, and that is the weakening this test exists to fail on.
    """
    quoted = "| 08-07 ... | today `grep -rl '```mermaid' docs/` returns nothing |"
    assert _FENCE.match(quoted) is None
    assert _FENCE.search(quoted) is None


def test_a_real_fence_is_a_rendered_block():
    for line in ("```mermaid", "   ```mermaid", "```mermaid   "):
        assert _FENCE.match(line) is not None, line


def test_the_real_trap_file_is_not_counted_as_a_diagram():
    """End to end over the real tree, with the trap proven to exist first.

    `docs/phases/phase-8/TODO.md` really does contain the literal fence string,
    inside a table cell that quotes the grep command. If that first assertion
    ever stops holding this test has lost its subject and says so, rather than
    passing over a file that no longer poses the problem.
    """
    trap = "docs/phases/phase-8/TODO.md"
    assert "```mermaid" in common.read_tracked(trap), (
        f"{trap} no longer quotes the fence string -- this test has lost its subject"
    )
    assert trap not in docs.mermaid_blocks()


def test_table5_refuses_a_cited_row_that_was_never_produced():
    """An empty backing set must be a GAP, not a vacuous pass."""
    verdict, evidence = table5._worst(("NO-SUCH-ROW",), {})
    assert verdict == common.GAP
    assert "not produced by this run" in evidence


def test_table5_takes_the_worst_of_its_cited_rows():
    rows = {
        "A": common.judge("A", GROUP, "r", True, "e", "p"),
        "B": common.unjudged("B", GROUP, "r", "w"),
        "C": common.judge("C", GROUP, "r", False, "e", "p"),
    }
    assert table5._worst(("A",), rows)[0] == common.PASS
    assert table5._worst(("A", "B"), rows)[0] == common.UNJUDGED
    assert table5._worst(("A", "B", "C"), rows)[0] == common.GAP


def test_superseded_row_is_unjudged_when_nothing_is_superseded(monkeypatch):
    """Deleting a banner must not be a way to turn this row green."""
    monkeypatch.setattr(honesty, "superseded_terms", dict)
    row = honesty.superseded_row("we ship a trained tabular Q-Learning policy")
    assert row.verdict == common.UNJUDGED
    assert row.verdict != common.PASS


def test_superseded_row_fires_on_an_unqualified_mention(monkeypatch):
    monkeypatch.setattr(honesty, "superseded_terms",
                        lambda: {"docs/PRD_x.md": ["Q-Learning"]})
    assert honesty.superseded_row("decides moves with a Q-learning policy").verdict \
        == common.GAP


def test_superseded_row_accepts_a_qualified_mention(monkeypatch):
    monkeypatch.setattr(honesty, "superseded_terms",
                        lambda: {"docs/PRD_x.md": ["Q-Learning"]})
    assert honesty.superseded_row(
        "the Q-learning policy was superseded in Phase 3").verdict == common.PASS


def test_phase_status_row_is_unjudged_with_no_verification_files(monkeypatch):
    monkeypatch.setattr(honesty, "_verified_phases", list)
    assert honesty.phase_status_row("| 3 | in progress |").verdict == common.UNJUDGED


def test_phase_status_row_fires_on_a_verified_phase_called_in_progress(monkeypatch):
    monkeypatch.setattr(honesty, "_verified_phases", lambda: ["03"])
    assert honesty.phase_status_row(
        "| 3 | Strategy module (in progress) |").verdict == common.GAP


def test_provider_key_shapes_are_recognised():
    planted = "sk-" + "ant-" + "A" * 24
    assert scan._provider_match(planted)
    assert not scan._provider_match("sk-ant-")


def test_both_scanner_controls_fire():
    provider, generic = scan._controls()
    assert provider and generic


def test_generic_pattern_matches_a_credential_shaped_assignment():
    import re
    assert re.search(scan.GENERIC_PATTERN, 'api_key = "' + "B" * 20 + '"')
    assert not re.search(scan.GENERIC_PATTERN, 'api_key = "short"')
