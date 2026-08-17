"""Task 3: the `log_` builder cannot run during play (D-64, SEC-04, rule 18).

`security/ledger.py` states its file "is never read or written by anything on
the wire path (D-64)", and rule 18 keeps every nonce secret for exactly as long
as the game is live. Only SEC-04's end-of-game publication makes the ledger
readable, so a builder that joins the ledger into an emailed artifact must be
unreachable from the turn loop.

A GREP IN A SUMMARY ROTS; THIS DOES NOT. The scan below runs over `src/` on
every suite run, is floored so it cannot pass by having looked at nothing
(D7-6's standard), and carries a control proving it can find an import that IS
there. `pursuit.network.turn_commit_ledger` is the WRITER and is deliberately
not on the forbidden list -- writing the ledger before the send is D-64 itself.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
PACKAGE = "pursuit.services.reporting"
LOG_ARTIFACT_MODULES = frozenset(
    f"{PACKAGE}.{name}" for name in ("artifact_log", "log_join", "log_read", "log_turn_fields")
)
LEDGER_MODULE = "pursuit.security.ledger"
CONTROL_IMPORT = "pursuit.network.turn_commit_ledger"
MIN_SCANNED = 100
# The package re-exports these, so `from pursuit.services.reporting import
# write_log_artifact` reaches the builder without ever naming its module. A
# scan that watched module paths alone would miss the import form 07-07 is
# most likely to use -- probe 16 measured exactly that and it passed 6/6.
LOG_ARTIFACT_NAMES = frozenset(
    {
        "artifact_log", "log_join", "log_read", "log_turn_fields",
        "build_log_artifact", "write_log_artifact", "verify_log_artifact",
        "verify_log_turns", "join_game", "LogArtifactField",
    }
)


def _imported_modules(path: Path) -> set[str]:
    """Every module this file imports, by AST -- not by substring, which a
    docstring mention would trip.

    A `from X import Y` contributes BOTH `X` and `X.Y`: the second form is what
    makes `from pursuit.services.reporting import artifact_log` visible.
    """
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            modules.add(node.module)
            modules.update(f"{node.module}.{alias.name}" for alias in node.names)
            if node.module.startswith(PACKAGE):
                modules.update(alias.name for alias in node.names)
    return modules


def _scan() -> tuple[dict[str, set[str]], list[Path]]:
    """`{module path -> imported modules}` for every `.py` under `src/`."""
    files = sorted(SRC.rglob("*.py"))
    return {p.relative_to(SRC).as_posix(): _imported_modules(p) for p in files}, files


@pytest.fixture(scope="module")
def scan():
    imports, files = _scan()
    assert len(files) > MIN_SCANNED, "the scan looked at almost nothing"
    return imports


def test_the_scanner_finds_an_import_that_is_really_there(scan):
    """The control. Without it, every assertion below could pass because the
    scanner is broken rather than because the tree is clean."""
    joiner = scan["pursuit/services/reporting/log_join.py"]
    assert CONTROL_IMPORT in joiner
    assert f"{PACKAGE}.log_read" in joiner
    # The package `__init__` re-exports by NAME; the scan must see that form
    # too, or the gate below would only cover module-path imports -- which is
    # the hole probe 16 found, where a turn-loop module importing
    # `artifact_log` from the package passed 6/6.
    package_init = scan["pursuit/services/reporting/__init__.py"]
    assert package_init.issuperset(
        {f"{PACKAGE}.artifact_log", "build_log_artifact", "verify_log_turns",
         "write_log_artifact"}
    )


def test_no_turn_loop_module_imports_the_log_artifact_builder(scan):
    turn_loop = {
        name for name in scan
        if name.startswith("pursuit/network/turn_") or name.endswith("orchestrator.py")
    }
    assert len(turn_loop) > 1, "no turn-loop module found -- the check would be vacuous"
    offenders = sorted(
        name for name in turn_loop
        if scan[name] & LOG_ARTIFACT_MODULES or scan[name] & LOG_ARTIFACT_NAMES
    )
    assert offenders == [], f"the log_ builder is reachable from the turn loop: {offenders}"


def test_nothing_in_src_imports_the_log_artifact_builder_except_its_own_package(scan):
    """07-07 wired it from the game-end path, and did so from INSIDE the
    package (`end_of_game.py`) rather than from `network/` -- so this stays
    empty while the builder is no longer dead code. See the next test, which
    is what stops an empty list here from being green for the wrong reason."""
    importers = sorted(
        name for name, imports in scan.items()
        if (imports & LOG_ARTIFACT_MODULES or imports & LOG_ARTIFACT_NAMES)
        and not name.startswith("pursuit/services/reporting/")
    )
    assert importers == []


def test_the_builder_has_a_production_caller_and_it_is_the_game_end_hook(scan):
    """D7-14, closed by 07-07. Every `src/` module reaching the four `log_`
    modules, named -- so the empty list above cannot be green because nothing
    uses the builder at all, and a NEW reacher fails here rather than in a
    grader's inbox. `end_of_game.py` is the production caller; the other four
    are the package's own internals."""
    reachers = sorted(
        name for name, imports in scan.items()
        if imports & LOG_ARTIFACT_MODULES or imports & LOG_ARTIFACT_NAMES
    )
    assert reachers == [
        "pursuit/services/reporting/__init__.py",  # the package re-export surface
        "pursuit/services/reporting/artifact_log.py",  # the builder itself
        "pursuit/services/reporting/end_of_game.py",  # THE production caller
        "pursuit/services/reporting/log_join.py",  # the join, on log_read
        "pursuit/services/reporting/result_agreement.py",  # rule 35, on log_read
    ]
    assert "write_log_artifact" in scan["pursuit/services/reporting/end_of_game.py"]


def test_the_builder_never_reaches_for_the_ledger_reader_itself(scan):
    """The join uses its own crash-tolerant reader, so `CommitLedger.read_all`'s
    deliberate fail-loud contract for the AUDIT path is not weakened, widened
    or shared."""
    assert len(LOG_ARTIFACT_MODULES) == 4, "a thinned module set would loop over nothing"
    for name in sorted(LOG_ARTIFACT_MODULES):
        tree = ast.parse((SRC / (name.replace(".", "/") + ".py")).read_text(encoding="utf-8"))
        # Checked on the SYNTAX, not on the source text: three of these modules
        # discuss `CommitLedger.read_all` in their docstrings, which is exactly
        # the point -- they explain, in prose, why they do not call it.
        bound = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        assert "CommitLedger" not in bound, f"{name} imports the ledger reader"
        attributes = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        assert "read_all" not in attributes, f"{name} calls the audit path's reader"


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
