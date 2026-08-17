"""THE SEAM that keeps the test suite out of the shipped `config/` tree.

WHY IT EXISTS (07-00). `config/{police,thief}/games_played.json` holds the
number rule 37 makes this team declare at the start of every league game,
and rule 38 (`docs/RULES.md:79`) makes declaring it falsely an ABSOLUTE
DISQUALIFICATION. Three integration files call `write_declaration` with
`load_agent_config("config/police")`, so `cfg.config_dir` is the REAL
directory and every `pytest` run advanced the real counter. Measured at
HEAD `de32c0b` over ONE full run: police 1895 -> 1909, thief 1888 -> 1902,
+14 each, for zero games played.

WHY IT GUARDS THE WRITE, NOT THE CALLER. `record_game_played` is the only
writer, and its body reaches `durable_write_json` through `step0_collect`'s
OWN module-level binding. Replacing THAT binding catches the write no
matter which function reached it and no matter whether a caller imported
`record_game_played` by name or by module attribute. A guard installed on
the caller would only catch the callers we happened to think of -- and the
whole lesson of this defect is that the caller we did not think of is the
one that gets you.

WHY IT RAISES INSTEAD OF REDIRECTING. Quietly rewriting the target to
`tmp_path` would make the suite green and hide the NEXT production path
that writes the config tree at the wrong moment. That is exactly how this
defect survived from Phase 6 into Phase 7 with a document certifying it as
correct behaviour (`docs/phases/phase-6/GATE-6-MEASUREMENT.md`, corrected
by 07-00). Loud is the requirement, not a preference.

`read_counters` backs the SECOND, independent half of the seam in
`conftest.py`: a raw before/after snapshot of both files across the whole
session, which catches a write arriving by any route the patch above does
not cover -- late, but caught, and never silently.
"""

from __future__ import annotations

import importlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIPPED_CONFIG_ROOT = REPO_ROOT / "config"
SHIPPED_COUNTERS = (
    SHIPPED_CONFIG_ROOT / "police" / "games_played.json",
    SHIPPED_CONFIG_ROOT / "thief" / "games_played.json",
)

WRITER_ATTR = "durable_write_json"

#: EVERY module that binds `durable_write_json` into its own namespace, plus
#: the module that defines it. D7-18 (07-09): until this list existed the guard
#: covered `step0_collect` ALONE, so it caught `games_played.json`'s writer and
#: not the RULE, which is "no test writes the shipped config tree". 07-07's
#: revert probe 17 pointed `QuotaManager` at `config/police/` and the suite
#: happily wrote `config/police/reporting_quota.json` -- no test failed for the
#: WRITE. A binding is patched per module because `from ... import
#: durable_write_json` copies the function object: patching only the defining
#: module would leave all five copies live.
#: `tests/unit/test_shipped_config_guard.py` re-derives this list by AST over
#: `src/`, so a SIXTH writer fails there rather than escaping the guard.
DURABLE_WRITE_BINDERS = (
    "pursuit.network.agent_step0_wiring",
    "pursuit.sdk.view_publish",
    "pursuit.security.step0_collect",
    "pursuit.services.reporting.artifacts",
    "pursuit.services.reporting.quota",
    "pursuit.shared.durable_write",
)


class ShippedConfigWriteError(RuntimeError):
    """A test tried to write inside the repository's real `config/` tree.

    Its own class, not a bare AssertionError, so it cannot be confused with
    an ordinary failed assertion and cannot be swallowed by a
    `pytest.raises(AssertionError)` somewhere else."""


def is_shipped_config_path(path: Path | str) -> bool:
    """True when *path* lands inside the repository's real `config/`
    directory. Both sides are resolved, so a RELATIVE path -- the shape
    every one of the +14 writes actually had, via
    `load_agent_config("config/police")` -- and any `..` hop are recognised
    too. Never raises: an unresolvable path cannot be the shipped tree."""
    try:
        resolved = Path(path).resolve()
    except (OSError, ValueError):
        return False
    return resolved == SHIPPED_CONFIG_ROOT or SHIPPED_CONFIG_ROOT in resolved.parents


def guarded(write_json):
    """Wrap a `durable_write_json`-shaped callable so a shipped-config
    target raises BEFORE any byte is written, and every other target calls
    through untouched. Calling through is not politeness: the guard has to
    DISCRIMINATE, or `test_step0_collect.py`'s legitimate `tmp_path`
    record-then-read round trip would break and the guard would be proving
    nothing except that writes can be blocked."""

    def _write(path, payload, **kwargs):
        if is_shipped_config_path(path):
            raise ShippedConfigWriteError(
                f"a test tried to write the shipped config file {path!r}. "
                "config/*/games_played.json is the rule-37 count this team declares "
                "to the league; only a real completed game may advance it, and a "
                "false number is an absolute disqualification (docs/RULES.md:79, "
                "rule 38). Point the test at tmp_path."
            )
        return write_json(path, payload, **kwargs)

    return _write


def install(patched) -> tuple[str, ...]:
    """Wrap EVERY binding in `DURABLE_WRITE_BINDERS`, returning the names
    patched so a caller can assert the count rather than trust it.

    `patched` is a `pytest.MonkeyPatch`, so every wrap is undone when its
    context exits -- the guard never outlives the session it guards.
    """
    for name in DURABLE_WRITE_BINDERS:
        module = importlib.import_module(name)
        patched.setattr(module, WRITER_ATTR, guarded(getattr(module, WRITER_ATTR)))
    return DURABLE_WRITE_BINDERS


def read_counters() -> dict[str, str | None]:
    """Raw snapshot of both shipped counters: file text, or None when the
    file is absent (it is gitignored, so a fresh clone has neither). Raw
    TEXT rather than the parsed int on purpose -- any write at all is then
    visible, including one that happens to rewrite the same number."""
    return {
        str(path): (path.read_text(encoding="utf-8") if path.is_file() else None)
        for path in SHIPPED_COUNTERS
    }
