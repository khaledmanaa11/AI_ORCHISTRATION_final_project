---
phase: 04-language-and-scent
plan: "06"
subsystem: services-llm
tags: [llm-provider, anthropic, haiku-4-5, template-fallback, provider-registry, d-32, d-33, d-52, lang-06]

# Dependency graph
requires:
  - "04-03: Gatekeeper/GatekeeperOverflow/CallResult (services/llm/gatekeeper.py) -- submit(fn, *, estimated_tokens)"
  - "04-03: LanguageParams/load_language_config (shared/language_config.py) -- the model: dict this plan fills and validates"
provides:
  - "Provider protocol (services/llm/provider.py) -- one async complete(system_prompt, user_prompt, schema=None) -> LlmResult | LlmFailure"
  - "LlmFailure/LlmFailureReason -- D-33's non-exceptional failure vocabulary, returned, never raised"
  - "register_provider()/get_provider_class() -- self-registering explicit dict registry, unknown name raises ValueError at lookup"
  - "TemplateProvider (services/llm/template_provider.py) -- zero-token, zero-network book-default fallback, selects from an injected phrase sequence"
  - "AnthropicProvider (services/llm/anthropic_provider.py) -- claude_api / Haiku 4.5, one request per complete(), submitted through Gatekeeper.submit(), served_model recorded on first success"
  - "build_client() (services/llm/client.py) -- lazy ANTHROPIC_API_KEY read, None (no client constructed) when unset"
  - "language.json's model group populated + validated (shared/language_model_config.py: ModelKey, validate_model_group)"
affects: [04-07-hint-decoder, 04-10-bluff-generator, phase-7-gmail-reporting, 04-14-gate-4-measurement]

# Tech tracking
tech-stack:
  added: ["anthropic>=0.121.0 (uv add, never pip)"]
  patterns:
    - "Self-registering provider registry: each concrete provider module imports Provider/LlmResult/LlmFailure from provider.py and calls register_provider(name, cls) on itself at the bottom of its own file, instead of provider.py importing its own implementations (which would cycle). services/llm/__init__.py is the composition root that imports every concrete provider so registration has run before any caller asks for the registry."
    - "Deferred (function-body) import to break a genuine package-level cycle: shared/language_model_config.py wants to validate model.provider against services.llm's registry, but services.llm.gatekeeper already imports shared/language_config.py at ITS top level. The services.llm import is deferred inside validate_model_group() so it only runs after shared/language_config.py's own top-level execution has finished."
    - "Local, zero-network token estimate (input_chars/4 + max_tokens) instead of a live SDK count_tokens() call -- keeps exactly one network call per complete(), matching D-34's 'the provider never calls the API directly' with no carve-out; TokenBudget.settle() reconciles against real response.usage regardless."
    - "Exception-to-reason mapping via an ordered tuple of (type, reason) pairs walked with isinstance, most-specific subclass first (APITimeoutError before its own parent APIConnectionError), with a final catch-all UNKNOWN reason -- never an uncaught exception past complete()."

key-files:
  created:
    - src/pursuit/services/llm/provider.py
    - src/pursuit/services/llm/template_provider.py
    - src/pursuit/services/llm/client.py
    - src/pursuit/services/llm/anthropic_provider.py
    - src/pursuit/shared/language_model_config.py
    - tests/unit/services/test_provider.py
    - tests/unit/services/test_anthropic_provider.py
    - tests/unit/services/test_anthropic_provider_errors.py
    - tests/unit/test_language_model_config.py
    - tests/unit/test_language_config_model.py
  modified:
    - src/pursuit/services/llm/__init__.py
    - src/pursuit/shared/language_config.py
    - config/police/language.json
    - config/thief/language.json
    - pyproject.toml
    - uv.lock
    - .env-example
    - tests/unit/test_language_config.py

