# Phase 1: Base Logic - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-27
**Phase:** 1-Base Logic
**Areas discussed:** Package name, Config vs constants split, Barrier mechanics, Turn order & capture timing, End-states produced

**Seed:** User pasted the canonical Phase-1 directive verbatim from
`docs/KHALED_PERSONAL_PLAN.md` (§"PHASE 1 — Base logic"), which locked all scaffolding,
numeric values, capture types, and config separation. Discussion covered only the
implementation gray areas the directive left open.

---

## Package name

| Option | Description | Selected |
|--------|-------------|----------|
| `pursuit` | Short, neutral, works for both cop & thief repos | ✓ |
| `copsrobbers` | Explicit but longer | |
| `p2p_pursuit` | Emphasizes P2P | |

**User's choice:** `pursuit` (option a)
**Notes:** Used across `src/pursuit/…` everywhere and into both split repos in Phase 8.

---

## Config vs constants split

| Option | Description | Selected |
|--------|-------------|----------|
| One `game_params.json` duplicated byte-for-byte per side + per-side role file | All game numbers in config; matches rule 11 verification | ✓ |
| Single shared `config/game_params.json` (one copy) | Simpler but no two-file byte-for-byte compare | |

**User's choice:** Option a
**Notes:** Grounded in Appendix F §2 rule 1 (all params in config file) and rule 11
(byte-for-byte lock). `constants.py`/`Enum` holds only non-numeric structural values.

---

## Barrier mechanics

| Option | Description | Selected |
|--------|-------------|----------|
| 3a move + place same turn | Cop moves and places one barrier per turn | ✓ (via 4a) |
| 3b either move or place | One action per turn | |
| 3c any empty in-bounds cell | Placement unrestricted; on thief = capture | ✓ |
| 3d adjacency-restricted | Restrict to cells near the cop | |

**User's choice:** 3c (unrestricted placement); 3a confirmed by implication from turn
order choice 4a ("cop acts move &/or place").
**Notes:** 3d rejected because it would require a "placement radius" number absent from
PARAMETERS.md — inventing one violates project rule 1. Barriers are impassable cells;
placing on own cell / existing barrier is rejected without spending quota.

---

## Turn order & capture-check timing

| Option | Description | Selected |
|--------|-------------|----------|
| (a) cop acts → check cop-on-thief + barrier-on-thief → thief turn: check no-move → thief moves → increment | Standard sequence | ✓ |
| (b) different order | User-specified | |
| (c) you decide | Claude discretion | |

**User's choice:** Option a
**Notes:** Phase 1 has no orchestrator — this is the tested convention encoded by the
pure `detect_capture`/apply-action functions.

---

## End-states Phase 1 produces

| Option | Description | Selected |
|--------|-------------|----------|
| (a) Produce only CAPTURE & SURVIVAL; enum + config still define TIE & TECHNICAL_LOSS | Others produced in later phases | ✓ |
| (b) Model all four as reachable Phase-1 outcomes | | |
| (c) you decide | | |

**User's choice:** Option a — after explicitly asking why tie/technical-loss are deferred.
**Notes:** Explained: it is not a representation limit (all four are defined in the enum +
scored in config now). It is that the *triggering events* don't exist in Phase 1 — TIE is
a series aggregate across sub-games (Phase 8), and TECHNICAL_LOSS is produced only by the
commit-reveal audit / false-declaration machinery (Phase 6–7). Producing them now would be
untriggerable dead code and would pull later-phase logic forward, against the build order.
User accepted 5a and declined the optional early tie-aggregation function.

## Claude's Discretion

- Internal state data-model shape (immutable snapshot vs object; barriers as frozenset).
- Exact ≤150-line file split within `src/pursuit/`.
- Test structure under `tests/unit` and `tests/integration`.

## Deferred Ideas

- Adjacency/range-restricted barrier placement (needs a documented radius parameter; only
  by opponent agreement).
- Tie-aggregation function → Phase 8 (series/league).
- Technical-loss production path → Phase 6–7 (crypto audit / declarations).
