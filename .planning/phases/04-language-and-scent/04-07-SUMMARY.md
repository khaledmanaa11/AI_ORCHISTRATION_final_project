---
phase: 04-language-and-scent
plan: "07"
subsystem: services-llm
tags: [hint-decoder, constrained-json, prompt-injection, hebrew, d-41, d-44, d-33, lang-06]

# Dependency graph
requires:
  - "04-06: Provider protocol / LlmResult / LlmFailure / LlmFailureReason (services/llm/provider.py)"
  - "04-06: TemplateProvider (services/llm/template_provider.py) -- the zero-token mode that cannot decode"
  - "04-04: DirectionWord, the five-word heading vocabulary (moved to shared/directions.py by this plan)"
provides:
  - "Inference + NO_EVIDENCE + no_evidence_for() (shared/inference.py) -- the decoder's output type, consumed by 04-09"
  - "Region + REGION_NAMES (shared/inference.py) -- the nine-sector claim vocabulary, also used by 04-08"
  - "DECODE_SCHEMA + validate() (services/llm/decode_schema.py) -- the json_schema sent, and the re-validator applied"
  - "build_system_prompt()/build_user_prompt() (services/llm/decode_prompt.py)"
  - "decode_hint(text, DecodeContext) -> Inference (services/llm/decode.py) -- total, never raises"
  - "DirectionWord / Origin / DEFAULT_ORIGIN / axis_signs (shared/directions.py) -- one heading vocabulary and one axis convention"
  - "tests/fixtures/hints_{en,he}.json -- (hint, recorded response, expected decode) triples, replayable live by 04-14"
affects: [04-09-belief-fusion, 04-10-bluff-generator, 04-12-turn-pipeline, 04-14-gate-4-measurement]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Re-export instead of re-declare when a type has to cross a forbidden layer edge: DirectionWord moved DOWN to shared/ and network/move_payload.py imports it, rather than a second copy appearing under strategy/ to dodge the STRAT-03 import gate. Satisfying a structural gate by duplication converts an import violation into a duplication violation."
    - "Schema on the request AND re-validation on the response. Constrained decoding is a request the API may not honour (unavailable, disabled, served by a fallback), so the only guarantee of our types is our own check; rejection is total and returns the neutral value, never a partial parse."
    - "Totality by construction at a hostile boundary: one entry point, every branch returning the same neutral type, plus a final try/except that converts an escaping exception into the SAME LlmFailure the well-behaved path returns -- so the function has exactly one failure branch rather than two."
    - "Asymmetric prompt delimiters (`<<<OPPONENT_HINT` opening, bare `OPPONENT_HINT` closing) so opponent text echoing the opening marker cannot forge a matching pair and close the quoted block early."

key-files:
  created:
    - src/pursuit/shared/inference.py
    - src/pursuit/shared/directions.py
    - src/pursuit/services/llm/decode_schema.py
    - src/pursuit/services/llm/decode_prompt.py
    - src/pursuit/services/llm/decode.py
    - tests/fixtures/hints_en.json
    - tests/fixtures/hints_he.json
    - tests/unit/test_inference.py
    - tests/unit/test_directions.py
    - tests/unit/services/test_decode_schema.py
    - tests/unit/services/test_decode_prompt.py
    - tests/unit/services/test_decode.py
  modified:
    - src/pursuit/network/move_payload.py
    - src/pursuit/services/llm/__init__.py

