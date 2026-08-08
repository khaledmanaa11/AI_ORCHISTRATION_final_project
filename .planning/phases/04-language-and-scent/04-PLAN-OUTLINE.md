# Phase 4 Plan Outline — Language and Scent

**Phase:** `04-language-and-scent` · **Written:** 2026-08-08 · **Plans:** 04-01 … 04-14
**Context:** [`04-CONTEXT.md`](04-CONTEXT.md) · **Requirements:** LANG-01 … LANG-07
**Gate:** §10.4 milestone 4 — *a hint becomes an inference; the scent map updates and decays;
the LLM emits a hint every turn, sometimes true and sometimes false.*

**No RESEARCH.md was produced.** The phase's domain knowledge is in the book itself, and the
book was read directly this session — chapter 4 (pp. 24–31, PDF 40–47), §6.1–6.6 (pp. 41–52,
PDF 57–68) and §5.3 (pp. 34–36, PDF 50–52). Quotations below carry **book page (PDF page)**.
Per [[verify-rules-against-the-book-not-extracts]], **PDF page = book page + 16.**

**All plans are subject to the standing gates and they are not restated per plan:**
`ruff check` → 0 · `pytest --cov` ≥ 85% · every file ≤ 150 non-blank/non-comment lines ·
`uv` only · zero hardcoded numbers (config / `constants.py` / `Enum`) · zero secrets ·
every external call through the gatekeeper · tests alongside code, all LLM calls mocked.

---

## 1. The contradiction this phase had to settle first

`04-CONTEXT.md` §Phase Boundary flagged it as the researcher question: *"what exactly is
revealed per turn vs at game end?"* The book answers **both ways**, in two different chapters.

> **§5.3.2, book p.35 (PDF 51):** *"**חשיפה (Reveal).** הסוכן שולח ליריב את הפעולה (Move) ואת
> המשפט המילולי. ה-Nonce נשאר חבוי בשלב זה."* — the agent sends the opponent **the action
> (Move)** and the verbal sentence; only the nonce stays hidden. Figure 6 (p.36 / PDF 52) draws
> `Reveal: Move + Hint (Nonce hidden)` flowing in **both** directions, **every step**.

> **§6.4, book p.47 (PDF 63):** *"שני הצדדים סימטריים לחלוטין: **אף אחד מהם אינו רואה את מיקומו
> של היריב האמיתי**. כל צד יודע היכן הוא עצמו, ומקבל את מפת הריח של הצד השני ורמז מילולי שעשוי
> להיות כוזב."* — **neither side sees the opponent's real location**; hence the belief map, a
> grid of `P(opponent in cell)`, updated by Bayes with a **reliability coefficient** on the text.

These cannot both be literally true. The book anticipates exactly this:

> **Preface, "חופש אקדמי במקרה של סתירה" (p. v):** *"…ייתכן שתמצאו בו סתירה … לכם החופש האקדמי
> לבחור באחת מן האפשרויות ולהמשיך על פיה, **ובלבד שתציינו זאת במפורש בדוח שלכם**: היכן זיהיתם
> את הסתירה, במה בחרתם, ומדוע."*

### D-48 — the choice, and why

**We keep the per-turn Reveal, and we express the move as a natural-language direction token.
The opponent's position is therefore known *one turn behind*, and the belief map is the
one-turn-ahead predictive distribution over where the opponent will be when our move lands.**

1. **The protocol reading is load-bearing and cannot be dropped.** Rules 15/16 (barrier
   declared truthfully), 19 (any hash mismatch → 0), 21/22 (capture declared truthfully) and
   46–48 (both sides score the ending identically) are only computable if both peers maintain a
   synchronised physical world. Phase 2 already does this. Deleting the Reveal breaks the audit
   rule 36 depends on.
2. **§6.4 stays fully meaningful.** At the moment we commit, the opponent's move **for this
   turn** is genuinely unknown — that is the entire purpose of Commit→Acknowledge→Reveal
   (§5.3.2: *"…the reveal will occur only when both sides have already fixed their moves"*).
   `P(opponent cell at end of this turn)` is a real, non-degenerate distribution, and scent and
   hints are real evidence about it.
