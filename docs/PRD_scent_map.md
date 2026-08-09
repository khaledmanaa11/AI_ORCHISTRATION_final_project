# PRD — the scent model (dynamic pheromones)

**Mechanism:** how each agent emits, decays, and locally reads its own and its reconstructed
opponent's pheromone trail — the non-verbal half of Phase 4's information channel.
**Status:** implemented (plan 04-01, extended by 04-02/04-05/04-09) · **Segal §2.3:** every
algorithm or central mechanism carries its own PRD. This is that document.
**Rules note:** [`docs/phases/phase-4/RULES-RESOLUTION-LANG.md`](phases/phase-4/RULES-RESOLUTION-LANG.md)
D-49 records why the field is derived locally and never transmitted.

---

## 1. The problem this mechanism solves

§4.1–4.3 of the book (pp. 24–27, PDF 40–43) describe each agent leaving a decaying pheromone
trail as it moves, which the opponent can sense as indirect evidence of where it has recently
been. Two constraints make this more than a cosmetic flavour mechanic:

- **Rule 23 requires the decay model to be cryptographically locked before the game starts** —
  any deviation in the formula voids the game. That is only enforceable if both sides compute
  the *same* field from the *same* locked numbers.
- **The field must never leak the emitter's exact position over the wire.** `τ = 0.9` at the
  source cell is, numerically, a coordinate in disguise; the field has to be reconstructed
  locally by each side, not transmitted (D-49).

## 2. The locked model — every number sourced

All three parameters are **fixed** by the book's own Appendix ו (PARAMETERS.md Table 16) —
deviation in any one of them voids the game (rule 23):

| # | Parameter | Value | Status | Source |
|---|---|---|---|---|
| 1 | Scent strength at source | **0.9** | **fixed** | Table 16 row 1 |
| 2 | Scent decay rate ρ | **0.10** per turn | **fixed** | Table 16 row 2 |
| 3 | Scent field size (emission window) | **5×5** | **fixed** | Table 16 row 3 |

### The emission kernel — transcribed, not invented (D-50)

Figure 4 (book p.28, PDF 44) draws the 5×5 emission window as a table of values around the
emitting cell. `src/pursuit/shared/scent_kernel.py` ships this table verbatim:

```
0.04  0.14  0.20  0.14  0.04
0.14  0.42  0.62  0.42  0.14
0.20  0.62  0.90  0.62  0.20
0.14  0.42  0.62  0.42  0.14
0.04  0.14  0.20  0.14  0.04
```

This reproduces `0.9 · exp(−3d² / 8)` (`d` = Euclidean distance from the emitting cell, at the
centre) to two decimals — that closed form is an **observation** about the transcribed table
used to sanity-check it at load time, not a second, independently book-given formula. The kernel
is symmetric on all four axes and its centre cell equals the source strength (0.9) exactly; both
are asserted by `shared/scent_kernel.py`'s own validation, which runs every time the config is
loaded, on both sides.

### The decay law

> **§4.3, book p.27 (PDF 43):** `τ(t+1) = max(0, (1−ρ)·τ(t) + Δτ)`

Implemented in `strategy/scent.py` as three pure functions: `emission()` (apply the kernel around
a newly-occupied cell), `decay()` (one step of the law above), and
`expected_strength_after(model, n)` (the closed-form projection used by the belief map's
scent-likelihood inversion, D-42 — see [`docs/PRD_belief_map.md`](PRD_belief_map.md) §3). All
three are edge-clipped (a kernel cell off the board contributes nothing) and epsilon-pruned (a
cell whose strength decays below a configured floor is dropped from the trail dict rather than
kept as a vanishing float forever).

### The worked lock example

> **§4.5 red box, book p.31 (PDF 47):** `0.9 → 0.9·(1−0.10) = 0.81`

`shared/scent_kernel.py`'s `check_worked_example()` **recomputes** this from the config's own
`source`/`decay` fields and asserts it matches `0.81` at load time — the example is not merely
stored as a comment, it is a live self-consistency check that fails loud if the shipped numbers
ever drift.

## 3. The locked payload and the digest — rule 23 in code

§4.5's red box requires exchanging the model *"together with the numeric example... verify both
sides interpret it identically, and only then lock the agreement cryptographically."*
`config/police/scent.json` and `config/thief/scent.json` are byte-identical and carry all four
elements together: the kernel table, ρ, the window, and the worked example. `scent_digest()`
(`shared/scent_config.py`) canonically re-serializes the loaded model
(`sort_keys=True, separators=(",", ":")`, the same canonicalisation `config_hash.py` uses
project-wide) and SHA-256-hashes it.

**The shipped digest, verbatim, for a league opponent to match:**

```
c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e
```

Plan 04-02 carries this digest as a second key (`HandshakeKey.SCENT_DIGEST`) inside the existing
Phase-2 handshake offer, alongside the config digest. `handshake_evaluate.py::evaluate()` checks
config first, then scent, using `secrets.compare_digest` (never `==`) via the shared
`compare_named_digest()` helper. Four outcomes are tested end to end: both agree → `AGREED`;
config differs → `CONFIG_MISMATCH` named; scent differs → `SCENT_MISMATCH` named; the peer's
payload omits the key entirely → `SCENT_MISMATCH` worded "absent". Any mismatch aborts to
`State.ERROR` before move 1 on **both** sides — `perform_handshake` and `respond_to_handshake`
share one evaluation call site, so a peer cannot pass one digest and silently fail the other.

