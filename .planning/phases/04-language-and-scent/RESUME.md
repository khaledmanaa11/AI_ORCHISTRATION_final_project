# Phase 4 — resume point

**Updated:** 2026-08-09 · **Status:** waves 1–6 EXECUTED (12/14 plans: 04-01..04-12). Wave 6 is
now COMPLETE (04-12). Waves 7–8 not started.

Nothing is half-finished: every dispatched plan completed, merged, and passed the gates.

## Where things stand

All work is on branch **`claude/gsd-parallelism-config-6b4aqp`**, pushed. Get it with:

```
git fetch origin claude/gsd-parallelism-config-6b4aqp
git checkout claude/gsd-parallelism-config-6b4aqp
```

| Wave | Plan | Delivered | Summary |
|---|---|---|---|
| 1 | 04-01 | Locked scent model — Table 16 values + Figure-4 kernel, byte-identical `scent.json` both sides, digest `c0e6322…`; `ScentField` with independent own/opponent trails (D-49) | ✅ |
| 1 | 04-03 | API gatekeeper — Table 19 token bucket, D-35 budget ladder, FIFO queue that **queues on overflow rather than crashing** | ✅ |
| 1 | 04-04 | Language channel — direction-token move/barrier codec (coordinates off the wire), `MessageType.HINT`, atomic move+hint buffering | ✅ |
| 2 | 04-02 | Scent digest carried in the handshake — `SCENT_MISMATCH` distinct from `CONFIG_MISMATCH`, compared via `secrets.compare_digest` | ✅ |
| 2 | 04-05 | Belief map — legal-motion model, `BeliefMap` invariants, scent likelihood inverting the locked decay law (D-42) | ✅ |
| 2 | 04-06 | Provider layer — `Provider` protocol + registry, zero-token `TemplateProvider`, Haiku 4.5 provider routed through the gatekeeper; no key ⇒ degrades to `NO_KEY` | ✅ |

| 3 | 04-07 | Hint decoder — constrained JSON plus our own re-validation, EN **and** HE fixtures, a prompt-injection case, every failure path ⇒ `NO_EVIDENCE`, never raises | ✅ |
| 3 | 04-08 | Deception planner — a `DeceptionPlan` whose constructor refuses a lying capture/barrier claim, thief danger-adaptive lying with a measured truth floor, cop herding scored with the Phase-3 evaluation | ✅ |
| 4 | 04-09 | Belief fusion — `scent_check.contradicts()` (Sec4.4 lie detector, reproduces 0.9→0.81 exactly), `reliability.Reliability` (bounded adaptive coefficient, D-51), `belief_hint.hint_likelihood()` (D-40 mix, weighted below scent, never zeroes a cell) | ✅ |
| 4 | 04-10 | Bluff generator — `compose()`, the three-layer word limit (D-45): one call, one retry on overflow, truncate, `assert_no_coordinates`, total fallback to a seeded `HintBank` on every failure path; `bluff_prompt.py`'s style guide (D-39) never reveals `intent` to the model (D-36) | ✅ |
| 5 | 04-11 | `BeliefAdapter` — Figure-7 per-turn order (observe→predict→update(scent)→update(hint)→sample), Option A believed-state substitution (D-43 samples, never argmax), `registry.build_brain()` wired behind a `belief.enabled` config flag with a seeded RNG | ✅ |
| 6 | 04-12 | Turn-pipeline integration — Figure 7 wired live into `take_my_turn`/`await_opponent_turn`, `agent_lifecycle.default_context` now builds a REAL brain+ScentField+LanguageRuntime (first plan to wire Phase 3/4 into the live network loop), `PLACEHOLDER_HINT_TEXT` gone, four degradation games, a real two-peer concurrency bug found and fixed (late/duplicate hint no longer ends the game) | ✅ |

Gates on the merged tree after wave 6 (04-12) — measured, not inherited from agent self-reports:

