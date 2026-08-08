---
phase: 04-language-and-scent
plan: "03"
subsystem: infra
tags: [llm-gatekeeper, rate-limiting, token-bucket, token-budget, asyncio, table-19, qual-03, qual-05]

# Dependency graph
requires: []
provides:
  - "language.json (config/police, config/thief) + LanguageKey + load_language_config() -- Table 19/18 sourced, floor-checked, byte-identical role files"
  - "TokenBucket (services/llm/bucket.py) -- Table 19's token-bucket law, injected clock, no time.sleep"
  - "TokenBudget + DegradeLevel (services/llm/budget.py) -- D-35 cumulative spend, reserve/settle, ratcheted degrade ladder, report()"
  - "Gatekeeper + GatekeeperOverflow + CallResult (services/llm/gatekeeper.py) -- the one door: budget reserve, FIFO queue bounded at queue_depth, parallel-call semaphore, rate-limited retry/backoff, budget settle"
  - "services/llm package public surface (__init__.py) re-exporting all of the above"
affects: [04-06-provider-layer, 04-07-hint-decoder, 04-10-bluff-generator, phase-7-gmail-reporting]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Injected clock/sleep seams (default time.monotonic/asyncio.sleep) so every timing-sensitive class is testable with a FakeClock/FakeSleep and no test ever calls time.sleep"
    - "Reserve-then-settle budget accounting: optimistic reserve() before a call so queued-but-not-yet-run calls already count toward the degrade level; settle() reconciles with observed usage afterwards and only ever adds (never subtracts) to the running total, which is what makes the degrade level provably non-regressing"
    - "FIFO admission queue built from asyncio.Semaphore's own waiter ordering plus a separate _waiting counter bounding queue_depth, rather than a second explicit queue data structure"
    - "CallResult(value, input_tokens, output_tokens) as the generic fn contract for Gatekeeper.submit() -- keeps the gatekeeper provider-agnostic while still letting it settle real observed usage"

key-files:
  created:
    - src/pursuit/shared/language_config.py
    - src/pursuit/services/llm/__init__.py
    - src/pursuit/services/llm/bucket.py
    - src/pursuit/services/llm/budget.py
    - src/pursuit/services/llm/gatekeeper.py
    - config/police/language.json
    - config/thief/language.json
    - tests/unit/test_language_config.py
    - tests/unit/services/__init__.py
    - tests/unit/services/test_bucket.py
    - tests/unit/services/test_budget.py
    - tests/unit/services/test_gatekeeper.py
    - tests/unit/services/test_gatekeeper_retry.py
  modified: []

key-decisions:
  - "TokenBucket's capacity and refill_rate are generic constructor kwargs (not tied to LanguageParams); Gatekeeper is the single place that derives capacity=requests_per_minute and refill_rate=requests_per_minute/60 from Table 19 row 1, documented inline -- no new number invented, and bucket.py stays reusable without a config dependency"
  - "Gatekeeper.submit(fn, *, estimated_tokens) requires fn to return a CallResult(value, input_tokens, output_tokens) rather than an arbitrary object, because settle() needs real observed usage and a fully opaque return value can't supply that generically; Phase 7's Gmail integration passes input_tokens=output_tokens=0"
  - "GatekeeperOverflow keeps its plan-mandated name despite ruff's N818 (Error-suffix) rule -- noqa'd with the same justification precedent as network/deadline.py's DeadlineExpired"
  - "Vendor SDK names (the two the module docstring warns against) are never spelled out anywhere in services/llm/ source, including in prose explaining their absence -- the plan's own verify step is a literal `grep -rn` for those words, so naming them defensively would itself fail the check"
  - "test_gatekeeper.py split into test_gatekeeper.py + test_gatekeeper_retry.py at the 150-code-line gate, mirroring the existing test_deadline.py/test_deadline_retry.py precedent (shared fakes defined once, imported by the sibling)"

patterns-established:
  - "Reserve/settle budget accounting: any future per-series resource tracker (not just tokens) can follow the same reserve(estimate) -> settle(actual) -> ratcheted-level shape"
  - "Package __init__.py as the sole public-import surface for a multi-module services/ subpackage, re-exporting via __all__"

