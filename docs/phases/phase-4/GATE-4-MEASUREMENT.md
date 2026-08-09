# GATE-4 measurement — Phase 4, book §10.4 milestone 4

**Status:** MOCKED measured and PASSING on every criterion below; LIVE **PENDING** (blocked on
`ANTHROPIC_API_KEY` absent on the measurement machine — see [Live status](#live-status)).
**Date:** 2026-08-09 · **Plan:** 04-14 · **Method:** `scripts/measure_gate4.py`, reproducible from
its own recorded seeds (`GATE4_SEEDS = (30260801, 30260802, 30260803)`, `scripts/gate4_games.py`).

Per rule 38 and this plan's own must_haves: **the phase is not complete while the live row is
pending.** `/gsd:verify-work 4` must not tick GATE-4 until `--live` actually runs and this
document's [Live status](#live-status) section is updated from a real run.

Raw JSON:
[`gate4_measurement_mocked.json`](gate4_measurement_mocked.json) ·
[`gate4_measurement_live.json`](gate4_measurement_live.json) (currently the PENDING stub).

---

## The three criteria — quoted verbatim from `.planning/ROADMAP.md` Phase 4 (not ours to edit)

> **Success Criteria** (book milestone gate, §10.4):
>
> 1. A hint is translated into an inference (belief map updates via Bayes from scent + hints)
> 2. The scent map updates (0.9 at source, 0.10 decay/turn, 5×5 window) and decays each turn; the
>    decay model is locked pre-game
> 3. The LLM emits a ≤15-word hint each turn, either true or false, with the `intent` flag
>    committed in advance; comms stay natural-language-only

Each gets a number below, a method, and a verdict that follows from the number — not the reverse.

---

## Criterion 1 — a hint becomes an inference

**Method.** Three seeded two-peer games (`GATE4_SEEDS`, belief enabled, `--mocked` provider fed
from `tests/fixtures/hints_{en,he}.json`'s own recorded `response` dicts). `BeliefAdapter.decide`
— the real, unmodified method every live game calls — is wrapped for the run's duration
(`scripts/gate4_beliefspy.py`) to read `self.belief.posterior()` immediately before and after each
call, bucketed by whether that turn's decoded `Inference.is_evidence` was true. Nothing in `src/`
is touched or special-cased.

| Number | Value |
|---|---|
| Turns measured (both roles, 3 games) | **136** |
| Turns where the hint decoded to evidence | **22** (16.2%) |
| Mean absolute posterior change (L1) on exactly those 22 turns | **1.171** |
| Mean absolute posterior change on the 114 no-evidence turns | 0.0 (by construction — `hint_likelihood` returns an all-zero grid at confidence 0, `BeliefMap.update`'s zero-guard makes it an exact no-op) |

**Verdict: PASS.** A hint that decodes to evidence measurably moves the posterior (1.171 average
L1 shift on a distribution that sums to 1, i.e. a large, non-trivial reallocation of mass); a hint
that does not carry evidence changes nothing, exactly as designed. Both halves of "translated into
an inference" are demonstrated with a number, not a boolean.

**Honesty note on the 16.2% figure.** The fixture pool itself is ~45% evidence-bearing responses
(5 of 11 canned cases), yet only 16.2% of decode *attempts* in the real turn loop found evidence.
The gap is not a defect: `decode_turn_hint` (`services/language_turn.py`) returns `NO_EVIDENCE`
**without ever calling the provider** whenever no hint is cached for that turn — and D-48's
one-turn-behind Reveal (design note 7) means several turns per game genuinely have nothing cached
yet (the first mover's opening turn, and any turn where the opponent's hint has not yet completed
its own round trip). The 16.2% therefore measures "fraction of *decision points*, including the
ones with no hint to decode at all, that produced evidence" — a stricter, more honest number than
"fraction of hints, once one exists, that decode to evidence" would be. This report leaves it as
measured rather than reframing it to look larger.

---

## Criterion 2 — the scent map updates and decays, model locked

**Method, decay law.** The event log carries no per-turn scent-grid snapshot (04-12 logs belief
entropy/argmax/reliability, not the scent field itself), so this is measured by driving the
shipped `ScentField`/`strategy/scent.py` directly with the **locked, loaded** `scent.json` model —
the same objects a real game mutates every turn, not a reimplementation (`scripts/gate4_scent.py`):
one emission at a fixed cell, then 12 consecutive `.advance()` calls with no re-emission, compared
at every step against the closed-form `scent.expected_strength_after()`.

**Method, handshake lock.** `shared/scent_config.scent_digest()` — the exact function both real
peers call at handshake (`agent_lifecycle.default_context`/`run_agent`, D-46) — computed
independently on `config/police/scent.json` and `config/thief/scent.json`.

| Number | Value |
|---|---|
| Decay-only turns checked (≥ the plan's own 10-turn floor) | **12** |
| Max deviation from the closed-form law over those 12 turns | **1.11 × 10⁻¹⁶** (float noise) |
| Police scent digest | `c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e` |
| Thief scent digest | `c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e` |
| Digests match | **true** |

**Verdict: PASS.** The shipped decay law reproduces the closed form to machine precision over more
than the required 10 turns, and both peers' locked payloads hash identically — the same digest
04-01/RESUME.md's wave-1 table already recorded (`c0e6322…`), an independent cross-check that this
measurement is reading the real, shipped config and not a stale copy.

---

## Criterion 3 — a hint every turn, ≤15 words, both intents, flag committed first

**Method.** Same three seeded games as criterion 1. Every criterion-3 number below is read from
the police side's own JSONL (`event == "language_turn"` and `event == "message_sent"` with
`envelope.type == "move"`), not from special instrumentation.

| Number | Value |
|---|---|
| Hints sent (police side, 3 games) | **68** |
| Turns played (police side, 3 games) | **68** |
| Hint every turn | **true** (68/68) |
| Max word count observed | **11** (limit 15) |
| Within the configured word limit (`language.json` → `hint_word_limit`) | **true** |
| `intent = truth` count | 13 |
| `intent = lie` count | 55 |
| Both intent values occurred | **true** |
| Outgoing coordinate leaks (hint text + move payload, scanned every turn) | **0** |
| Intent committed before text | **1.0** (see method note below) |

**Consistency check.** Criterion 1's belief-adapter spy counted 136 `decide()` calls across
**both** roles over the same 3 games; 2 × 68 = 136 exactly, confirming the police-only count above
is representative of a symmetric game rather than an artifact of only checking one side.

**Method note — "intent committed before text".** The JSONL fuses `text` and `intent` into one
`outgoing_hint` payload once both exist, so there is no pair of *timestamps* to diff. The property
is instead verified **structurally**, which is a stronger guarantee than a timestamp comparison
could give: `turn_language_io.send_turn_hint` calls `build_deception_plan()` (which fixes
`plan.intent`) and only then calls `compose_outgoing(plan, ...)` — `plan` is a **required
positional argument**, so no call that produces hint text can exist without an intent already
decided. `tests/integration/test_gate4.py::test_intent_is_always_committed_before_the_hint_text_exists`
freezes this with a live call-order spy over a full game (mirroring
`tests/integration/test_language_pipeline.py`'s own Figure-7 order test), and it passes.

**Verdict: PASS.** Every measured sub-condition holds with a number behind it, and the coordinate
scan (rule 27) found zero leaks across every outgoing hint and every outgoing move payload.

---

## Decode-fixture accuracy (EN and HE, separately)

**Mocked method.** Each fixture case's own recorded `response` is fed back through
`decode_hint()` via a provider that returns exactly that dict — the same technique
`tests/unit/services/test_decode.py` uses. This exercises decode.py's **own schema
re-validation** (it must independently reject the prompt-injection case's claimed confidence of
1.0), not a live model's language understanding.

| Language | Cases | Matched | Accuracy |
|---|---|---|---|
| EN | 7 | 7 | **1.0** |
| HE | 4 | 4 | **1.0** |

A decoder that only worked in English would be a finding worth its own line (per the plan's own
instruction) — it is not what happened here, though this number is necessarily a ceiling: it
proves the re-validation and schema logic are correct in both languages, not that a real model
would produce these exact responses from these exact sentences. **That is what `--live` measures**
(see below) — the mocked accuracy above must not be read as a live decode-accuracy result.

---

## Latency (mocked)

| Number | Value |
|---|---|
| Mean per-turn wall time | **31 ms** |
| p95 per-turn wall time | **39 ms** |
| `network.watchdog_threshold` | 60 s |
| Margin (p95 vs threshold) | **~1500×** |

This is in-process function-call latency (no network hop — the mocked provider never leaves the
Python process), consistent with 04-12's own measured ~37 ms language-ON figure. **It says nothing
about real API latency.** The live run is what measures true per-turn latency against the
watchdog budget; see [Live status](#live-status).

---

## Belief-on vs belief-off — reported honestly, not smoothed over

Outline §1's honesty clause predicts **no scoring gain** from the belief layer in Regime A (the
believed-state substitution is the identity once the Reveal is exact). The measured result:

| | belief ON | belief OFF |
|---|---|---|
| Cop win rate (3 seeded games each) | **1.0** (3/3) | **0.0** (0/3) |

**This does not match the honesty clause's prediction, and that is stated plainly rather than
explained away.** But it also is not the comparison the honesty clause is actually about, and
that mismatch is itself worth recording precisely:

`network/turn_language.py::choose_destination`'s `belief.enabled = false` fallback does not give
the raw brain a *blind* mover with no Bayesian help — it gives it **the true, un-blinded current
opponent cell straight off `ctx.state`** (`opponent_cell = ctx.state.thief if agent == "cop" else
ctx.state.cop`), because that fallback path predates D-48/D-43 and was never rewritten to feed a
one-turn-behind revealed cell instead. So "belief off" in this codebase is "omniscient, zero-lag
mover", not "blind mover, no belief map" — a materially *easier* condition than what
`BeliefAdapter` operates under, not a harder one. With only 3 seeds and that confound in play, the
measured 1.0 vs 0.0 gap cannot be attributed to the belief layer's own contribution one way or the
other; it most plausibly reflects the *thief* also becoming omniscient under `belief.enabled =
false` (better evasion) outweighing the cop's own already-perfect information, but this is
speculation past what the measurement itself proves.

**What would be needed to test the honesty clause's actual claim:** a third arm — a raw brain fed
the *same* one-turn-behind revealed cell `BeliefAdapter` receives via `known_cell`, rather than the
always-current true cell. That arm does not exist in the shipped code and is out of this plan's
scope to add (07-scope: measurement, not a new strategy variant). Recorded here as an honest gap,
not fixed silently.

---

## Robustness (outline §8 item 4 — not the book's gate, the league's reality)

Already measured and passing, by 04-12's own test suite (`tests/integration/test_llm_degradation.py`,
four full two-peer games): no API key (template-only path), every provider call failing (cycling
every `LlmFailureReason`), the token budget pre-exhausted past `TEMPLATE_ONLY`, and a silent peer
that sends no hints at all — all four finish with a correctly-scored, agreeing outcome. Not
re-measured here to avoid duplicating that plan's own evidence; see `04-12-SUMMARY.md`.

---

## Live status

**PENDING — blocked on `ANTHROPIC_API_KEY` absent on this measurement machine.** Verified before
this plan started (environment constraint) and reconfirmed by actually invoking `--live`, which
correctly attempted **zero** network calls and wrote the PENDING stub below rather than silently
falling back to template numbers:

```json
{
  "mode": "live",
  "seeds": [],
  "live": {
    "status": "PENDING",
    "reason": "ANTHROPIC_API_KEY not set on this machine -- no live call attempted",
    "rerun_command": "ANTHROPIC_API_KEY=... uv run python scripts/measure_gate4.py --live"
  }
}
```

**Rerun command:**

```
ANTHROPIC_API_KEY=sk-ant-... uv run python scripts/measure_gate4.py --live
```

**What that run will produce, once it runs (`scripts/gate4_runner.run_live`):**

- **Liveness proof (D-33's own blind spot).** `response.model` must name Haiku 4.5
  (`AnthropicProvider.served_model`), provider calls must be non-zero, and token usage must be
  non-zero. A wrong model id, a dead key, or a rate-limited account all currently produce a clean
  finished game on the template fallback path — "the game completed" is not evidence the API was
  reached. If this assertion fails, the script marks `live.status = "VOID"` and the report
  explicitly says not to treat any of its other live numbers as real.
- **Real token spend**, in tokens from `response.usage` (never estimated) and in USD at
  Anthropic's published Haiku 4.5 rate (`gate4_report.HAIKU_INPUT_USD_PER_MTOK` /
  `HAIKU_OUTPUT_USD_PER_MTOK` — cited, not a `docs/PARAMETERS.md` value; reconfirm before Phase
  7's league spend email, PARAMETERS.md Table 18 row 4), extrapolated to a six-opponent series
  (`gate4_report.extrapolate_series_cost`).
- **Real per-turn latency**, mean and p95, against `network.watchdog_threshold` — this document's
  mocked 31 ms/39 ms figures are in-process and say nothing about a real network round trip.
- **Real decode accuracy** on the EN and HE fixtures, scored against `expect` while **ignoring**
  each case's canned `response` (the fixture file's own documented contract) — the number that
  actually tests whether Haiku 4.5 understands the sentences, not just whether our own
  re-validation logic is correct.

**Per this plan's own rule: none of the mocked numbers above may be presented as live ones, and
the phase is not fully measured while this section reads PENDING.**