| Check | Result |
|---|---|
| `uv run pytest --cov` | **1048 passed, 95.21%** (floor 85%) |
| `uv run ruff check .` | 0 violations |
| `scripts/check_line_limit.sh` | clean repo-wide |
| `scripts/check_no_llm_in_strategy.py` | clean — `strategy/` imports no `pursuit.services` |
| End-to-end Sec4.4 reproduction | fully-lying opponent's reliability 0.5→0.2→0.05 within 2 turns; fully-truthful holds at 0.5 for 10 turns; fused-posterior argmax follows scent in both regimes (`tests/unit/strategy/test_belief_fusion_e2e.py`) |
| `grep -nE "\b15\b" src/pursuit/services/llm/` | no match — the word limit is config-only everywhere |
| `compose()` adversarial property test | 300 iterations, always non-empty/in-limit/coordinate-free, never raises (`tests/unit/services/test_bluff_property.py`) |
| `git diff --stat` on `valuebrain.py`/`matrix.py`/`features.py`/`equilibrium.py` | empty across all three 04-11 commits — Phase 3's mover genuinely untouched |
| Belief-enabled per-turn decision time | cop max 4.99ms, thief max ~3.7–4.99ms, against a 50ms `strategy.max_decision_ms` budget (`tests/integration/test_belief_policy.py`) |
| Per-turn wall time, language ON/OFF | ~37ms/turn ON, ~18ms/turn OFF, against `network.watchdog_threshold=60s` (`tests/integration/test_language_timing.py`) |
| Four degradation games (no key, all calls fail, budget exhausted, silent peer) | all finish with a correctly-scored, agreeing outcome (`tests/integration/test_llm_degradation.py`) |
| `grep -rn "PLACEHOLDER_HINT_TEXT\s*=" src/` | no match — 04-04's placeholder is gone |

Remaining waves: `w7: 13` · `w8: 14`.

## The next command

```
/gsd:execute-phase 4 --wave 7
```

This starts wave 7 at 04-13 (docs + `RULES-RESOLUTION-LANG.md` + phase triplet) — wave 6 (04-12)
is fully done. Drop the `--wave` flag to run waves 7–8 straight through. Run it on a fresh context.

**If you are resuming in a Claude-Code-on-the-web container, the slash command will not
resolve** — the GSD plugin is not installed there (`.claude/` holds only `settings.json`, there
is no `.claude/commands/gsd/`). Wave 3 was executed by reading `04-07-PLAN.md` and
`04-08-PLAN.md` and following them task by task, running every check in each plan's
`<verification>` block and quoting the results in its SUMMARY. That works; a local run with the
real GSD install is still the intended path.

**`parallelization` is now `true`** in `.planning/config.json` (it was `false`, which was a
scaffold default, not a decision). Plans within a wave now execute concurrently. GSD's own
default for this key is `true`, and `execute-phase` still drops a wave back to sequential by
itself if it detects two plans in it touching the same file.

## Carry-overs from execution — read before continuing wave 7 (04-13) and beyond

**Every wave-3/4/5 carry-over addressed TO 04-12 by name is now DISCHARGED (04-12-SUMMARY.md has
the full accounting); each is marked below in place rather than deleted, so the calling-convention
detail stays discoverable. New in wave 6 (04-12), for 04-13/04-14:**

- **U. `known_cell`/D-48's regime is computed ONCE per `take_my_turn` call, in
  `network/turn_language.known_opponent_cell(ctx, agent)`, BEFORE `record_action`/`maybe_resolve`
  run** — those mutate the exact state the regime check reads, so a caller that recomputes it
  afterward can silently answer a different question than the one the move was chosen under. The
  computed value is logged verbatim as `"regime": "A"|"B"` in the new `turn_events.language_turn_record`
  JSONL line, once per turn, on both sides.