requirements-completed: [QUAL-03, QUAL-05, LANG-06]

# Metrics
duration: ~30min (Tasks 2-4 this session; Task 1 completed in a prior, interrupted session)
completed: 2026-08-08
---

# Phase 4 Plan 03: LLM Gatekeeper Summary

**The project's one API gatekeeper: Table-19 token-bucket rate limiting, a FIFO admission queue bounded at `queue_depth` that raises typed `GatekeeperOverflow` on overflow, retry/backoff on any failure including a timeout, and a D-35 cumulative token budget that degrades `FULL -> SHORT_PROMPT -> TEMPLATE_ONLY` and never hard-stops a game.**

## Performance

- **Duration:** ~30 min for Tasks 2-4 (this session). Task 1 (`language.json` + loader) was completed and committed in a prior, interrupted agent session at `d5eed52`; this session verified it against the plan's own acceptance criteria before continuing.
- **Completed:** 2026-08-08
- **Tasks:** 4/4 (1 verified-complete from a prior session, 3 executed this session)
- **Files created:** 13 (4 source modules + 2 config files + 7 test files, including 2 scaffolding `__init__.py` files for new test package directories)

## Accomplishments

- `LanguageParams`/`load_language_config()` (Task 1, verified not redone): `config/{police,thief}/language.json` byte-identical, three groups (`gatekeeper`, `budget`, `model`), Table 19's five MINIMUM rows floor-checked with `ValueError` naming the key, degrade thresholds labelled as engineering defaults (D-18).
- `TokenBucket` (Task 2): Table 19's law verbatim, `tokens <- min(C, tokens + r*dt)`, admit iff `tokens >= 1`. Generic `capacity`/`refill_rate` kwargs, injected clock, `time_until_available()` for precise awaiting. Zero `time.sleep` in the module or its tests.
- `TokenBudget` + `DegradeLevel` (Task 3): cumulative input/output token accounting, `reserve()`/`settle()` estimate-then-reconcile, a level that crosses `FULL -> SHORT_PROMPT -> TEMPLATE_ONLY` in order and never regresses within one instance's life, `report()` that round-trips through `json.dumps`.
- `Gatekeeper` + `GatekeeperOverflow` + `CallResult` (Task 4): the single door every external call passes through. `submit(fn, *, estimated_tokens)` reserves against the budget, admits through a `queue_depth`-bounded FIFO queue (raising `GatekeeperOverflow` beyond it without disturbing already-queued work), acquires a `parallel_requests`-sized semaphore, awaits the token bucket once per attempt, runs `fn` under `response_timeout_seconds` with `retries_before_failure` retries and `wait_after_error_seconds` backoff on any failure (a timeout included), then settles the budget and returns `fn`'s value.
- `services/llm/__init__.py`: the package's public import surface (`Gatekeeper`, `GatekeeperOverflow`, `CallResult`, `TokenBucket`, `TokenBudget`, `DegradeLevel`).
- No `anthropic`/`openai` import or even a textual mention anywhere in `src/pursuit/services/llm/` — confirmed by `grep -rn`.

## `Gatekeeper.submit()` signature and `GatekeeperOverflow` contract (verbatim, for 04-06/04-07/04-10)

```python
from pursuit.services.llm import CallResult, Gatekeeper, GatekeeperOverflow
from pursuit.shared.language_config import load_language_config

gatekeeper = Gatekeeper(params=load_language_config(path))
# clock/sleep are also accepted as keyword-only overrides (default
# time.monotonic / asyncio.sleep) -- production code never passes them.

async def call_the_provider() -> CallResult:
    response = await my_llm_client.send(...)
    return CallResult(
        value=response,                       # opaque -- whatever the caller wants back
        input_tokens=response.usage.input,     # REQUIRED, no default -- pass 0 for a non-token call
        output_tokens=response.usage.output,   # REQUIRED, no default
    )

try:
    result = await gatekeeper.submit(call_the_provider, estimated_tokens=800)
except GatekeeperOverflow:
    ...   # D-33 deterministic fallback: the queue (>= queue_depth Table 19 row 5) is full
except Exception:
    ...   # D-33 deterministic fallback: every retry (Table 19 row 4) failed, incl. a timeout
```