key-decisions:
  - "`confidence` is the DECODER's read-confidence, never a belief that the hint is TRUE. Truthfulness is 04-09's adaptive reliability coefficient (D-51), applied separately and multiplied in later. Conflating them would let a fluent lie carry full weight, which is exactly the attack a deceiving opponent runs."
  - "The word limit enters through DecodeContext as a required field rather than being read from language.json here. 04-07 owns no config file; the same Table 14 row 2 number governs the hints we EMIT, and 04-10 is the plan that adds it to language.json. A required field with no default means no call site can silently fall back to an invented ceiling. See Interface notes."
  - "An over-limit incoming hint is rejected locally with zero tokens spent. Rule 26 caps a hint at the negotiated word limit, so a 5000-word 'hint' is both a rule violation and a budget attack; the plan's own must_haves lists it among the no-evidence paths."
  - "An off-board cell in a response is a REJECTION, not a filter. It means the model was working from a board it invented, so the rest of its answer is not trustworthy either."
  - "The prompt tells the model to report a heading-only sentence at confidence 0. This reconciles a genuine tension inside the plan -- see Deviations item 1."

patterns-established:
  - "Fixture files carrying (input, recorded response, expected output) triples, so ONE file drives both the mocked unit tests now and a live-API accuracy replay later (04-14) without either consumer needing its own copy."

requirements-completed: [LANG-06, LANG-05]

# Metrics
duration: single session, 1 commit (797448a)
completed: 2026-08-08
---

# Phase 4 Plan 07: Hint Decoder Summary

**One opponent sentence becomes a schema-valid `Inference` or it becomes `NO_EVIDENCE`. There is no third outcome, for any input, from any provider, in either language.**

## Accomplishments