- **V. A real two-peer CONCURRENT game (never run before this plan — every prior phase-4 test
  either called direct engine functions or drove one real `run_turn_loop` against injected
  envelopes) found a genuine bug: 04-04's own "late hint"/"duplicate hint" `HintProtocolError`
  checks fire on ordinary jitter once the move and the hint are independent, variable-latency
  round-trips.** Fixed in `turn_buffer.record_hint`: a late hint (turn < `ctx.state.turn`) is
  silently dropped; a second hint from the same sender before resolution overwrites rather than
  raising. **04-13 should record this in `RULES-RESOLUTION-LANG.md` or the phase PRD as a concrete
  "why the real two-peer harness matters" example** — it is exactly the class of defect a
  single-sided or engine-only test cannot surface.
- **W. `tests/integration/two_peer_game.py::play_two_peer_game(cfg_a, cfg_b, *, game_uid,
  log_dir, wire=None)` is the reusable two-real-peer harness** (`agent_lifecycle.default_context`
  both sides, in-memory `Client(server)` cross-wiring, one real handshake, then both
  `run_turn_loop`s via `asyncio.gather`). `wire`, when supplied, runs once per built context
  before the handshake — the seam `test_llm_degradation.py` uses to swap providers, pre-load the
  token budget, or blank out `ctx.language` entirely. **04-14 should reuse this rather than
  hand-rolling a second two-peer runner** for the GATE-4 measurement game.
