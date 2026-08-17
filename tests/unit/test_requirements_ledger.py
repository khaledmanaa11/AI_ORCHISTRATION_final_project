"""`.planning/REQUIREMENTS.md`'s gate, and the hole its own probe found (08-02).

THE FIRST VERSION OF THIS GATE PASSED THE PROBE THAT WAS MEANT TO BREAK IT.
Flipping `SUB-05` from `[ ]` to `[x]` produced **exit 0**, because the open row
legitimately cited the artifact explaining why it was open and a path-and-quote
check cannot tell "evidence that this is done" from "evidence that this is not".
One character produced a green ledger claiming a Git tag existed while
`git tag -l` was empty.

Three independent rules close it, and all three are pinned below:

1. a ticked row must carry `**evidence:**` with a resolvable `path` "quote";
2. an open row must carry `**open:**` and must NOT carry `**evidence:**`;
3. every traceability row declares `**N/M ticked**`, and the gate counts the
   family and compares -- which catches the flip, catches the reverse (quietly
   un-ticking earned work), and cannot be defeated by renaming a marker.

The live ledger is asserted green here too, so a future edit that breaks it
fails the suite rather than waiting for someone to run the script.
"""

from __future__ import annotations

import pytest

from tests.unit.submission_gate_helpers import load

ledger_mod = load("requirements_ledger")
trace = load("requirements_trace")

LIVE = ledger_mod.LEDGER.read_text(encoding="utf-8")


def _parse(text: str):
    return ledger_mod.parse(text)


def test_the_live_ledger_is_clean():
    parsed = _parse(LIVE)
    assert parsed.violations == []
    assert ledger_mod.emptiness(parsed) == []


def test_the_live_ledger_declares_its_real_total():
    parsed = _parse(LIVE)
    assert parsed.total == parsed.declared_total
    assert parsed.total > 0, "a ledger with no checkboxes proves nothing"


def test_every_tick_resolved_to_a_real_quote():
    parsed = _parse(LIVE)
    assert parsed.citations_resolved == len(parsed.ticked)


def test_flipping_one_row_to_ticked_fails():
    """PROBE 1 -- the case the first version of this gate let through."""
    assert "- [ ] **SUB-05**:" in LIVE, "this test has lost its subject"
    parsed = _parse(LIVE.replace("- [ ] **SUB-05**:", "- [x] **SUB-05**:", 1))
    assert parsed.violations, "a bare flip must not produce a clean ledger"
    assert any("SUB: traceability declares" in v for v in parsed.violations)


def test_quietly_unticking_earned_work_fails():
    """Rule 38 cuts both ways -- understating is a violation too."""
    assert "- [x] **SEC-04**:" in LIVE, "this test has lost its subject"
    parsed = _parse(LIVE.replace("- [x] **SEC-04**:", "- [ ] **SEC-04**:", 1))
    assert any("SEC: traceability declares 8 ticked" in v for v in parsed.violations)


def test_a_tick_quoting_absent_text_fails():
    parsed = _parse(LIVE.replace('"BASE-01 | SATISFIED"',
                                 '"a sentence that is in no artifact"', 1))
    assert any("with text that is not in it" in v for v in parsed.violations)


def test_a_tick_citing_a_missing_artifact_fails():
    parsed = _parse(LIVE.replace(".planning/phases/01-base-logic/01-VERIFICATION.md",
                                 ".planning/phases/01-base-logic/NO-SUCH-FILE.md", 1))
    assert any("cites a missing artifact" in v for v in parsed.violations)


def test_an_open_row_carrying_evidence_fails():
    """`**evidence:**` means satisfied; an open row uses `**status:**`."""
    row = ('- [ ] **ZZZ-01**: probe — **open:** something outstanding here '
           '— **evidence:** `README.md` "P2P"')
    assert any("carries `**evidence:**`" in v for v in _parse(row).violations)


def test_an_open_row_naming_nothing_outstanding_fails():
    parsed = _parse("- [ ] **ZZZ-01**: probe with no open clause at all")
    assert any("names nothing outstanding" in v for v in parsed.violations)


def test_bare_pending_fails_when_a_verification_exists():
    stale = "| BASE-01 … BASE-08 | Phase 1 — Base Logic | Pending |"
    assert any("still reads bare `Pending`" in v for v in _parse(stale).violations)


def test_a_traceability_row_declaring_no_count_fails():
    """An undeclared row can never disagree with the checkboxes."""
    problems = trace.check_declared_counts(
        "BASE-01 … BASE-08", "Verified passed", ["BASE-01"], ["BASE-02"])
    assert any("declares no `**N/M ticked**` count" in p for p in problems)


@pytest.mark.parametrize(
    ("declared", "expected_fragment"),
    [("**1/2 ticked**", "declares 1 ticked"), ("**1/9 ticked**", "declares 9 requirements")],
)
def test_declared_counts_are_compared_in_both_dimensions(declared, expected_fragment):
    problems = trace.check_declared_counts(
        "BASE-01 … BASE-08", declared, ["BASE-01", "BASE-02"], ["BASE-03"])
    assert any(expected_fragment in p for p in problems)


def test_an_empty_ledger_is_never_clean():
    parsed = _parse("# Requirements\n\n(nothing here)\n")
    reasons = ledger_mod.emptiness(parsed)
    assert len(reasons) == 3
    assert parsed.total == 0 and parsed.trace_rows == 0 and parsed.citations_resolved == 0
