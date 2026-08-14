---
phase: 05-cloud-exposure-and-tunneling
plan: "07"
subsystem: infra
tags: [llm-fallback, step0-declaration, hmac, observability, prompt-engineering, rule-38]

# Dependency graph
requires:
  - phase: 04-language-and-scent
    provides: "the sanctioned keyless fallback (bluff.compose -> HintBank), the claude_api/template provider registry, and the STYLE_GUIDE that docs/PRD_deception.md quotes verbatim"
  - phase: 06-security-commit-reveal
    provides: "the HMAC-signed Step-0 declaration whose llm_name field this plan re-values, and handshake_step0's digest verification before move 1"
provides:
  - "client.has_api_key() -- a presence-only key probe beside the ONE definition of the env var name"
  - "a single startup WARNING when a real provider is configured with no key, on bare stderr with no logging.basicConfig"
  - "language_wiring.declared_llm_name() -- the honest Step-0 llm_name (rule 38), decided by the resolved provider CLASS"
  - "a first-person compose prompt, and a test that pins docs/PRD_deception.md's quote to the shipped STYLE_GUIDE"
  - "a shape-stability test naming the declaration's ten Sec5.5 keys, so an HMAC-relevant field change fails loudly"
affects: [05-08-remote-round-attempt-2, phase-07-reporting-shell, submission-league-games]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Capability is probed, never assumed: what a process DECLARES is derived from what it can actually do, not from what its config asks for"
    - "One question, one site: both the warning and the declared name resolve the provider CLASS via get_provider_class, so no third place learns the string 'claude_api'"
    - "A doc that says 'verbatim' gets a test that makes it true"

key-files:
  created:
    - tests/unit/services/test_llm_client.py
  modified:
    - src/pursuit/services/llm/client.py
    - src/pursuit/services/llm/anthropic_provider.py
    - src/pursuit/services/llm/bluff.py
    - src/pursuit/services/llm/bluff_prompt.py
    - src/pursuit/network/language_wiring.py
    - src/pursuit/network/agent_audit_wiring.py
    - tests/unit/test_language_wiring.py
    - tests/unit/test_agent_audit_wiring.py
    - tests/unit/services/test_bluff_prompt.py
    - docs/PRD_deception.md
    - docs/phases/phase-5/TODO.md
    - docs/phases/phase-6/gate6_measurement_evidence.json

key-decisions:
  - "The keyless fallback BEHAVIOUR is unchanged: a missing key still degrades to the template bank and never becomes a startup failure -- the four Phase-4 degradation tests pass unedited, and that is the evidence, not the claim"
  - "declared_llm_name() lives in language_wiring.py, not agent_audit_wiring.py: its docstring pushed agent_audit_wiring to 157 code lines, and it is the SAME question _build_provider already asks -- split, never compressed"
  - "WARNING, not INFO: this project installs no logging.basicConfig, so the root logger's WARNING default is the only level that reaches an operator's stderr -- measured with a bare `python -c` probe, not assumed"
  - "DEBUG, not WARNING, for compose's per-turn fallback line: at WARNING it would fire every turn and bury the one startup warning that matters"
  - "The provider string 'claude_api' is never compared: both new call sites resolve the CLASS, so registering another real provider later stays correct for free"
  - "No post-compose first-person validator: person detection is fuzzy, and a false positive would silently divert a good hint to the bank -- recreating the exact silent-fallback failure this plan closes"
  - "src/ now has exactly ONE executable occurrence of the literal 'ANTHROPIC_API_KEY'; anthropic_provider's NO_KEY message formats the shared constant, and the message text stays byte-identical so its existing test passes unedited"

patterns-established:
  - "Presence-only secret probes: the helper returns a bool and lives beside the env var's one definition; a sentinel-value control test proves the value reaches no log record and no declaration"
  - "Shape-stability tests for signed payloads: spell the field names out in the test rather than reading them back from the enum, so a rename on either side fails"

# Metrics
duration: 63min
completed: 2026-08-14
---

# Phase 5 Plan 07: Keyless-LLM Legibility (G5) Summary

**A keyless run now says so — one startup WARNING naming the env var, and a Step-0 declaration reading `template-fallback (no LLM calls)` instead of `claude-haiku-4-5` — with the sanctioned fallback behaviour itself byte-for-byte unchanged.**