key-decisions:
  - "model_id ships as the alias claude-haiku-4-5, not the dated snapshot claude-haiku-4-5-20251001 04-CONTEXT.md also records -- a dated snapshot pins the whole league season to one build, and the league explicitly permits changing code between games (docs/PARAMETERS.md rules attached to Appendix F)."
  - "Token estimation is a local heuristic, never a live count_tokens() call -- Task 2's own action text mentions count_tokens 'where the call is worth it', but the plan's must_haves is unambiguous ('the provider never calls the API directly', no carve-out) and QUAL-03/the wave_1_context both forbid a second network path. Resolved in favor of the stricter, must_haves-level rule: a live count_tokens() call would itself be an ungated request, doubling per-turn traffic against Table 19's requests_per_minute floor for every hint."
  - "LlmFailureReason gained an 11th value, UNKNOWN, beyond the 10 the plan enumerates -- the floor for an SDK error class no explicit mapping claims, so the final `except Exception` arm (which the plan explicitly sanctions) still returns a value instead of forcing an unrelated class into a misleading specific reason."
  - "DISABLED and BUDGET_EXHAUSTED are defined in LlmFailureReason but never produced by this plan's own code. D-35 is explicit that TokenBudget never hard-stops, so AnthropicProvider does not invent a refusal at any degrade level; a caller (04-07/04-10) that wants to skip calling complete() at a given every_n_steps/budget level can use these reasons for its OWN synthesized result without ever reaching the network."
  - "max_tokens=300 (engineering default, D-18 discipline) and timeout_seconds=30 (deliberately the same magnitude as gatekeeper.response_timeout_seconds, Table 19 row 6 -- not a second independently-invented number, the SDK client's own request timeout mirrors the value the gatekeeper's outer asyncio.wait_for already uses)."

patterns-established:
  - "Self-registering provider/plugin registry with a package __init__.py composition root -- reusable if Phase 7's Gmail integration or a later phase ever needs a second pluggable-by-config-string family of implementations."
  - "Deferred intra-project import to resolve a real (not merely stylistic) package-level cycle between a config-validation layer and the runtime registry it validates against."

requirements-completed: [LANG-06, QUAL-03]

# Metrics
duration: ~25min across 3 commits (22:14-22:25 UTC), preceded by SDK-verification research (installed-package introspection, no training-data guessing)
completed: 2026-08-08
---

# Phase 4 Plan 06: Provider Layer Summary

**One `Provider` protocol, one non-exceptional `LlmFailure` type, a zero-token `TemplateProvider` and a Haiku-4.5 `AnthropicProvider` that never calls the SDK outside `Gatekeeper.submit()` -- config validated at load, no secret in source, every test mocked.**

## Performance

- **Duration:** ~25 minutes across 3 atomic task commits (22:14:59-22:25:03 UTC), preceded by SDK-verification research directly against the installed `anthropic` package's source (type stubs, exception hierarchy, client signatures) rather than trained-in assumptions, since Table 19/D-34 leave zero room for a wrong SDK-shape guess to silently degrade every call.
- **Completed:** 2026-08-08
- **Tasks:** 3/3
- **Files created:** 10 (5 source modules + 5 test files). **Files modified:** 8.

## Accomplishments