3. **Rule 27 is honoured, and the canonical directive requires it.**
   `docs/KHALED_PERSONAL_PLAN.md:437` — *"Numeric coordinates in the protocol are FORBIDDEN
   (rule 27) — **this replaces the coordinate transport from Phase 2**."* Today
   `turn_actions.py:62` sends `payload={"x": …, "y": …}`. Phase 4 replaces it (D-53).
4. **It degrades, which is what the league actually needs.** Against a peer whose reveal we
   cannot integrate — silent, late, or coordinate-free in a shape we do not accept — the *same*
   belief map runs on scent and hints alone and diffuses over turns. One implementation, two
   regimes:

   | Regime | Opponent's pre-turn cell | Belief map's job |
   |---|---|---|
   | **A** (reveal integrable) | known exactly | predict the *next* cell; supply an opponent-action prior and a sampled target |
   | **B** (reveal missing/opaque) | unknown | full 7×7 posterior from scent + hints, diffusing each turn |

**This is written up for the grader**, not buried: plan 04-13 produces
`docs/phases/phase-4/RULES-RESOLUTION-LANG.md` in the shape Phase 3 already set
(`docs/phases/phase-3/RULES-RESOLUTION.md`), quoting both sides and stating the choice.

**Honesty clause, to be stated in `docs/PRD_belief_map.md` and not smoothed over:** in Regime A
the believed-state substitution is the identity, so the belief map contributes nothing to move
*scoring* there. Its value in Regime A is (a) LANG-05 compliance, (b) the opponent-action prior,
(c) the deception channel that shapes **their** belief, (d) survival in Regime B.

### D-49 — scent is derived locally, never transmitted

§4.4 (p.29 / PDF 45) says each agent *"can sample the board and receive its opponent's scent
map."* In a refereeless P2P game there is no board to sample. We do **not** add a scent message.

**Rule 23 only makes sense under local derivation.** Locking the decay model
cryptographically is pointless if the numbers are transmitted — you would simply trust them.
It matters precisely because **both sides compute the field independently** and must agree.
§4.5's red box says exactly that: exchange the model *"together with the numeric example …
verify both sides interpret it identically, and only then lock the agreement cryptographically."*

Transmitting the field would also be self-defeating and rule-27-adjacent: `τ = 0.9` marks the
emitter's exact cell, so publishing it hands the opponent our position in numbers.

---

## 2. Decisions — D-32 … D-53

D-32 … D-47 are transcribed from `04-CONTEXT.md` `<decisions>`, not re-derived.
D-48 … D-53 are new, resolved from the book this session under the autonomy directive.

