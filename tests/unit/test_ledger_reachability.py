"""The nonce ledger's importer and caller pins (D-64, SEC-04, rule 18).

Split from `test_log_artifact_reachability.py` at the 150-code-line gate --
that file keeps the log-builder pins, this one keeps the ledger's. Both run
the same shared scanner (`reachability_helpers`), each with its own scan-size
floor so neither can pass vacuously.
"""

from __future__ import annotations

import pytest

from tests.unit.reachability_helpers import MIN_SCANNED, SRC, scan_src

LEDGER_MODULE = "pursuit.security.ledger"


@pytest.fixture(scope="module")
def scan():
    imports, files = scan_src()
    assert len(files) > MIN_SCANNED, "the scan looked at almost nothing"
    return imports


def test_every_importer_of_the_ledger_module_in_src_is_named(scan):
    """Whoever imports `security.ledger` at all, named -- so a NEW importer,
    on the wire path or anywhere else, fails here rather than in a grader's
    inbox. Four of these six take only `LedgerField`'s key names; the writer
    and the game-end audit are the two that touch a file."""
    importers = sorted(name for name, imports in scan.items() if LEDGER_MODULE in imports)
    assert importers == [
        "pursuit/network/agent_audit_wiring.py",  # read_all, at game end
        "pursuit/network/turn_commit_ledger.py",  # append, before the send (D-64)
        "pursuit/security/audit_shape.py",  # LedgerField names only
        "pursuit/security/audit_state.py",  # LedgerField names only
        "pursuit/services/reporting/log_join.py",  # LedgerField names only
        "pursuit/services/reporting/log_turn_fields.py",  # LedgerField names only
    ]


def test_read_all_has_exactly_one_production_call_site(scan):
    """`CommitLedger.read_all()` is the nonce-publication read. Exactly one
    module in `src/` calls it, and it is the game-end audit -- reached from
    `agent_entrypoint.run_agent` only AFTER `run_turn_loop` has returned."""
    callers = sorted(
        name for name in scan if ".read_all()" in (SRC / name).read_text(encoding="utf-8")
    )
    assert callers == ["pursuit/network/agent_audit_wiring.py"]
    entrypoint = (SRC / "pursuit/network/agent_entrypoint.py").read_text(encoding="utf-8")
    assert entrypoint.index("run_turn_loop(ctx)") < entrypoint.index("run_final_audit(ctx")
