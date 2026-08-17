"""Sec14 professional packaging -- every package declares `__all__` (08-03).

WHY TWO KINDS OF PACKAGE, AND WHY THAT IS NOT AN EXCUSE. Four packages
(`strategy`, `strategy.graph`, `services.llm`, `services.reporting`) re-export a
curated API: their `__init__.py` imports names and lists exactly those. Seven do
not import anything at all, and forcing them to would be a real change of
behaviour -- `network/` alone is 54 mutually-importing modules and a package-level
re-export is how a circular import gets introduced days before a deadline. Those
seven declare their **submodule inventory** instead, which is the documented
meaning of `__all__` on a package (`from pkg import *` imports the named
submodules) and needs no import statement at all.

WHY THE INVENTORY IS DERIVED FROM `git ls-files` AND NOT TYPED HERE. An `__all__`
typed once and never revisited is a decoration. Derived, it is a guard: a module
added to `network/` without being exported fails this test, and a module deleted
while its name stays in `__all__` fails it too. The list is read from the TRACKED
set specifically, so an untracked file cannot make the check pass or fail.

WHY `test_every_tracked_package_is_classified` exists. Without it, a new package
could be added to `src/pursuit/` and belong to neither list, and every assertion
below would keep passing while saying nothing about it.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_PREFIX = "src/pursuit/"
#: Packages that declare their submodule inventory (they import nothing).
INVENTORY_PACKAGES = (
    "src/pursuit",
    "src/pursuit/gui",
    "src/pursuit/network",
    "src/pursuit/sdk",
    "src/pursuit/security",
    "src/pursuit/services",
    "src/pursuit/shared",
)
#: Packages that re-export a curated API and list exactly the names they import.
API_PACKAGES = (
    "src/pursuit/services/llm",
    "src/pursuit/services/reporting",
    "src/pursuit/strategy",
    "src/pursuit/strategy/graph",
)
#: A package with fewer children than this is not one this test can say anything
#: useful about; the floor stops an emptied inventory reading as agreement.
MIN_CHILDREN = 1


def tracked() -> list[str]:
    """Every tracked path, POSIX-separated, straight from git."""
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    return [line.strip() for line in out.splitlines() if line.strip()]


def packages(paths: list[str]) -> list[str]:
    """Tracked package directories under `src/pursuit/`, longest path last."""
    return sorted(
        path[: -len("/__init__.py")]
        for path in paths
        if path.startswith(PKG_PREFIX) and path.endswith("/__init__.py")
    )


def public_children(package: str, paths: list[str]) -> set[str]:
    """The public submodules and subpackages directly inside `package`."""
    children: set[str] = set()
    for path in paths:
        if not path.startswith(package + "/"):
            continue
        rest = path[len(package) + 1:]
        if rest.count("/") == 0 and rest.endswith(".py") and rest != "__init__.py":
            children.add(rest[: -len(".py")])
        elif rest.count("/") == 1 and rest.endswith("/__init__.py"):
            children.add(rest.split("/")[0])
    return {name for name in children if not name.startswith("_")}


def declared_all(package: str) -> list[str] | None:
    """`__all__` as written in the package's `__init__.py`, parsed never imported."""
    source = (REPO_ROOT / package / "__init__.py").read_text(encoding="utf-8")
    for node in ast.parse(source).body:
        targets = getattr(node, "targets", [])
        if not (targets and isinstance(targets[0], ast.Name)):
            continue
        if targets[0].id == "__all__":
            return [element.value for element in node.value.elts]
    return None


def imported_names(package: str) -> set[str]:
    """Every name an `__init__.py` binds with an import statement."""
    source = (REPO_ROOT / package / "__init__.py").read_text(encoding="utf-8")
    bound: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            bound.update(alias.asname or alias.name for alias in node.names)
    return bound


def test_every_tracked_package_is_classified() -> None:
    """Anti-drift: a new package must be added to one of the two lists."""
    found = set(packages(tracked()))
    assert found, "git ls-files found no packages under src/pursuit/"
    classified = set(INVENTORY_PACKAGES) | set(API_PACKAGES)
    unclassified = sorted(found.symmetric_difference(classified))
    assert found == classified, f"packages this test does not classify: {unclassified}"


def test_every_package_declares_a_non_empty_all() -> None:
    for package in INVENTORY_PACKAGES + API_PACKAGES:
        names = declared_all(package)
        assert names, f"{package}/__init__.py declares no (or an empty) __all__"


def test_inventory_packages_export_exactly_their_tracked_children() -> None:
    paths = tracked()
    for package in INVENTORY_PACKAGES:
        children = public_children(package, paths)
        assert len(children) >= MIN_CHILDREN, f"{package}: no tracked children found"
        assert sorted(declared_all(package) or []) == sorted(children), (
            f"{package}/__init__.py __all__ does not match its tracked children; "
            f"missing {sorted(children.difference(declared_all(package) or []))}, "
            f"stale {sorted(set(declared_all(package) or []).difference(children))}"
        )


def test_api_packages_export_only_names_they_import() -> None:
    for package in API_PACKAGES:
        bound = imported_names(package)
        exported = set(declared_all(package) or [])
        assert exported, f"{package}: nothing exported"
        assert exported <= bound, (
            f"{package}/__init__.py exports names it never imports: "
            f"{sorted(exported - bound)}"
        )


def test_the_parser_returns_none_when_there_is_no_all() -> None:
    """The control. Without it every assertion above could be reading `None`."""
    module = ast.parse("x = 1\n")
    assert not [
        node for node in module.body
        if getattr(node, "targets", []) and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "__all__"
    ]
