"""The three human-run runbooks 08-11 owes (08-11).

08-12, 08-13 and 08-14 are the phase's three `autonomous: false` plans. Each is
handed a runbook, and a runbook is only worth its paper if (a) every path and
command it tells a human to run actually exists, and (b) it says plainly which
steps no agent may take.

`unresolved_citations` RESOLVES AGAINST `git ls-files`, NOT THE FILESYSTEM: an
untracked file cannot reach the human following the runbook on another machine.
The same helper caught a README citing a script deleted three commits earlier.

EVERY ASSERTION HERE CARRIES A COUNT. A runbook that was never tracked reads as
empty text through `read_tracked`, and an empty document trivially has no broken
citations -- so the citation counts are floored rather than merely checked.
"""

from __future__ import annotations

from tests.unit.doc_citation_helpers import cited_paths, unresolved_citations
from tests.unit.submission_gate_helpers import load

common = load("submission_common")

PHASE_8 = "docs/phases/phase-8/"
RUNBOOKS = {
    f"{PHASE_8}PUBLISH-RUNBOOK.md": "08-12",
    f"{PHASE_8}LEAGUE-RUNBOOK.md": "08-13",
    f"{PHASE_8}SUBMISSION-RUNBOOK.md": "08-14",
}
#: The four acts an agent may not perform, each named in every runbook.
FORBIDDEN_ACTS = ("credential", "consent", "repositor", "mail")
#: A runbook citing fewer paths than this is not telling anyone what to run.
MIN_CITED_PATHS = 6
#: Paths a runbook may cite that `git ls-files` will never return, with the reason.
#: The first run of this module found these three cited as though they shipped.
#: `test_the_local_only_exemptions_are_really_untracked` refuses an exemption for
#: anything that IS tracked, so this list cannot be used to wave through a typo.
LOCAL_ONLY_PATHS = {
    "config/police/games_played.json": "live rule-37 state, gitignored and per-machine (D-77)",
    "config/thief/games_played.json": "live rule-37 state, gitignored and per-machine (D-77)",
    "config/police/league_ledger.json": "written on league day by 08-13; absent until then",
    "config/thief/league_ledger.json": "written on league day by 08-13; absent until then",
}


def _text(path: str) -> str:
    return common.read_tracked(path)


def test_all_three_runbooks_are_tracked_and_non_empty() -> None:
    sizes = {path: len(_text(path)) for path in RUNBOOKS}
    assert len(sizes) == 3
    assert all(size > 2000 for size in sizes.values()), sizes


def test_every_runbook_names_the_plan_that_runs_it() -> None:
    missing = [path for path, plan in RUNBOOKS.items() if plan not in _text(path)]
    assert not missing, f"runbook does not name its own plan: {missing}"


def test_every_runbook_states_what_no_agent_may_do() -> None:
    """The boundary, in the document itself -- not only in a plan's summary."""
    gaps = {}
    for path in RUNBOOKS:
        lowered = _text(path).lower()
        absent = [word for word in FORBIDDEN_ACTS if word not in lowered]
        if absent or "cannot" not in lowered:
            gaps[path] = absent or ["cannot"]
    assert not gaps, f"runbooks that do not state the agent boundary: {gaps}"


def test_every_path_each_runbook_cites_resolves() -> None:
    broken = {
        path: [missing for missing in unresolved_citations(path)
               if missing not in LOCAL_ONLY_PATHS]
        for path in RUNBOOKS
    }
    broken = {path: missing for path, missing in broken.items() if missing}
    assert not broken, f"runbooks citing paths that do not exist: {broken}"


def test_the_local_only_exemptions_are_really_untracked() -> None:
    """An exemption for a path that ships is a hole, not an exemption."""
    tracked = common.tracked_files()
    wrongly_exempt = [path for path in LOCAL_ONLY_PATHS if path in tracked]
    assert not wrongly_exempt, (
        f"these are tracked and must not be exempted: {wrongly_exempt}"
    )
    assert len(LOCAL_ONLY_PATHS) == 4


def test_every_runbook_that_cites_a_local_only_path_says_it_is_local_only() -> None:
    """A human on a fresh clone must not go looking for a file that is not there."""
    silent = [
        path for path in RUNBOOKS
        if any(local in _text(path) for local in LOCAL_ONLY_PATHS)
        and "gitignored" not in _text(path)
    ]
    assert not silent, f"cites a gitignored path without saying so: {silent}"


def test_each_runbook_cites_enough_paths_to_be_followable() -> None:
    """The anti-vacuity floor: an untracked runbook reads as '' and cites nothing."""
    counts = {path: len(cited_paths(path)) for path in RUNBOOKS}
    assert all(count >= MIN_CITED_PATHS for count in counts.values()), counts


def test_the_citation_checker_fires_on_a_path_that_does_not_exist() -> None:
    """The control for the two tests above."""
    from tests.unit import doc_citation_helpers as helpers

    planted = "`scripts/definitely_not_a_real_script.py`"
    assert helpers.CITED.findall(planted) == ["scripts/definitely_not_a_real_script.py"]
    tracked = common.tracked_files()
    assert "scripts/definitely_not_a_real_script.py" not in tracked


def test_no_runbook_tells_a_human_to_push_from_the_development_repository() -> None:
    """The trap the 08 outline names: `git push` typed in the wrong window."""
    publish = _text(f"{PHASE_8}PUBLISH-RUNBOOK.md")
    assert "never in the development repository" in publish
    assert "git push --tags" in publish, "the reflex that must be warned against is not named"
