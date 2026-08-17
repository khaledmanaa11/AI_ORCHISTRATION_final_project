# PRD — Display Belief (rules 8–9 publication owner)

**Mechanism:** `src/pursuit/strategy/display_belief.py`
**Owning plan:** 07-11 · **Status:** implemented · **Version:** 1.00
**Governs:** what a `LocalView` is allowed to publish about the opponent's position.

---

## 1. Problem

Rule 9 (`docs/RULES.md:30`) makes displaying the objective board state in the live
interface a **project disqualification**; `RULES.md:115` ranks it third among the cheapest
ways to score zero. 07-03 built a firewall against it: `sdk/local_view.py` is a closed set
of frozen dataclasses that cannot carry a `GameState`, and `tests/unit/test_local_view_firewall.py`
proves the opponent's true cell never appears as a *value* in a serialised view.

**That firewall asked the wrong question, and passed.** A heatmap does not have to print a
coordinate to display one. An adversarial pass over 07-03 measured the following end to
end, through the shipped code path, with the real `config/police/*.json`:

| Channel | Measured at HEAD | Recovers the truth? |
|---|---|---|
| `belief.argmax` | `(5, 3)` | directly |
| `belief.rows` support | `[(4,3),(5,2),(5,3),(5,4),(6,3)]` — 5 of 49, P(true) 0.5556 | by geometric inversion → `[(5, 3)]` |
| `scent.opponent` argmax | `(5, 3)` at value `0.9` | directly; 0.9 is exactly `scent.json`'s `"source"`, the unmixed kernel centre |
| sealed thief (2 barriers, quota 14) | `argmax (0,0)`, `entropy -0.0`, lit cells `[(0,0,1.0)]` | a one-pixel heatmap painted on the truth |

### 1.1 The chain

`turn_language.py:57` returns `ctx.state.thief` as `known_cell` on every cop turn > 0 →
`choose_destination` (`turn_language.py:86-88`) passes it to `BeliefAdapter.decide` →
`beliefadapter.py` calls `observe_exact(known_cell)` **and** `emit_opponent(known_cell)` →
`belief.py:57` sets a hard 1.0/0.0 delta on that cell.

`belief_motion.spread:52-66` then disperses that delta over exactly that cell's legal
destinations, and `belief.py:80` multiplies pointwise, so a zeroed cell never reopens. The
published support is therefore *precisely* the legal-move **plus** centred on the true
pre-move cell — and the centre of a plus is uniquely recoverable.

### 1.2 Why nobody owned it

`beliefadapter.py`'s own docstring said `state` keeps carrying the true joint position
because *"rule 3's 'local truth' is a display-layer concern, not this one's"* — the
strategy layer handed rule 9 to the display layer, and the display layer
(`sdk/view_builder._belief_view`) published the value unredacted. Both delegated; neither
owned. This mechanism ends that: rule 9 is decided in **one** module, in writing.

### 1.3 The obvious fix is a trap

Deleting `BeliefView.argmax` makes 07-03's `coordinate_hits` scanner return `[]` — a clean
verdict with the leak fully intact, because the support still inverts. Any fix validated
by a coordinate-absence test will look successful and will not be.
`test_local_truth_recovery.test_the_argmax_only_fix_would_still_leak` pins this permanently.

---

## 2. Decision: option (a), not option (b)

Two options were on the table.

| | Option (a) — **chosen** | Option (b) — rejected |
|---|---|---|
| Mechanism | A display-only `BeliefMap`, never fed `ctx.state.thief`, published in place of the strategy map | Publish the strategy belief only on turns where `observe_exact` did not fire; placeholder otherwise |
| Cop-side result | A real, honestly-derived heatmap on every turn | A **permanently blank panel**: `turn_language.py:57` returns the true cell whenever `turn > 0`, so `observe_exact` fires on every turn but turn 0 |
| Honesty | Publishes what a peer that ignored the Reveal would believe | Hides the leak by deleting the feature |
| Grader-facing | A working belief panel | An empty box for the whole game |

**Option (b) is not a redaction policy, it is the removal of the panel.** Option (a) was
chosen for that reason.

### 2.1 What the display belief is fed

| Input | Fed? | Why |
|---|---|---|
| Legal-motion `predict` (`belief_motion.spread`) | yes | the movement rules are public |
| Declared barriers | yes | rule 22 — barriers are declared on the wire, shared knowledge |
| Decoded hint likelihood | yes | the opponent's own broadcast claim, possibly a lie; believing it is our mistake to make |
| `observe_exact(known_cell)` | **never** | this is the leak |
| `scent_likelihood` over `ctx.scent_field` | **never** | that grid is stamped by `emit_opponent(known_cell)` from the engine's answer; feeding it back re-imports the truth through the side door |
| Its own reconstructed trail | **never** | circular — its own emission returning as evidence for itself |