## Performance

- **Duration:** 63 min
- **Started:** 2026-08-14T13:52:00Z
- **Completed:** 2026-08-14T14:55:00Z
- **Tasks:** 2
- **Files modified:** 12 (1 created)

## Accomplishments

- **The operator can tell.** On this keyless box, `_build_provider` prints to bare stderr, with no
  `logging.basicConfig` anywhere in the process:
  `ANTHROPIC_API_KEY is not set: AnthropicProvider cannot call the model, so EVERY hint this game comes from the deterministic template bank and the Step-0 declaration will say so. Set ANTHROPIC_API_KEY before the game for live hints.`
  Measured with `env -u ANTHROPIC_API_KEY uv run python -c ...`, not inferred from a caplog test.
- **The declaration is honest (rule 38).** Measured for every combination:

  | provider | key present | declared `llm_name` |
  |---|---|---|
  | `claude_api` | no | `template-fallback (no LLM calls)` |
  | `claude_api` | yes | `claude-haiku-4-5` (the configured `model_id`) |
  | `template` | yes | `template-fallback (no LLM calls)` |
  | `template` | no | `template-fallback (no LLM calls)` |

  The live GATE-6 run confirms it end-to-end: both sides' collected declarations now read
  `'llm_name': 'template-fallback (no LLM calls)'` where the 2026-08-13 machine-B artifact read
  `claude-haiku-4-5` on a box that made zero calls.
- **The declaration's shape is provably unchanged.** `len(declaration) == 10` and the key set is
  asserted against the ten Sec5.5 names **spelled out in the test**, not read back from
  `DeclarationField` — so a rename or an addition on either side fails. GATE-6 criterion 3
  (`step0_verified_before_move_1`) re-measured **PASS**.
- **The prompt asks for the sentence the player would say.** `"phrasing a claim for a player"` —
  the wording that produced machine A's turn-4 `"The player is currently positioned..."` — became
  `"You are a player ... stating a claim about yourself"`, plus a first-person `STYLE_GUIDE` bullet.
  `docs/PRD_deception.md` Sec6's verbatim quote was updated in the **same commit**, and a new test
  parses that fenced block out of the markdown and asserts it **equals** the shipped string, so the
  two can never drift silently again.
- **The fallback still falls back.** `tests/integration/test_llm_degradation.py` (4 tests),
  `test_language_timing.py` and `test_gate4.py` all pass **unedited** with the key explicitly unset.
  No test was weakened, loosened or deleted.

## Task Commits

1. **Task 1: the operator can tell the LLM is off** — `951d87d` (feat)
2. **Task 2: an honest declaration and a first-person prompt** — `50ac2fe` (feat)

## Files Created/Modified

- `src/pursuit/services/llm/client.py` — `has_api_key()`, presence-only; `_API_KEY_ENV_VAR` promoted
  to public `API_KEY_ENV_VAR` now that two network-layer callers name it in operator-facing text.
- `src/pursuit/services/llm/anthropic_provider.py` — the NO_KEY message formats the shared constant
  instead of restating the literal. Message text byte-identical; its existing test passes unedited.
- `src/pursuit/network/language_wiring.py` — the startup WARNING inside `_build_provider`'s existing
  branch structure, and the new `declared_llm_name()` beside it.
- `src/pursuit/network/agent_audit_wiring.py` — `declare_step0` calls `declared_llm_name` instead of
  echoing `model_id`. **134 code lines** after the split (was 128; 157 before it).
- `src/pursuit/services/llm/bluff.py` — a `_log.debug` on the `LlmFailure -> hint_bank` branch.
- `src/pursuit/services/llm/bluff_prompt.py` — first person pinned in the system template and in
  `STYLE_GUIDE`. **68 code lines.**
- `docs/PRD_deception.md` — Sec6's verbatim `STYLE_GUIDE` quote, same commit as the string itself.
- `tests/unit/services/test_llm_client.py` (new) — 6 tests for the probe, incl. the rule-4 control.
- `tests/unit/test_language_wiring.py` — 4 warning tests / **5 cases** (once / never / template x key
  parametrised / no key-shaped value).
- `tests/unit/test_agent_audit_wiring.py` — 4 declaration tests / **5 cases**, shape checked on
  every path through the helper.
