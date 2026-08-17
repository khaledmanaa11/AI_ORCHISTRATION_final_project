"""Sec2.3's "critical requirement" -- a PRD per mechanism -- checked against the
PACKAGE TREE, never against a `docs/PRD_*.md` glob (08-01).

WHY THE DIRECTION MATTERS. Globbing the PRDs and counting thirteen answers the
question "how many PRDs are there", which no requirement asks. Sec2.3 asks
whether every mechanism HAS one, so the inventory has to come from the code:
every directory under `src/pursuit/` carrying a tracked `__init__.py` is a
mechanism candidate, and the answer for each is read from a committed register,
`docs/mechanism-prd-map.json`.

THE CONSEQUENCE IS THE POINT: a package added to the tree and not answered for
in the register is a GAP the next run reports by itself. A probe that plants an
empty `src/pursuit/<name>/__init__.py` proves it -- the walk finds a package the
register has never heard of, and a new row appears.

A SUPERSEDED PRD IS NOT COVERAGE. `docs/PRD_rl_strategy.md` carries a
DO-NOT-IMPLEMENT banner; a register entry pointing at it closes nothing, and the
resolver refuses it by name.
"""

from __future__ import annotations

import json

from submission_common import (
    GROUP_1,
    REPO_ROOT,
    judge,
    read_tracked,
    tracked_matching,
)

REGISTER = "docs/mechanism-prd-map.json"
PACKAGE_ROOT = "src/pursuit/"
_INIT = "/__init__.py"


def discovered_packages() -> tuple[str, ...]:
    """Every tracked package directory under `src/pursuit/`, sorted.

    Derived from `git ls-files`, so an untracked scratch directory is invisible
    and a newly committed package is not.
    """
    return tuple(
        path[: -len(_INIT)]
        for path in tracked_matching(prefix=PACKAGE_ROOT, suffix=_INIT)
        if path[: -len(_INIT)] != PACKAGE_ROOT.rstrip("/")
    )


def _load_register() -> tuple[dict, str]:
    raw = read_tracked(REGISTER)
    if not raw:
        return {}, f"{REGISTER} is absent or untracked"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {}, f"{REGISTER} is not valid JSON: {exc}"
    mechanisms = parsed.get("mechanisms")
    if not isinstance(mechanisms, dict):
        return {}, f"{REGISTER} has no `mechanisms` object"
    return mechanisms, ""


def _prd_is_live(path: str) -> tuple[bool, str]:
    """A cited PRD counts only when it is tracked AND not superseded."""
    text = read_tracked(path)
    if not text:
        return False, f"{path} is absent or untracked"
    if "SUPERSEDED" in text:
        return False, f"{path} carries a SUPERSEDED banner"
    return True, ""


def _entry_row(package: str, entry: object) -> object:
    """One row per package, IDENTIFIED BY PATH rather than by position.

    The first draft numbered these `G1-M01`, `G1-M02`, ... in walk order, and the
    planted-empty-package probe caught what that costs: inserting one package
    renumbered every row after it, so a stable register row silently changed its
    own id and a diff of two runs was unreadable. A row's identity has to be the
    thing it judges.
    """
    requirement = f"Sec2.3 per-mechanism PRD for `{package}/`"
    item_id = f"G1-M[{package}]"
    if entry is None:
        return judge(item_id, GROUP_1, requirement, False,
                     f"package is in the tree but absent from {REGISTER}", REGISTER)
    if not isinstance(entry, dict):
        return judge(item_id, GROUP_1, requirement, False,
                     f"{REGISTER} entry is not an object", REGISTER)
    prds = entry.get("prds") or []
    reason = (entry.get("reason") or "").strip()
    if prds:
        broken = [note for path in prds for ok, note in [_prd_is_live(path)] if not ok]
        return judge(item_id, GROUP_1, requirement, not broken,
                     f"cites {prds}" + (f"; unusable: {broken}" if broken else ""),
                     prds[0] if broken else "docs/")
    if reason:
        return judge(item_id, GROUP_1, requirement, True,
                     f"no PRD needed, recorded reason: {reason}", "")
    return judge(item_id, GROUP_1, requirement, False,
                 f"{REGISTER} entry names neither a PRD nor a reason", REGISTER)


def _stale_row(packages: tuple[str, ...], register: dict) -> object:
    """The register may not answer for a package that no longer exists."""
    stale = sorted(set(register) - set(packages))
    return judge(
        "G1-M99", GROUP_1,
        f"{REGISTER} answers for the tree and nothing else",
        not stale,
        f"register entries with no matching package: {stale}",
        REGISTER,
    )


def _tunnel_row() -> object:
    """The tunnel is a mechanism INSIDE a package, and its package's PRD says so.

    `docs/PRD_mcp_transport.md` puts "ngrok/Localtonet tunneling" out of scope in
    as many words, so `network/`'s PRD provably does not cover
    `network/tunnel_manager.py`. Derived, not asserted: the module has to exist
    and the disclaimer has to still be in the file.
    """
    module = "src/pursuit/network/tunnel_manager.py"
    transport = read_tracked("docs/PRD_mcp_transport.md")
    disclaimed = "Out of scope" in transport and "tunneling" in transport
    covered = [
        path for path in tracked_matching(prefix="docs/PRD_", suffix=".md")
        if "tunnel" in path
    ]
    present = (REPO_ROOT / module).is_file()
    return judge(
        "G1-M-TUNNEL", GROUP_1,
        "Sec2.3 per-mechanism PRD for the tunnel (`network/tunnel_manager.py`)",
        bool(covered) or not present,
        f"module tracked: {present}; PRD_mcp_transport declares tunneling out of scope: "
        f"{disclaimed}; tunnel-named PRDs: {covered or 'none'}",
        "docs/PRD_tunnel.md",
    )


def mechanism_items() -> tuple[list, int]:
    """Every mechanism row, and the number of packages the walk discovered.

    The count is returned so `submission_report` can refuse a run whose walk
    found nothing -- an inventory of zero mechanisms trivially has a PRD for all
    of them, which is the vacuous PASS this whole gate exists to refuse.
    """
    packages = discovered_packages()
    register, error = _load_register()
    if error:
        return [judge("G1-M00", GROUP_1, "Sec2.3 mechanism register is readable",
                      False, error, REGISTER)], len(packages)
    rows = [_entry_row(package, register.get(package)) for package in packages]
    rows.append(_stale_row(packages, register))
    rows.append(_tunnel_row())
    return rows, len(packages)
