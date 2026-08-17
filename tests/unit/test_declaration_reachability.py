"""The declaration writer has a PRODUCTION call site, and it stays wired.

WHY THIS GATE EXISTS. This is the defect 08-04 closed, in its own words:
`build_declaration_artifact` / `write_declaration_artifact` /
`DeclarationContext` were built by 07-02 and, at HEAD, reachable only from
their own module, the package re-export and tests. Every test of them passed
for a year of plans while `declaration_<game_id>.json` -- one of rule 50's FOUR
MANDATORY artifacts -- was never written by a game. Deleting the one line in
`end_of_game._report` that calls `declare_game` would put it straight back, and
`tests/integration/test_end_of_game_declaration.py` is the only thing that
would notice.

So this file asserts the SHAPE of the real source, the way
`test_end_of_game_wiring.py` and `test_log_artifact_reachability.py` do: a
summary of the call graph is not the call graph.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
REPORTING = SRC / "pursuit/services/reporting"
HOOK = REPORTING / "end_of_game.py"
DECLARATION = REPORTING / "end_of_game_declaration.py"
ENTRYPOINT = SRC / "pursuit/network/agent_entrypoint.py"

#: The three names 08-01 found dead. Each must be reachable from production.
PREVIOUSLY_DEAD = ("build_declaration_artifact", "write_declaration_artifact", "DeclarationContext")

#: Modules that do not count as a production caller: the name's own home, the
#: package re-export, and this plan's own writer module is the ONLY new one.
NOT_A_CALLER = ("artifact_declaration.py", "artifact_declaration_fields.py", "__init__.py")


def _production_modules() -> list[Path]:
    return [path for path in SRC.rglob("*.py") if path.name not in NOT_A_CALLER]


@pytest.mark.parametrize("name", PREVIOUSLY_DEAD)
def test_each_previously_dead_name_has_a_production_caller(name):
    """The grep 08-01 ran, as a test. It returned only the module and the
    re-export; it must now return a real caller too."""
    callers = sorted(
        path.relative_to(SRC).as_posix()
        for path in _production_modules()
        if name in path.read_text(encoding="utf-8")
    )
    assert callers, f"{name} still has no production caller outside its own module"
    assert "pursuit/services/reporting/end_of_game_declaration.py" in callers


def test_the_writer_module_is_itself_reachable_from_the_game_end_hook():
    """A caller nothing calls is the same defect one level up."""
    imported = {
        f"{node.module}.{alias.name}"
        for node in ast.walk(ast.parse(HOOK.read_text(encoding="utf-8")))
        if isinstance(node, ast.ImportFrom) and node.module and not node.level
        for alias in node.names
    }
    assert "pursuit.services.reporting.end_of_game_declaration.declare_game" in imported


def test_declare_game_is_called_exactly_once_in_src_and_from_the_hook():
    """A second call site would write the artifact twice for one game."""
    callers = sorted(
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if "declare_game(" in path.read_text(encoding="utf-8") and path != DECLARATION
    )
    assert callers == ["pursuit/services/reporting/end_of_game.py"]
    assert HOOK.read_text(encoding="utf-8").count("declare_game(") == 1


def test_the_call_sits_before_the_chain_is_built_and_after_both_artifacts():
    """Position, not just presence. After the two sealed artifacts so a
    transport that refuses to construct still leaves them; before the send so
    the declaration lands even if the mail ladder later fails."""
    source = HOOK.read_text(encoding="utf-8")
    result = source.index("record_sub_game(")
    call = source.index("declare_game(\n")
    chain = source.index("sender = chain or build_reporting_chain(")
    assert result < call < chain


def test_the_entrypoint_threads_the_peers_envelope_through():
    """The artifact embeds BOTH sides' signed envelopes (D-71). `run_agent` is
    the only holder of the peer's, so a hook called without it would silently
    record every peer as digest-only."""
    source = ENTRYPOINT.read_text(encoding="utf-8")
    assert "peer_declaration_envelope=result.peer_step0_declaration," in source


def test_the_declaration_path_never_reads_ctx_state():
    """Rules 8-9. 07-11 closed a disqualifying local-truth leak and a
    declaration field must not reopen it. By AST over attribute access, so a
    docstring promising it cannot satisfy this."""
    leaks = {
        node.attr
        for node in ast.walk(ast.parse(DECLARATION.read_text(encoding="utf-8")))
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "ctx"
    }
    assert leaks == {"log_path", "game_uid"}, f"the declaration path reads {sorted(leaks)}"
