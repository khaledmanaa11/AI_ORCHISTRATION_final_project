"""The three research documents may not carry a number, a path or a commit
that is not real (08-09).

THE GENERATED BLOCKS ARE RE-RENDERED AND COMPARED. Each of
`docs/SENSITIVITY.md`, `docs/TOKEN-COST.md` and `docs/PROMPT_LOG.md` embeds
a block between two markers; the renderer is re-run here against the
committed artifact and the result must appear in the file verbatim. A figure
edited in by hand fails here instead of reaching a grader.

THE CITATIONS ARE RESOLVED, NOT TRUSTED. Every backticked repository path in
the three documents is put to the filesystem and every short commit hash to
`git cat-file`. The immediate reason is that an earlier plan in this phase
shipped two script names that did not exist; the general reason is that a
document whose citations do not resolve is worse than one with no citations,
because it invites a reader to stop checking.
"""

from __future__ import annotations

import re
import subprocess

import pytest

from tests.unit.submission_gate_helpers import REPO_ROOT, load

common = load("submission_common")
sensitivity = load("sensitivity_report")
reconcile = load("sensitivity_reconcile")
token_cost = load("token_cost_report")
prompt_log = load("prompt_log_evidence")

SENSITIVITY_DOC = "docs/SENSITIVITY.md"
TOKEN_COST_DOC = "docs/TOKEN-COST.md"
PROMPT_LOG_DOC = "docs/PROMPT_LOG.md"
DOCS = (SENSITIVITY_DOC, TOKEN_COST_DOC, PROMPT_LOG_DOC)
#: `submission_docs.MIN_DOC_LINES` -- the floor the Sec17 gate applies.
MIN_LINES = 20
_ROOTS = ("docs/", "scripts/", "src/", "tests/", "training/", "artifacts/",
          "notebooks/", "config/", ".planning/")
_PATH = re.compile(r"`([^`\s]+\.[A-Za-z0-9]+[^`\s]*|[^`\s]+/)`")
_HASH = re.compile(r"`([0-9a-f]{7})`")


def _text(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


@pytest.mark.parametrize("relative", DOCS)
def test_each_document_is_tracked_and_clears_the_gate_floor(relative):
    assert common.is_tracked(relative), relative
    lines = [line for line in _text(relative).splitlines() if line.strip()]
    assert len(lines) >= MIN_LINES, f"{relative}: {len(lines)} non-blank lines"


def test_the_sweep_tables_are_regenerated_not_typed():
    block = sensitivity.render(sensitivity.load())
    assert block in _text(SENSITIVITY_DOC), "run scripts/sensitivity_report.py and re-splice"


def test_the_reconciliation_table_is_regenerated_not_typed():
    import json
    data = json.loads((REPO_ROOT / "artifacts" / "sensitivity" / "reconcile.json")
                      .read_text(encoding="utf-8"))
    assert reconcile.render(data) in _text(SENSITIVITY_DOC)


def test_the_token_cost_tables_are_regenerated_not_typed():
    assert token_cost.render(token_cost.build()) in _text(TOKEN_COST_DOC)


def test_the_prompt_evidence_table_is_regenerated_not_typed():
    block = prompt_log.render(prompt_log.hint_rounds(), prompt_log.word_limit())
    assert block in _text(PROMPT_LOG_DOC)


def test_a_hand_edited_figure_would_be_caught():
    """The control for the four tests above: they compare a BLOCK, so a
    single changed digit inside it breaks the match."""
    block = token_cost.render(token_cost.build())
    tampered = block.replace("96.4%", "99.9%", 1)
    assert tampered != block, "the mutation did not land"
    assert tampered not in _text(TOKEN_COST_DOC)


@pytest.mark.parametrize("relative", DOCS)
def test_every_cited_repository_path_resolves(relative):
    cited = {
        candidate.split(":")[0]
        for candidate in _PATH.findall(_text(relative))
        if candidate.startswith(_ROOTS)
    }
    assert len(cited) >= 5, f"{relative}: the path regex matched almost nothing: {cited}"
    for path in sorted(cited):
        if "*" in path or "[" in path:
            assert list(REPO_ROOT.glob(path)), f"{relative} cites `{path}`, which matches nothing"
        else:
            assert (REPO_ROOT / path).exists(), f"{relative} cites `{path}`, which does not exist"


def test_every_cited_commit_hash_resolves():
    """NOT parametrized, deliberately.

    Only `docs/PROMPT_LOG.md` cites commits; the other two carry none, so a
    per-document version would pass over an empty list for two of its three
    parametrizations and the regex would be proven live by only one of them.
    Gathering across all three and asserting a floor makes every run check
    something. Skipped on a tree with no history -- 08-10's split repos are
    built with a single initial commit and a hash from this repo cannot
    exist there -- and the skip names its reason rather than passing.
    """
    depth = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=False)
    if depth.returncode != 0 or int(depth.stdout.strip() or 0) < 50:
        pytest.skip("no development history here (a split/export tree)")
    cited = {short for relative in DOCS for short in _HASH.findall(_text(relative))}
    assert len(cited) >= 3, f"the commit-hash regex matched almost nothing: {cited}"
    for short in sorted(cited):
        found = subprocess.run(["git", "cat-file", "-e", f"{short}^{{commit}}"],
                               cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        assert found.returncode == 0, f"cited commit `{short}` does not exist"


def test_no_document_claims_a_league_result_or_a_games_played_value():
    """Rule 38 makes a false games-played declaration an absolute
    disqualification, and no league game has been played at all.

    The disclaimer rule has two branches -- a document that mentions the
    league must carry "no league game", and one that never mentions it needs
    nothing. `docs/PROMPT_LOG.md` takes the trivial branch, so the test
    additionally asserts that the NON-trivial branch is exercised by at
    least one document. Without that, deleting the disclaimer from all three
    and every mention of the league with it would still pass.
    """
    disclaimed = 0
    for relative in DOCS:
        text = _text(relative).lower()
        for forbidden in ("games_played_declared", "games played so far", "league standing",
                          "we won", "our record against"):
            assert forbidden not in text, f"{relative} contains {forbidden!r}"
        if "league" in text:
            assert "no league game" in text, f"{relative} mentions the league without the clause"
            disclaimed += 1
    assert disclaimed >= 2, "no document exercised the disclaimer branch"
