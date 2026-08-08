# Simultaneous-turn resolution contract

**Status:** binding · **Date:** 2026-08-08 · **Supersedes:** D-12 (sequential turn order)
**Source:** `police_thief_p2p.pdf` (Segal, book v3.0.0), read directly. **PDF page = book page + 16.**

This document pins every predicate the engine needs to resolve one *joint* turn. Each row is
either **BOOK** (quoted, not negotiable) or **NEGOTIATED** (undefined by the book, agreed with
the opponent before move 1 under §3.2). Nothing here is inferred silently.

---

## 1. Why the turn is simultaneous

The engine resolved turns sequentially — cop acts, capture is checked, *then* the thief decides
while already seeing the cop's new cell. That is not a strategy defect, it is a protocol defect.

> **§5.3.2, book p.35 (PDF 51), Acknowledge phase:**
> *"This acknowledgement prevents the sender from retreating from its commitment, and at the
> same time guarantees that the reveal will occur only when both sides have already fixed
> their moves."*

> **§5.2, book p.33 (PDF 49)** names the three frauds the protocol exists to prevent. The second
> is *"changing a move after the opponent's move has been revealed."*

> **§5.3, book p.34 (PDF 50):** *"In every game step each agent performs four mandatory
> cryptographic phases, in order."* — **each** agent, every step. Figure 6 (book p.36) shows
> Reveal flowing in **both** directions after a single Acknowledge.

The mandatory Commit → Acknowledge → Reveal → Audit protocol has no purpose under sequential
play. Both agents choose from the same pre-turn state; both actions are then applied at once.

## 2. Action spaces

| Role | Actions | Source |
|---|---|---|
| Thief | STAY + 4 orthogonal steps, minus out-of-bounds and barriered cells. `|A_t| ≤ 5` | **BOOK** §3.4 p.21: *"move one cell in one of the four orthogonal directions … or choose to stay. Diagonal movement is forbidden."* Table 15 row 1 marks the movement set **fixed**. |
| Cop | Move (as thief) **XOR** place one barrier. Barrier target = the cop's own cell **or** one of its 4 orthogonal neighbours. `|A_c| ≤ 10` | **BOOK** §3.4 p.21: *"in a turn where the cop forgoes movement it may place a barrier on any cell one step away from it — the cell on which it stands or one of the four orthogonally adjacent cells."* |

**Engine defect corrected:** `barrier.py:69` rejects the cop's own cell. The book explicitly
permits it. Under simultaneity self-placement is a live denial move against a thief stepping in.

## 3. Terminal predicates, in evaluation order

Let `cop_pre, thief_pre` be the pre-turn cells, `cop_post, thief_post` the post-turn cells, and
`b` the barrier cell placed this turn (or none). Barriers are applied before the terminal tests.

| # | Predicate | Verdict | Status |
|---|---|---|---|
| 1 | `b == thief_pre` | CAPTURE | **BOOK** — rule 46; §3.4 p.21: *"if the cop places a barrier on the cell where the thief stands **at that moment** — the thief is captured."* `ברגע זה` = the **pre**-move cell. |
| 2 | `b == thief_post` | CAPTURE | **NEGOTIATED** — the thief moved into the cell being sealed. Undefined by the book. |
| 3 | `cop_post == thief_post` | CAPTURE | **BOOK** — §3.5 p.22 Table 2: *"the cop lands on the thief's cell and declares Capture Claim."* Under simultaneity, both landing on one cell is the joint-turn reading of "lands on". |
| 4 | `cop_post == thief_pre and thief_post == cop_pre` (swap) | CAPTURE | **NEGOTIATED** — otherwise the two agents pass through one another, which no reading of §3.4 supports. |
| 5 | every orthogonal neighbour of `thief_post` blocked (barrier or edge) | CAPTURE | **BOOK** — rule 47; §3.4 p.21: *"a thief imprisoned without any legal move (all adjacent cells blocked and/or at the board edges) is likewise considered captured."* |
| 6 | `turn + 1 >= survival_threshold` | SURVIVAL | **BOOK** — §3.5 p.22: *"the thief survives [survival threshold] valid steps without capture."* |

Capture conditions are evaluated **before** survival: a capture landed on the final turn is a
capture, not a survival.

**Deliberately NOT a capture:** `thief_post == cop_pre` while the cop moved elsewhere. The cop
has vacated the cell; nothing in §3.5 makes an empty cell dangerous. This closes the live bug
where a thief could walk onto the cop, be spared, and escape.

