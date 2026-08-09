---
phase: 04-language-and-scent
plan: "10"
subsystem: services-llm
tags: [bluff-generator, template-bank, word-limit, hint-composition, d-33, d-36, d-39, d-45, lang-01, lang-02]

# Dependency graph
requires:
  - "04-06: Provider/LlmResult/LlmFailure/LlmFailureReason, TemplateProvider, DegradeLevel (services/llm/provider.py, template_provider.py, budget.py) -- the provider seam compose() calls through"
  - "04-08: DeceptionPlan/ClaimKind/Intent/ALWAYS_TRUE_KINDS (shared/deception_types.py), declare_truthfully (strategy/deception.py) -- the input this module phrases and never alters"
provides:
  - "wordcount.count(text)/wordcount.truncate(text, limit) -- one whitespace-splitting rule, shared by the validator, the retry decision and the truncator"
  - "hintbank.HintBank(rng=...).select(plan, arena=...) -- the total, zero-token, kind/intent-aware fallback bank, import-time validated against the real shipped word limit"
  - "hintbank.validate_bank(word_limit) -- the reusable guard, independent of the module's own self-check"
  - "bluff.BluffContext / bluff.compose(plan, context) -- the total hint composer: one call, one retry, truncate, coordinate check, bank fallback on every failure path"
  - "bluff_prompt.STYLE_GUIDE / build_system_prompt / build_user_prompt -- D-39's style guide, and a prompt that never reads plan.intent/true_region/true_heading"
  - "shared/hint_guard.assert_no_coordinates -- moved here from network/hint_payload.py so services/llm/ can reach it without a new services<->network dependency"
  - "language.json's model group gains hint_word_limit (Table 14 row 2), validated by shared/language_model_config.py"
affects: [04-11-belief-adapter, 04-12-turn-pipeline, 04-13-phase-docs, 04-14-gate-4-measurement]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A stateful per-game fallback bank with a structural (not configured) no-repeat guarantee: HintBank shuffles a FULL cycle of a key's own templates and pops from it, so the window before any repeat IS the bucket size -- no second magic number invented for 'how often is too often'."
    - "A module reading its OWN package's already-negotiated config value at import time via a direct json.load + loader_helpers call, deliberately bypassing the package's own validated loader (load_language_config()/validate_model_group()) to avoid a genuine circular import: that loader's model-group validation calls back into pursuit.services.llm's provider registry, and hintbank.py is itself part of that package."
    - "A prompt-building module that receives a full decision object (DeceptionPlan, including intent) as a parameter but deliberately never reads certain fields (intent, true_region, true_heading) -- the omission itself, not a runtime check, is what makes the module structurally incapable of leaking or deciding the withheld value (D-36)."

key-files:
  created:
    - src/pursuit/services/llm/wordcount.py
    - src/pursuit/services/llm/hintbank.py
    - src/pursuit/services/llm/hintbank_templates.py
    - src/pursuit/services/llm/bluff.py
    - src/pursuit/services/llm/bluff_prompt.py
    - src/pursuit/shared/hint_guard.py
    - tests/unit/services/test_wordcount.py
    - tests/unit/services/test_hintbank.py
    - tests/unit/services/test_hintbank_templates.py
    - tests/unit/services/test_bluff.py
    - tests/unit/services/test_bluff_prompt.py
    - tests/unit/services/test_bluff_property.py
  modified:
    - src/pursuit/network/hint_payload.py
    - src/pursuit/services/llm/__init__.py
    - src/pursuit/shared/language_model_config.py
    - config/police/language.json
    - config/thief/language.json
    - tests/unit/test_language_model_config.py
    - tests/unit/test_language_config_model.py

