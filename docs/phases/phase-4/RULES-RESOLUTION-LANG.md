# Language and belief resolution contract

**Status:** binding · **Date:** 2026-08-09 · **Supersedes:** nothing in
[`docs/phases/phase-3/RULES-RESOLUTION.md`](../phase-3/RULES-RESOLUTION.md) — that document's six
terminal predicates, action spaces and parameter table are unchanged by Phase 4. This document
adds two new binding calls (D-48, D-49) and records every Phase-4 rule status alongside them.
**Source:** `police_thief_p2p.pdf` (Segal, book v3.0.0), read directly this session (chapter 4,
book pp. 24–31 / PDF 40–47; §6.1–6.6, book pp. 41–52 / PDF 57–68; §5.3, book pp. 34–36 / PDF
50–52). **PDF page = book page + 16** for the numbered body (verified directly against the PDF
this session — see the page-mapping note at the end of this document). The preface uses roman
numerals and is cited by its own PDF page, not by the +16 rule (also verified directly).

---

## 1. The contradiction: what does a peer reveal, and when?

`04-CONTEXT.md`'s own Phase Boundary section flagged this as the researcher question before any
Phase-4 code existed: *"what exactly is revealed per turn vs at game end?"* The book answers it
**two different ways**, in two different chapters, and both readings are internally coherent on
their own terms.

### Side A — §5.3.2 requires a per-turn Reveal of the Move

> **§5.3.2, book p.35 (PDF 51), "Reveal":** *"הסוכן שולח ליריב את הפעולה (Move) ואת המשפט
> המילולי. ה-Nonce נשאר חבוי בשלב זה."* — **"The agent sends the opponent the action (Move) and
> the verbal sentence. The Nonce stays hidden at this stage."**

Figure 6, the very next page (**book p.36, PDF 52**), draws the four-phase sequence
`Commit → Acknowledge → Reveal → Final Reveal/Audit` with **Step 3 explicitly labelled "Reveal:
Move + Hint (Nonce hidden)"**, flowing in **both directions**, cop→thief and thief→cop, on a
diagram whose own caption reads: *"רצף חילופי ההודעות בין השוטר לגנב לאורך ארבעת שלבי
Commit→Acknowledge→Reveal→Audit. שימו לב שה-Nonce נחשף אך ורק בשלב הביקורת הסופי, בתום המשחק."*
— **"the message-exchange sequence between the cop and the thief across the four
Commit→Acknowledge→Reveal→Audit phases. Note that the Nonce is disclosed only at the final audit
stage, at the end of the game."** This is a **per-turn**, **per-step** exchange: Move and Hint
both cross the wire every single step, with only the Nonce withheld until game end.

### Side B — §6.4 requires that neither side ever sees the opponent's real location

> **§6.4, book p.47 (PDF 63), "Distance Heuristics and Belief Heatmap":** *"שני הצדדים סימטריים
> לחלוטין: אף אחד מהם אינו רואה את מיקום היריב האמיתי. כל צד יודע היכן הוא עצמו, ומקבל את מפת
> הריח של הצד השני, ומשום כך כל צד בונה מפת אמונות (belief map) משלו."* — **"Both sides are
> completely symmetric: neither of them sees the opponent's real location. Each side knows where
> it itself is, and receives the other side's scent map, and because of this each side builds its
> own belief map.""** The section goes on to define the belief map as a `[board size]×[board
> size]` grid of `P(opponent in cell)`, driven by scent evidence and a verbal hint that "may be
> false" (`רמז מילולי שעשוי להיות כוזב`), fused by Bayes' rule with a reliability coefficient on
> the text.

**These cannot both be literally true of the same quantity at the same moment.** If the Move is
revealed every step (Side A), a peer that simply reads its own inbox knows the opponent's exact
cell after every turn — there is nothing left for a probability grid to estimate. If neither side
ever learns the opponent's real location (Side B), the per-turn Reveal of the Move in §5.3.2 must
be describing something other than the physical cell, or must not run on the position channel at
all.

### The book's own escape hatch