**Engine defect corrected:** rule 47 was unreachable dead code — `get_legal_moves` appends STAY
unconditionally, so `if not get_legal_moves(...)` never fired. The book's wording is about the
*four adjacent cells*, and says nothing about STAY, so predicate 5 tests neighbours directly.

## 4. Turn counting

One joint turn = one increment. `survival_threshold` and `move_ceiling` (both **minimum** 35,
Table 15 rows 3–4) therefore count joint turns, not half-turns.

## 5. How the negotiated rows are agreed without breaking the handshake

Rule 11 requires the shared config file to be **byte-identical** on both sides, and
`handshake.py` aborts before move 1 on a digest mismatch. Adding fields to `game_params.json`
would therefore make our digest differ from every opponent who has not adopted them — an abort
and 0/0 on games that never start.

So: `game_params.json` stays byte-compatible with a book-faithful peer. Resolution semantics
live in a **separate optional negotiated block**. When the opponent sends no block, we fall back
to the **BOOK-only** subset (predicates 1, 3, 5, 6) — exactly what a faithful implementation
computes — so we can never diverge at the rule-36 mutual audit. When a block is agreed, both
sides use it and it is covered by the declaration.

This is what §3.2 p.18 describes:

> *"The game contract is not dictated from above but negotiated between each pair of teams …
> The agreed contract is a floor, not a ceiling … it is permitted and even desirable to exploit
> any legal loophole not defined here … as long as everything is legal and agreed between the
> parties."*

## 6. Parameters — the only numeric source is Appendix ו

| Parameter | Value | Status |
|---|---|---|
| Board size | 7×7 | minimum |
| Number of agents | 2 | **fixed** |
| Cop start / thief start | (0,0) / (3,3) | **negotiated** — *not* fixed. Training on one start trains for a board we may not be given. |
| Movement set | 4 orthogonal + stay | **fixed** |
| Barrier quota | 14 | minimum |
| Move ceiling / survival threshold | 35 / 35 | minimum |
| Capture score (cop, thief) | 20, 5 | **fixed** |
| Survival score (cop, thief) | 5, 10 | **fixed** |
| Draw score | 2 each | **fixed** |
| Technical loss | 0, 0 | **fixed** |

Status meanings (Appendix ו §1, book p.139): **fixed** — *"deviation from this value disqualifies
the team"*; **minimum** — may be negotiated upward only; **negotiated** — any agreed value, with
the example as the default absent agreement.

## 7. League facts that shape the strategy

| Fact | Value | Source |
|---|---|---|
| Counted games per opponent | **exactly one** | rule 52, book p.133 |
| Unscored warm-up games | **permitted** | rule 52 |
| Code may change between games | yes, with the commit hash declared | Appendix ו §2 rule 5 |
| Opponents in the series | 6 | Table 18 row 1 |
| Max games per team | 10 | Table 18 row 5 |
| Diversity bonus for beating a new opponent | +10 | Table 18 row 2 |
| Minimum games to pass | 2 | Table 18 row 3 |

**Consequences for the algorithm.** One counted game per opponent means there is no adaptation
window inside a scored match — the policy must be strong on arrival, and a *deterministic* policy
hands a competent opponent a free read. But warm-ups are legal and code may change between games,
so scouting a peer in a warm-up and refitting offline before the scored game is both permitted
and worth building for.

Computational fairness (§5.5 p.39) normalises the league score so raw hardware cannot decide the
race: *"a light, fast solution on a modest machine that beats a heavy opponent is a victory of
development over computational muscle."* This argues for a shallow search with a good evaluation,
not a deep one.

## 8. Rules this contract must not break

| Rule | Requirement |
|---|---|
| 2 | No shared memory or variables between the two sides — immediate disqualification. |
| 11 | Config byte-identical on both sides, cryptographically locked. |
| 13/14 | Orthogonal only; a diagonal move is rejected by the opponent and is a technical loss. |
| 15/16 | Every barrier placement declared openly and truthfully; lying about its location is a severe disqualification. |
| 21/22 | Capture declared truthfully; a false capture claim is immediate disqualification. |
| 25 | *(recommended, not mandatory)* the language model must not choose the move. **We treat this as hard.** |
| 27 | **Forbidden** to put direct numeric positions in the protocol — hints are natural language. |
| 42 | Academic README with model, tables, strategy, and RL curves if a learner is used. |
| 47/46/48 | Trapped thief captured; barrier-on-thief captured; every ending scored per the table. |

RL is **optional**: §6.3 p.43 calls reinforcement learning *"an optional tool only"*. We ship a
learned component because 12–24 tuned weights beat guessed ones cheaply and produce the curve
rule 42 wants — not because the book compels it.