- **`shared/inference.py`** — frozen `Inference(region, cells, direction, confidence, raw_text)`, the `NO_EVIDENCE` singleton, `no_evidence_for(text)` (neutral but carrying the sentence, so 04-14 can tell *"we failed to read it"* from *"it said nothing"*), and the nine-sector `Region` vocabulary. The `[0, 1]` bound on `confidence` is enforced in `__post_init__`, so no code path anywhere can hold an out-of-range weight. `is_evidence` is the single predicate 04-09 should branch on.
- **`shared/directions.py`** (new, see Deviations) — `DirectionWord`, `DIRECTION_WORDS`, `Origin`, `DEFAULT_ORIGIN`, `axis_signs()`. One heading vocabulary and one axis-origin convention for the wire, the decoder and 04-08's planner.
- **`services/llm/decode_schema.py`** — `DECODE_SCHEMA` (sent as `output_config.format`'s `json_schema`) and `validate()`, which re-checks the response on our side. Rejects: a non-dict, any key set other than exactly the four, a non-numeric or out-of-range confidence, a region or direction outside the vocabulary, a malformed or off-board cell, and positive confidence while implicating nowhere.
- **`services/llm/decode_prompt.py`** — arena and board extent from config (never a literal), the full schema vocabulary, rule 25 stated in prose as well as in the architecture, D-44's both-languages-in/English-out instruction, and the untrusted-content framing with asymmetric delimiters.
- **`services/llm/decode.py`** — `decode_hint(text, DecodeContext)`. Local short-circuits before any token is spent (non-string, empty, over the word limit, template provider); then provider → `validate` → `Inference`. Every other path returns the neutral result, logged at debug with the reason.
- **Fixtures** — 7 English cases and 4 Hebrew, including a prompt-injection hint **and** the same attack assuming it succeeded (a confident inference about nowhere), which only our own re-validation catches.

## The `Inference` contract, verbatim (for 04-09 and 04-14)

```python
from pursuit.shared.inference import NO_EVIDENCE, Inference, Region, no_evidence_for
from pursuit.shared.directions import DirectionWord

@dataclass(frozen=True)
class Inference:
    region: Region | None = None            # the claimed sector
    cells: tuple[tuple[int, int], ...] = () # specific cells, usually empty
    direction: DirectionWord | None = None  # a claimed heading, if stated
    confidence: float = 0.0                 # OUR READ-confidence, in [0, 1]
    raw_text: str = ""                      # the sentence as received

    @property
    def is_evidence(self) -> bool:          # confidence > 0 AND (region or cells)
```

`Region`: `north, northeast, east, southeast, south, southwest, west, northwest, center`.
Turning a `Region` into cells is **`strategy/regions.py`** (created by 04-08) — `region_of`, `region_cells`, `region_center`, `region_distance`. 04-09 must use it rather than deriving a second sector grid.

```python
from pursuit.services.llm import DecodeContext, decode_hint

context = DecodeContext(provider=..., board_size=7, arena="New York", word_limit=15)
inference = await decode_hint(opponent_text, context)   # never raises
```

## Fixture file format

```json
{"language": "en", "note": "...", "cases": [
  {"id": "plain-region", "why": "...", "hint": "I am way over on the north side of the map.",
   "response": {"region": "north", "cells": [], "direction": null, "confidence": 0.85},
   "expect":   {"region": "north", "direction": null, "cells": [], "confidence": 0.85, "is_evidence": true}}
]}
```

`response` is what a mocked provider returns (used now). `expect` is what `decode_hint` must produce — and it is also the scoring target when **04-14** sends `hint` to the real API once and ignores `response`.

## Gates measured on the merged tree

| Check | Result |
|---|---|
| `uv run pytest tests/ --cov` | **750 passed, 93.94%** (floor 85) at this commit |
| `uv run ruff check .` | 0 violations |
| `bash scripts/check_line_limit.sh` | clean repo-wide |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| `grep "def decode_hint" -A200 decode.py \| grep -c "raise"` | **0** |
| Coverage of the six new modules | **100% each** |
| Network I/O in tests | none — every provider is a fake or `TemplateProvider` |

## Interface notes the next plans need

1. **`DecodeContext.word_limit` has no default.** 04-10 adds `hint_word_limit` to `language.json`'s `model` group (it owns the emission side of PARAMETERS.md Table 14 row 2); **04-12 must pass that value here**. Until then every call site supplies it explicitly, which is deliberate — a defaulted ceiling would be an invented number.
2. **A heading-only hint is carried, not counted.** `direction` is preserved with `confidence == 0`, so `is_evidence` is `False`. 04-09 can still use the heading with the motion model, but it must not treat it as a positional likelihood. See Deviations item 1 for why.
3. **The template provider decodes nothing, by design.** In the zero-token configuration the belief map runs on scent alone. That is a real capability difference between the two provider modes, not a bug, and 04-14 should report the two regimes separately.

## Deviations from Plan

### 1. [Resolved tension inside the plan] A heading-only hint decodes at confidence 0 rather than being rejected

- **Found during:** Task 1, writing `validate`'s rejection list against Task 4's fixture list.
- **Issue:** Task 1 says reject when *"both `region` and `cells` [are] absent while confidence is above zero"*. Taken literally with a positive confidence, that **discards the `direction` field entirely** for the one case where a heading is the only thing stated — so D-41's *"direction of motion if the hint states one"* would be unreachable, and Task 4's directional fixture would be meaningless.
- **Fix:** The rejection rule is implemented **exactly as written** (the `must_haves` framing — *"implicated cells or a named region ... and a direction of motion if the hint states one"* — makes locational content the thing confidence attaches to). The prompt then instructs the model to report a heading-only sentence with `confidence: 0`, which `validate` accepts, so the heading survives into the `Inference` with `is_evidence == False`. No information is lost and no plan rule is bent.
- **Consequence for 04-09:** a heading is available but is not positional evidence on its own. If 04-09 wants a heading to shift mass by itself, **that must be resolved in the plan first, not in the code** — the same posture 04-06 took on `count_tokens()`.
- **Verification:** `test_a_bare_heading_at_zero_confidence_is_accepted`, `test_confidence_about_nowhere_is_rejected`, and the `heading-only` fixture in both languages.

### 2. [Rule 3 — Blocking] `DirectionWord` moved to a new `shared/directions.py`; `network/move_payload.py` re-exports it

- **Found during:** Task 1, choosing the schema's `direction` vocabulary.
- **Issue:** The decoder's heading vocabulary and the wire's D-53 direction token are the same five words, and 04-08 needs them too. `DirectionWord` lived in `network/move_payload.py`, but `strategy/` may not import `pursuit.network` at all — `scripts/check_no_llm_in_strategy.py` fails CI on it (STRAT-03). Importing it into `shared/inference.py` would have made every `strategy/` consumer of `Inference` transitively pull `pursuit.network`, which satisfies the gate's letter while defeating its purpose; re-declaring the five words under `strategy/` would trade an import violation for a duplication violation (CLAUDE.md: extract at 2+ copies).
- **Fix:** The vocabulary moved **down** to `shared/directions.py`. `network/move_payload.py` imports it and every existing `from pursuit.network.move_payload import DirectionWord` call site still resolves. 04-08 later moved `Origin`/`DEFAULT_ORIGIN`/`axis_signs` for the same reason.
- **Files modified:** `src/pursuit/network/move_payload.py` (not in this plan's `files_modified`), `src/pursuit/shared/directions.py` (new).
- **Verification:** `tests/unit/test_directions.py::test_network_re_export_is_the_same_object` asserts the identity, so a future re-declaration fails loudly; `tests/unit/test_move_payload.py` (20 pre-existing tests) unchanged and green.

### 3. [Rule 2 — Missing functionality] Three test files beyond the plan's list

- **Issue:** CLAUDE.md requires a test file per module, happy path and error case. The plan named `test_decode.py` and `test_decode_schema.py` but the work created three further modules (`inference.py`, `directions.py`, `decode_prompt.py`). Same precedent as 04-03's and 04-06's own summaries.
- **Fix:** Added `tests/unit/test_inference.py` (13), `tests/unit/test_directions.py` (5), `tests/unit/services/test_decode_prompt.py` (13).
- **Verification:** all three modules at 100% coverage.

### 4. [Rule 3 — Blocking] `services/llm/__init__.py` extended

- **Issue:** 04-03's docstring establishes the package `__init__` as the public surface (*"import from here, not from the sibling modules directly"*), and 04-06 already extended it on the same reasoning; it is not in this plan's `files_modified`.
- **Fix:** Re-exports `decode_hint`, `DecodeContext` and `DECODE_SCHEMA`.

---

**Total deviations:** 4 — one resolved plan-internal tension (documented above, with the consequence handed to 04-09 rather than silently absorbed), two Rule-3 blocking structural fixes, one Rule-2 test-coverage addition. No architectural change and no scope creep; the public `Inference`/`decode_hint` contract is exactly what the plan specified.

## Issues Encountered

- **The `direction` tension (Deviation 1)** was the only real design problem, and it is a contradiction *inside the plan*, not between the plan and the book. It is recorded rather than smoothed over because a reader comparing 04-07-PLAN.md's Task 1 to the shipped `validate()` would otherwise think the rejection list had been quietly relaxed — it has not.
- **`json_schema` cannot carry numeric bounds.** `minimum`/`maximum` on `confidence` are rejected by the API, so the range check must live in `validate`. A comment in `decode_schema.py` and `test_schema_carries_no_unsupported_numeric_bound` both exist to stop a well-meaning "fix" that would fail every request and degrade every hint to no-evidence with nothing in the logs pointing at the schema.

## Next Phase Readiness

- **04-09** imports `Inference`/`Region`/`NO_EVIDENCE` from `pursuit.shared.inference` (never from `services/`) and `strategy/regions.py` for the sector-to-cells step. Read Interface note 2 before designing the hint likelihood.
- **04-10** shares `Region` and `DirectionWord` as the claim vocabulary, and should add `hint_word_limit` to `language.json` (Interface note 1).
- **04-14** replays `tests/fixtures/hints_{en,he}.json` against the live API for an accuracy figure, and should report the `claude_api` and `template` regimes separately.
- No blockers.

---
*Phase: 04-language-and-scent · Commit: `797448a`*