### 2.2 The strategy belief is untouched

`BeliefAdapter.belief` still receives `known_cell` and still collapses to a delta. The
provenance is protocol-legitimate — the opponent's own honest Reveal, folded in by
`turn_resolve` — and **rule 9 governs the display, not the provenance**. Play is not
degraded: measured after the fix, the strategy map's argmax is still `(5, 3)` with entropy
1.88 while the *published* map reads argmax `(1, 3)`, entropy 5.5469, support 47 of 49.

### 2.3 Scent is fixed too, because it leaks independently

`emit_opponent(known_cell)` stamps the kernel at full source strength. Decay is a uniform
scalar, so **two consecutive published snapshots subtract to recover the fresh deposit** —
an animate-only GUI would leak every turn. The published `opponent` grid is therefore
emitted from the *display* belief. The `own` grid is passed through exactly as it is: it is
local truth by definition, which is what rule 8 asks for.

### 2.4 Cop seat only — by provenance, not by role name

The substitution fires on `DisplayBelief.contaminated`, set the first time an exact
observation is taken — never on a hard-coded `"cop"`. The thief never calls `observe_exact`
(`turn_language.py:58` returns `ctx.pending_cop_action.move`, which is `None` at its decide
point on every turn under commit-reveal, `"commit_reveal": true` in **both**
`config/police/security.json` and `config/thief/security.json`), so its genuinely
multi-modal belief is published untouched — verified byte-identical before and after,
sha256 `0b046a9430b79af3d1b7f3a58a4bf91ffdce383d739d3d5267f3e03e1ba0e3b0`.

Keying on provenance rather than on the role name also covers any future path that *did*
hand the thief an exact cell, without anyone having to remember to come back here.

---

## 3. The floors (`belief.json` → `display`)

A guard, not the mechanism. The honest pipeline has no way to reach a delta — the hint
likelihood mixes with uniform and can never zero a cell — so these are expected to hold on
every turn of every game. They exist because *"expected to"* is what the leaked path was
also true of, and because a floor that is never checked is not a floor.

| Field | Value | Derivation (never invented — CLAUDE.md rule 1, D-18 discipline) |
|---|---|---|
| `min_support_cells` | 6 | One cell's legal destination set is STAY plus four orthogonal moves = `len(DIRECTION_WORDS)` = 5. A support of 6+ cannot fit inside any single cell's step neighbourhood, so the geometric inversion returns `[]` — structurally impossible, not merely unlikely. |
| `min_entropy_bits` | 1.0 | One full bit is the entropy of a fair coin between two cells. Below that the map effectively *names* a cell whatever its support size. |

`display_config.validate_display_floors` refuses a `min_support_cells` at or below
`MAX_STEP_NEIGHBOURHOOD`: a floor that admits the measured leak is not a floor.

When the floors are breached, `published_belief` returns `None` and `published_scent`
returns the own trail with an empty opponent grid. `view_builder` renders `belief=None` —
the same honest "no belief to show" a disabled belief layer already produces, never a
fabricated stand-in.

---

## 4. Test plan

| Test | Question |
|---|---|
| `tests/unit/test_local_truth_recovery.py` | Can the true cell be **recovered** — by argmax, by scent peak, by geometric inversion, or below the floors? Includes the sealed-thief endgame. |
| ↳ `test_the_inversion_attack_is_not_a_no_op` | Anti-vacuity: the identical inversion, on the support HEAD actually produced, returns the true cell and only it. |
| ↳ `test_the_argmax_only_fix_would_still_leak` | The trap, pinned: an argmax-only fix earns a clean scanner verdict and still fails the geometric test. |
| `tests/unit/strategy/test_display_belief.py` | The floor guard fires; the uncontaminated seat is passed through identically; the display map never takes an exact observation. |
| `tests/unit/test_local_view_firewall.py` | 07-03's field-set/absence half, unchanged in intent — it asks a different question and neither file replaces the other. |

## 5. Out of scope

`network/turn_language.belief_snapshot` still writes the true argmax to the JSONL event
log. That is **correct**: the log is the audit record (rule 38), not the live interface, and
rules 8–9 govern the live interface. **07-08's replay viewer must not render it live** —
filed in `deferred-items.md`.
