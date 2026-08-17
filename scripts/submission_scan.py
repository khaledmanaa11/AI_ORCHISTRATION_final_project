"""The credential scan behind G4-02, split from `submission_security.py` (08-01).

TWO CLASSES OF PATTERN, AND ONLY ONE OF THEM IS EXEMPTABLE.

* PROVIDER shapes -- `sk-ant-`, `AIza`, `ghp_` -- are unconditional. No
  allowlist entry can suppress them, anywhere, ever. A real Anthropic key inside
  an allowlisted test fixture still fires.
* The GENERIC assignment shape (`token = "<16+ chars>"`) catches the pattern a
  leaked credential wears, and also catches every synthetic HMAC fixture in
  `tests/`. Those five files are named in `docs/credential-scan-allowlist.json`
  with a reason each.

THE ALLOWLIST CANNOT ROT INTO A BLANKET EXEMPTION. An entry whose file no longer
produces a generic match is STALE and fails the row by itself, so a fixture that
is deleted or rewritten takes its exemption with it instead of leaving a
permanently open door in a file nobody re-reads. That is the same refusal
`submission_mechanisms._stale_row` makes about the PRD register.

BOTH CLASSES CARRY A POSITIVE CONTROL, assembled from fragments at runtime so
this file holds no credential of any shape. A clean result from a scanner that
matches nothing is evidence about the scanner, not about the tree.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from submission_common import read_tracked, tracked_files

ALLOWLIST = "docs/credential-scan-allowlist.json"

#: Provider-issued key shapes. Never exemptable.
PROVIDER_PATTERNS = (
    r"sk-ant-[A-Za-z0-9]{8,}",
    r"AIza[A-Za-z0-9_\-]{20,}",
    r"ghp_[A-Za-z0-9]{20,}",
)
#: The generic assignment shape a leaked credential wears. Exemptable by path.
GENERIC_PATTERN = (
    r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[\"'][A-Za-z0-9_\-]{16,}[\"']"
)
#: Text extensions worth scanning; a PNG cannot carry a greppable credential.
SCANNABLE = (".py", ".md", ".json", ".toml", ".yml", ".yaml", ".sh", ".txt", ".cfg", ".ini")


@dataclass(frozen=True)
class ScanResult:
    """One whole-tree scan, with every count the row needs to be non-vacuous."""

    scanned: int
    provider_hits: tuple[str, ...]
    generic_hits: tuple[str, ...]
    allowed: tuple[str, ...]
    stale_allowlist: tuple[str, ...]
    provider_control: bool
    generic_control: bool
    allowlist_error: str

    @property
    def clean(self) -> bool:
        return not (
            self.provider_hits or self.generic_hits
            or self.stale_allowlist or self.allowlist_error
        )

    @property
    def controls_fired(self) -> bool:
        return self.provider_control and self.generic_control

    def summary(self) -> str:
        return (
            f"controls fired (provider/generic): {self.provider_control}/"
            f"{self.generic_control}; tracked text files scanned: {self.scanned}; "
            f"provider-shape hits: {len(self.provider_hits)} {list(self.provider_hits)[:3]}; "
            f"unexempted generic hits: {len(self.generic_hits)} "
            f"{list(self.generic_hits)[:3]}; allowlisted: {len(self.allowed)}; "
            f"STALE allowlist entries: {len(self.stale_allowlist)} "
            f"{list(self.stale_allowlist)}"
            + (f"; allowlist error: {self.allowlist_error}" if self.allowlist_error else "")
        )


def _load_allowlist() -> tuple[dict, str]:
    raw = read_tracked(ALLOWLIST)
    if not raw:
        return {}, f"{ALLOWLIST} is absent or untracked"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {}, f"{ALLOWLIST} is not valid JSON: {exc}"
    allow = parsed.get("allow")
    if not isinstance(allow, dict):
        return {}, f"{ALLOWLIST} has no `allow` object"
    unreasoned = sorted(path for path, why in allow.items() if not str(why).strip())
    if unreasoned:
        return allow, f"allowlist entries carry no reason: {unreasoned}"
    return allow, ""


def _provider_match(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in PROVIDER_PATTERNS)


def _controls() -> tuple[bool, bool]:
    """The scanner run over synthetic values built here, not stored here."""
    provider = _provider_match("sk-" + "ant-" + "A" * 24)
    generic = bool(re.search(GENERIC_PATTERN, 'api_key = "' + "B" * 20 + '"'))
    return provider, generic


def scan_tracked_set() -> ScanResult:
    """Every tracked text file, classified into the two pattern classes."""
    allow, error = _load_allowlist()
    provider_hits, generic_hits, scanned = [], [], 0
    matched_generic = set()
    for path in tracked_files():
        if not path.endswith(SCANNABLE):
            continue
        scanned += 1
        text = read_tracked(path)
        if _provider_match(text):
            provider_hits.append(path)
        if re.search(GENERIC_PATTERN, text):
            matched_generic.add(path)
            if path not in allow:
                generic_hits.append(path)
    provider_control, generic_control = _controls()
    return ScanResult(
        scanned=scanned,
        provider_hits=tuple(sorted(provider_hits)),
        generic_hits=tuple(sorted(generic_hits)),
        allowed=tuple(sorted(allow)),
        stale_allowlist=tuple(sorted(set(allow) - matched_generic)),
        provider_control=provider_control,
        generic_control=generic_control,
        allowlist_error=error,
    )