| ID | Decision | Source |
|----|----------|--------|
| **D-32** | Model **Claude Haiku 4.5** (`claude-haiku-4-5`) via the `anthropic` SDK. Model id is a **config value**; key from `ANTHROPIC_API_KEY` env only, never in source | CONTEXT |
| **D-33** | **Deterministic fallback, never stall.** Decode failure → hint is no-evidence (belief skips it); bluff failure → template bank. An API error may never crash or freeze a league game | CONTEXT |
| **D-34** | **Minimal gatekeeper built now.** Every LLM call goes through it: rate limit, token count, queue-not-crash. Phase 7 extends the same object for Gmail (QUAL-03, QUAL-05) | CONTEXT |
| **D-35** | **Token budget: count + degrade.** Cumulative tokens tracked against `[token budget per series]` (Table 18 row 4, ~200,000, negotiable); near the threshold degrade — shorter prompts, then template-only. **No mid-game hard stop.** Spend is reported | CONTEXT |
| **D-36** | **The algorithm decides `intent`.** Code picks `truth\|lie` and the informational payload; the LLM only phrases it. The flag is fixed **before the text exists** (rule 25, STRAT-07) | CONTEXT |
| **D-37** | **Thief: danger-adaptive lying.** Lie probability scales with estimated cop distance; truths sprinkled when safe so the lies stay credible. Thresholds from config | CONTEXT |
| **D-38** | **Cop: herding lies.** Lie to steer the thief toward barriers and corners the cop controls — optimised for driving movement, not for hiding | CONTEXT |
| **D-39** | **Bluff style is Claude's discretion**, leaning plausible-specific: concrete false statements consistent with the board | CONTEXT |
| **D-40** | **Hint trust: fixed config prior.** Hints enter the Bayes update with a likelihood weight **well below** scent's — scent cannot lie, words can | CONTEXT |
| **D-41** | **Decoder contract: region + confidence.** Constrained JSON — implicated cells/region, confidence, direction-of-motion if stated. Schema-invalid output → rejected → no-evidence | CONTEXT |
| **D-42** | **Scent fusion: likelihood field from trail age.** Sensed strength inverts the fixed decay law into "the opponent was here N turns ago", then the motion model projects to NOW. **Never chase the strongest cell directly** | CONTEXT |
| **D-43** | **Policy link: SAMPLE from the belief, not argmax.** The mover receives a belief-weighted sampled cell each turn. Phase 3's one-target-cell contract is unchanged; only the selection rule is stochastic. Seeded RNG so tests reproduce | CONTEXT |
| **D-44** | **Emit English, decode both.** Outgoing bluffs in English (unambiguous word counting); the decoder handles Hebrew **and** English, with Hebrew test fixtures | CONTEXT |
| **D-45** | **Word limit: validate + one retry + truncate.** Prompt demands it, code counts, one LLM retry on overflow, then truncate. Limit from `docs/PARAMETERS.md` Table 14 row 2 via config. Never send an illegal hint; never crash | CONTEXT |
| **D-46** | **Scent lock (rule 23) lands in Phase 4, not deferred.** Canonical JSON of the decay model → SHA-256, exchanged in the Phase-2 handshake **alongside** the config hash, using the same helper. Phase 6 folds it into the full audit | CONTEXT |
| **D-47** | **Hints ride the typed envelope** as a new `MessageType.HINT` with a free-text payload — no separate protocol shape (LANG-02) | CONTEXT |
| **D-48** | **The §5.3.2 / §6.4 contradiction is resolved in favour of a per-turn Reveal with a direction-token move**, position known one turn behind, belief map = one-turn-ahead predictive distribution, degrading to scent+hints-only in Regime B. Written up for the grader | §1 above; book preface p. v |
| **D-49** | **Scent is derived locally and never transmitted.** No scent message is added to the protocol | §1 above; §4.5 p.31 (PDF 47) |
| **D-50** | **The emission kernel is transcribed from Figure 4 (p.28 / PDF 44), not invented.** The 5×5 table is `0.04 / 0.14 / 0.20 / 0.42 / 0.62 / 0.90`, which reproduces `0.9·exp(−3d²/8)` (`d` = Euclidean distance from the emitting cell) to two decimals. **The kernel table, ρ, the window and a worked numeric example (`0.9 → 0.81`) all live inside the locked payload**, per §4.5's red box | §4.3 p.27 (PDF 43), Figure 4 |
| **D-51** | **Hint reliability becomes a bounded adaptive coefficient. This is a DISCLOSED REVISION of D-40's "fixed" framing, taken under the autonomy directive — not a pure extension.** D-40's *mechanical* content survives intact: the fixed config weight `w` still holds hints below scent, and it is still fixed. What changes is the thing D-40 *titled* "hint trust": the book's own trust/reliability coefficient, which §4.4 (p.30 / PDF 46) shows being **lowered when a hint contradicts the scent field** — declared "I moved north", expected `(1−ρ)·0.9 ≈ 0.81` there, measured `0.00` ⇒ *"The cop concludes with high confidence that the thief is lying. It lowers the trust coefficient it assigns to that opponent's verbal declarations."* A constant coefficient would leave the book's most concrete worked mechanism unimplemented. **Because a reader comparing `04-CONTEXT.md` to the shipped code would otherwise see a locked decision walked back silently, 04-13 states the revision in `PRD_belief_map.md` and `RULES-RESOLUTION-LANG.md` as a revision** | §4.4, §6.4; autonomy directive |
| **D-52** | **Provider abstraction with four documented slots, two shipped.** §6.5.1 (p.50 / PDF 66) names `template` (default, zero tokens), `ollama`, `claude_api`, `claude_cli`, plus `every_n_steps` for cost control. We ship **`template`** (always-available fallback, D-33) and **`claude_api`** (our default, D-32); `ollama` and `claude_cli` are registry extension points, not code. `every_n_steps` defaults to **1** because the §10.4 gate requires a hint **every** turn | §6.5.1 |
| **D-53** | **Outgoing move payload becomes a direction token; incoming accepts a direction token *or* Phase-2 coordinates.** Rule 27 is satisfied on our side with zero interop risk against a peer still speaking `{x,y}` | rule 27; KHALED_PERSONAL_PLAN.md:437 |

