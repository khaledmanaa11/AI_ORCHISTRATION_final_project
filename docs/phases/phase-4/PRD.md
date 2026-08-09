# Phase 4 PRD — Language and Scent

**Milestone gate (book §10.4, stage 4):** a hint becomes an inference; the scent map updates and
decays; the LLM emits a hint every turn, sometimes true and sometimes false.

**Status:** ◐ implemented, gate **not yet measured** — plan 04-14 (wave 8) runs the live-API
measurement this document's §3 depends on. Do not read this PRD as claiming the gate is passed;
that claim belongs to 04-14's own report, not to this one.
**Binding rules contract:** [`RULES-RESOLUTION-LANG.md`](RULES-RESOLUTION-LANG.md) — read this
first. It documents the one place the book contradicts itself (§5.3.2's per-turn Reveal vs
§6.4's "neither side sees the opponent's real location") and the choice this phase makes (D-48),
plus why scent is never transmitted (D-49). Every other decision in this phase downstream of
that contradiction routes a reader here rather than making them discover it.
**Mechanism PRDs:**
[`docs/PRD_scent_map.md`](../../PRD_scent_map.md) ·
[`docs/PRD_belief_map.md`](../../PRD_belief_map.md) ·
[`docs/PRD_deception.md`](../../PRD_deception.md)

---

## 1. What this phase delivers

| # | Deliverable | Where | Plan |
|---|---|---|---|
| D1 | Locked scent model — Table 16 values, Figure-4 kernel, cryptographic digest exchanged at handshake (rule 23) | `strategy/{scent,scentfield}.py`, `shared/scent_config.py`, `network/handshake*.py` | 04-01, 04-02 |
| D2 | LLM gatekeeper — Table 19 token bucket, FIFO overflow queue, D-35 budget/degrade ladder | `services/llm/{gatekeeper,bucket,budget}.py` | 04-03 |
| D3 | Transport for hints and direction-token moves — `MessageType.HINT`, rule-27-compliant wire shape | `network/{move_payload,hint_payload,turn_buffer}.py` | 04-04 |
| D4 | Provider layer — registry, zero-token `template`, Haiku 4.5 `claude_api` | `services/llm/{provider,template_provider,anthropic_provider}.py` | 04-06 |
| D5 | Hint decoder — constrained JSON, EN+HE, total (never raises) | `services/llm/decode*.py`, `shared/inference.py` | 04-07 |
| D6 | Bayesian belief map — grid, motion model, scent+hint likelihoods, adaptive reliability | `strategy/{belief,belief_motion,belief_scent,belief_hint,reliability,scent_check}.py` | 04-05, 04-09 |
| D7 | Deception planner — intent + claim, both role policies, structurally rule-25-safe | `strategy/{deception,deception_thief,deception_cop,regions}.py` | 04-08 |
| D8 | Bluff generator — word-limited, total, style-guided | `services/llm/{bluff,bluff_prompt,hintbank,wordcount}.py` | 04-10 |
| D9 | `BeliefAdapter` — Option A believed-state substitution, D-43 sampling | `strategy/beliefadapter.py` | 04-11 |
| D10 | Live turn-pipeline integration — Figure 7 wired into the real two-process turn loop | `network/turn_*.py`, `network/agent_lifecycle.py`, `services/language_turn.py` | 04-12 |
| D11 | Three per-mechanism PRDs + this triplet + the rules note | this directory, `docs/PRD_{scent_map,belief_map,deception}.md` | 04-13 |
| D12 | GATE-4 measurement against the live API | (pending) | 04-14 |

## 2. Acceptance criteria (= §10.4 milestone gate)

The book states the gate as three observable behaviours. 04-14 is the plan that measures all
three against a live game; this PRD states what "measured" will mean so the report cannot quietly
redefine the bar after the fact.

1. **A hint becomes an inference.** A seeded game log must show a decoded hint changing the
   belief map's posterior, with before/after mass reported; a schema-invalid hint must change
   nothing (`shared/inference.NO_EVIDENCE`'s all-zero-grid guarantee, already unit-proven —
   see [`docs/PRD_belief_map.md`](../../PRD_belief_map.md) §4 — 04-14 reproduces it inside a live
   game rather than a unit test).
2. **The scent map updates and decays.** The decay law must be asserted numerically over ≥10
   turns against the locked table, and both peers' scent digests must match at handshake
   (already true on every game this phase's tests run — 04-14 confirms it once more on the live
   path with a real API key present).
3. **The LLM emits a ≤15-word hint every turn, true and false.** Over one full 35-turn game:
   every turn must carry a hint, every hint must be ≤ the configured limit, both `intent` values
   must occur, and the flag must be fixed before the text is generated (structurally guaranteed —
   see [`docs/PRD_deception.md`](../../PRD_deception.md) §3/§6 — 04-14 confirms it holds against
   the real Anthropic API, not only the mocked/template paths this phase's own test suite uses).

A fourth check, not in the book's gate but in the league's reality, is also 04-14's to run: a game
must complete with the API key unset (template-only path) and with a forced API error on every
call (D-33) — both already proven in this phase's own test suite
(`tests/integration/test_llm_degradation.py`, four full games), to be reconfirmed live.

## 3. Requirements covered

| REQ | Landed by |
|---|---|
| LANG-01 ≤15-word free-text hint each turn | 04-10, 04-12 |
| LANG-02 natural language only, no coordinates in the protocol | 04-04, 04-12 |
| LANG-03 hints may lie; `intent` committed in advance | 04-08 |
| LANG-04 scent 0.9 / 0.10 / 5×5 | 04-01 |
| LANG-05 Bayesian belief map from scent + hints | 04-05, 04-09 |
| LANG-06 LLM decodes hints and writes bluffs | 04-06, 04-07, 04-10 |
| LANG-07 decay model cryptographically locked pre-game | 04-01, 04-02 |
| STRAT-07 / rule 25 the LLM never chooses the move | structural CI guard + 04-08 |
| QUAL-03 / QUAL-05 gatekeeper on every external call, queue never crashes | 04-03 |
| DOC-01 per-mechanism PRDs + phase triplet | 04-13 |

## 4. In scope / out of scope (this phase)

**In:** the scent model and its cryptographic lock; the LLM gatekeeper and provider layer; the
hint transport and direction-token move codec; the hint decoder; the Bayesian belief map (both
regimes); the deception planner (both roles); the bluff generator; wiring all of the above into
the live two-process turn loop; GATE-4 measurement.

**Out:** tunnelling and public exposure (Phase 5); commit-reveal, nonce handling, and Step-0
(Phase 6 — only the scent *digest* lands here, D-46/rule 23, per D-49's argument for why that much
had to move earlier); Gmail reporting and the live GUI (Phase 7); the book's §6.5.1 beige-box
"LLM-based tactics by mutual agreement" default (this project keeps rule 25 hard — see
`docs/phases/phase-3/RULES-RESOLUTION.md` §8 — the algorithm decides, never the model).

## 5. Dependencies

- **Depends on:** Phase 3 (`strategy/valuebrain.py`'s matrix-game mover, unmodified by this
  phase — `git diff --stat` empty across every belief-adapter commit) and Phase 2's handshake,
  turn state machine, and event log, all extended rather than replaced.
- **External:** `anthropic>=0.121.0` (`uv add`, D-32) for the `claude_api` provider; no other new
  runtime dependency.

## 6. Measured results (from the phase's own build; GATE-4 itself is 04-14's to measure)

Held on the merged tree after wave 6 (04-12), all measured, none inherited from a self-report:

| Check | Result |
|---|---|
| `uv run pytest --cov` | 1048 passed, 95.21% (floor 85%) |
| `uv run ruff check .` | 0 violations |
| `scripts/check_line_limit.sh` | clean repo-wide |
| `scripts/check_no_llm_in_strategy.py` | clean — `strategy/` imports nothing under `pursuit.services` |
| §4.4 lie-detector reproduction | 0.9 → 0.81 exact; lying opponent's reliability 0.5→0.2→0.05 within 2 turns; truthful holds at 0.5 for 10 turns |
| Fused-posterior `argmax` | tracks the real scent trail, not the claim, in both regimes |
| Belief-enabled decision time | cop max 4.99ms, thief max ~3.7–4.99ms, against a 50ms budget |
| Per-turn wall time, language ON/OFF | ~37ms/turn ON, ~18ms/turn OFF, against a 60s watchdog threshold |
| Four degradation games (no key, all calls fail, budget exhausted, silent peer) | all finish correctly scored |
| Thief lie-rate curve | flat at 0.8 ceiling near danger, ramps to 0.333 floor at distance 6, never 0 or 1 |
| Cop lie rate | 125/194 = 0.644 over random legal positions, no degenerate single-sector answer |

## 7. Known limitations, stated rather than hidden

1. **Regime A's belief map contributes modestly to move scoring, not primarily.** Stated in full,
   not smoothed over, in [`docs/PRD_belief_map.md`](../../PRD_belief_map.md) §6 — its real value
   there is LANG-05 compliance, the opponent-action prior, the deception surface, and Regime B
   survival.
2. **The cop's herding lever is shallow (one-step lookahead)**, per
   [`docs/PRD_deception.md`](../../PRD_deception.md) §5 — measured as non-degenerate, not as
   strategically deep.
3. **All numbers in this document and its linked PRDs are measured on the mocked/template test
   paths this phase's own suite exercises.** No test in waves 1–7 calls the real Anthropic API
   (every provider is a fake, `TemplateProvider`, or an explicitly-failing stub) — 04-14 is the
   first and only plan that runs against the live API, and its numbers (token cost, decode
   accuracy, live latency) supersede this phase's local estimates where they differ.

## 8. Handoff to Phase 5 (and to 04-14 first)

**04-14 must run before this phase can be verified.** The §10.4 gate is a live-API claim by its
own wording ("the LLM emits a hint every turn"); everything this phase built is ready for that
measurement (`tests/integration/two_peer_game.py` is the reusable two-real-peer harness 04-14
should reuse, per `RESUME.md` carry-over W) but the measurement itself has not run. This PRD's
§2 states the bar in advance so 04-14 cannot redefine it after seeing the result.

**Nothing in Phases 1–3 blocks Phase 5.** The scent lock, the belief map, the deception channel
and the live turn-pipeline are all independent of tunnelling; Phase 5 only needs the handshake
and turn loop this phase extended, both unchanged in shape.