> **Preface, "חופש אקדמי במקרה של סתירה" ("Academic freedom in case of contradiction"), book p. v
> (PDF 5 — roman-numbered front matter; the body's +16 offset does not apply here):**
> *"ספר זה נכתב כמיטב היכולת להיות עקבי, אך ייתכן שתתקלו בו סתירה — שני מקומות שנראים כמכתיבים
> התנהגות שונה. במקרה כזה נתונה לכם החופש האקדמי לבחור באחת מן האפשרויות ולהמשיך על פיה, ובלבד
> שתציינו זאת במפורש בדוח שלכם: היכן זיהיתם את הסתירה, במה בחרתם, ומדוע."* — **"This book was
> written to the best of my ability to be consistent, but you may run into a contradiction — two
> places that appear to dictate different behaviour. In that case you are given the academic
> freedom to choose one of the options and proceed on it, PROVIDED THAT YOU STATE THIS EXPLICITLY
> IN YOUR REPORT: where you identified the contradiction, what you chose, and why."**

This document is that statement. It is not a courtesy write-up; the preface makes it the price of
being allowed to resolve the contradiction at all.

---

## D-48 — the choice, and the four reasons

**We keep the per-turn Reveal, and we express the revealed move as a natural-language direction
token rather than a coordinate pair. The opponent's position is therefore known one turn behind
— never the current turn, at commit time. The belief map is the one-turn-ahead predictive
distribution over where the opponent will be when our own move lands, fused with scent and hint
evidence. Under a peer whose Reveal we cannot integrate (missing, silent, or a shape we do not
accept), the same belief map runs on scent and hints alone.**

Two regimes, one implementation:

| Regime | Opponent's pre-turn cell | Belief map's job |
|---|---|---|
| **A** (Reveal integrable) | known exactly, one turn stale | predict the *next* cell; supply an opponent-action prior and a sampled target |
| **B** (Reveal missing or opaque) | unknown | full posterior from scent + hints, diffusing each turn without exact evidence |

**1. The protocol reading is load-bearing and cannot be dropped.** Rules 15/16 (barrier declared
truthfully), 19 (any hash mismatch → technical loss, score 0), 21/22 (capture declared
truthfully), and 46–48 (every ending scored per the table, identically on both sides) are only
computable if both peers maintain a synchronised physical world to audit against. Phase 2/3
already build and depend on this synchronised state; deleting the Reveal breaks the mutual
log audit rule 36 requires at the end of every game.

**2. §6.4 stays fully meaningful under this reading — it is not explained away.** At the moment
either side **commits**, the opponent's move **for the current turn** is genuinely unknown; that
is the entire purpose of the mandatory Commit → Acknowledge → Reveal sequence
(§5.3.2: *"...the reveal will occur only when both sides have already fixed their moves"*, quoted
in full in [`docs/phases/phase-3/RULES-RESOLUTION.md`](../phase-3/RULES-RESOLUTION.md) §1).
`P(opponent cell at the end of THIS turn)` is a real, non-degenerate distribution at decision
time, and scent and hints are real evidence about it — §6.4's belief map is not vestigial, it is
the predictive step this codebase's belief map actually runs.

**3. Rule 27 is honoured, and the project's own canonical directive requires it.**
`docs/KHALED_PERSONAL_PLAN.md:437`: *"Numeric coordinates in the protocol are FORBIDDEN
(rule 27) — this replaces the coordinate transport from Phase 2."* Phase 2's `turn_actions.py`
sent `payload={"x": ..., "y": ...}` on the wire. Phase 4 replaces this outright (D-53, plan
04-04): the Reveal now carries a direction token (`north`/`south`/`east`/`west`/`stay`) plus a
`kind` (`move`/`barrier`), never a coordinate. A legacy `{"x","y"}` payload from a Phase-2-only
peer is still decoded on receipt for interop, but this codebase never emits one.

**4. It degrades, which is what the league actually needs.** Rule 52 gives exactly one counted
game per opponent (book p.133) — there is no adaptation window. A design that only works when the
opponent also reveals moves in our exact accepted shape would forfeit every game against a peer
that stays silent, replies late, or sends coordinates in an unrecognised shape. The *same*
`BeliefMap` object runs identically in both regimes (`strategy/belief.py`, plan 04-05): Regime A
calls `observe_exact` before `predict`; Regime B skips straight to `predict`, fed only by
`scent_likelihood()` and `hint_likelihood()`. One implementation, two regimes, chosen per turn by
`network/turn_language.known_opponent_cell()` (plan 04-12) before any state mutation can change
the answer.

**Measured, not just designed:** plan 04-12's real two-peer harness
(`tests/integration/two_peer_game.py`) is what found and fixed a genuine concurrency bug in the
hint-buffering layer (04-04's original "late hint"/"duplicate hint" checks turned ordinary
network jitter into a spurious technical loss) — concrete evidence that a per-turn Reveal
integrated live, not merely unit-tested, is where a design like this earns its keep. See
[`docs/phases/phase-4/PRD.md`](PRD.md) §6 for the full account.

---

## D-49 — scent is derived locally and never transmitted

§4.4 (book p.29, PDF 45) describes each agent as one that *"can sample the board and receive its
opponent's scent map"* (`יכול לדגום את הלוח ולקבל את מפת הריח של יריבו`). In a refereeless P2P
game there is no shared board to sample and no third party to hand out a scent map. **We do not
add a scent message to the protocol.** Each side computes its own trail and its reconstruction of
the opponent's trail entirely locally (`strategy/scentfield.py`'s `ScentField`, plan 04-01) from
what it already legitimately knows: its own emissions, and the opponent's revealed moves (Regime
A) or believed cells (Regime B).