- `fn` is a **zero-argument async callable** returning a `CallResult` -- never an
  Anthropic/OpenAI-shaped request object (D-34). `estimated_tokens` is reserved against the
  budget **before** admission, so a deep FIFO queue already reflects every queued call's
  contribution to the degrade level, not just completed ones.
- `GatekeeperOverflow` fires **only** when the FIFO queue is already at `queue_depth` (Table 19
  row 5); it is deliberately a plain `Exception` subclass (see Deviations) so callers can catch
  it narrowly. It is the caller's job to convert it into the D-33 fallback -- `submit()` never
  does that itself, and it never propagates unhandled into the turn loop by design.
- After `retries_before_failure` (Table 19 row 4) failed attempts -- **any** exception from `fn`,
  including a timeout past `response_timeout_seconds` (row 6, raised by `asyncio.wait_for` as
  `TimeoutError`) -- the **last** exception is re-raised unchanged. There is no separate
  "exhausted" exception type; catch broadly if 04-06/04-07/04-10 need one fallback path for both
  failure modes, or catch `GatekeeperOverflow` and `Exception` separately if they need to
  distinguish "queue full" from "the call itself failed."
- `gatekeeper.budget` is a public attribute (a live `TokenBudget`): `gatekeeper.budget.level` for
  the current `DegradeLevel` (to decide what prompt shape to build **before** calling `submit`),
  `gatekeeper.budget.report()` for the plain, `json.dumps`-able spend dict Phase 7's league email
  needs.

## Task Commits

Each task was committed atomically:

1. **Task 1: language.json config + loader with Table 19 floor checks** - `d5eed52` (feat) --
   completed in a prior, interrupted session; verified this session against the plan's own
   acceptance criteria (byte-identical role files, floor-checked minima, `LanguageKey` with no
   numeric literal) before continuing. Not redone.
2. **Task 2: the token bucket** - `cc192a7` (feat)
3. **Task 3: the cumulative budget and its degrade ladder** - `088e4da` (feat)
4. **Task 4: the gatekeeper itself** - `214cb77` (feat)

_No TDD-cycle multi-commits -- this plan's tasks are `type="auto"` without `tdd="true"`; each
task's tests were written alongside its implementation and committed together, per CLAUDE.md's
"every module gets a test file" rule._

## Files Created/Modified

- `config/police/language.json`, `config/thief/language.json` - byte-identical gatekeeper/budget/model config, Table 19 + Table 18 row 4 sourced
- `src/pursuit/shared/language_config.py` - `LanguageKey`, `LanguageParams`, `load_language_config()`; floor-checks Table 19's five MINIMUM rows
- `src/pursuit/services/llm/bucket.py` - `TokenBucket`: Table 19's token-bucket law, injected clock
- `src/pursuit/services/llm/budget.py` - `TokenBudget`, `DegradeLevel`: D-35 cumulative spend + ratcheted degrade ladder
- `src/pursuit/services/llm/gatekeeper.py` - `Gatekeeper`, `GatekeeperOverflow`, `CallResult`: the one door (rate limit, queue, retry/backoff, budget)
- `src/pursuit/services/llm/__init__.py` - package's public re-export surface
- `tests/unit/test_language_config.py` - Task 1's loader tests (12 tests)
- `tests/unit/services/__init__.py` - test package scaffolding
- `tests/unit/services/test_bucket.py` - `TokenBucket` tests (8) + shared `FakeClock`
- `tests/unit/services/test_budget.py` - `TokenBudget` tests (13)
- `tests/unit/services/test_gatekeeper.py` - `Gatekeeper` happy-path/budget/queue/overflow tests (9) + shared `FakeSleep`/`_params()`
- `tests/unit/services/test_gatekeeper_retry.py` - `Gatekeeper` retry/backoff/timeout tests (6)

## Decisions Made

