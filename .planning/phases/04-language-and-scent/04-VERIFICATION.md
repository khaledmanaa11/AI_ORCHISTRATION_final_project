---
phase: 04-language-and-scent
verified: 2026-08-09T04:09:22Z
status: human_needed
score: 3/3 book success-criteria mechanisms verified (mocked); 1/1 robustness item verified; live-API confirmation is the sole open item
human_verification:
  - test: "Run GATE-4 measurement against the real Anthropic API"
    expected: >
      `ANTHROPIC_API_KEY=sk-ant-... uv run python scripts/measure_gate4.py --live` completes,
      writes a non-PENDING `docs/phases/phase-4/gate4_measurement_live.json`, and
      `scripts/gate4_runner.run_live`'s own liveness assertion passes: `response.model` names
      Haiku 4.5, provider call count > 0, token usage > 0. If that assertion fails the script
      marks `live.status = "VOID"` rather than reporting template numbers as live ones.
    why_human: >
      Requires a real ANTHROPIC_API_KEY, which is absent on this machine and cannot be
      fabricated or bypassed — CLAUDE.md rule 39-40 forbids committing one, and D-33's mocked
      fallback makes "the game finished" insufficient evidence the API was ever reached. This
      was flagged as the single open item in RESUME.md before this verification ran and is
      confirmed still open, not a newly discovered gap.
---

# Phase 4: Language and Scent Verification Report

**Phase Goal:** Free-text hints, pheromone emission and decay, LLM for hint decoding and
deception.
**Verified:** 2026-08-09T04:09:22Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (book §10.4 milestone gate, verbatim from ROADMAP.md)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | A hint is translated into an inference (belief map updates via Bayes from scent + hints) | ✓ VERIFIED (mocked) / ? PENDING (live) | `strategy/belief.py::BeliefMap.update`, `strategy/belief_hint.py::hint_likelihood` exist, are wired through `network/turn_language_io.py::decode_turn_hint` → `network/turn_language.py::choose_destination` into `network/turn_actions.py::take_my_turn` (grep-confirmed, not inferred from summaries). `scripts/measure_gate4.py --mocked` reproduced independently this session: 22/136 turns evidence, mean posterior L1 shift 1.171 on those turns, exact no-op on the other 114. Mechanism proven; **live decode accuracy against a real model is the pending half** (see human_verification). |
| 2 | The scent map updates (0.9/0.10/5×5) and decays each turn; decay model locked pre-game | ✓ VERIFIED | `config/police/scent.json` and `config/thief/scent.json` are byte-identical (`diff` confirms), kernel table matches Figure 4 exactly (`0.04/0.14/0.20/0.14/0.04 …` rows), decay law `max(0.0, retain * strength)` in `strategy/scent.py`. Handshake carries `SCENT_DIGEST` alongside `DIGEST` (`network/handshake_wire.py`, `network/handshake_evaluate.py`), compared via `secrets.compare_digest` (reused `compare_named_digest` in `network/config_hash.py`), distinct `SCENT_MISMATCH` outcome. Independently re-ran `--mocked`: max deviation from closed form 1.11e-16 over 12 turns, both peer digests match (`c0e6322…`). This criterion has no live-API dependency — it is not part of the pending item. |
| 3 | The LLM emits a ≤15-word hint each turn, true or false, `intent` committed in advance, comms natural-language-only | ✓ VERIFIED (mocked) / ? PENDING (live) | `services/llm/bluff.py::compose` enforces the D-45 three-layer limit (prompt + count + retry + truncate); `services/llm/wordcount.py` has `count`/`truncate`. `shared/deception_types.py::DeceptionPlan.__post_init__` structurally refuses `intent=lie` for `ALWAYS_TRUE_KINDS` (rules 15/16/21/22), and `network/turn_language_io.py::send_turn_hint` calls `build_deception_plan()` (fixes `plan.intent`) strictly before `compose_outgoing(plan, …)` — `plan` is a required positional argument, so no call path can produce text before an intent exists; `tests/integration/test_gate4.py` freezes this with a live call-order spy (re-ran: 3 passed). `shared/hint_guard.py::assert_no_coordinates` blocks digit-pair/row-column patterns on the send path, called from both `bluff.py` and the move-payload path. Re-ran `--mocked`: 68/68 turns carried a hint, max 11 words (limit 15), both intents occurred (13 truth / 55 lie), 0 coordinate leaks. **Live-API word-limit/intent behavior under a real model's output variance is the pending half.** |