key-decisions:
  - "The Table 14 row 2 word limit's config home is language.json's model group (ModelKey.HINT_WORD_LIMIT), NOT deception.json/deception_config.py as 04-10-PLAN.md's own files_modified listed -- it governs the LLM CHANNEL (shared by bluff.py's emission side and 04-07's DecodeContext.word_limit on the decode side), not the deception POLICY. Documented as a deviation below; RESUME.md carry-over A closed, carry-over J opened for 04-12."
  - "assert_no_coordinates moved from network/hint_payload.py to a new shared/hint_guard.py, re-exported unchanged -- services/llm/bluff.py needs the exact same check LANG-02 already required on the send path, and there is no established services<->network dependency anywhere in this codebase. Follows 04-08's identical precedent for Intent/DirectionWord."
  - "hintbank.py reads the shipped config/police/language.json directly (json.load + loader_helpers.require_int), bypassing load_language_config()/validate_model_group() -- that path's deferred import re-enters pursuit.services.llm's own provider registry, and hintbank.py is itself part of that package; calling it from hintbank.py's own import time would risk exactly the class of cycle 04-06 already worked around in the opposite direction. Verified empirically safe both import orders (hintbank imported directly first, and via the package)."
  - "compose()'s retry-failure handling: if the one retry attempt itself returns an LlmFailure or an empty completion, compose() truncates the ORIGINAL over-length completion rather than falling back to the bank -- a verbose-but-real response is still worth truncating; the bank is reserved for 'no usable model text at all'."
  - "bluff_prompt.py's build_user_prompt never reads plan.intent, plan.true_region or plan.true_heading -- phrasing a claim confidently is the identical operation whether it is true or a lie, so the model receives no signal to leak or decide the flag (D-36), enforced by omission rather than by a runtime check."
  - "HintBank's no-repeat guarantee is structural: a fresh shuffled permutation of a key's own templates, popped until exhausted, with a boundary swap to avoid an immediate repeat across cycles. No second 'window' number is configured -- the window is the bucket size."

patterns-established:
  - "Per-game stateful fallback objects (HintBank) constructed once and held for a game's duration, matching 04-09's Reliability ownership precedent -- never persisted, never shared between the cop and thief processes."

requirements-completed: [LANG-01, LANG-02, LANG-06]

# Metrics
duration: ~55min, 3 task commits
completed: 2026-08-09
---

# Phase 4 Plan 10: Bluff Generator Summary

**`compose()` turns a `DeceptionPlan` into an English hint that is always in-limit, always coordinate-free and never empty -- one word-counting rule, one retry, and a seeded per-game template bank that never touches the network.**

## Performance

- **Duration:** ~55 min (estimate; exact start time not captured), 3 atomic task commits
- **Completed:** 2026-08-09
- **Tasks:** 3/3
- **Files created:** 12 (6 source modules, 6 test files). **Files modified:** 7.

## Accomplishments

- `wordcount.py` (Task 1): `count()`/`truncate()` share exactly one rule (whitespace `str.split()`), documented as deliberately the least clever rule available so an opponent's own word count can never silently disagree with ours. `truncate()` keeps a grammatical-looking sentence: cuts to the limit, drops a trailing conjunction/preposition (never emptying to nothing), strips leftover punctuation, closes with a period.
- `hintbank.py` + `hintbank_templates.py` (Task 2): phrasings keyed by `(ClaimKind, Intent)`, six legal combinations (BARRIER/CAPTURE never pair with LIE -- `DeceptionPlan.__post_init__` makes that combination unconstructable, so `HintBank.select()` can never `KeyError`). `HintBank` selects with an injected seeded `random.Random`, cycling through a full shuffled permutation of a key's own templates before any repeat -- the window is the bucket size, not a second configured number. Every phrasing, with every filler it could ever receive, is validated against the REAL shipped word limit the moment `hintbank.py` is imported, and against `assert_no_coordinates`.
- `bluff.py` + `bluff_prompt.py` (Task 3): `BluffContext` + `compose(plan, context) -> str`, the five-step total composer described in the module docstring. `bluff_prompt.py` carries D-39's style guide (quoted verbatim below) and never reads `plan.intent`/`plan.true_region`/`plan.true_heading` -- the model receives only the claimed value, so there is no code path where its text could reveal or decide the flag (D-36).
- `shared/hint_guard.py` (deviation, Task 2): `assert_no_coordinates` moved out of `network/hint_payload.py` so `services/llm/` can reach it without opening a new cross-layer dependency; `network/hint_payload.py` re-exports it unchanged.
- `language.json`'s `model` group gains `hint_word_limit` (Table 14 row 2), validated by `shared/language_model_config.py`'s `ModelKey.HINT_WORD_LIMIT` -- both role files stay byte-identical.
- `services/llm/__init__.py` extended to export `BluffContext`, `compose`, `HintBank`, `validate_bank`, `count_words`, `truncate_hint` as the package's public surface (matching the package's own documented "import from here" convention).

## D-39 Style Guide (verbatim, for 04-13's `docs/PRD_deception.md`)