- `tests/unit/services/test_bluff_prompt.py` — 3 tests incl. the PRD-drift guard.

6 + 5 + 5 + 3 = **19 new cases**, which is exactly the suite delta below.
- `docs/phases/phase-5/TODO.md` — 05-07 row moved to in-progress with the measured evidence.
- `docs/phases/phase-6/gate6_measurement_evidence.json` — regenerated by this plan's GATE-6 re-run.
- `.planning/graphs/GRAPH_REPORT.md` — refreshed (7205 nodes, 13045 edges); `declared_llm_name`
  resolves with edges to `get_provider_class`, `has_api_key` and back from `declare_step0`.

## Decisions Made

See `key-decisions` in the frontmatter. The two worth repeating:

1. **Where `declared_llm_name` lives.** Putting it in `agent_audit_wiring.py` — where the plan's
   `files_modified` implied — took that file to **157 code lines**, over the hard gate. The rule is
   "split files, never compress code to fit", so it moved to `language_wiring.py`, which is not a
   dumping ground but the module that already resolves the provider class for exactly the same
   reason. The warning and the declared name are now the same question asked in the same file for
   two different audiences, which is a *stronger* form of the plan's own truth #4 than two sites
   would have been.
2. **What was deliberately NOT built.** No post-compose person validator (constraint 5), no hard
   startup failure (constraint 1), no change to the declaration's field set (constraint 2), and no
   touch of `config/*/games_played.json` (rule 38 — those files are untracked, and only real games
   moved them).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `agent_audit_wiring.py` breached the 150-code-line gate**
- **Found during:** Task 2
- **Issue:** `_declared_llm_name` plus its four imports and its docstring took the file from 128 to
  **157 code lines**. The gate counts docstring lines as code; the pre-commit hook and CI would
  both have rejected it, and `--no-verify` is forbidden.
- **Fix:** Moved the helper to `src/pursuit/network/language_wiring.py` as the public
  `declared_llm_name(model)`, together with its two name constants. `agent_audit_wiring.py` imports
  it. No behaviour change; the four `services.llm` imports left `agent_audit_wiring` entirely.
- **Files modified:** `src/pursuit/network/agent_audit_wiring.py`, `src/pursuit/network/language_wiring.py`
- **Verification:** `bash scripts/check_line_limit.sh` exit 0; **134** and **129** code lines
  respectively; full suite green.
- **Committed in:** `50ac2fe` (Task 2 commit)

**2. [Rule 2 - Missing Critical] The env var NAME was duplicated in executable code**
- **Found during:** Task 1
- **Issue:** The plan's truth is that the name is not restated anywhere, and verification step 6
  asks for it in `client.py` only. `anthropic_provider.py:101` already carried a second executable
  copy inside the NO_KEY failure message. Adding a third consumer without fixing that would have
  cemented the duplication this plan is meant to prevent.
- **Fix:** `_API_KEY_ENV_VAR` -> public `API_KEY_ENV_VAR`; the NO_KEY message became
  `f"{API_KEY_ENV_VAR} is not set"`. The rendered text is byte-identical.
- **Files modified:** `src/pursuit/services/llm/client.py`, `src/pursuit/services/llm/anthropic_provider.py`
- **Verification:** `grep -rn "ANTHROPIC_API_KEY" src/` now returns **one executable line**
  (`client.py:25`) plus three docstring mentions;
  `tests/unit/services/test_anthropic_provider.py:156`, which asserts the literal message, passes
  **unedited**.
- **Committed in:** `951d87d` (Task 1 commit)

**3. [Rule 3 - Blocking] Two test paths in the plan did not exist**
- **Found during:** Tasks 1 and 2
- **Issue:** The plan named `tests/unit/test_llm_client.py` and `tests/unit/test_bluff_prompt.py`;
  this repo puts `services/llm` tests under `tests/unit/services/`.
- **Fix:** Created `tests/unit/services/test_llm_client.py` and extended the existing
  `tests/unit/services/test_bluff_prompt.py`. Same files, house layout.
- **Files modified:** as above
- **Verification:** both collected and green.
- **Committed in:** `951d87d`, `50ac2fe`

---