**Rule 23 only makes sense under local derivation.** *"Cryptographically lock the scent-emission
model before the game starts"* (rule 23) is pointless if the numbers themselves are transmitted
turn by turn — a receiver would simply trust whatever arrived. It matters precisely because
**both sides compute the field independently from the same locked model** and must therefore
agree exactly, with no opportunity to paper over a silent divergence. §4.5's red box (book p.31,
PDF 47) states this directly: exchange the model *"together with the numeric example... verify
both sides interpret it identically, and only then lock the agreement cryptographically."* Plan
04-01 does exactly this — the locked payload's own worked example (`0.9 → 0.9·(1−0.10) = 0.81`)
is re-derived and checked at load time, not merely stored — and plan 04-02 carries the resulting
digest (`c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e`, shipped and pinned by
`tests/unit/test_handshake_scent.py`) inside the existing Phase-2 handshake, verified with
`secrets.compare_digest`, aborting to `State.ERROR` with a distinct `SCENT_MISMATCH` outcome on
disagreement.

Transmitting the field would also be self-defeating on its own terms and rule-27-adjacent:
`τ = 0.9` marks the emitter's exact cell (Table 16 row 1). Publishing the raw field would hand
the opponent our position in numbers through a side channel — exactly the leak rule 27 forbids on
the primary channel.

---

## D-51 note (cross-referenced, not re-argued here)

D-51 (the hint-reliability coefficient becoming a bounded, adaptive value) is a disclosed revision
of D-40, not a new contradiction with the book. It is recorded in full, with the §4.4 worked
example that motivates it, in [`docs/PRD_belief_map.md`](../../PRD_belief_map.md) §5 — that
document is the authoritative source; this file only points to it so a reader following the
"three deliberate source-of-truth deviations" list (`RESUME.md`) finds all three from either
entry point.

---

## 2. BOOK / NEGOTIATED / DERIVED — every Phase-4 rule call

Same three-column discipline as
[`docs/phases/phase-3/RULES-RESOLUTION.md`](../phase-3/RULES-RESOLUTION.md) §6: **BOOK** (quoted,
non-negotiable), **NEGOTIATED** (undefined by the book, agreed between peers before move 1),
**DERIVED** (transcribed from a book figure or worked example, not invented).

