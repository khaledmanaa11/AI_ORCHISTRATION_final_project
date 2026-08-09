# Phase 4 PLAN — Language and Scent

**Version:** 1.00 · **Updated:** 2026-08-09

> Phase-scoped architecture. Inherits the project [PLAN.md](../../PLAN.md); this document
> captures only the design specific to this phase. Full component-by-plan mapping:
> [`.planning/phases/04-language-and-scent/04-PLAN-OUTLINE.md`](../../../.planning/phases/04-language-and-scent/04-PLAN-OUTLINE.md)
> §4 ("Where the code goes"). This file summarises; the outline is the authoritative source for
> exact file-to-plan ownership.

## Components & files

```
src/pursuit/strategy/          <- ALGORITHM. no LLM import, ever (CI-enforced)
  scent.py / scentfield.py     kernel + decay law, per-agent field       (04-01)
  belief.py                    grid, predict/update/observe/sample       (04-05)
  belief_motion.py             legal-action motion model (shared)        (04-05)
  belief_scent.py               scent likelihood, D-42                    (04-05)
  belief_hint.py                hint likelihood, D-40                     (04-09)
  reliability.py                adaptive trust coefficient, D-51          (04-09)
  scent_check.py                Sec4.4 lie-detector reproduction          (04-09)
  deception.py / _thief.py / _cop.py   intent + claim, D-36/37/38         (04-08)
  regions.py                    Region <-> cells, shared translation      (04-08)
  beliefadapter.py               sample -> believed-state substitution    (04-11)

src/pursuit/services/llm/      <- LANGUAGE ONLY. never returns a move
  gatekeeper.py / bucket.py / budget.py   Table 19 law, D-35 ladder       (04-03)
  provider.py / template_provider.py / anthropic_provider.py / client.py (04-06)
  decode.py / decode_schema.py / decode_prompt.py                        (04-07)
  bluff.py / bluff_prompt.py / hintbank.py / wordcount.py                 (04-10)

src/pursuit/services/
  language_turn.py              the ONE timeout-guarded language-turn entry point (04-12)

src/pursuit/network/           <- TRANSPORT
  envelope.py                   + MessageType.HINT                        (04-04)
  move_payload.py / hint_payload.py   direction-token codec, hint shape   (04-04)
  turn_buffer.py / turn_resolve.py / turn_language.py / turn_language_io.py
                                 the turn-pipeline split (04-04, 04-12)
  handshake_wire.py / handshake_evaluate.py   + scent digest key          (04-02)
  language_wiring.py / brain_wiring.py   LanguageRuntime, brain+scent construction (04-12)

src/pursuit/shared/
  scent_config.py / scent_kernel.py   locked payload + validation          (04-01)
  language_config.py / language_model_config.py   Table 19/18 config       (04-03/06)
  belief_config.py / reliability_config.py / hint_likelihood_config.py / belief_toggle_config.py
                                       belief.json's four groups            (04-05/09/11)
  deception_config.py                 deception.json                       (04-08)
  deception_types.py / directions.py / inference.py / hint_guard.py
                                       cross-layer shared types             (04-07/08/10)
```

## Interfaces & contracts