## 4. Why the field is derived locally, never transmitted (D-49)

§4.4 (book p.29, PDF 45) describes an agent that *"can sample the board and receive its
opponent's scent map"* — a framing that presumes a referee or a shared board to sample from. This
project has neither: it is refereeless P2P (rule 1/2). **No scent message is added to the
protocol.** Each side's `ScentField` (`strategy/scentfield.py`) holds two independent grids —
`own` (this agent's real trail, updated by its own moves) and `opponent` (this agent's local
*reconstruction* of the opponent's trail, built from whatever it legitimately observes: revealed
moves in Regime A, or the belief posterior's `emit_opponent(cell, weight)` calls in Regime B). No
process ever reads the other side's `own` grid — the two grids are never shared objects, never a
module-level singleton, and never cross a process boundary (rule 2).

**Rule 23 only has a purpose under this reading.** Locking the decay formula cryptographically is
pointless if the numbers themselves are simply handed over on the wire — a receiver would trust
whatever arrived without needing to compute anything. It matters exactly because **both sides
compute the field independently from the same locked model** and must agree byte-for-byte with no
opportunity to paper over silent divergence; that is what the §3 handshake digest actually
verifies. Full argument, both sides of the book's own apparent tension, and the two other
deliberate deviations this phase discloses: see
[`docs/phases/phase-4/RULES-RESOLUTION-LANG.md`](phases/phase-4/RULES-RESOLUTION-LANG.md) D-49.

Publishing the raw field would also be self-defeating: `τ = 0.9` marks the emitter's exact cell.
A transmitted field would hand the opponent a numeric fix on our position through a side channel
— the exact leak rule 27 forbids on the primary channel, reproduced here by another route.

## 5. `ScentField` — the object every later mechanism reads

`emit_own(cell)` / `emit_opponent(cell, weight=1.0)` apply the kernel; `advance()` applies one
decay step to both grids (called exactly once per resolved joint turn, centrally, by
`network/turn_resolve.maybe_resolve()` — plan 04-12 — never per-decision, so the trail cannot be
advanced twice or skipped in a turn where either side is slow); `strength(grid_name, cell)` and
`freshest(grid_name)` read it back, validated against an explicit `('own', 'opponent')` allow-list
rather than `getattr` so an unknown grid name fails loud. `emit_opponent`'s single primitive
serves **both** belief regimes without `ScentField` ever deciding which one applies: Regime A
calls it once at full weight for an exactly revealed cell; Regime B calls it once per
`(cell, probability)` pair in the belief's posterior (`strategy/belief_hint.py` /
`strategy/beliefadapter.py`, plan 04-11).

## 6. Compliance

- **Rule 23** — the decay model is cryptographically locked before the game starts, verified
  each handshake, aborting on any mismatch. Enforced end to end by plans 04-01/04-02, tested by
  `tests/unit/test_handshake_scent.py`.
- **Rule 2 / D-49** — no shared runtime object between the cop and thief processes; each
  `ScentField` is a fresh, process-local instance, and no scent message exists on the wire.
- **Rule 27** — the field is never serialized onto the network in any form.
- **Segal Table 5** — every source file ≤150 code lines (the original single-file draft of
  `scent_config.py` was split into `scent_config.py` + `scent_kernel.py` at the ceiling rather
  than compressed); zero hardcoded values (every number in `scent.py`/`scentfield.py` is read
  from the loaded `ScentModel`, never a literal).

## 7. Acceptance criteria and links to the plans that built it

| Criterion | Measured by |
|---|---|
| Kernel, ρ, source, window match Table 16 and Figure 4 exactly | `tests/unit/test_scent_config.py`, `tests/unit/strategy/test_scent.py` |
| Decay law matches §4.3 and the §4.5 worked example self-checks at load | `shared/scent_kernel.py::check_worked_example`, `tests/unit/strategy/test_scent.py` |
| Both role configs byte-identical, one stable digest | `tests/unit/test_scent_config.py` (`cmp`-equivalent test) |
| Handshake enforces the lock, aborts on mismatch, names which commitment broke | `tests/unit/test_handshake_scent.py` (4 required cases + mutated-kernel end-to-end) |
| No cross-process shared state, no scent message on the wire | `scripts/check_no_llm_in_strategy.py`'s import-boundary discipline + `ScentField`'s own construction (fresh instance per process) |

**Built by:** plan 04-01 (locked model, `ScentField`, digest helper), plan 04-02 (handshake
carries the digest), plan 04-05 (scent-likelihood inversion consumes `expected_strength_after`),
plan 04-09 (`scent_check.contradicts()` reuses the same closed form for the §4.4 lie detector —
see [`docs/PRD_belief_map.md`](PRD_belief_map.md) §5).

**Requirements covered:** LANG-04 (0.9/0.10/5×5 exact), LANG-07 (decay model cryptographically
locked pre-game).

---

*Phase: 04-language-and-scent · Numbers traced to 04-01-SUMMARY.md, 04-02-SUMMARY.md.*