- **`TokenBucket` stays generic** (raw `capacity`/`refill_rate` kwargs, no `LanguageParams` coupling) so it is independently testable and reusable; `Gatekeeper` is the single place that derives `capacity = requests_per_minute` and `refill_rate = requests_per_minute / 60` from Table 19 row 1, with the derivation documented inline rather than repeated or hidden.
- **`fn` must return `CallResult(value, input_tokens, output_tokens)`**, not an arbitrary object. Task 3's `settle(usage)` needs real observed usage, and a fully opaque return value cannot supply that generically without either narrowing to a specific provider's response shape (forbidden, D-34) or losing the "returns more tokens than estimated still lands in the running total" property (explicitly required). `CallResult` is the smallest generic shape that preserves both. Non-token calls (Phase 7 Gmail) pass `input_tokens=output_tokens=0` -- required, not defaulted, so every `fn` author states it explicitly.
- **The FIFO queue is `asyncio.Semaphore`'s own waiter ordering** plus a `_waiting` counter bounding `queue_depth`, not a second explicit `asyncio.Queue`. `Semaphore.acquire()` already blocks and wakes waiters in FIFO order; adding a second queue data structure would duplicate that ordering guarantee rather than reuse it.
- **Budget degrade level ratchets forward only.** `reserve()`/`settle()`'s optimistic accounting (adding the full estimate immediately, only topping up the excess at settle time) could otherwise let the computed level dip below a level a deep, still-in-flight queue had already reached — the spec explicitly forbids that regression, so `TokenBudget` tracks the highest level reached and only advances it, never lowers it.
- **`GatekeeperOverflow` keeps its plan-mandated name** rather than renaming to `GatekeeperOverflowError` to satisfy ruff's N818. `# noqa: N818` with an inline justification, following the exact precedent already in this codebase (`network/deadline.py`'s `DeadlineExpired`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Vendor SDK names removed from gatekeeper.py's own docstrings**
- **Found during:** Task 4, first `uv run pytest` pass of the vendor-absence test.
- **Issue:** The plan's own verify step for this task is a literal `grep -rn "anthropic" src/pursuit/services/llm/gatekeeper.py` that must return nothing. My first draft's module and class docstrings named the vendor defensively ("never an `Anthropic` request shape", "an `Anthropic` response") to *explain* why no such import exists -- which itself fails that exact grep.
- **Fix:** Reworded every mention to vendor-neutral language ("a vendor-specific request shape", "an LLM provider's response") — the intent (provider-agnostic, no SDK coupling) is unchanged, only the literal word is gone.
- **Files modified:** `src/pursuit/services/llm/gatekeeper.py`
- **Verification:** `grep -rni "anthropic\|openai" src/pursuit/services/llm/*.py` returns nothing; the dedicated `test_no_anthropic_or_openai_import_in_gatekeeper_module` test passes.
- **Committed in:** `214cb77` (Task 4 commit)

**2. [Rule 3 - Blocking] `tests/unit/services/test_gatekeeper.py` split at the 150-line gate**
- **Found during:** Task 4, after writing the full test suite and running `scripts/check_line_limit.sh`.
- **Issue:** The complete `Gatekeeper` test suite (happy path, budget, FIFO/parallel-cap ordering, overflow, retry/backoff, timeout, and the vendor-absence check) reached 158 code lines against the 150 hard limit -- and the plan's own Task 4 guidance anticipates exactly this for the *source* file ("If this file approaches 150 lines, split ... rather than compressing"), with the standing project rule ("split files, never compress code to fit") applying equally to test files (CLAUDE.md: "Test files obey the 150-line limit too").
- **Fix:** Split into `test_gatekeeper.py` (happy path, budget reflection, FIFO queue/parallel-cap/overflow -- plus the shared `FakeSleep`/`_params()` fixtures) and `test_gatekeeper_retry.py` (retry/backoff/timeout/vendor-absence, importing the shared fakes), mirroring the codebase's existing `tests/unit/test_deadline.py`/`test_deadline_retry.py` precedent exactly (shared fakes defined once, imported by the sibling).
- **Files modified:** `tests/unit/services/test_gatekeeper.py`, `tests/unit/services/test_gatekeeper_retry.py` (new)
- **Verification:** `bash scripts/check_line_limit.sh` passes on both files; all 32 `services/llm` tests still pass; 100% coverage of `src/pursuit/services/llm/`.
- **Committed in:** `214cb77` (Task 4 commit)