| # | Call | Status | Source |
|---|---|---|---|
| 1 | Scent strength at source = **0.9** | **BOOK — fixed** | PARAMETERS.md Table 16 row 1 (Appendix ו) |
| 2 | Scent decay rate ρ = **0.10** per turn | **BOOK — fixed** | Table 16 row 2 |
| 3 | Scent field size = **5×5** | **BOOK — fixed** | Table 16 row 3 |
| 4 | Emission kernel (5×5, `0.04/0.14/0.20/0.42/0.62/0.90`) | **DERIVED** — transcribed from Figure 4 (book p.28, PDF 44), reproducing `0.9·exp(−3d²/8)` to two decimals; the Gaussian form is an *observation* about the transcribed table, not a separate book-given formula | Figure 4; D-50 |
| 5 | Decay law `τ(t+1) = max(0, (1−ρ)·τ(t) + Δτ)` | **BOOK — fixed** | §4.3, book p.27 (PDF 43) |
| 6 | Worked lock example `0.9 → 0.81` | **BOOK — fixed** | §4.5 red box, book p.31 (PDF 47) |
| 7 | Direction vocabulary (`north/south/east/west/stay`, `move`/`barrier` kind) | **NEGOTIATED** | not specified by the book beyond rule 27's coordinate ban; agreed as this project's wire shape (D-53) |
| 8 | Hint payload shape (`text`/`intent`/`turn` on `MessageType.HINT`) | **NEGOTIATED** | rule 26 (natural language only) and rule 27 (no coordinates) constrain it; the exact envelope keys are ours (D-47) |
| 9 | Locked-payload contents (kernel table + ρ + window + worked example, exchanged together) | **BOOK** | §4.5 red box, book p.31 (PDF 47) |
| 10 | Hint word limit = **15** | **BOOK — negotiable, pilot default** | PARAMETERS.md Table 14 row 2 |
| 11 | Game arena = **"New York"** | **BOOK — negotiable, pilot default** | Table 14 row 1 |
| 12 | Per-turn Reveal carries Move + Hint, Nonce hidden | **BOOK — fixed** | §5.3.2, book p.35 (PDF 51); Figure 6, book p.36 (PDF 52) |
| 13 | Neither side sees the opponent's true location; belief map required | **BOOK — fixed**, resolved per D-48 above | §6.4, book p.47 (PDF 63) |
| 14 | Scent is derived locally, never transmitted | **DERIVED / D-49** — required by rule 23's own logic, never stated as a prohibition in so many words | §4.4 p.29 (PDF 45); §4.5 p.31 (PDF 47) |
| 15 | Hint reliability: fixed mixing weight `w` **and** an adaptive trust coefficient `r` | **BOOK (mechanism) / DERIVED (implementation) — D-51**, disclosed revision of D-40 | §4.4, book p.30 (PDF 46); §6.4, book p.47 (PDF 63) |
| 16 | `intent` (`truth`/`lie`) committed before the hint text exists | **BOOK — fixed** (rule 25's structural reading) + **NEGOTIATED** (the flag's wire representation) | §5.3.1, book p.34 (PDF 50); rule 25 |
| 17 | The LLM never chooses the move | **BOOK — recommended, treated as hard here** (per `docs/phases/phase-3/RULES-RESOLUTION.md` §8) | rule 25 |
| 18 | Sample from the belief, not `argmax` (D-43) | **NEGOTIATED / engineering** — the book's own worked figure (Figure 8, book p.48/PDF64) shows `arg maxₛ b(s)` as the *displayed* target, not a mandated policy input | §6.4 Figure 8; D-43 |

---

## 3. Two-peer testing, an explicit worked example of why it matters

RESUME.md's carry-over V records a concrete finding worth stating here for the report, since it
is exactly the outcome this document's D-48 choice was designed to survive: plan 04-12's real
two-peer concurrent game (`tests/integration/two_peer_game.py`, the first genuinely concurrent
run against injected latency rather than one-sided direct calls) found that 04-04's own
"late hint"/"duplicate hint" protocol checks fired on ordinary jitter once the move and the hint
became two independent, variable-latency round-trips — turning a normal timing gap into a
spurious technical loss. It was fixed (a late hint drops silently; a duplicate overwrites) and
re-verified across four full degradation games (no API key, every call failing, budget exhausted,
a silent peer) plus timing measurements (~37ms/turn language ON vs ~18ms/turn OFF, against a 60s
watchdog threshold). No single-sided or engine-only test in the phase's first five waves could
have surfaced this; it took the real two-process harness the per-turn Reveal exists to support.

---

## Page-mapping verification note

Every book-page/PDF-page pair quoted above was checked directly against `police_thief_p2p.pdf`
this session (not re-copied from an earlier extract without verification): PDF pages 50–53 were
read to confirm §5.3.2's Reveal quote (PDF 51) and Figure 6 (PDF 52); PDF pages 62–64 were read
to confirm §6.4's opening paragraph and its section title (PDF 63); PDF page 5 was read to
confirm the preface's academic-freedom clause and its page label ("v"). The `PDF page = book
page + 16` rule holds for every numbered-body citation checked (35+16=51, 36+16=52, 47+16=63) and
does not apply to the roman-numbered preface, which is cited by its literal PDF page instead.

---

*Binding as of 2026-08-09. Dated per [[verify-rules-against-the-book-not-extracts]]: the book was
read directly, not from a prior extract, for every quotation in this document.*
