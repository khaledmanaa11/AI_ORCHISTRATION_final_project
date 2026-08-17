"""The Act 4.3 survival pair, corrected everywhere it is quoted (08-11).

08-09's sweep re-measured `docs/phases/phase-3/ENGINEERING-LOG.md` Act 4.3's
`89% -> 1%` thief-survival pair and got `32.0% -> 7.5%`. The pair had been quoted
onward into three more artifacts, all four of which ship into the two public
submission repositories. 08-09 recorded the finding and did not own the fix; this
file is the fix's pin.

WHAT IS ASSERTED, AND WHY EACH PART IS THERE:

* **the reproducible pair**, taken from `artifacts/sensitivity/reconcile.json`
  rather than typed here -- so a re-run that moves the numbers fails this test
  instead of quietly disagreeing with four documents;
* **the measuring script is named** in every site, because a corrected number
  with no way to re-derive it is the same defect one decimal place over;
* **the old claim survives** in every site. This is the append-with-correction
  discipline the GATE-6 claim and the `RULES.md` survival order already used
  here: a silent overwrite erases the evidence that the repository once
  published an unreproducible figure;
* **the cause is stated as never established.** The sweep did not identify which
  of the eight changed variables moved the number, and no site may imply it did.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECONCILE = REPO_ROOT / "artifacts" / "sensitivity" / "reconcile.json"

#: The four artifacts that quote the pair. ENGINEERING-LOG is where it originated.
SITES = (
    "docs/phases/phase-3/ENGINEERING-LOG.md",
    "docs/phases/phase-3/PRD.md",
    "docs/phases/phase-3/PLAN.md",
    "src/pursuit/shared/resolution.py",
)
MEASURING_SCRIPT = "scripts/sensitivity_reconcile.py"

#: The like-for-like arms: shipped weights, negotiated opening -- the setting the
#: original claim describes. Named, not indexed, so a renamed arm fails loudly.
BOOK_ONLY_ARM = "run2/book_only/negotiated"
SWAP_ARM = "run2/swap/negotiated"

_NOT_ESTABLISHED = re.compile(r"cause was n(?:ot|ever) established", re.IGNORECASE)


def measured_pair() -> tuple[str, str]:
    """`('32.0%', '7.5%')` -- rendered from the artifact, never typed."""
    arms = json.loads(RECONCILE.read_text(encoding="utf-8"))["arms"]
    missing = [name for name in (BOOK_ONLY_ARM, SWAP_ARM) if name not in arms]
    assert not missing, f"reconcile.json no longer carries arm(s) {missing}"
    return f"{arms[BOOK_ONLY_ARM]['rate']:.1%}", f"{arms[SWAP_ARM]['rate']:.1%}"


def recorded_pair() -> tuple[str, str]:
    """`('89%', '1%')` -- the claim being corrected, also read from the artifact."""
    claim = json.loads(RECONCILE.read_text(encoding="utf-8"))["recorded_claim"]
    return f"{claim['book_only_percent']}%", f"{claim['swap_percent']}%"


def _text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_all_four_sites_are_tracked_files() -> None:
    """The control: a correction written into an untracked file ships nowhere."""
    tracked = subprocess.run(
        ["git", "ls-files", *SITES], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert len(SITES) == 4
    assert sorted(tracked) == sorted(SITES), f"not tracked: {set(SITES) - set(tracked)}"


def test_the_artifact_still_yields_both_pairs() -> None:
    """A parser that returns nothing would make every assertion below vacuous."""
    measured, recorded = measured_pair(), recorded_pair()
    assert all(re.fullmatch(r"\d+(\.\d)?%", value) for value in measured + recorded)
    assert measured != recorded


def test_every_site_carries_the_reproducible_pair() -> None:
    book_only, swap = measured_pair()
    missing = [path for path in SITES
               if book_only not in _text(path) or swap not in _text(path)]
    assert not missing, (
        f"these artifacts do not quote the re-measured pair {book_only} -> {swap}: {missing}"
    )


def test_every_site_names_the_script_that_measured_it() -> None:
    missing = [path for path in SITES if MEASURING_SCRIPT not in _text(path)]
    assert not missing, f"corrected without naming {MEASURING_SCRIPT}: {missing}"


def test_every_site_still_shows_the_claim_it_corrects() -> None:
    """Append-with-correction. A silent overwrite passes the two tests above."""
    old_book_only, old_swap = recorded_pair()
    pattern = re.compile(rf"(?<!\d){re.escape(old_book_only)}")
    swap_pattern = re.compile(rf"(?<!\d){re.escape(old_swap)}")
    missing = [path for path in SITES
               if not pattern.search(_text(path)) or not swap_pattern.search(_text(path))]
    assert not missing, (
        f"the superseded {old_book_only} -> {old_swap} claim was erased rather than "
        f"corrected in: {missing}"
    )


def test_every_site_says_the_cause_was_never_established() -> None:
    missing = [path for path in SITES if not _NOT_ESTABLISHED.search(_text(path))]
    assert not missing, f"no 'cause was never established' statement in: {missing}"


def test_the_cause_phrase_detector_is_not_matching_everything() -> None:
    """Positive and negative control for the one regex the test above trusts."""
    assert _NOT_ESTABLISHED.search("the cause was never established by this sweep")
    assert _NOT_ESTABLISHED.search("The cause was not established.")
    assert not _NOT_ESTABLISHED.search("the cause was established: the weights moved")