**Total deviations:** 3 auto-fixed (2 blocking, 1 missing critical)
**Impact on plan:** No scope creep. Deviation 1 is the CLAUDE.md line gate forcing a split that
turned out to improve cohesion; 2 removes a duplicate of the very constant this plan makes
authoritative; 3 is a path correction. Every plan-specified behaviour shipped.

## Issues Encountered

- **`docs/phases/phase-6/gate6_measurement_evidence.json` changed more than timestamps.** Its
  `envelope_counts` moved: `police_received` gained `hint: 4` and `thief_received` gained `hint: 5`
  where the committed file recorded **no received hints at all**, and `thief_sent.hint` went 5 -> 4.
  Investigated before committing rather than waved through: the committed file was generated
  **2026-08-09** (commit `0427137`), *before* 05-06 fixed hint delivery (G3/G4 — the unsatisfiable
  receive-side drop window and the responder's mis-stamped outgoing turn). This is the first GATE-6
  re-run since, so 05-06's fix is simply appearing in the evidence for the first time; `thief_sent`
  4 is 05-06's other half (no hint composed for an already-resolved terminal turn). Nothing in
  05-07 can affect hint delivery — it changes one declaration string and two log lines. All three
  criteria PASS.
- **`04-10-SUMMARY.md` also quotes `STYLE_GUIDE` verbatim and was deliberately left alone.** It is a
  point-in-time record of what plan 04-10 shipped; rewriting it would falsify history. The live
  spec is `docs/PRD_deception.md`, which is what the plan names and what the new drift-guard test
  pins.

## Verification Results

| Gate | Result |
|---|---|
| `uv run ruff check .` | **All checks passed** (0 violations) |
| `uv run pytest tests/ --cov` | **1327 passed, 96.37%** (baseline 1308 / 96.36% -> **+19 tests**, coverage up) |
| `bash scripts/check_line_limit.sh` | **exit 0**; `agent_audit_wiring.py` = **134** code lines, `language_wiring.py` = 129, `bluff_prompt.py` = 68 |
| `uv run python scripts/check_no_llm_in_strategy.py` | **OK** — no forbidden imports |
| `uv run python scripts/measure_gate6.py` | **criterion 1 PASS · criterion 2 PASS · criterion 3 PASS** (`step0_verified_before_move_1` — the one this plan's blast radius covers) |
| Secret check | `grep -rn "ANTHROPIC_API_KEY" src/` -> 1 executable line (`client.py:25`) + 3 docstrings; **no value anywhere**. `grep -rn "claude_api" src/` -> 4 pre-existing sites, **zero added by this plan** |
| Behaviour unchanged | `env -u ANTHROPIC_API_KEY uv run pytest tests/ -q` -> **1327 passed**; the 4 `test_llm_degradation.py` cases pass **unedited** |
| `config/*/games_played.json` | untracked and **never edited** — only real games moved the counters (rule 38) |

The plan predicted +6 to +9 tests; the actual is **+19**, from the two rule-4 sentinel controls, the
four-way template/key parametrisation, the PRD drift guard, and the shape assertion running on every
declaration path rather than once.

## User Setup Required

None — no external service configuration required. `ANTHROPIC_API_KEY` remains **optional** exactly
as `REMOTE-ROUND-RUNBOOK.md` documents; the only change is that its absence is now announced.

## Next Phase Readiness

- **G5 is closed.** Four of the five 2026-08-13 gaps (G1-G5) are now closed on the code side. Only
  **05-08** remains: the human-run remote round, attempt 2, which is what GATE-5 criterion 2 needs.
- **For 05-08 specifically:** the operator will now see the keyless warning at startup on any
  machine without a key, and the two machines' declarations will no longer be
  byte-indistinguishable when one is live and the other is not. If the runbook's evidence checklist
  wants it, `llm_name` is now a reliable field for telling the two rounds apart after the fact.
- No blockers.

## Self-Check: PASSED

- All 15 files claimed above exist on disk (checked with `[ -f ]`).
- Both task commits exist in `git log` (`951d87d`, `50ac2fe`).
- Every measured number in this summary was re-run at the final tree state, not copied from a
  mid-execution run: 1327 passed / 96.37%, ruff 0, line gate exit 0, GATE-6 three PASS.
- `client.py:25` is the single executable definition of the env var name, verified by `sed -n 25p`.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-14*