**3. [Rule 3 - Blocking] Two package-scaffolding `__init__.py` files added ahead of/alongside their owning task**
- **Found during:** Task 2 (`tests/unit/services/`) and confirmed as unnecessary for `src/pursuit/services/llm/` (left for Task 4 as the plan specifies).
- **Issue:** `tests/unit/services/` is a brand-new test directory; every sibling test directory in this codebase (`tests/unit/`, `tests/unit/strategy/`, `tests/unit/training/`) has an explicit `__init__.py`, and Task 2's own `<files>` list does not mention one (it wasn't anticipated as a new directory in the plan text).
- **Fix:** Added `tests/unit/services/__init__.py` (minimal docstring) in Task 2's commit, matching the established sibling-directory convention. Separately verified empirically (`uv run pytest` with no `src/pursuit/services/llm/__init__.py` present) that Python's namespace-package resolution imports `pursuit.services.llm.bucket` correctly without one -- so, per Task 4's own file list, `services/llm/__init__.py` was deliberately left uncreated until Task 4, which populates it with real content (the package's public re-export surface) rather than an empty stub.
- **Files modified:** `tests/unit/services/__init__.py`
- **Verification:** `uv run pytest tests/unit/services/test_bucket.py` passed both before and after `services/llm/__init__.py` existed.
- **Committed in:** `cc192a7` (Task 2 commit)

---

**Total deviations:** 3 auto-fixed, all Rule 3 (blocking issues resolved inline). No architectural changes, no scope creep — all three were necessary to satisfy the plan's own literal verify criteria or its explicitly stated "split, never compress" standing rule.
**Impact on plan:** None on the public contract described in this SUMMARY's `submit()`/`GatekeeperOverflow` section, which is what 04-06/04-07/04-10 code against.

## Issues Encountered

- **Arithmetic error in a first draft of `test_levels_cross_in_order_never_skip_or_regress`**: the expected level sequence for 4 settles of 60 tokens against thresholds (100, 200) was miscomputed (expected `TEMPLATE_ONLY` at the 3rd settle; the correct cumulative total there is 180, still `SHORT_PROMPT`). Caught immediately by the failing test, fixed by recomputing the running totals explicitly in a comment before asserting. No production code was affected.
- **Coverage gap on the bucket-wait branch inside `Gatekeeper._call_with_retry`** (`await self._sleep(wait)` when the bucket is empty): the initial test suite never exhausted the bucket within a single test (default `requests_per_minute=30` gives ample headroom for 2-3 calls). Added `test_exhausted_bucket_awaits_the_injected_sleep_before_the_next_call` with a small `requests_per_minute=2` override, bringing `src/pursuit/services/llm/` to 100% coverage.

## User Setup Required

None - no external service configuration required. This plan deliberately ships zero LLM-provider
SDK dependency (D-34); plan 04-06 introduces the actual provider and its API key requirement.

## Next Phase Readiness

- **04-06 (provider layer)** can construct `Gatekeeper(params=load_language_config(path))` and wrap
  its provider calls to return `CallResult`, without any changes to this plan's public surface.
- **04-07 (hint decoder)** and **04-10 (bluff generator)** call `gatekeeper.submit(...)` and handle
  `GatekeeperOverflow` / the surfaced retry-exhaustion exception via the D-33 deterministic
  fallback, exactly as documented above.
- **Phase 7 (Gmail reporting)** reuses this same `Gatekeeper` instance/class (D-34) and reads spend
  via `gatekeeper.budget.report()`; no rework anticipated.
- No blockers. `config/{police,thief}/language.json`'s `model` group is intentionally still `{}` --
  04-06 is the plan that defines and populates it, per this plan's own scope boundary.

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-08*