**Not in scope and not to be smuggled in:** tunnelling (Phase 5), commit-reveal / nonce / Step-0
(Phase 6 — only the *scent digest* lands here, D-46), Gmail and the GUI (Phase 7), and the
§6.5.1 beige-box "LLM-based tactics by mutual agreement" (the book's default and ours stays
algorithmic — rule 25 is treated as hard, per `RULES-RESOLUTION.md` §8).

---

## 3. Fixed numbers — every one of them sourced

No plan may introduce a number not in this table or already in `docs/PARAMETERS.md`.

| Value | Number | Status | Source |
|---|---|---|---|
| Scent strength at source | **0.9** | **fixed** | PARAMETERS Table 16 row 1 |
| Scent decay rate ρ | **0.10** per turn | **fixed** | Table 16 row 2 |
| Scent field size | **5×5** | **fixed** | Table 16 row 3 |
| Emission kernel (5×5) | `0.04 0.14 0.20 0.14 0.04 / 0.14 0.42 0.62 0.42 0.14 / 0.20 0.62 0.90 0.62 0.20 / …` | **transcribed** | Figure 4, p.28 (PDF 44) — D-50 |
| Decay law | `τ(t+1) = max(0, (1−ρ)·τ(t) + Δτ)` | **fixed** | §4.3 p.27 (PDF 43) |
| Worked lock example | `0.9 → 0.9·(1−ρ) = 0.81` | **fixed** | §4.5 red box p.31 (PDF 47) |
| Hint word limit | **15** | negotiable | Table 14 row 2 |
| Game arena | **New York** (`""` ⇒ generic cues) | negotiable | Table 14 row 1 |
| Token budget per series | **~200,000** | negotiable | Table 18 row 4 |
| Gatekeeper: req/min · parallel · wait-after-error · retries · queue depth | 30 · 2 · 5 s · 3 · 100 | **minimum** | Table 19 |
| Token-bucket law | `tokens ← min(C, tokens + r·Δt)`, allow iff `tokens ≥ 1` | — | Table 19 |
| Board size · move ceiling · survival threshold | 7×7 · 35 · 35 | minimum | Table 13/15 (already in `game_params.json`) |

**Everything else is an engineering default in config** and must be labelled as such — fusion
weights, the reliability prior and its bounds, lie-probability thresholds, `every_n_steps`,
`max_tokens`, the degrade ladder. D-18's numeric-sourcing discipline stays in force.

---

## 4. Where the code goes, and the structural proof of rule 25

`scripts/check_no_llm_in_strategy.py` already fails CI if anything under
`src/pursuit/strategy/` imports `anthropic`, `openai`, `google.generativeai`, `cohere`, or a
networking module. **Phase 4 leans on that guard rather than on a promise.**