New/changed contracts this phase introduces (full signatures in each mechanism's own PRD):

- **`ScentField.emit_own/emit_opponent/advance/strength/freshest`** — [`docs/PRD_scent_map.md`](../../PRD_scent_map.md) §5.
- **`BeliefMap.observe_exact/predict/update/posterior/sample`**, **`scent_likelihood()`**,
  **`hint_likelihood()`**, **`Reliability.observe()`**, **`scent_check.contradicts()`**,
  **`BeliefAdapter.decide(state, inference, opponent_field, rules, *, known_cell=None)`** —
  [`docs/PRD_belief_map.md`](../../PRD_belief_map.md) §2–§7.
- **`DeceptionPlan`, `declare_truthfully(kind)`, `plan_deception(...)`, `compose(plan, context)`**
  — [`docs/PRD_deception.md`](../../PRD_deception.md) §2, §6.
- **`Provider.complete(system_prompt, user_prompt, schema=None) -> LlmResult | LlmFailure`** —
  never raises (D-33); registered by name (`template`, `claude_api`).
- **`Gatekeeper.submit(fn, *, estimated_tokens)`** — the one door every external call passes
  through; `GatekeeperOverflow` on a full queue, budget `DegradeLevel` never hard-stops (D-35).
- **`MessageType.HINT`** on the existing four-key `Envelope`, carrying `{text, intent, turn}` —
  no new envelope shape (D-47).
- **Direction-token move/barrier codec** (`move_payload.encode/decode`) — replaces the Phase-2
  `{x,y}` coordinate wire shape outbound; a legacy coordinate payload is still decoded on receipt
  for interop (D-53).
- **`HandshakeKey.SCENT_DIGEST`** — a second digest carried in the existing Phase-2 handshake
  offer, verified with `secrets.compare_digest`, aborting with a distinct `SCENT_MISMATCH`.

## Phase ADRs

D-32 … D-53 are the full decision record for this phase, transcribed from `04-CONTEXT.md` (D-32
…D-47) and resolved from the book this session (D-48…D-53). They are recorded **by reference**,
not copied here, to keep one authoritative source:
[`04-PLAN-OUTLINE.md`](../../../.planning/phases/04-language-and-scent/04-PLAN-OUTLINE.md) §2.
The two decisions with the widest blast radius, both requiring a dedicated write-up because they
touch the book's own apparent contradiction or a prior locked decision, are expanded in
[`RULES-RESOLUTION-LANG.md`](RULES-RESOLUTION-LANG.md) (D-48, D-49) and
[`docs/PRD_belief_map.md`](../../PRD_belief_map.md) §5 (D-51, a disclosed revision of D-40).

| # | Decision | Rationale (full argument, linked) |
|---|---|---|
| P4-1 | Per-turn Reveal kept, expressed as a direction token; belief map is the one-turn-ahead predictive distribution (D-48) | [`RULES-RESOLUTION-LANG.md`](RULES-RESOLUTION-LANG.md) §D-48 |
| P4-2 | Scent derived locally, never transmitted (D-49) | [`RULES-RESOLUTION-LANG.md`](RULES-RESOLUTION-LANG.md) §D-49 |
| P4-3 | Hint reliability becomes adaptive, disclosed as a revision of D-40, not an extension (D-51) | [`docs/PRD_belief_map.md`](../../PRD_belief_map.md) §5 |
| P4-4 | Sample from the belief, never `argmax` (D-43) | [`docs/PRD_belief_map.md`](../../PRD_belief_map.md) §7 |
| P4-5 | Believed-state substitution, Option A over Option B (cost-bounded) | [`docs/PRD_belief_map.md`](../../PRD_belief_map.md) §7 |
| P4-6 | Provider abstraction: two shipped (`template`, `claude_api`), two documented extension points (D-52) | 04-06-SUMMARY.md |

## Test plan (TDD)

- **Unit:** one test file per new module across `strategy/`, `services/llm/`, `network/`,
  `shared/` — every plan's own SUMMARY lists its test files; 1048 tests total on the merged
  tree, 95.21% coverage.
- **Integration:** `tests/integration/two_peer_game.py` — the reusable two-real-peer harness (in-
  memory cross-wired `Client(server)`, one real handshake, both `run_turn_loop`s via
  `asyncio.gather`) that found the phase's one real concurrency bug (late/duplicate hint racing
  against independent round-trips). `test_language_pipeline.py`, `test_llm_degradation.py` (four
  full degradation games), `test_language_timing.py`, `test_belief_policy.py` all build on it.
- **The §10.4 gate demo:** 04-14, against the live Anthropic API — not yet run (see
  [`PRD.md`](PRD.md) §2/§8).
- **Coverage target:** ≥85% (`fail_under=85`) — measured 95.21% on the merged tree.

## Per-mechanism PRDs written this phase

- [`docs/PRD_scent_map.md`](../../PRD_scent_map.md)
- [`docs/PRD_belief_map.md`](../../PRD_belief_map.md)
- [`docs/PRD_deception.md`](../../PRD_deception.md)