**Score:** 3/3 mechanisms structurally and mocked-measurably verified; all three share the same one open item (live-API confirmation), which is a pre-flagged, documented, environment-caused gap — not a newly discovered defect.

### Required Artifacts (spot-checked against source, not SUMMARY claims — 14 plans, 04-01…04-14)

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/pursuit/strategy/scent.py` | Kernel + decay law, pure functions | ✓ VERIFIED | `emission()`, `decay()` (`max(0.0, …)`), `expected_strength_after()` all present; no I/O, no LLM import |
| `src/pursuit/shared/scent_config.py` | `load_scent_model`, `scent_digest` reusing `canonical_json` | ✓ VERIFIED | `scent_digest()` calls `hashlib.sha256(canonical_json(_as_payload(model))…)`; `ScentKey` lives here, not `config_keys.py` |
| `config/{police,thief}/scent.json` | Byte-identical locked payload | ✓ VERIFIED | `diff` reports identical; kernel matches Figure 4; worked example `0.9 → 0.81` present |
| `src/pursuit/network/handshake_wire.py` / `handshake_evaluate.py` | Scent digest rides handshake, `SCENT_MISMATCH` distinct, `compare_digest` | ✓ VERIFIED | `HandshakeKey.SCENT_DIGEST`, `HandshakeOutcome.SCENT_MISMATCH`, `_compare_offer` checks config then scent, `compare_named_digest` reuses `secrets.compare_digest` |
| `src/pursuit/services/llm/gatekeeper.py` / `bucket.py` / `budget.py` | Token bucket, FIFO overflow → typed exception (never crash), cumulative budget ladder | ✓ VERIFIED | `GatekeeperOverflow` exception, `TokenBucket` implements `tokens ← min(C, tokens + r·Δt)` exactly, `DegradeLevel` FULL→SHORT_PROMPT→TEMPLATE_ONLY, async throughout (`asyncio.Semaphore`, injected `asyncio.sleep`) |
| `src/pursuit/network/envelope.py` / `move_payload.py` / `tools.py` | `MessageType.HINT`, direction-token codec, `receive_hint` | ✓ VERIFIED | `HINT = "hint"` added to enum, `REQUIRED_KEYS` unchanged; direction tokens incl. `stay`; `receive_hint` tool decodes via `Envelope.from_dict` |
| `src/pursuit/strategy/belief.py` / `belief_scent.py` / `belief_motion.py` | `BeliefMap` core, D-42 inversion, legal-motion spread | ✓ VERIFIED | `observe_exact`, `predict`, `update`, `posterior`, `argmax`, `sample` all present; `belief_scent.py` imports `expected_strength_after` from `scent.py`; `belief_motion.py` imports `pursuit.sdk.actions`; neither file imports `services` or `network` |
| `src/pursuit/services/llm/provider.py` / `anthropic_provider.py` / `template_provider.py` | Provider registry, Haiku 4.5 via gatekeeper, zero-token fallback | ✓ VERIFIED | `LlmFailure`/`LlmFailureReason`, `register_provider`; `anthropic_provider.py` never calls SDK directly — routes through `self._gatekeeper.submit`; `served_model` recorded from `response.model`; `config/police/language.json` has `model_id: "claude-haiku-4-5"` (alias, not dated snapshot), `every_n_steps: 1` |
| `src/pursuit/shared/inference.py` / `services/llm/decode_schema.py` / `decode.py` | `NO_EVIDENCE`, constrained JSON schema, total `decode_hint` | ✓ VERIFIED | `NO_EVIDENCE = Inference()`; schema requires `region/cells/direction/confidence`; every `LlmFailure` branch returns `NO_EVIDENCE`, never raises |
| `src/pursuit/shared/deception_types.py` / `strategy/deception.py` / `deception_thief.py` / `deception_cop.py` | `DeceptionPlan`, structural lie-refusal on always-true kinds, danger-adaptive / herding policies | ✓ VERIFIED | `__post_init__` raises `ValueError` if `intent=LIE` and `kind in ALWAYS_TRUE_KINDS`; `deception_thief.py::lie_probability` scales monotonically with `expected_opponent_distance` |
| `src/pursuit/strategy/belief_hint.py` / `reliability.py` / `scent_check.py` | Uniform-mixed hint likelihood, bounded adaptive reliability, §4.4 contradiction test | ✓ VERIFIED | `hint_likelihood` mixes `r·q(c) + (1−r)·u(c)`, never zeroes a cell; `Reliability` clamps to `[r_min, r_max]`; `scent_check.contradicts` uses `expected_strength_after` |
| `src/pursuit/services/llm/wordcount.py` / `bluff.py` / `hintbank.py` | Word count/truncate, total `compose()`, template fallback bank | ✓ VERIFIED | `count`/`truncate` present; `compose()` calls `assert_no_coordinates`; `HintBank` keyed by `(ClaimKind, Intent, arena-flavour)` |
| `src/pursuit/strategy/beliefadapter.py` | `BeliefAdapter.decide` — sample not argmax, fills `Observation.target_cell` | ✓ VERIFIED | `sampled_cell = self.belief.sample(self.rng)`; `believed_state = replace(state, **{opponent_role: sampled_cell})`; `base.py`'s `target_cell` docstring names D-11/Phase-4 as the filler |
| `src/pursuit/services/language_turn.py`, `network/turn_language.py`, `turn_language_io.py` | One guarded language-turn entry point, Figure 7 order wired live | ✓ VERIFIED | `take_my_turn` in `turn_actions.py` calls `decode_turn_hint` → `choose_destination` → (move) → `send_turn_hint`, matching Figure 7's decode→belief→move→bluff order; `PLACEHOLDER_HINT_TEXT` no longer defined anywhere in `src/` (only referenced in a docstring explaining its removal) |
| `docs/PRD_scent_map.md`, `PRD_belief_map.md`, `PRD_deception.md`, `docs/phases/phase-4/{PRD,PLAN,TODO,RULES-RESOLUTION-LANG}.md` | Per-mechanism PRDs + phase triplet + rules-resolution writeup | ✓ VERIFIED | All six files exist, non-trivial size (7.5–17.5 KB); `PRD_belief_map.md` states the Regime-A honesty clause in plain words ("the belief map's value in Regime A is..."); `RULES-RESOLUTION-LANG.md` quotes both §5.3.2 and §6.4 with book+PDF page numbers, D-48/D-49/D-51 all covered |
| `docs/phases/phase-4/GATE-4-MEASUREMENT.md`, `scripts/measure_gate4.py` | Measured §10.4 criteria with numbers + method; reproducible seeded script | ✓ VERIFIED | Re-ran `--mocked` independently this session: results (22/136, 1.171 L1, 1.11e-16 decay deviation, 68/68 hints, max 11 words, both intents) matched the committed report exactly, only `generated_at` timestamp and wall-clock timing differed. Re-ran `--live`: correctly attempted zero network calls, wrote a `PENDING` (not `VOID`, not fabricated) status JSON |
| `.planning/graphs/GRAPH_REPORT.md` | Refreshed after phase-4 code landed (roadmap task 04-96) | ✓ VERIFIED | Built from commit `8d5e77f8`; `git log 8d5e77f..HEAD -- src/` shows zero further source changes, so the graph is current for the code as it stands |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `shared/scent_config.py` | `network/config_hash.py` | `scent_digest` reuses `canonical_json` (D-46) | ✓ WIRED | Confirmed by direct import and call in `scent_digest()` |
| `network/handshake.py`/`handshake_evaluate.py` | `shared/scent_config.py` | Handshake hashes the loaded `ScentModel` (rule 23) | ✓ WIRED | `_compare_offer` receives `local_scent_digest`, compares against `envelope.payload[SCENT_DIGEST]` |
| `services/llm/gatekeeper.py` | `services/llm/budget.py` | Gatekeeper consults degrade level before admitting a call (D-35) | ✓ WIRED | `DegradeLevel` imported and consulted in `gatekeeper.py`'s submit path |
| `network/tools.py` | `network/envelope.py` | `receive_hint` decodes via `Envelope.from_dict` (D-47) | ✓ WIRED | Confirmed in `tools.py::receive_hint` |
| `strategy/belief_scent.py` | `strategy/scent.py` | Inverts the same locked decay law the field emits with (D-42) | ✓ WIRED | `from pursuit.strategy.scent import expected_strength_after` |
| `strategy/belief_motion.py` | `sdk/actions.py` | Motion model spreads mass through the engine's legal action sets | ✓ WIRED | `from pursuit.sdk.actions import cop_actions, thief_actions` |
| `services/llm/anthropic_provider.py` | `services/llm/gatekeeper.py` | Provider submits through the single gatekeeper (D-34, QUAL-03) | ✓ WIRED | `await self._gatekeeper.submit(_call, estimated_tokens=estimate)` — no direct SDK call outside this |
| `services/llm/decode.py` | `services/llm/provider.py` | Decoder maps every `LlmFailure` onto `NO_EVIDENCE` | ✓ WIRED | Confirmed in `_complete`/decode_hint failure branches |
| `strategy/deception.py` | `strategy/belief.py` | Deception policy reads belief to choose a credible claim | ✓ WIRED | `from pursuit.strategy.belief import BeliefMap`, passed into `plan_thief_claim`/`plan_cop_claim` |
| `strategy/reliability.py` | `strategy/scent_check.py` | Reliability lowered by scent-contradiction signal (D-51) | ✓ WIRED | Both modules exist and `contradicts()` supplies the signal reliability consumes (per source and tests) |
| `services/llm/bluff.py` | `network/envelope.py` (via `shared/hint_guard.py`) | Composed hint validated by `assert_no_coordinates` before send | ✓ WIRED | `bluff.py` imports and calls `assert_no_coordinates`; `network/hint_payload.py` re-exports the same function for the move-payload path |
| `strategy/beliefadapter.py` | `strategy/base.py` | Adapter fills `Observation.target_cell` from a belief sample (D-43) | ✓ WIRED | `target_cell=sampled_cell` in `beliefadapter.py::decide`; `base.py` docstring names this seam |
| `network/turn_actions.py` | `services/language_turn.py` / `network/turn_language*.py` | Turn loop runs the language half through one guarded entry point, replacing 04-04's placeholder | ✓ WIRED | `take_my_turn` imports and calls `decode_turn_hint`, `choose_destination`, `send_turn_hint` in Figure-7 order; `PLACEHOLDER_HINT_TEXT` confirmed absent as a live constant |
| `docs/phases/phase-4/GATE-4-MEASUREMENT.md` | `.planning/ROADMAP.md` | Measurement answers the §10.4 criteria quoted verbatim | ✓ WIRED | Document quotes ROADMAP.md's own success-criteria text and maps a number to each |

### Requirements Coverage (LANG-01…07, per outline §7 mapping)

| Requirement | Status | Evidence |
|---|---|---|
| LANG-01 (≤15-word hint every turn) | ✓ SATISFIED (mocked) / pending live confirmation | `bluff.py::compose` three-layer limit; measured 68/68 turns, max 11 words |
| LANG-02 (natural language only, no coordinates) | ✓ SATISFIED | `assert_no_coordinates` on send path; direction-token move codec (no `{x,y}` outgoing); measured 0 coordinate leaks |
| LANG-03 (hints may lie; intent committed in advance) | ✓ SATISFIED | `DeceptionPlan` built before `compose_outgoing`; structural refusal for always-true kinds; call-order spy test passes |
| LANG-04 (scent 0.9/0.10/5×5) | ✓ SATISFIED | `scent.json` matches Table 16 exactly, byte-identical both roles |
| LANG-05 (Bayesian belief map from scent + hints) | ✓ SATISFIED | `BeliefMap.update`, `belief_scent.py`, `belief_hint.py` all present and wired into the live turn loop |
| LANG-06 (LLM decodes hints and writes bluffs) | ✓ SATISFIED (mocked) / pending live confirmation | `decode_hint`, `compose` both exist, are total, and are exercised by fixtures; **real-model behavior unmeasured** |
| LANG-07 (decay model cryptographically locked pre-game) | ✓ SATISFIED | Scent digest exchanged at handshake, `secrets.compare_digest`, mismatch aborts to `State.ERROR` |

**Note:** ROADMAP.md and `docs/TODO.md`/`docs/phases/phase-4/TODO.md` correctly show LANG-01…07 and every phase-4 task row still unticked — this is expected and correct per this project's convention (`/gsd:verify-work 4` owns ticking, and RESUME.md/04-13-PLAN.md/04-14-PLAN.md all explicitly forbid ticking before the live run lands). This verification does not tick anything.

### Anti-Patterns Found

None. Scanned every plan's primary artifact file (`scent.py`, `scentfield.py`, `belief.py`, `belief_hint.py`, `deception.py`, `beliefadapter.py`, all of `services/llm/*.py`, `network/turn_language*.py`, `move_payload.py`, `envelope.py`) for `TODO|FIXME|XXX|HACK` and placeholder-return patterns — zero hits. `PLACEHOLDER_HINT_TEXT` (04-04's known interim stub) is confirmed removed as a live constant; it survives only in two docstrings that explain its own removal.

### Standing Gates — re-run directly, not taken from SUMMARY claims

| Check | Result |
|---|---|
| `uv run ruff check .` | 0 violations |
| `bash scripts/check_line_limit.sh` | clean (no output, exit 0) |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports under .../src/pursuit/strategy` |
| `uv run pytest --cov` | **1051 passed**, coverage **95.21%** (floor 85%) — matches RESUME.md exactly |
| `uv run python scripts/measure_gate4.py --mocked` (re-run independently) | All three criteria PASS; numbers matched the committed `GATE-4-MEASUREMENT.md` exactly (only timestamp/wall-clock timing differed) |
| `uv run python scripts/measure_gate4.py --live` (re-run independently, no key) | Attempted zero network calls, wrote a clean `PENDING` status — confirms the documented pending state is real, not stale |
| `uv run pytest tests/integration/test_gate4.py` | 3 passed (structural absolutes, incl. intent-before-text call-order spy) |
| `git status` after re-runs | Clean — reverted the one incidental timestamp-only diff my own `--mocked` re-run produced in `gate4_measurement_mocked.json` |

### Human Verification Required

#### 1. Live GATE-4 confirmation against the real Anthropic API

**Test:** `ANTHROPIC_API_KEY=sk-ant-... uv run python scripts/measure_gate4.py --live`

**Expected:** The run completes and `docs/phases/phase-4/GATE-4-MEASUREMENT.md`'s Live status
section moves from `PENDING` to real numbers: `response.model` names Haiku 4.5 (liveness
proof — a wrong key/model/rate-limit must show as `VOID`, not silently pass on template
numbers), non-zero provider calls, non-zero token usage, real per-turn latency against the
60s watchdog, real token spend in tokens and USD, and real EN/HE decode accuracy against the
04-07 fixtures (scored against `expect`, ignoring each fixture's own canned `response`).

**Why human:** `ANTHROPIC_API_KEY` is not set on this machine (confirmed: `echo
$ANTHROPIC_API_KEY` empty, `env | grep -i anthropic` shows only `ANTHROPIC_BASE_URL`). This is
not a machine-checkable gap — no amount of code inspection substitutes for actually reaching
the model, and the codebase is deliberately built so a missing key produces a passing game on
the template fallback (D-33), which is why `run_live`'s own liveness assertion exists. This
was flagged as the single open item in `.planning/phases/04-language-and-scent/RESUME.md`
*before* this verification ran; this verification reconfirms it is still the only gap, not a
newly discovered one, and reconfirms the mocked/pending split is honestly reported rather than
smoothed over.

### Gaps Summary

No machine-checkable gaps found. All 14 execution plans' must_haves (truths, artifacts, key
links) were checked directly against source — not inferred from SUMMARY.md prose — and all
verified present, substantive, and wired into the live turn loop
(`network/turn_actions.py::take_my_turn` genuinely calls the language pipeline; this is not a
side module built and left unconnected). All five standing gates (ruff, line limit, rule-25
import guard, pytest coverage, GATE-4 mocked measurement) were re-run independently in this
session and matched the committed numbers exactly. The one item this report defers to a human
is the live-API GATE-4 run, which requires a real `ANTHROPIC_API_KEY` absent from this
environment — a pre-existing, explicitly documented, and correctly-reported environmental
constraint (RESUME.md, GATE-4-MEASUREMENT.md's own Live status section) rather than a gap this
verification discovered. Two items from RESUME.md's carry-over log are worth restating here
because they bound what "verified" means for this phase, without being gaps this phase needs
to close:

- **Finding BB (belief-off fallback confound).** `turn_language.py::choose_destination`'s
  `belief.enabled = false` path feeds the raw brain the true, un-blinded opponent cell rather
  than a blind mover — pre-dating D-48/D-43 and never updated. This makes the measured
  belief-on-vs-off comparison (1.0 vs 0.0 cop win rate) not attributable to the belief layer's
  own contribution. `GATE-4-MEASUREMENT.md` states this honestly rather than smoothing it over,
  and it is explicitly out of scope for this phase to fix (measurement-only plan, no strategy
  changes). Recorded here so it is not mistaken for something this verification missed.
- **Finding Z / AA** — the event log has no per-turn scent-grid snapshot (only entropy/argmax/
  reliability); a future replay-viewer plan (Phase 7) will need to add that field. Not a gap in
  Phase 4's own success criteria, which do not require per-turn scent replay.

---

_Verified: 2026-08-09T04:09:22Z_
_Verifier: Claude (gsd-verifier)_
