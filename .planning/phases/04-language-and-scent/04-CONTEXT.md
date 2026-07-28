# Phase 4: Language and Scent - Context

**Gathered:** 2026-07-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers the information war: a **≤15-word free-text hint** each turn (may be a
lie; `intent` flag `truth|lie` committed in advance), the **involuntary scent trail**
(strength 0.9 at source, 0.10 decay/turn, 5×5 window — **all fixed values**), a
**Bayesian belief map** fusing scent + hint evidence, and the **LLM in exactly two
places** — decoding incoming hints, phrasing outgoing bluffs — never choosing moves
(LANG-01…LANG-07, rule 25).

Out of scope: tunneling (Phase 5), full commit-reveal crypto (Phase 6 — but see the
scent-lock decision below), Gmail reporting/GUI (Phase 7).

**Planning-day note:** run `/gsd:ai-integration-phase 4` (**strongly recommended** — this
is the real LLM-integration phase: eval strategy, guardrails, failure modes) before
`/gsd:plan-phase 4 --chunked`. Refresh the graph (`/gsd:graphify`) first (task 04-96).

**Researcher question (resolve from RULES.md/the book before planning):** what exactly is
revealed per turn vs at game end? PROJECT_GUIDE.md says the per-turn Reveal sends "the
actual move and hint", yet belief/scent/deception presuppose hidden positions, and
LANG-02 bans coordinates in the open channel. The belief-map design depends on the
answer.

</domain>

<decisions>
## Implementation Decisions

### LLM integration
- **Model: Claude Haiku 4.5** (`claude-haiku-4-5-20251001`) via the `anthropic` SDK —
  model name is a config value; key from `ANTHROPIC_API_KEY` env var only.
- **Deterministic fallback, never stall**: decode failure → hint treated as no-evidence
  (belief update skips it); bluff failure → emit from a small template hint bank. An API
  error can never crash or freeze a league game.
- **Minimal gatekeeper built NOW** (Phase 4): every LLM call goes through it — rate
  limiting, token counting, queue-not-crash. Phase 7 extends the same gatekeeper for
  Gmail. (QUAL rule: every external call through the gatekeeper.)
- **Token budget: count + degrade**: gatekeeper tracks cumulative tokens against the
  ~200k/series budget (config); near the threshold it degrades gracefully — shorter
  prompts, then template-only hints. No mid-game hard stop. Spend is reported (league
  rule).

### Deception policy (algorithm-owned)
- **Algorithm decides intent**: the deception policy (code, config-driven) picks
  `truth|lie` and the informational payload; the LLM only phrases it. The intent flag is
  committed before the text exists. The LLM never makes a game decision (rule 25).
- **Thief: danger-adaptive lying** — lie probability scales with estimated cop distance
  (threshold + probabilities from config); sprinkle truths when safe to keep lies
  credible.
- **Cop: herding lies** — lie to steer the thief toward barriers/corners the cop
  controls; adaptive, optimized for driving movement rather than hiding.
- **Bluff style: Claude's discretion** (prompt-design question). Leaning
  plausible-specific — concrete false statements consistent with the board — but Claude
  owns the style guide.

### Belief map & evidence fusion
- **Hint trust: fixed discount weight** — hints enter the Bayes update with a
  config-tunable likelihood weight well below scent's (scent can't lie; words can).
- **Decoder contract: region + confidence** — constrained JSON output: implicated
  cells/region, confidence score, direction-of-motion if stated. Schema-invalid LLM
  output → rejected → treated as no-evidence.
- **Scent fusion: likelihood field from trail age** — sensed strength inverts the fixed
  decay law into "opponent was here N turns ago" (0.9 − 0.10·age), then the motion model
  projects to NOW. Never chase the strongest cell directly.
- **Policy link: SAMPLE from belief (user's explicit choice over argmax)** — the
  Q-policy receives a belief-weighted sampled cell each turn. Phase 3's "one target
  cell" contract is unchanged; only the selection rule is stochastic. Use a seeded RNG
  so tests are reproducible.

### Hint mechanics & scent lock
- **Language: emit English, decode both** — outgoing bluffs in English (unambiguous word
  counting); the decoder handles Hebrew AND English input, with Hebrew test fixtures.
- **Word limit: validate + retry + truncate** — prompt demands the limit, code counts,
  one LLM retry on overflow, then truncate. Limit value from PARAMETERS.md via config.
  Never send an illegal hint; never crash.
- **Scent lock (rule 23) in Phase 4, not deferred**: canonical-JSON of the decay model
  `{source: 0.9, decay: 0.10, window: 5}` → SHA-256, exchanged in the Phase-2 handshake
  alongside the config hash. Phase 6 folds it into the full audit; same hashing helper.
- **Hints ride the typed envelope** as new `type=hint` messages with free-text payload —
  no separate protocol shape. Coordinates progressively leave the open channel per
  LANG-02.

### Claude's Discretion
- Bluff style guide and both LLM prompts (decode + bluff)
- Template hint bank contents (fallback bluffs)
- Exact fusion weights / decode-confidence handling — config values, tuned in test games
- Module/file layout within the 150-line limit; test structure (all LLM calls mocked)

</decisions>

<specifics>
## Specific Ideas

- Scent parameters 0.9 / 0.10 / 5×5 are **fixed** by PARAMETERS.md — deviation voids the
  game; they appear only in config, referenced from the locked model hash.
- Per-mechanism PRDs due this phase (task 04-04): `PRD_scent_map.md`,
  `PRD_belief_map.md`, `PRD_deception.md`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-language-and-scent*
*Context gathered: 2026-07-28*