- **X. `local_scent_digest` is now passed for real on the LIVE path** (`agent_lifecycle.default_context`'s
  responder AND `run_agent`'s outbound `perform_handshake` call, both via `scent_digest(cfg.scent)`)
  — closing the "04-12 should pass a real digest" half of the still-open item 1 below. The
  "consider making it required" half was deliberately NOT taken: `test_handshake_abort.py`/
  `test_handshake_client.py` still build offers with no digest at all, and requiring it there is
  out of 04-12's scope.
- **Y. Hint-sending is now CONDITIONAL on `ctx.language is not None`** (a deliberate change from
  04-04's unconditional placeholder). Every REAL game (`agent_lifecycle.default_context`) always
  wires `ctx.language`, so LANG-01 holds for actual play (measured in
  `tests/integration/test_language_pipeline.py`/`test_llm_degradation.py`); a bare
  `tests/unit/_fakes_agent.make_ctx()` fixture that never opts in sends the move only. **If a
  later plan needs a fixture to exercise the language channel without full `default_context`
  wiring, build a `LanguageRuntime` via `network.language_wiring.build_language_runtime()`
  directly rather than reviving a placeholder constant.**

**New in wave 5 (04-11) — DISCHARGED by 04-12; they document the ACTUAL calling
conventions `beliefadapter.py`/`registry.py` shipped, some of which differ from the plan's own
literal prose (04-11-SUMMARY.md's `key-decisions` has the full reasoning for each):**

- **O. `BeliefAdapter(brain, role, game_params, belief_config, scent_model, rng)` —
  positional, in that order.** `role` is OUR OWN seat ("cop"/"thief"), not the opponent's;
  the adapter derives `opponent_role` internally. `rng` must be a `random.Random` the caller
  seeded (never module-level `random`, never `secrets`) — `registry.build_brain(...,
  belief_config=, scent_model=)` builds this seed via `_resolve_belief_seed(belief_config
  .belief.seed)`, which derives and LOGS a fallback when the config's `seed` is `null`.
- **P. DISCHARGED (04-12, see carry-over U above). `adapter.decide(state, inference,
  opponent_field, rules, *, known_cell=None)` — `known_cell` is REQUIRED reasoning, not optional
  decoration.** It is the one thing 04-12
  must supply correctly every turn: the opponent's pre-turn cell when THIS turn's Reveal was
  integrable (Regime A), or `None` when it was not (Regime B — `observe_exact` is skipped
  entirely and the belief runs on prediction + scent + hint alone). It cannot be derived from
  `state` itself — `state.cop`/`state.thief` keep carrying the engine's TRUE joint position
  regardless of regime (the engine needs it for `resolve_turn` either way), so "was the reveal
  usable this turn" is a fact 04-12's transport layer has to hand in explicitly. **`rules` is
  accepted by `decide()` but NOT read inside it** — the wrapped `ValueSearchBrain` already
  carries its own negotiated `ResolutionRules` from construction; do not expect changing the
  `rules` argument to change behaviour without also reconstructing the wrapped brain.
- **Q. DISCHARGED (04-12: `network/turn_language.observe_reliability(ctx, inference)` calls
  `scent_check.contradicts(...)` then `ctx.brain.reliability.observe(score)`, in that order,
  whenever a hint TEXT arrived this turn). `BeliefAdapter` owns `Reliability`, NOT 04-12 —
  closing 04-09's carry-over F with a different owner than that carry-over proposed.** `self.reliability` (and `self.belief`) are
  constructed fresh inside `BeliefAdapter.__init__`, exposed as public attributes. 04-12's job
  is narrower than carry-over F said: call `scent_check.contradicts(inference, opponent_field,
  model, belief_config)` then `adapter.reliability.observe(score)` — on the adapter's OWN
  instance — once per turn a hint arrives, in that order. Do NOT construct a second, separate
  `Reliability` for the same opponent; there is exactly one, and `BeliefAdapter` already built
  it. The "handshake time" moment carry-over F meant IS the moment 04-12 constructs the
  `BeliefAdapter` itself (via `registry.build_brain`).
- **R. `registry.build_brain(role, params, game_params, *, belief_config=None,
  scent_model=None)` — SAME function as before, two new OPTIONAL keyword args, not a second
  `build_brain_with_belief()`.** Supplying both, with `belief_config.belief.enabled`, returns a
  `BeliefAdapter`-wrapped brain; omitting either (or `enabled=false`) returns the identical raw
  `BrainBase` Phase 3 shipped. `build_brain`'s return type is therefore `BrainBase |
  BeliefAdapter` in practice — a caller that needs to know which it got should
  `isinstance(brain, BeliefAdapter)`, exactly as `tests/integration/test_belief_policy.py`'s own
  `decide()` dispatch helper does.
- **S. DISCHARGED (04-12: `network/turn_resolve.maybe_resolve()` calls `ctx.scent_field.advance()`
  exactly once, centrally, whenever a joint turn actually resolves — regardless of which side's
  call fills the second slot). One `ScentField` per ROLE (not per game, not per adapter) is
  04-12's to own and hold for the game's duration**, matching the `Reliability`/`HintBank` ownership pattern 04-09/04-10
  already established. `BeliefAdapter.decide()` MUTATES the field it is given every call
  (`emit_own`/`emit_opponent`) but never calls `.advance()` — decay is a POST-resolution,
  once-per-joint-turn operation (`ScentField.advance()`'s own docstring), and `decide()` runs
  BEFORE the turn resolves. **04-12 must call `field.advance()` exactly once per joint turn,
  after `resolve_turn`, on both the cop's-view and thief's-view fields** — forgetting this
  turns the trail into a monotonically growing, never-decaying pile.
- **T. The believed-state substitution is NOT what gets sent to the opponent or logged as the
  "real" move context.** `BeliefAdapter.decide()` returns a plain `Decision` (move/source/
  barrier) — identical in shape to what a raw `BrainBase` returns. 04-12's turn pipeline can
  treat a `BeliefAdapter`-wrapped brain and a raw one interchangeably from the OUTSIDE; only the
  call site differs (`.decide(state, inference, opponent_field, rules, known_cell=...)` vs.
  `._decide_move(observe(state, role), state)`), never the returned `Decision`'s meaning.

**New in wave 4 (04-10) — 04-11/04-12 need these:**

- **J. DISCHARGED (04-12: `network/language_wiring.build_language_runtime()` reads
  `language.model[ModelKey.HINT_WORD_LIMIT.value]` once and passes the SAME int into both
  `DecodeContext.word_limit` and `BluffContext.word_limit`). The word limit's config home is
  `language.json`'s `model` group
  (`hint_word_limit`, `ModelKey.HINT_WORD_LIMIT`, validated by
  `shared/language_model_config.py`), NOT `deception.json`/
  `deception_config.py` as 04-10-PLAN.md's own `files_modified` listed.**
  Reasoning: the limit governs the LLM CHANNEL (shared by `bluff.py`'s
  emission side and `DecodeContext.word_limit` on the decode side, both
  already reading `language.json`'s `model` group for `game_arena`), not
  the deception POLICY (`deception.json`'s lie-probability/herding knobs,
  which decide WHAT is claimed, never how many words phrase it).
  **04-12 must read `language_params.model["hint_word_limit"]` ONCE and
  pass the SAME int into both `DecodeContext.word_limit` (closes
  wave-3 carry-over A) and `BluffContext.word_limit`** — one negotiated
  number, one config field, read on both sides.
- **K. DISCHARGED (04-12: `network/turn_language_io.send_turn_hint()` rebuilds `BluffContext` via
  `dataclasses.replace(..., degrade_level=ctx.language.gatekeeper.budget.level)` before every
  `compose_outgoing()` call; exactly one `HintBank` is built in `build_language_runtime()` and
  held on `LanguageRuntime` for the game's duration). `BluffContext` has one field that goes stale
  mid-game: `degrade_level`.** `provider`/`arena`/`word_limit`/`hint_bank` are
  stable for the whole game and should be set up once; `degrade_level`
  must be re-read from `gatekeeper.budget.level` and refreshed before
  EVERY turn's `compose()` call (unlike `DecodeContext`, which has no
  degrade-sensitive field at all). **04-12 should construct exactly one
  `HintBank(rng=...)` per game** (same ownership pattern as 04-09's
  `Reliability`: built once at wiring time, held for the game's duration,
  seeded so a replay reproduces byte-identically) **and reuse that same
  instance across every turn's `BluffContext`** — a fresh `HintBank` each
  turn would reset the no-repeat rotation and defeat D-39's
  signature-avoidance goal.
- **L. `compose()` never calls `TemplateProvider.complete()`, even when
  the configured provider name is `"template"` or the budget is
  `TEMPLATE_ONLY`.** It goes straight to `HintBank.select()` instead — the
  bank is `DeceptionPlan`-aware (kind/intent/arena-flavoured); a generic
  `TemplateProvider(phrases=[...])` has no way to know what claim it's
  supposed to be phrasing. `TemplateProvider` remains the registered
  `"template"` provider for the DECODE side (04-07) and for provider-name
  validation (`get_provider_class`), just not for the bluff fallback path.
- **M. `assert_no_coordinates` now lives in `shared/hint_guard.py`**
  (moved out of `network/hint_payload.py`, which re-exports it unchanged
  — same precedent 04-08 set for `Intent`/`DirectionWord`). Any new code
  needing this guard (04-12 included) should import it from
  `pursuit.shared.hint_guard`, not from the network re-export.
- **N. `compose()`'s retry-failure behaviour, for anyone re-reading the
  code:** if the ONE retry attempt itself comes back as an `LlmFailure`
  (or an empty completion), `compose()` truncates the ORIGINAL
  over-length completion rather than falling back to the bank — the bank
  is reserved for "no usable model text at all", and a verbose-but-real
  response is still worth truncating rather than discarding.

**New in wave 4 (04-09) — 04-10/04-11/04-12 need these:**

- **F. DISCHARGED — closed by wave-5 carry-over Q (`BeliefAdapter` itself constructs
  `Reliability`, not 04-12; see Q above), then DISCHARGED again in that narrower shape by 04-12's
  own carry-over Q entry. `Reliability` is per-opponent, per-game, and is never constructed by
  anything in this plan's own scope.** `04-12` (turn-pipeline integration) is the intended owner of building one
  `Reliability(config.reliability)` per opponent at handshake time and holding it for the game's
  duration — never persisted, never shared across games (rule 52). Each incoming hint: call
  `scent_check.contradicts(inference, opponent_field, model, config)` first, then
  `reliability.observe(score)` — in that order, once per turn a hint arrives.
- **G. `hint_likelihood.weight` (D-40's fixed mixing weight `w`) and `reliability.prior` (D-51's
  adaptive coefficient's starting point) are TWO INDEPENDENT `belief.json` fields**, not the same
  number reused twice. If a later plan's prose reads as if they should be unified, that is the
  same ambiguity 04-09 resolved by keeping them separate — resolve it in the plan text first, not
  by quietly merging the config fields.
- **H. `hint_likelihood(inference, reliability, board_size, config)` takes `config: BeliefParams`
  directly** (the full loaded object, not a sub-group) — same calling convention as
  `belief_scent.scent_likelihood(..., config: BeliefParams)`. Both read their own group off the
  same `BeliefParams` instance.
- **I. A heading-only `Inference` (no region, no cells) produces NO shift in `hint_likelihood`** —
  confirmed consistent with carry-over B (confidence 0 washes it out) and, independently, with
  `hint_likelihood`'s own fallback for the case where a positive-confidence heading-only shape
  reaches it anyway (a shape the real decoder never emits, but a defensive path exists and is
  tested).

**New in wave 3 (04-07 / 04-08) — a wave-4 executor needs all five:**

- ~~**A. `DecodeContext.word_limit` has no default and no config key yet.**~~ **FULLY CLOSED**:
  `hint_word_limit` lives in `language.json`'s `model` group (04-10, wave-4 carry-over J), and
  04-12's `language_wiring.build_language_runtime()` now passes
  `language.model["hint_word_limit"]` into `DecodeContext` for real on the live path — the
  previously-open half is discharged.
- **B. A heading-only hint decodes at confidence 0, so it is NOT positional evidence.**
  04-07-PLAN.md Task 1 says reject when region and cells are both absent while confidence is
  above zero; taken literally that would discard `direction` for the one case where a heading is
  all that was stated. The rule ships exactly as written, and the prompt asks for
  `confidence: 0` on such a hint, so the heading survives on the `Inference` with
  `is_evidence == False`. **If 04-09 wants a bare heading to shift mass, change the plan first,
  not the code.**
- **C. DISCHARGED (04-12: `network/turn_language.build_deception_plan()` passes
  `scent=ctx.scent_field` and `weights=getattr(inner_brain(ctx.brain), "weights", None)`).
  `plan_deception` needs `params`, and takes two optional keywords the plan did not name.**
  Signature is `plan_deception(role, state, params, belief, rng, config, *, scent=None,
  weights=None)`. Both omit-safely; the loss is silent quality, not an error.
- **D. The cop's herding lever is real but shallow, and that is measured.** One-step lookahead
  cannot see a trap two steps away. 04-08's `test_the_lie_drives_the_thief_somewhere_less_connected`
  uses a board found by randomised search rather than a hand-built cul-de-sac, because the
  hand-built one did not exercise the mechanism at all. Do not read the cop's 0.644 lie rate as
  proof the claims are strategically strong — read it as proof they are non-degenerate.
- **E. Three types moved down into `shared/` so `strategy/` could reach them without importing
  `pursuit.network`** (STRAT-03): `DirectionWord`/`Origin`/`DEFAULT_ORIGIN`/`axis_signs` →
  `shared/directions.py`, and `Intent` → `shared/deception_types.py`. Both network modules
  re-export, so existing call sites are unchanged, and two tests assert the *identity* of the
  re-exports so a future re-declaration fails loudly instead of drifting.

**Still open from waves 1–2:**

1. **DISCHARGED by 04-12 (see carry-over X above): a real `local_scent_digest` is now passed on
   the live path.** The "consider making it required" half was deliberately not taken —
   `test_handshake_abort.py`/`test_handshake_client.py` still build offers with none, out of
   04-12's scope to change.
2. **04-06 estimates tokens locally instead of calling `count_tokens()`.** The plan's `must_haves`
   ("the provider never calls the API directly", no carve-out) is stricter than its own task text;
   the executor obeyed the stricter one. If a later plan wants exact counts, that tension must be
   resolved in the plan first, not in the code. Still open — unrelated to 04-12.
3. ~~The knowledge graph is STALE~~ **REFRESHED by 04-12** (this session ran locally): `graphify
   update .` → 5221 nodes / 9687 edges / 336 communities, `GRAPH_REPORT.md` copied to
   `.planning/graphs/` and committed. `graph.html` was NOT regenerated this pass — 5221 nodes
   exceeds graphify's 5000-node HTML visualization limit; the prior (now stale) `graph.html`
   remains on disk as a gitignored artifact. If a later wave runs in the cloud container again,
   `which graphify` will find nothing there and this step must move back to a local session.
4. **Phase-4 code currently shares a branch with a GSD toolchain change** (enabling parallelization
   and adding `scripts/ensure_gsd.sh`). If you want the phase reviewed on its own, split it before
   opening a phase PR. Still open — unrelated to 04-12.
5. **`docs/phases/phase-4/` does not exist**, though CLAUDE.md's per-phase triplet rule says
   `/gsd:plan-phase 4` should have created `{PRD,PLAN,TODO}.md` there and approved them *before*
   execution. The plan set instead assigns the triplet to **04-13 (wave 7)**, so the two rules
   disagree about when it lands. 04-12 did not create it either, for the same reason wave 3 did
   not: writing a phase-wide PRD/PLAN/TODO from inside a single wave would either duplicate
   04-13's deliverable or invent content for waves not yet executed. **04-13 is next — this is
   its job now, not a choice remaining to be made.**
6. **`tests/integration/test_beats_baseline.py` does not exist** — 04-11 confirmed via `git log
   --all` that it was deleted in Phase 3's run-2 rebuild (commit `f3d9847`), before ANY Phase-4
   plan started. Any later plan or verify-work step whose text names this file (04-11-PLAN.md's
   own verification block did) should treat it as a stale reference, not a regression to chase.
   `tests/integration/test_strategy_pluggable.py` — the file that same text usually pairs it
   with — DOES exist and stays the real GATE-3 regression anchor.

## What a reader should still know (unchanged from planning)

1. **Read `04-PLAN-OUTLINE.md` §1 first.** The book contradicts itself about what a peer reveals
   each turn (§5.3.2 says the Move is revealed every turn; §6.4 says neither side ever sees the
   opponent's real location). D-48 resolves it under the preface's academic-freedom clause. Plans
   04-04, 04-05, 04-11 and 04-12 only make sense downstream of that decision.
2. **Three source-of-truth deviations are deliberate and documented**, and 04-13 must write all
   three up or the phase is not submission-ready:
   - **D-48** — the reveal contradiction and our choice.
   - **D-49** — scent is derived locally and never transmitted.
   - **D-51** — a *disclosed revision* of `04-CONTEXT.md`'s "hint trust: fixed discount weight":
     the fixed weight survives, the trust coefficient becomes adaptive per §4.4.
3. ~~Plan 04-01 Task 4 closes a live hole in the rule-25 guard.~~ **Done in wave 1** —
   `scripts/check_no_llm_in_strategy.py` now rejects `pursuit.services` imports under `strategy/`,
   and the gate is green with `services/llm/` present.
4. **Four config blocks, one owner each** — `scent.json` (04-01 ✅), `language.json` (04-03 ✅),
   `belief.json` (04-05 ✅), `deception.json` (04-08 ✅). Their key enums live beside their
   loaders in `shared/`, **not** in `config_keys.py`. All four role-file pairs are byte-identical
   and asserted so by a test.

## Working-environment notes

- **Do not rewrite plan files with Python's `write_text` on Windows** — it converts `\n` to
  `\r\n`, and the GSD frontmatter parser then reports every required field as missing. Use the
  editing tools, or write bytes explicitly.
- **Never `git merge` a worktree branch from inside a worktree.** It silently targets that
  worktree, reports "Already up to date", and leaves the real branch untouched. Run every
  main-branch git command from the repository root. This cost a near-miss during wave 1.
- **Do not trust a fresh worktree's base commit.** One wave-2 worktree was created off a commit
  predating wave 1; only the base assertion in the executor contract caught it and reset it.
