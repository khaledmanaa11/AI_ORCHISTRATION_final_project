---
phase: 06-security-and-cryptography
plan: "01"
subsystem: security
tags: [hashlib, secrets, canonical-json, commit-reveal, sha256, config-loader]

# Dependency graph
requires:
  - phase: 02-fastmcp-infrastructure
    provides: config_hash.canonical_json / digests_match (the one project-wide canonicalisation + constant-time compare idiom, QUAL-02)
  - phase: 04-language-and-scent
    provides: deception_types.Intent (TRUTH/LIE, reused verbatim as commit's intent flag)
provides:
  - "src/pursuit/security/ package: build_commit_payload/commit/verify_reveal (D-59), build_state_record (D-60), CommitLedger (D-64) -- 100% covered"
  - "src/pursuit/shared/security_config.py: SecurityKey/SecurityParams/load_security_config, the 11th per-agent config block"
  - "config/{police,thief}/security.json byte-identical pair: commit_reveal=true, team_code=khm-mn17 (D-65)"
affects: [06-02-wire-protocol, 06-03-step0-and-audit, 06-04-gate-and-docs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ONE payload-builder (build_commit_payload) called by both commit() and verify_reveal() -- never two independent dict constructions (D-59, Pitfall 2)"
    - "move stays shape-opaque to commit_pack.py (isinstance(move, dict) only) -- 06-02's composite {move, barrier} dict is exercised by tests but never validated internally here"
    - "the *Key-beside-loader convention (SecurityKey next to load_security_config) -- 11th application, following TunnelKey/ScentKey/LanguageKey/BeliefKey/DeceptionKey"
    - "CommitLedger.append mirrors event_log.append_event's exact validate->serialize->write->flush->os.fsync durability order"

key-files:
  created:
    - src/pursuit/security/__init__.py
    - src/pursuit/security/commit_pack.py
    - src/pursuit/security/state_record.py
    - src/pursuit/security/ledger.py
    - src/pursuit/shared/security_config.py
    - config/police/security.json
    - config/thief/security.json
    - tests/unit/test_security_config.py
    - tests/unit/test_commit_pack.py
    - tests/unit/test_state_record.py
    - tests/unit/test_ledger.py
  modified: []

key-decisions:
  - "D-59/D-60/D-64/D-65 implemented exactly as 06-PLAN-OUTLINE.md specified -- no re-derivation, no invented number"
  - "commit_pack.py imports canonical_json/digests_match from pursuit.network.config_hash -- the plan's one documented, deliberate exception to the security/ package's own 'sdk/shared only' boundary"
  - "state_record.py's non-bool-int guard is a local 4-line duplicate of envelope.py's _require_non_bool_int, matching the existing 3-site precedent for this exact guard rather than a cross-package import"

patterns-established:
  - "Pattern: security/ package files import sdk/shared only, plus the one narrow config_hash exception documented in security/__init__.py's own docstring -- every file 06-02/06-03 add to this package inherits the same boundary"

# Metrics
duration: 35min
completed: 2026-08-09
---

# Phase 6 Plan 1: Crypto Core (commit_pack, state_record, ledger, security_config) Summary

**Standalone SHA-256 commit/reveal hashing (D-59), the D-60 five-field state record, and a durable fsync'd nonce ledger (D-64), all stdlib-only and 100% unit-covered, plus the byte-identical security.json config pair (D-65) -- nothing wired into the turn loop yet, that is 06-02's job.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 3
- **Files created:** 11 (4 source, 1 config-loader, 2 config JSON, 4 test files)

## Accomplishments
- `commit()`/`verify_reveal()` round-trip correctly via the ONE `build_commit_payload()` function (D-59), and reject any single-field tamper -- state, the top-level `move` key, the nested `barrier` key inside a composite action, intent, or nonce -- proven with both a move-only and a barrier-bearing example so the function's shape-opacity is genuinely exercised, not just asserted.
- `build_state_record()` returns exactly D-60's five fixed fields, nesting `position` as `{row, col}`, rejecting a `bool` passed as `turn`/`barriers_remaining`.
- `CommitLedger` durably persists and reproduces per-turn `{turn, h_commit, payload}` records (nonce included inside `payload`) across a fresh append -> read_all cycle, mirroring `event_log.append_event`'s exact durability order; a missing ledger file returns `[]` (not an error), a malformed line raises `json.JSONDecodeError` (fail-loud, no silent skip).
- `security.json` ships in both `config/police/` and `config/thief/`, byte-identical, carrying only `commit_reveal` (default `true`) and the already-decided `team_code = "khm-mn17"` -- verified 8 characters, no spaces, by test.
- The entire new `src/pursuit/security/` package measures **100% coverage** (77/77 statements) — no uncovered branch left for a later plan.

## Task Commits

Each task was committed atomically:

1. **Task 1: security_config.py + the security.json pair** - `ca84968` (feat)
2. **Task 2: commit_pack.py + state_record.py** - `cdcc39c` (feat)
3. **Task 3: ledger.py — the durable per-turn nonce ledger** - `c85b302` (feat)

**Plan metadata:** (this commit, appended after STATE.md/graph update)

## Files Created/Modified
- `src/pursuit/security/__init__.py` - package docstring stating the sdk/shared-only boundary + the one documented config_hash exception
- `src/pursuit/security/commit_pack.py` - `CommitKey`, `build_commit_payload`, `commit`, `verify_reveal` (D-59)
- `src/pursuit/security/state_record.py` - `StateRecordKey`, `build_state_record` (D-60)
- `src/pursuit/security/ledger.py` - `LedgerField`, `CommitLedger` (D-64)
- `src/pursuit/shared/security_config.py` - `SecurityKey`, `SecurityParams`, `load_security_config`
- `config/police/security.json` / `config/thief/security.json` - byte-identical pair (D-65)
- `tests/unit/test_security_config.py`, `test_commit_pack.py`, `test_state_record.py`, `test_ledger.py` - 34 new tests total

## Exact Signatures for 06-02 (verbatim, do not re-derive)

```python
# src/pursuit/security/commit_pack.py
class CommitKey(str, Enum):
    STATE = "state"; MOVE = "move"; INTENT = "intent"; NONCE = "nonce"

def build_commit_payload(*, state: dict, move: dict, intent: str, nonce: str) -> dict: ...
def commit(state: dict, move: dict, intent: str) -> tuple[str, str]: ...  # (h_commit, nonce)
def verify_reveal(h_commit: str, *, state: dict, move: dict, intent: str, nonce: str) -> bool: ...

# src/pursuit/security/state_record.py
class StateRecordKey(str, Enum):
    GAME_ID = "game_id"; TURN = "turn"; ROLE = "role"
    POSITION = "position"; BARRIERS_REMAINING = "barriers_remaining"

def build_state_record(
    *, game_id: str, turn: int, role: str,
    position: tuple[int, int], barriers_remaining: int,
) -> dict: ...
# returns {"game_id":..., "turn":..., "role":..., "position": {"row":..., "col":...}, "barriers_remaining":...}

# src/pursuit/security/ledger.py
class LedgerField:
    TURN = "turn"; H_COMMIT = "h_commit"; PAYLOAD = "payload"

class CommitLedger:
    def __init__(self, path: Path | str) -> None: ...
    def append(self, *, turn: int, h_commit: str, payload: dict) -> None: ...
    def read_all(self) -> list[dict]: ...  # [] if the file does not exist

# src/pursuit/shared/security_config.py
class SecurityKey(str, Enum):
    VERSION = "version"; COMMIT_REVEAL = "commit_reveal"; TEAM_CODE = "team_code"

@dataclass(frozen=True)
class SecurityParams:
    version: str; commit_reveal: bool; team_code: str

def load_security_config(path: Path | str) -> SecurityParams: ...
```

**What 06-02 needs to know:**
- `commit()`'s `move` argument is whatever composite action dict `turn_commit.py` builds (`{"move": <direction-token dict>, "barrier": <direction-token dict> | None}` per D-59/D-66) — `commit_pack.py` does not know or care about that internal shape, so 06-02 is free to pass it straight through.
- `verify_reveal` takes `h_commit` positionally, everything else keyword-only — matches `commit`'s own `(h_commit, nonce)` return order so a caller can write `h_commit, nonce = commit(...)` then later `verify_reveal(h_commit, state=..., move=..., intent=..., nonce=nonce)` with no reshaping.
- `CommitLedger` is constructed once per game (per the ledger-file-beside-event-log precedent); `.append` is called once per turn with the SAME payload dict `build_commit_payload` produced (or reproduces on reveal), so the ledger stores the real `{state,move,intent,nonce}` shape under `payload`, not a re-derived one.
- `load_security_config(...).commit_reveal` is the toggle 06-02 branches on to bypass the whole four-phase exchange when off (byte-equivalent wire per D-66's own note).

## Decisions Made
No new decisions beyond what D-59/D-60/D-64/D-65 and the plan already specified. One implementation note worth recording: `verify_reveal`'s tamper tests exercise the nested `"barrier"` key specifically (not just the top-level `"move"` key) to prove `build_commit_payload`'s opacity is real — a shallow top-level-only tamper test would not have caught a validator that flattened or re-derived the composite dict.

## Deviations from Plan

None - plan executed exactly as written. The one documented architectural exception (commit_pack.py importing `canonical_json`/`digests_match` from `pursuit.network.config_hash`) was pre-authorized by the plan itself, not a deviation.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. Everything in this plan is stdlib (`hashlib`/`secrets`/`json`) plus config files.

## Next Phase Readiness
- `src/pursuit/security/` is a complete, self-contained, 100%-covered crypto/config layer ready for 06-02 to wire into `turn_actions.py`'s Commit/Ack/Reveal exchange.
- Full repo gates green: 1150 passed / 1 pre-existing timing flake (unrelated to this plan, passes in isolation), 95.81% coverage, ruff 0 violations, line-limit clean, `check_no_llm_in_strategy.py` OK.
- Knowledge graph refreshed this session (6035 nodes / 10756 edges / 384 communities); `commit_pack`/`CommitLedger`/`security_config`/`build_state_record` all confirmed present in `GRAPH_REPORT.md`.
- No blockers for 06-02.

---
*Phase: 06-security-and-cryptography*
*Completed: 2026-08-09*

## Self-Check: PASSED

All 11 created files verified present on disk; all 3 task commits (`ca84968`, `cdcc39c`,
`c85b302`) verified present in `git log --oneline --all`. Full gate suite re-run and
independently confirmed: 1150 passed / 1 pre-existing timing flake (isolated re-run: passes),
95.81% coverage, `ruff check .` 0 violations, `scripts/check_line_limit.sh` clean,
`scripts/check_no_llm_in_strategy.py` OK.
