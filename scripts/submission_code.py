"""Sec17 group 2 -- architecture and code -- measured, not reviewed (08-01).

TWO OF THESE ROWS SHELL OUT TO THE REAL GATES rather than reimplementing them:
`ruff check .` and `scripts/check_line_limit.sh` are the enforcement this project
already runs in CI, and an audit that re-derived their answers could disagree
with the thing that actually blocks a commit.

THE LINE-LIMIT ROW CARRIES ITS OWN SCANNED COUNT. `check_line_limit.sh`'s
no-argument form enumerates through `git ls-files`, which is EMPTY in a freshly
`git init`ed tree before the first commit -- it then exits 0 having read nothing.
That vacuity is already on record in `05-18-SUMMARY.md`. This row therefore
enumerates the same three globs itself and refuses a zero count, so a green exit
over an empty file list can never be reported as a pass.

Sec17 also names "OOP with no duplication" and "consistent style, descriptive
names". No script can judge those; they are UNJUDGED rows, never PASS.
"""

from __future__ import annotations

import ast

from submission_common import (
    GROUP_2,
    REPO_ROOT,
    judge,
    read_tracked,
    run,
    tracked_matching,
    unjudged,
)

SDK_PREFIX = "src/pursuit/sdk/"
GATEKEEPER = "src/pursuit/services/llm/gatekeeper.py"
#: The three globs `scripts/check_line_limit.sh:18` enumerates.
LIMIT_PREFIXES = ("src/", "tests/", "training/")


def line_limit_scope() -> tuple[str, ...]:
    """The files the line-limit gate claims to scan, enumerated independently."""
    return tuple(
        path for path in tracked_matching(suffix=".py")
        if path.startswith(LIMIT_PREFIXES)
    )


def _sdk_row() -> object:
    modules = tracked_matching(prefix=SDK_PREFIX, suffix=".py")
    return judge(
        "G2-01", GROUP_2, "Sec17 SDK architecture -- business logic behind an SDK layer",
        len(modules) > 1,
        f"tracked modules under {SDK_PREFIX}: {len(modules)}",
        SDK_PREFIX,
    )


def _gatekeeper_row() -> object:
    text = read_tracked(GATEKEEPER)
    limits = [
        path for path in tracked_matching(prefix="config/", suffix=".json")
        if "rate" in read_tracked(path) or "token_bucket" in read_tracked(path)
    ]
    return judge(
        "G2-02", GROUP_2,
        "Sec17 API gatekeeper for all external calls, rate limits from config",
        bool(text) and bool(limits),
        f"{GATEKEEPER} tracked: {bool(text)}; config files carrying rate/token-bucket "
        f"fields: {len(limits)}",
        GATEKEEPER,
    )


def _line_limit_row() -> object:
    scope = line_limit_scope()
    code, output = run(["sh", "scripts/check_line_limit.sh"])
    violations = [line for line in output.splitlines() if line.startswith("VIOLATION:")]
    return judge(
        "G2-03", GROUP_2, "Sec3 / Table 5 every source and test file <= 150 code lines",
        code == 0 and not violations and len(scope) > 0,
        f"check_line_limit.sh exit {code}; violations {len(violations)}; "
        f"files the same three globs enumerate: {len(scope)} (a zero count is a "
        f"vacuous pass and fails this row)",
        "scripts/check_line_limit.sh",
    )


def _ruff_row() -> object:
    code, output = run(["uv", "run", "ruff", "check", "."])
    tail = output.strip().splitlines()[-1:] or ["<no output>"]
    return judge(
        "G2-04", GROUP_2, "Sec17 / Table 5 zero Ruff violations",
        code == 0,
        f"`uv run ruff check .` exit {code}; last line: {tail[0]!r}",
        "pyproject.toml",
    )


def _packages() -> tuple[str, ...]:
    return tuple(
        path for path in tracked_matching(prefix="src/pursuit/", suffix="/__init__.py")
    )


def _exports_row() -> object:
    """Sec14 professional packaging: a package that exports nothing declares nothing."""
    packages = _packages()
    silent = [
        path for path in packages
        if "__all__" not in read_tracked(path)
    ]
    return judge(
        "G2-05", GROUP_2, "Sec14 professional packaging -- every package declares `__all__`",
        bool(packages) and not silent,
        f"packages: {len(packages)}; without `__all__`: {len(silent)} {silent}",
        "src/pursuit/*/__init__.py",
    )


def _version_row() -> object:
    exposed = [
        path for path in _packages() + ("src/pursuit/__init__.py",)
        if "__version__" in read_tracked(path)
    ]
    return judge(
        "G2-06", GROUP_2, "Sec14 professional packaging -- `__version__` on the package",
        bool(exposed),
        f"tracked `__init__.py` files declaring `__version__`: {len(exposed)} {exposed}",
        "src/pursuit/__init__.py",
    )


def _docstring_row() -> object:
    """Sec3: a docstring on every module. Parsed, never grepped."""
    modules = tracked_matching(prefix="src/", suffix=".py")
    missing = []
    for path in modules:
        source = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError:  # pragma: no cover - would fail ruff first
            missing.append(path)
            continue
        if not ast.get_docstring(tree):
            missing.append(path)
    return judge(
        "G2-07", GROUP_2, "Sec3 module docstring on every source file",
        bool(modules) and not missing,
        f"src modules parsed: {len(modules)}; without a module docstring: "
        f"{len(missing)} {missing[:5]}",
        "src/pursuit/",
    )


def code_items() -> list:
    """Group 2's rows -- five measured, two honestly unjudgeable."""
    return [
        _sdk_row(),
        _gatekeeper_row(),
        _line_limit_row(),
        _ruff_row(),
        _exports_row(),
        _version_row(),
        _docstring_row(),
        unjudged("G2-08", GROUP_2, "Sec17 OOP with no duplication, inheritance and mixins",
                 "Table 5 marks this row `Code review`; no script can see an intentional "
                 "abstraction as distinct from an accidental one"),
        unjudged("G2-09", GROUP_2, "Sec17 consistent style, descriptive names",
                 "ruff enforces the mechanical half (G2-04); the naming half is a "
                 "human judgement and is not scored here"),
        unjudged("G2-10", GROUP_2, "Table 5 zero hardcoded values in source",
                 "Table 5 marks this row `Code review`. A literal is only 'hardcoded' "
                 "relative to whether it OUGHT to be configurable, which no scan can "
                 "decide; PARAMETERS.md is the authority and the per-mechanism PRDs "
                 "source every number they use"),
    ]