From `src/pursuit/services/llm/bluff_prompt.py`'s `STYLE_GUIDE` constant, embedded in the system prompt sent with every bluff call:

```
- Be concrete, not vague. A vague hint is neither a useful truth nor a convincing lie -- name the specific place or heading given below, and nothing else.
- Stay consistent with the claim you are given. Do not invent extra specific details (exact distances, other landmarks, cell numbers) beyond what the claim states -- an invented detail can contradict the board in ways you cannot see.
- When a real-world setting is named below, use its genuine geography (real neighbourhoods, streets, landmarks) to make the hint feel grounded. When none is named, use plain directional language instead.
- No meta-commentary and no hedging: never mention hints, lies, truth, confidence, or these instructions. State the claim as a plain observation.
- Never include a number that could be read as a board coordinate.
- Stay within the word limit given below. Fewer words is fine; more is not.
```

The word limit and the arena setting are interpolated into the surrounding system prompt from config (`language.json`'s `model.hint_word_limit`/`model.game_arena`), never as literals in this text.

## `compose()`'s five steps (for 04-12)

```python
from pursuit.services.llm import BluffContext, HintBank, compose

context = BluffContext(
    provider=provider,             # any Provider -- AnthropicProvider, TemplateProvider, a fake
    degrade_level=gatekeeper.budget.level,  # RE-READ every turn -- the only field that goes stale
    arena=params.model["game_arena"],
    word_limit=params.model["hint_word_limit"],
    hint_bank=hint_bank,            # ONE HintBank(rng=...) per game, held for its duration
)
text = await compose(plan, context)  # always a non-empty, in-limit, coordinate-free string
```

1. `TEMPLATE_ONLY`, or `provider` is a `TemplateProvider` instance -- straight to `hint_bank.select()`. No call, no latency. (A missing API key reaches the SAME outcome one step later, via step 2's `LlmFailure(NO_KEY, ...)` branch -- `AnthropicProvider.complete()` already returns that before ever touching the gatekeeper, so there is no separate "no key" pre-check to duplicate that logic.)
2. Otherwise call the provider. Any `LlmFailure` (any reason, including one raised instead of returned) -- straight to the bank.
3. Count the result. Over the limit -- exactly one retry with an explicit shortening instruction. Still over, or the retry itself failed -- truncate the best text in hand (the original completion if the retry failed, the retry's text if it succeeded).
4. Validate with `assert_no_coordinates`. On violation -- straight to the bank; never attempt to repair model text.
5. Return.

## Task Commits

Each task was committed atomically:

1. **Task 1: one tokenisation rule, used everywhere** - `96e6a1f` (feat) -- `wordcount.py`, `test_wordcount.py`.
2. **Task 2: the template bank** - `4fe296c` (feat) -- `hintbank.py`, `hintbank_templates.py`, `shared/hint_guard.py` (deviation), `network/hint_payload.py` (deviation), `shared/language_model_config.py` (deviation), both `config/{police,thief}/language.json` (deviation), `test_hintbank.py`, `test_hintbank_templates.py`, `test_language_model_config.py`, `test_language_config_model.py`.
3. **Task 3: compose -- the three-layer limit and the total fallback** - `5ca802b` (feat) -- `bluff.py`, `bluff_prompt.py`, `services/llm/__init__.py`, `test_bluff.py`, `test_bluff_prompt.py`, `test_bluff_property.py` (deviation split).

## Files Created/Modified

- `src/pursuit/services/llm/wordcount.py` - `count()`, `truncate()`
- `src/pursuit/services/llm/hintbank.py` - `HintBank`, `validate_bank()`, `_slot_for()`, `_all_slot_fillers()`, `_shipped_word_limit()`
- `src/pursuit/services/llm/hintbank_templates.py` - the phrasing/filler data tables, `BANK`
- `src/pursuit/services/llm/bluff.py` - `BluffContext`, `compose()`, `_complete()`, `_usable_text()`
- `src/pursuit/services/llm/bluff_prompt.py` - `STYLE_GUIDE`, `build_system_prompt()`, `build_user_prompt()`, `_describe_claim()`
- `src/pursuit/shared/hint_guard.py` - `assert_no_coordinates` (moved from `network/hint_payload.py`)
- `src/pursuit/network/hint_payload.py` - re-exports `assert_no_coordinates` from `shared/hint_guard.py`
- `src/pursuit/services/llm/__init__.py` - exports the new public names
- `src/pursuit/shared/language_model_config.py` - `ModelKey.HINT_WORD_LIMIT`, its validation
- `config/police/language.json`, `config/thief/language.json` - `model.hint_word_limit: 15`, byte-identical
- `tests/unit/services/test_wordcount.py` - 25 tests
- `tests/unit/services/test_hintbank.py` - 19 tests; `tests/unit/services/test_hintbank_templates.py` - 9 tests
- `tests/unit/services/test_bluff.py` - 12 tests; `tests/unit/services/test_bluff_prompt.py` - 14 tests; `tests/unit/services/test_bluff_property.py` - 3 tests (deviation split)
- `tests/unit/test_language_model_config.py`, `tests/unit/test_language_config_model.py` - extended for `hint_word_limit`

## Decisions Made

See frontmatter `key-decisions` for the full list. The two with the widest blast radius for 04-12:

- **The word limit's one config home is `language.json`'s `model` group**, read once and passed into both `DecodeContext.word_limit` (04-07) and `BluffContext.word_limit` (this plan) -- 04-12 must not invent a second read path.
- **`BluffContext.degrade_level` is the one field that changes mid-game** and must be refreshed every turn; every other field (including the one `HintBank`) is constructed once per game and held, matching 04-09's `Reliability` precedent.

## Deviations from Plan

### Auto-fixed / Deliberate Issues

**1. [Rule 4-adjacent architectural choice, resolved per carry-over A's own instruction] Word limit's config home moved from `deception.json` to `language.json`**
- **Found during:** Task 2, before writing `hintbank.py`'s import-time validation.
- **Issue:** 04-10-PLAN.md's `files_modified` lists `shared/deception_config.py` and `config/{police,thief}/deception.json` as the word limit's home, but RESUME.md's carry-over A explicitly asked this plan to "decide one home, state the reasoning" between that and `language.json`'s `model` group, since the two disagreed.
- **Fix:** Chose `language.json`'s `model` group (`ModelKey.HINT_WORD_LIMIT`, `shared/language_model_config.py`) because the limit is a property of the LLM CHANNEL shared by the decode side (`DecodeContext.word_limit`, 04-07) and the emission side (this plan) -- both already read `model.game_arena` from the same file for the same reason. `deception.json` governs the lie/herding POLICY (D-37/D-38's knobs) and never needed this number. `deception.json`/`deception_config.py` were therefore left untouched by this plan.
- **Files modified:** `src/pursuit/shared/language_model_config.py`, `config/police/language.json`, `config/thief/language.json` (instead of the deception equivalents).
- **Verification:** `tests/unit/test_language_model_config.py`/`test_language_config_model.py` (extended), `test_hintbank.py::test_the_shipped_word_limit_validates_every_phrasing`.
- **Committed in:** `4fe296c` (Task 2 commit).

**2. [Rule 3 - Blocking] `assert_no_coordinates` moved to a new `shared/hint_guard.py`**
- **Found during:** Task 2/3, resolving carry-over E's explicit instruction to check whether `services/` may import `network/` before importing the validator directly.
- **Issue:** No existing code in this repository has `services/` importing `network/` (or vice versa) in either direction; opening that edge for one function would be a new, undocumented cross-layer dependency, and 04-08 already set the precedent of moving a cross-cutting piece two layers both need down into `shared/` (`Intent`, `DirectionWord`/`Origin`) rather than introducing a new import direction.
- **Fix:** `assert_no_coordinates` (and its two regex patterns) moved to `shared/hint_guard.py`; `network/hint_payload.py` re-exports it unchanged, so every existing `from pursuit.network.hint_payload import assert_no_coordinates` call site (including `tests/unit/test_hint_payload.py`) resolves identically with zero test changes needed there.
- **Files modified:** `src/pursuit/shared/hint_guard.py` (new), `src/pursuit/network/hint_payload.py`.
- **Verification:** `tests/unit/test_hint_payload.py` (unchanged, still green), `tests/unit/test_turn_buffer.py`, `tests/unit/test_orchestrator_loop.py`, `tests/unit/test_deception_types.py` re-run clean.
- **Committed in:** `4fe296c` (Task 2 commit).

**3. [Rule 3 - Blocking] `hintbank.py` reads `language.json` directly, bypassing `load_language_config()`**
- **Found during:** Task 2, designing the "validated at import time" self-check.
- **Issue:** The obvious implementation -- call `load_language_config()` and read `.model["hint_word_limit"]` -- routes through `validate_model_group()`'s own deferred `from pursuit.services.llm import get_provider_class` import (04-06's own cycle workaround, for the OPPOSITE direction: `shared -> services.llm`). Triggering that call from `hintbank.py`'s own module-import time (itself `services.llm.hintbank`) risks re-entering the same package while it may be transitively mid-init, depending on import order.
- **Fix:** `hintbank.py` reads the file directly with `json.load()` plus the same `loader_helpers.require_int()` every other loader uses, importing only `ModelKey` (a plain enum, no cycle risk) from `shared/language_model_config.py` -- never `load_language_config`/`validate_model_group`. Verified empirically safe in both import orders (importing `pursuit.services.llm.hintbank` directly first, and importing the `pursuit.services.llm` package first).
- **Files modified:** `src/pursuit/services/llm/hintbank.py`.
- **Verification:** Manual probes both import orders (documented in the module's own docstring); full suite green; `pursuit.services.llm` package import and `load_language_config()` both re-confirmed clean after the change.
- **Committed in:** `4fe296c` (Task 2 commit).

**4. [Rule 3 - Blocking] `hintbank_templates.py` created beyond the plan's `files_modified`**
- **Found during:** Task 2, after the phrasing/filler tables plus selection logic pushed `hintbank.py` toward the 150-code-line gate.
- **Issue:** Segal Table 5's hard line limit; "split files, never compress code to fit."
- **Fix:** Pure data (the phrasing tuples, the region/heading filler tables, `BANK`) split into `hintbank_templates.py`; `hintbank.py` keeps selection logic, import-time validation and the `HintBank` class only.
- **Files modified:** `src/pursuit/services/llm/hintbank_templates.py` (new).
- **Verification:** `bash scripts/check_line_limit.sh` clean for both files.
- **Committed in:** `4fe296c` (Task 2 commit).

**5. [Rule 3 - Blocking] `test_bluff.py` split into `test_bluff.py` + `test_bluff_property.py`**
- **Found during:** Task 3, after the direct behavioural cases plus the AST structural checks plus the 300-iteration adversarial property test reached 201 code lines.
- **Issue:** Same 150-line gate, applied to a test file.
- **Fix:** `test_bluff.py` keeps `FakeProvider`/`_plan`/`_context`/`_result`/`WORD_LIMIT` and the direct behavioural cases (verify bullets 1-5); `test_bluff_property.py` (new) imports those fakes and holds the AST no-raise/no-bare-except proof plus the adversarial property test (verify bullet 6) -- exact precedent of `test_gatekeeper.py`/`test_gatekeeper_retry.py`.
- **Files modified:** `tests/unit/services/test_bluff.py`, `tests/unit/services/test_bluff_property.py` (new).
- **Verification:** `bash scripts/check_line_limit.sh` clean for both files; full suite green.
- **Committed in:** `5ca802b` (Task 3 commit).

**6. [Rule 2 - Missing functionality] `hintbank_templates.py`, `bluff_prompt.py` each get a dedicated test file**
- **Found during:** Tasks 2/3, after creating modules not individually named in the plan's `files_modified` (which listed only `test_bluff.py`/`test_hintbank.py`/`test_wordcount.py`).
- **Issue:** CLAUDE.md's "every module gets a test file" rule, same precedent 04-03/04-06/04-08 already set for their own split-out modules.
- **Fix:** Added `tests/unit/services/test_hintbank_templates.py` (9 tests: data-shape invariants -- every legal `(kind, intent)` pair covered, every region/heading has both an arena and a generic filler, the two always differ) and `tests/unit/services/test_bluff_prompt.py` (14 tests: arena/generic system-prompt branching, the style guide embedded verbatim, and -- the load-bearing one -- that `build_user_prompt` never leaks `intent`/`true_region`/`true_heading` for any of the four `ClaimKind`s).
- **Files modified:** `tests/unit/services/test_hintbank_templates.py` (new), `tests/unit/services/test_bluff_prompt.py` (new).
- **Verification:** All tests pass; both new source modules show 100% coverage.
- **Committed in:** `4fe296c` (Task 2), `5ca802b` (Task 3).

---

**Total deviations:** 6 -- one carry-over-directed architectural choice (word limit's config home, explicitly invited by the plan itself), three Rule-3 blocking structural fixes (the coordinate-guard relocation, the circular-import-avoiding config read, one file split), one further Rule-3 line-limit split, one Rule-2 test-coverage addition. No scope creep; `deception.json`/`deception_config.py` were correctly left untouched since nothing in this plan needed a new field there.
**Impact on plan:** All deviations were necessary to satisfy either a hard CI gate, a genuine circular-import risk, or the plan's own explicit invitation to resolve carry-over A. The public `compose()`/`BluffContext`/`HintBank` contracts match the plan's `must_haves` exactly.

## Issues Encountered

None beyond what is captured above as deviations.

## Verification (plan's own block, run in full on the merged tree)

1. `uv run ruff check .` -> **0 violations**. `uv run pytest tests/ --cov` -> **1001 passed, 94.81%** (floor 85%).
2. `bash scripts/check_line_limit.sh` -> clean, repo-wide (no output, exit 0).
3. No test performs network I/O -- every provider in every new test is `FakeProvider`/`TemplateProvider`/a plain mock; `grep`-checked for `requests.`/`httpx.`/`aiohttp.`/`socket.`/`urlopen` across the new test files -- no match.
4. `grep -nE "\b15\b" src/pursuit/services/llm/` -> **no match** (exit 1 / empty). The limit is config-only in both `bluff_prompt.py` (interpolated) and `hintbank.py`'s import-time check (read from the real shipped file).
5. `grep -c "retry" src/pursuit/services/llm/bluff.py` -> **6** occurrences (docstring + code), corroborated by `test_an_over_length_completion_retries_exactly_once_then_truncates` and `test_a_third_call_never_happens_even_when_the_retry_is_also_over_length`, both asserting `provider.calls == 2` (one original call, one retry, never a third).
6. `compose` contains no `raise` and no bare `except` -- enforced by an AST-walking regression test (`test_compose_contains_no_raise_statement`, `test_compose_contains_no_bare_except`), not just a manual read.

Additionally: `uv run python scripts/check_no_llm_in_strategy.py` -> clean (this plan touches no `strategy/` file at all, confirmed by the same gate).

## User Setup Required

None -- no external service configuration required. This plan's own tests never call the real Anthropic API (every provider is mocked); the API-key path was already covered by 04-06.

## Next Phase Readiness

- **04-11 (`BeliefAdapter`)** is unaffected by this plan -- no dependency either direction.
- **04-12 (turn-pipeline integration)** is the direct consumer: read carry-overs J-N in `RESUME.md` before wiring `compose()` into the turn loop. In particular: read `language.json`'s `model.hint_word_limit` once and feed the SAME value into both `DecodeContext.word_limit` and `BluffContext.word_limit`; construct exactly one `HintBank(rng=...)` per game and reuse it across every turn; refresh `BluffContext.degrade_level` from `gatekeeper.budget.level` before every call.
- **04-13** should quote this SUMMARY's "D-39 Style Guide" section verbatim into `docs/PRD_deception.md`, and should record the word-limit config-home deviation (carry-over A closed, per this SUMMARY) in `RULES-RESOLUTION-LANG.md` if it discusses Table 14's implementation.
- **04-14 (GATE-4 measurement)** owns the one number this plan deliberately does NOT produce: the measured fallback rate over a full game against the REAL Anthropic API. This plan's `_AdversarialProvider` property test proves `compose()`'s behaviour is correct against a mocked adversary; it is not a substitute for a live-API measurement, and no test in this plan calls the real API (per this plan's own environment constraints).
- Knowledge graph refreshed this session (4917 nodes / 8593 edges / 311 communities); `GRAPH_REPORT.md` committed alongside this SUMMARY.
- No blockers.

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-09*

## Self-Check: PASSED

All 19 claimed source/test files verified present on disk with `[ -f ]`, plus this
SUMMARY.md, `RESUME.md`, and `.planning/graphs/GRAPH_REPORT.md`. All 3 claimed task
commit hashes (`96e6a1f`, `4fe296c`, `5ca802b`) verified present in `git log --oneline
--all`. No missing items.

Full-suite re-confirmation at self-check time: `uv run pytest tests/ --cov` -- 1001
passed, 94.81% coverage (required 85%); `uv run ruff check .` -- 0 violations;
`bash scripts/check_line_limit.sh` (project-wide) -- 0 violations; `uv run python
scripts/check_no_llm_in_strategy.py` -- clean.