- `provider.py` (Task 1): `Provider` (a `runtime_checkable` `Protocol`, one async `complete()` method), `LlmResult`/`LlmFailure`/`LlmFailureReason` (11 values: the plan's 10 plus `UNKNOWN`), and a self-registering `{name: class}` registry (`register_provider`/`get_provider_class`) that mirrors `strategy/registry.py`'s explicit-dict pattern without provider.py ever importing its own implementations.
- `template_provider.py` (Task 1): `TemplateProvider` -- zero tokens, zero network, selects from an injected phrase sequence via an injected `random.Random` seam. Registers itself as `"template"`.
- `client.py` + `anthropic_provider.py` (Task 2): `build_client()` reads `ANTHROPIC_API_KEY` from the environment only and returns `None` (no `AsyncAnthropic` ever constructed) when unset. `AnthropicProvider.complete()` builds one `messages.create` request (with `output_config={"format": {"type": "json_schema", "schema": ...}}` when a schema is supplied), submits it through `Gatekeeper.submit()` as a zero-argument callable, maps every SDK error class plus `GatekeeperOverflow` onto an `LlmFailure`, reconciles the budget from real `response.usage`, and records `served_model` from the first successful response. Registers itself as `"claude_api"`.
- `language_model_config.py` (Task 3, new -- see Deviations): `ModelKey` + `validate_model_group()` -- `provider` must be a registered key, `model_id` non-empty, `every_n_steps >= 1`, `max_tokens`/`timeout_seconds` positive, `game_arena` may be empty (generic cues). Never touches `os.environ`.
- `language_config.py` (Task 3): `load_language_config()` now calls `validate_model_group()` on the `model` group via a deferred import (see Deviations for why it must be deferred).
- `config/{police,thief}/language.json`'s `model` group filled and kept byte-identical: `provider="claude_api"`, `model_id="claude-haiku-4-5"`, `max_tokens=300`, `timeout_seconds=30`, `every_n_steps=1`, `game_arena="New York"`.
- `uv add anthropic` (never pip); `.env-example` gained `ANTHROPIC_API_KEY=your-key-here` with a comment explaining the D-33 degrade path.

## `Provider` signature and `LlmFailureReason` (verbatim, for 04-07/04-10)

```python
from pursuit.services.llm import (
    AnthropicProvider, TemplateProvider, LlmResult, LlmFailure, LlmFailureReason,
    get_provider_class, Gatekeeper,
)

class Provider(Protocol):
    async def complete(
        self, *, system_prompt: str, user_prompt: str, schema: dict | None = None,
    ) -> LlmResult | LlmFailure: ...

# LlmResult(text, parsed, input_tokens, output_tokens, model=None)
# LlmFailure(reason: LlmFailureReason, message: str)
```

`LlmFailureReason` values: `NO_KEY, AUTH, RATE_LIMITED, TIMEOUT, CONNECTION, BAD_REQUEST, SCHEMA_INVALID, OVERFLOW, BUDGET_EXHAUSTED, DISABLED, UNKNOWN`. D-33's contract: **every one of these is a return value; `complete()` never raises.** 04-07/04-10 should treat any `LlmFailure` (any reason) as "no evidence" / "fall back to the template path" -- the specific reason is for logging/diagnostics, not for a different control-flow branch, except where a caller specifically wants to distinguish (e.g. `OVERFLOW` meaning the call was never attempted at all).

**Constructor asymmetry 04-07/04-10 need to know:** `TemplateProvider(phrases=[...], rng=None)` and `AnthropicProvider(gatekeeper=..., model_id=..., max_tokens=..., timeout_seconds=...)` do **not** share a constructor signature -- `get_provider_class(name)` returns the *class*, not a ready instance, exactly like `strategy/registry.py`'s `build_brain()` precedent, but there is no shared `build_provider()` helper in this plan (the two providers' required construction-time context is too different: a phrase bank vs. a live `Gatekeeper`). Each caller constructs the provider it needs directly; `get_provider_class`/the registry exists for *validation* (Task 3's load-time check) and for anyone who genuinely branches on the configured name, not for blind generic instantiation.

## Estimated token cost (local heuristic; 04-14 reports the real number)

The budget ladder in 04-03 was configured against an estimate; this plan's `_estimate_tokens()` (`input_chars // 4 + max_tokens`) is that estimate's actual implementation, not a live measurement -- no API key exists in this sandbox and no test may reach the network. Computed against representative decode- and bluff-shaped prompts at the shipped `max_tokens=300`:

| Call shape | System + user prompt (approx.) | Estimated tokens |
|---|---|---|
| Decode-shaped (04-07) | ~340 chars (schema-driving system prompt + one hint sentence) | **390** |
| Bluff-shaped (04-10) | ~290 chars (style-guide system prompt + intent/payload) | **368** |

Both are dominated by the `max_tokens=300` output ceiling, which is the conservative half of the estimate (`TokenBudget.settle()` only ever reconciles this *up*, never down, against real `response.usage`). 04-14's live run against the real API is what turns this into a measured number.

## Task Commits

Each task was committed atomically:

1. **Task 1: the protocol, the failure type and the registry** - `fec0a85` (feat) -- `provider.py`, `template_provider.py`, `tests/unit/services/test_provider.py`.
2. **Task 2: the Haiku 4.5 provider** - `b6e4a6a` (feat) -- `client.py`, `anthropic_provider.py`, `services/llm/__init__.py` (deviation), `pyproject.toml`, `uv.lock`, `.env-example`, `tests/unit/services/test_anthropic_provider.py`, `tests/unit/services/test_anthropic_provider_errors.py` (deviation split).
3. **Task 3: config, provider selection and every_n_steps** - `5d2881e` (feat) -- `language_config.py`, `language_model_config.py` (deviation split), both `config/{police,thief}/language.json`, `tests/unit/test_language_config.py`, `tests/unit/test_language_config_model.py` (deviation split), `tests/unit/test_language_model_config.py` (deviation).

_No TDD-cycle multi-commits -- this plan's tasks are `type="auto"` without `tdd="true"`; each task's tests were written alongside its implementation and committed together, per CLAUDE.md's "every module gets a test file" rule._

## Files Created/Modified

- `src/pursuit/services/llm/provider.py` - `Provider`, `LlmResult`, `LlmFailure`, `LlmFailureReason`, `register_provider`, `get_provider_class`
- `src/pursuit/services/llm/template_provider.py` - `TemplateProvider`
- `src/pursuit/services/llm/client.py` - `build_client()`
- `src/pursuit/services/llm/anthropic_provider.py` - `AnthropicProvider`, `_map_exception`, `_estimate_tokens`
- `src/pursuit/services/llm/__init__.py` - extended to import + re-export both concrete providers (deviation)
- `src/pursuit/shared/language_model_config.py` - `ModelKey`, `validate_model_group()` (new, deviation split)
- `src/pursuit/shared/language_config.py` - wires `validate_model_group()` into `load_language_config()`
- `config/police/language.json`, `config/thief/language.json` - `model` group filled, byte-identical
- `pyproject.toml`, `uv.lock` - `anthropic>=0.121.0` (`uv add`)
- `.env-example` - `ANTHROPIC_API_KEY` dummy entry
- `tests/unit/services/test_provider.py` - Task 1 tests (10)
- `tests/unit/services/test_anthropic_provider.py` - Task 2 tests (11) + shared fakes
- `tests/unit/services/test_anthropic_provider_errors.py` - Task 2 error-mapping tests (9, incl. 7 parametrized) (deviation split)
- `tests/unit/test_language_config.py` - `model=={}`  assertion fixed to compare against the file's own `model` group
- `tests/unit/test_language_model_config.py` - `validate_model_group()` field-by-field tests (13) (deviation)
- `tests/unit/test_language_config_model.py` - `load_language_config()` model-group wiring/integration tests (4) (deviation split)

## Decisions Made

See frontmatter `key-decisions` for the full list (model_id alias vs. snapshot, local token estimate vs. live `count_tokens()`, the `UNKNOWN`/`DISABLED`/`BUDGET_EXHAUSTED` reason semantics, `max_tokens`/`timeout_seconds` sourcing). The two with the widest blast radius for future plans:

- **The provider registry validates and looks up by name; it does not blindly instantiate.** `get_provider_class(name)` returns a class, and 04-07/04-10 must construct it with the right per-provider kwargs themselves (see "Constructor asymmetry" above) -- there is no `build_provider(name, **kwargs)` in this plan.
- **Token estimation never touches the network.** Any future plan tempted to "improve accuracy" with a live `count_tokens()` pre-flight must wrap that call in `Gatekeeper.submit()` too (D-34's "one door" has no exception), and should first weigh doubling per-turn request volume against Table 19's `requests_per_minute` floor.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `services/llm/__init__.py` extended beyond the plan's `files_modified` list**
- **Found during:** Task 2, while designing the registry so `provider.py` never imports its own concrete implementations (which would create `provider.py` <-> `anthropic_provider.py` / `template_provider.py` cycles).
- **Issue:** The self-registering registry pattern (`register_provider()` called by each leaf module) only works if *something* imports every concrete provider module so its registration side effect actually runs. `provider.py` cannot be that something without cycling. `services/llm/__init__.py` is the established composition root (04-03's own docstring: "import from here, not from the sibling modules directly"), but it is not in 04-06-PLAN.md's `files_modified`.
- **Fix:** Extended `__init__.py` to import `anthropic_provider`/`template_provider` (triggering their `register_provider()` calls) and re-export the new public names.
- **Files modified:** `src/pursuit/services/llm/__init__.py`
- **Verification:** `uv run python -c "import pursuit.services.llm as llm; llm.get_provider_class('claude_api')"` succeeds; full import-chain traced by hand and confirmed acyclic (`__init__` -> `anthropic_provider` -> `provider`/`client`/`gatekeeper` -> `bucket`/`budget`/`shared.language_config`, with `language_config`'s own `services.llm` import deferred -- see deviation 2).
- **Committed in:** `b6e4a6a` (Task 2 commit)

**2. [Rule 3 - Blocking] Deferred import in `language_model_config.py` to break a real package-level cycle**
- **Found during:** Task 3, first attempt at a top-level `from pursuit.services.llm import get_provider_class` in the model-group validator.
- **Issue:** `services.llm.gatekeeper` already imports `shared.language_config` (04-03) at its own top level. A top-level `shared.language_model_config -> services.llm -> services.llm.anthropic_provider -> services.llm.gatekeeper -> shared.language_config` chain is a genuine cycle (not just a style smell) -- confirmed empirically as `ImportError: cannot import name 'get_provider_class' from partially initialized module`.
- **Fix:** The `from pursuit.services.llm import get_provider_class` import moved inside `validate_model_group()`'s function body. By the time that function is ever *called* (never at either module's import time), both modules have already finished their own top-level execution, so the import resolves cleanly regardless of which module triggers the chain first. Verified empirically both directions (importing `pursuit.services.llm` first, and calling `load_language_config()` cold).
- **Files modified:** `src/pursuit/shared/language_model_config.py`
- **Verification:** `uv run pytest tests/ --cov` (full suite, 565 tests) passes; manual chain trace in the module's own comment.
- **Committed in:** `5d2881e` (Task 3 commit)

**3. [Rule 3 - Blocking] `language_config.py`'s model-group validation split into a new file, `language_model_config.py`**
- **Found during:** Task 3, immediately after wiring `_validate_model_group()` inline -- `bash scripts/check_line_limit.sh` reported 173 counted lines against the 150 limit.
- **Issue:** CLAUDE.md/Segal Table 5's file-size gate is hard-enforced by the pre-commit hook; "split files, never compress code to fit" applies regardless of the plan's literal `files_modified` list (which named only `language_config.py`, not a new module).
- **Fix:** Moved `model`'s own key enum (renamed `ModelKey`, scoped to just the six model fields) and its validation function into `shared/language_model_config.py`; `language_config.py` calls `validate_model_group()`.
- **Files modified:** `src/pursuit/shared/language_config.py`, `src/pursuit/shared/language_model_config.py` (new)
- **Verification:** `bash scripts/check_line_limit.sh` passes both files (`language_config.py` back to well under 150; `language_model_config.py` new and under 150); all `language_config`/`language_model_config` tests pass.
- **Committed in:** `5d2881e` (Task 3 commit)

**4. [Rule 3 - Blocking] Two test files split at the same line-limit gate**
- **Found during:** Task 2 (`test_anthropic_provider.py` reached 143/150 before the 7-scenario error-mapping table was even added) and Task 3 (`test_language_config.py` reached 158/150 after adding model-group integration tests).
- **Issue:** Same hard gate as deviation 3, applied to test files (CLAUDE.md: "Test files obey the 150-line limit too"), following the exact `test_gatekeeper.py`/`test_gatekeeper_retry.py` precedent 04-03 already set.
- **Fix:** `test_anthropic_provider.py` keeps the shared fakes (`FakeClient`/`FakeMessage`/`SpyGatekeeper`/`make_provider`) and the non-error-mapping tests; `test_anthropic_provider_errors.py` (new) imports those fakes and holds the parametrized error-mapping suite. `test_language_config.py`'s pre-existing tests are untouched (only its stale `model == {}` assertion was corrected); the 4 new model-group *integration* tests moved to `test_language_config_model.py` (new), importing `_write_variant`/`POLICE_LANGUAGE`.
- **Files modified:** `tests/unit/services/test_anthropic_provider.py`, `tests/unit/services/test_anthropic_provider_errors.py` (new), `tests/unit/test_language_config.py`, `tests/unit/test_language_config_model.py` (new)
- **Verification:** `bash scripts/check_line_limit.sh` passes every file; full suite green.
- **Committed in:** `b6e4a6a` (Task 2), `5d2881e` (Task 3)

**5. [Rule 2 - Missing functionality] `tests/unit/test_language_model_config.py` added beyond the plan's `files_modified` list**
- **Found during:** Task 3, after creating `language_model_config.py` (deviation 3).
- **Issue:** CLAUDE.md's "every module gets a test file, happy path and error case" is a hard constraint, and the new module wasn't anticipated by 04-06-PLAN.md (which only listed the pre-existing `language_config.py`). 04-03's own SUMMARY set this exact precedent (`tests/unit/test_language_config.py` added beyond *its* file list) with the same justification.
- **Fix:** Added a dedicated unit-level test file for `validate_model_group()`/`ModelKey` (13 tests: every validation rule, both error and happy paths, plus the D-05 "no numeric literal on the enum" discipline check).
- **Files modified:** `tests/unit/test_language_model_config.py` (new)
- **Verification:** All 13 tests pass; `src/pursuit/shared/language_model_config.py` shows 100% coverage.
- **Committed in:** `5d2881e` (Task 3 commit)

---

**Total deviations:** 5, all Rule 2/3 (auto-added missing test coverage / auto-fixed blocking issues -- a real circular import and two hard line-limit violations). No architectural changes, no scope creep, no Rule 4 checkpoint needed. All five were necessary to satisfy either a hard CI gate or the plan's own literal verify criteria; none change the public `Provider`/`LlmResult`/`LlmFailure` contract 04-07/04-10 code against.

## Issues Encountered

- **A real (not stylistic) circular import**, discovered empirically rather than by inspection alone: `shared.language_config` (imported by `services.llm.gatekeeper`) needed to validate against `services.llm`'s provider registry, which transitively imports `services.llm.gatekeeper`. Resolved with a deferred import (deviation 2) after confirming the failure mode with a real `ImportError` and then confirming the fix with a full-suite green run plus a standalone `import pursuit.services.llm` smoke test.
- **SDK-shape verification against the installed package, not memory**: `anthropic` 0.121.0's `output_config={"format": {"type": "json_schema", "schema": ...}}`, the async `messages.create`/`count_tokens` signatures, the full `APIStatusError` subclass hierarchy, and `httpx.Response`/`Request` construction for building real exception instances in tests were all confirmed by reading the installed package's own type stubs and source (`.venv/lib/python3.11/site-packages/anthropic/`) before writing `anthropic_provider.py`, since a wrong assumption here would silently degrade every call to a template hint (D-33) with no test able to catch it against a live API.

## User Setup Required

**To exercise the `claude_api` path against the real API** (not required for any test, CI, or `/gsd:execute-phase` run -- everything in this plan works with the key unset, degrading to `NO_KEY`):

1. Obtain an Anthropic API key.
2. Set it in a local, gitignored `.env` (or the environment directly): `ANTHROPIC_API_KEY=sk-ant-...`.
3. Never commit it -- `.env` is gitignored (confirmed pre-existing in `.gitignore`); `.env-example` carries only the dummy placeholder.

No other external service configuration is required by this plan.

## Next Phase Readiness

- **04-07 (hint decoder)** and **04-10 (bluff generator)** import `Provider`/`LlmResult`/`LlmFailure`/`LlmFailureReason`/`AnthropicProvider`/`TemplateProvider`/`get_provider_class` from `pursuit.services.llm` (the package, not a submodule), construct the provider they need directly (see "Constructor asymmetry" above -- there is no generic `build_provider()`), call `.complete(system_prompt=..., user_prompt=..., schema=...)`, and treat any `LlmFailure` as D-33's "no evidence" / template fallback.
- **04-14 (GATE-4 measurement)** should assert on `AnthropicProvider.served_model` after a live run to catch a wrong `model_id` (which otherwise degrades silently to a template hint per D-33 and would make the whole phase look healthy on the fallback path alone) and can pull the *real* token cost from `gatekeeper.budget.report()` to replace this plan's local-heuristic estimate.
- **Phase 7 (Gmail reporting)** is unaffected by this plan; it continues to depend only on 04-03's `Gatekeeper`/`TokenBudget`, unchanged here.
- No blockers. `config/{police,thief}/language.json`'s `model` group is now fully populated and validated; both role files remain byte-identical (Rule 11).

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-08*

## Self-Check: PASSED

All 18 claimed files verified present on disk (`ls -la`): 7 source modules (5 in
`services/llm/`, 2 in `shared/`), 5 config/dependency files (`config/{police,thief}
/language.json`, `pyproject.toml`, `uv.lock`, `.env-example`), 6 test files, plus this
SUMMARY.md itself. All 3 claimed commit hashes verified present in `git log --oneline
--all` (`fec0a85`, `b6e4a6a`, `5d2881e`). No missing items.

Full-suite re-confirmation at self-check time: `uv run pytest tests/ --cov` -- 565
passed, 93.13% coverage (required 85%); `uv run ruff check .` -- 0 violations;
`bash scripts/check_line_limit.sh` (project-wide) -- 0 violations.