```
src/pursuit/strategy/          ← ALGORITHM. no LLM import, ever (CI-enforced)
  scent.py                     kernel + decay law            (04-01)
  scentfield.py                per-agent field, local derivation (04-01)
  belief.py                    grid, predict, normalise      (04-05)
  belief_motion.py             legal-action motion model     (04-05)
  belief_scent.py              scent likelihood (D-42)       (04-05)
  belief_hint.py               hint likelihood (D-40)        (04-09)
  reliability.py               adaptive coefficient (D-51)   (04-09)
  scent_check.py               §4.4 contradiction test       (04-09)
  deception.py                 intent + payload (D-36/37/38) (04-08)
  beliefadapter.py             sample → obs/state (D-43)     (04-11)

src/pursuit/services/llm/      ← LANGUAGE ONLY. never returns a move
  gatekeeper.py                token bucket, queue, budget   (04-03)
  bucket.py / budget.py        Table 19 law, D-35 ladder     (04-03)
  provider.py                  registry + protocol           (04-06)
  template_provider.py         zero-token fallback (D-52)    (04-06)
  anthropic_provider.py        claude_api / Haiku 4.5        (04-06)
  decode.py                    hint → JSON inference (D-41)  (04-07)
  bluff.py                     payload → ≤15 words (D-45)    (04-10)
  hintbank.py                  template fallback bank        (04-10)

src/pursuit/network/           ← TRANSPORT
  envelope.py                  + MessageType.HINT            (04-04)
  tools.py                     + receive_hint                (04-04)
  move_payload.py              direction-token codec (D-53)  (04-04)
  turn_actions.py              direction move + hint         (04-04, 04-12)
  handshake_wire.py            + scent digest key            (04-02)
```

### Four negotiated config blocks, one owner each

| File + loader | Key enum | Created by | Extended by |
|---|---|---|---|
| `config/{role}/scent.json` · `shared/scent_config.py` | `ScentKey` | 04-01 | — |
| `config/{role}/language.json` · `shared/language_config.py` | `LanguageKey` | 04-03 | 04-06 |
| `config/{role}/belief.json` · `shared/belief_config.py` | `BeliefKey` | 04-05 | 04-09, 04-11 |
| `config/{role}/deception.json` · `shared/deception_config.py` | `DeceptionKey` | 04-08 | 04-10 |

Three consequences, all deliberate:

1. **They are separate negotiated blocks, not fields in `game_params.json`** — exactly the pattern
   `resolution.json` established, for the reason recorded in `RULES-RESOLUTION.md` §5: rule 11
   requires `game_params.json` to be byte-identical with a book-faithful peer, so adding fields
   there would abort every game before move 1.
2. **The key enums live beside their loaders in `shared/`, not in `config_keys.py`.**
   `config_keys.py` is already **90 of its 150 permitted lines**; four more enums would breach the
   hard limit the pre-commit hook enforces. The standing rule is *split files, never compress code
   to fit* — so each enum ships in the module that validates it. Note the deviation from the
   existing convention in each loader's docstring.
3. **Every plan owns exactly one config file exclusively, and each extender depends on its
   creator.** That is what makes the wave labels below honest: no two plans in one wave touch the
   same file.

---

## 5. Plans and waves

| Plan | Delivers | Wave | Depends on |
|---|---|---|---|
| **04-01** | Locked scent model — kernel table, decay law, `ScentField`, `scent.json`, digest helper | 1 | — |
| **04-03** | LLM gatekeeper — token bucket, FIFO overflow queue, cumulative budget + degrade ladder | 1 | — |
| **04-04** | Transport — `MessageType.HINT`, `receive_hint`, direction-token move out / both-shapes in | 1 | — |
| **04-02** | Handshake carries the scent digest beside the config digest (D-46, rule 23) | 2 | 04-01 |
| **04-05** | Belief map core — grid, motion/predict, scent likelihood, normalise, Regime A/B | 2 | 04-01 |
| **04-06** | Provider layer — registry, `template`, `claude_api` (Haiku 4.5), `every_n_steps` | 2 | 04-03 |
| **04-07** | Hint decoder — constrained JSON, EN + HE, invalid → no-evidence | 3 | 04-06 |
| **04-08** | Deception policy — intent + payload, cop herding / thief danger-adaptive | 3 | 04-05 |
| **04-09** | Belief fusion — hint likelihood, adaptive reliability, scent-contradiction detection | 4 | 04-05, 04-07 |
| **04-10** | Bluff generator — word limit, retry, truncate, NYC cues, template bank | 4 | 04-06, 04-08 |
| **04-11** | `BeliefAdapter` — sample from belief, believed-state substitution, seeded RNG | 5 | 04-09 |
| **04-12** | Turn-pipeline integration in §6.2 Figure 7 order + integration tests | 6 | 04-02, 04-04, 04-10, 04-11 |
| **04-13** | `PRD_scent_map` · `PRD_belief_map` · `PRD_deception` · `RULES-RESOLUTION-LANG` · phase triplet · graph refresh | **7** | 04-12 |
| **04-14** | GATE-4 measurement and the phase verdict | **8** | 04-12, 04-13 |

