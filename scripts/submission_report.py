"""Aggregation and the three-state exit contract for the Sec17 audit (08-01).

    0  every judged row PASSes
    1  at least one row is a GAP
    2  the evidence set judged NOTHING

`gate7_report.GateExit`'s contract, inherited deliberately. The third state is
not decoration: three separate gates in this project have been caught reporting
OK for having looked at nothing, and one of them was protecting a
disqualification rule. `EMPTY_EVIDENCE` therefore outranks `GAPS_FOUND`, because
a run that judged nothing cannot know whether it has gaps.

FOUR INDEPENDENT WAYS TO JUDGE NOTHING, and each is checked by name rather than
folded into one count -- an aggregate emptiness check can itself be satisfied by
one populated field:

* no rows at all, or no rows carrying a PASS/GAP verdict (UNJUDGED is not judged);
* an empty tracked set -- `git ls-files` returning nothing means every path-based
  row answered about a repository it never read;
* a mechanism walk that found no packages -- an inventory of zero mechanisms has
  a PRD for all of them;
* no README rows -- the Sec2.1 section would then be silently absent.
"""

from __future__ import annotations

from datetime import datetime, timezone

from submission_common import (
    ALL_GROUPS,
    GAP,
    PASS,
    UNJUDGED,
    Item,
    SubmissionExit,
    tracked_files,
)


def counts(items: list[Item]) -> dict[str, int]:
    """PASS / GAP / UNJUDGED tallies, plus the judged and total totals."""
    tally = {PASS: 0, GAP: 0, UNJUDGED: 0}
    for item in items:
        tally[item.verdict] = tally.get(item.verdict, 0) + 1
    return {
        "pass": tally[PASS],
        "gap": tally[GAP],
        "unjudged": tally[UNJUDGED],
        "judged": tally[PASS] + tally[GAP],
        "total": len(items),
    }


def emptiness(items: list[Item], mechanism_count: int, readme_count: int) -> list[str]:
    """Every reason this run judged nothing, named. Empty list means it judged."""
    tally = counts(items)
    reasons = []
    if not items:
        reasons.append("no audit rows were produced at all")
    if not tally["judged"]:
        reasons.append("no row carries a PASS or GAP verdict (UNJUDGED is not judged)")
    if not tracked_files():
        reasons.append("`git ls-files` returned nothing -- every path row read no repository")
    if not mechanism_count:
        reasons.append("the package walk found no mechanisms to require a PRD of")
    if not readme_count:
        reasons.append("no Sec2.1 README row was produced")
    return reasons


def build_report(items: list[Item], mechanism_count: int, readme_count: int,
                 run_suite: bool) -> dict:
    """The evidence JSON: every row, grouped, with the counts and the verdict."""
    empty = emptiness(items, mechanism_count, readme_count)
    tally = counts(items)
    if empty:
        verdict, code = "EMPTY_EVIDENCE", SubmissionExit.EMPTY_EVIDENCE
    elif tally["gap"]:
        verdict, code = "GAPS_FOUND", SubmissionExit.GAPS_FOUND
    else:
        verdict, code = "PASS", SubmissionExit.OK
    return {
        "gate": "Segal Sec17 final checklist + Sec19.1 Table 5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite_was_run": run_suite,
        "mechanisms_discovered": mechanism_count,
        "readme_rows": readme_count,
        "tracked_files": len(tracked_files()),
        "counts": tally,
        "empty_evidence_reasons": empty,
        "verdict": verdict,
        "exit_code": int(code),
        "rows": [item.as_dict() for item in items],
    }


def exit_code(report: dict) -> int:
    """The report's own recorded code -- one place decides, and it is above."""
    return int(report["exit_code"])


def _group_line(group: str, items: list[Item]) -> str:
    rows = [item for item in items if item.group == group]
    tally = counts(rows)
    return (f"  {group}: {tally['pass']} PASS, {tally['gap']} GAP, "
            f"{tally['unjudged']} UNJUDGED")


def print_summary(report: dict, items: list[Item]) -> None:
    """One line per group, then every GAP with the path its fix belongs in."""
    print("Sec17 + Table-5 submission audit")
    for group in ALL_GROUPS:
        print(_group_line(group, items))
    tally = report["counts"]
    print(f"  TOTAL: {tally['pass']} PASS, {tally['gap']} GAP, "
          f"{tally['unjudged']} UNJUDGED over {tally['total']} rows "
          f"({tally['judged']} judged)")
    print(f"  mechanisms discovered: {report['mechanisms_discovered']}; "
          f"tracked files: {report['tracked_files']}; suite run: {report['suite_was_run']}")
    gaps = [item for item in items if item.verdict == GAP]
    if gaps:
        print(f"\nGAPS ({len(gaps)}) -- each with the path its fix must land in:")
        for item in gaps:
            print(f"  [{item.item_id}] {item.requirement}")
            print(f"      -> {item.fix_path or '<no path recorded>'}  |  {item.evidence}")
    for reason in report["empty_evidence_reasons"]:
        print(f"EMPTY EVIDENCE: {reason}")
    print(f"\nVERDICT: {report['verdict']} (exit {report['exit_code']})")