```
w1: 04-01      04-03      04-04
      |    \     |
w2: 04-02   04-05        04-06        (04-06 ← 04-03)
              |            |
w3:        04-08         04-07
              |            |
w4:        04-10 ← ← ← ← 04-09        (04-10 ← 04-06+04-08; 04-09 ← 04-05+04-07)
                           |
w5:                     04-11
                           |
w6:                     04-12         (← 04-02, 04-04, 04-10, 04-11)
                           |
w7:                     04-13
                           |
w8:                     04-14
```

**Two wave-graph rules this satisfies, both checked rather than assumed:**

1. **A plan is never in the same wave as something it depends on.** 04-13 depends on 04-12 and is
   therefore wave 7, not 6; 04-14 follows at wave 8. 04-13 needs all twelve prior `SUMMARY.md`
   files *and* needs 04-04's placeholder hint already deleted by 04-12 — neither is guaranteed
   inside a shared wave.
2. **No two plans in one wave modify the same file.** The four-block config split above is what
   buys this: each extender (04-06, 04-09, 04-10, 04-11) already depends on its block's creator,
   so the writes are ordered by the graph rather than by luck.

## 6. Decision → plan coverage trace

Every `D-NN` below must appear in at least one plan's `must_haves` block — the §13a
decision-coverage gate greps `must_haves` only, never task bodies ([[decision-coverage-gate-scans-must-haves]]).

| Plan | Owns |
|---|---|
| 04-01 | D-46 (payload), D-49, D-50 |
| 04-02 | D-46 |
| 04-03 | D-34, D-35 |
| 04-04 | D-47, D-53 |
| 04-05 | D-42, D-48 |
| 04-06 | D-32, D-33, D-52 |
| 04-07 | D-41, D-44 |
| 04-08 | D-36, D-37, D-38 (+ D-43, D-51 by cross-reference) |
| 04-09 | D-40, D-51 |
| 04-10 | D-33, D-39, D-45 (+ D-36, D-44) |
| 04-11 | D-43, D-48 |
| 04-12 | D-48, D-53 (+ D-33) |
| 04-13 | D-48, D-49 |
| 04-14 | measurement only (+ D-32, the live-API run) |

Verified after writing: all 22 of D-32 … D-53 appear in at least one plan's `must_haves`.

## 7. Requirement coverage

| REQ | Landed by |
|---|---|
| LANG-01 ≤15-word free-text hint each turn | 04-10, 04-12 |
| LANG-02 natural language only, no coordinates in the protocol | 04-04, 04-12 |
| LANG-03 hints may lie; `intent` committed in advance | 04-08 |
| LANG-04 scent 0.9 / 0.10 / 5×5 | 04-01 |
| LANG-05 Bayesian belief map from scent + hints | 04-05, 04-09 |
| LANG-06 LLM decodes hints and writes bluffs | 04-06, 04-07, 04-10 |
| LANG-07 decay model cryptographically locked pre-game | 04-01, 04-02 |
| STRAT-07 / rule 25 the LLM never chooses the move | structural (§4) + 04-08 |
| QUAL-03 / QUAL-05 gatekeeper on every external call, queue never crashes | 04-03 |
| DOC-01 per-mechanism PRDs + phase triplet | 04-13 |

## 8. §10.4 gate — what 04-14 must measure

1. **A hint becomes an inference.** A seeded game log shows a decoded hint changing the belief
   map's posterior, with before/after mass reported. A schema-invalid hint changes nothing.
2. **The scent map updates and decays.** Assert the decay law numerically over ≥ 10 turns
   against the locked table, and assert both peers' digests matched at handshake.
3. **The LLM emits a ≤15-word hint every turn, true and false.** Over a full 35-turn game:
   every turn carries a hint, every hint ≤ the configured limit, both `intent` values occur,
   and the `intent` flag is fixed before the text is generated.
4. **Robustness, not in the book's gate but in the league's reality:** a game completes with the
   API key unset (template-only path) and with a forced API error on every call (D-33).
