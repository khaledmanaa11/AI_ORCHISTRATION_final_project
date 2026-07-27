# Phase 1: Base Logic - Context

**Gathered:** 2026-07-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the **pure game engine** for the cops-and-robbers match, plus the
**one-time project scaffolding** (this is the first code phase). Concretely:

- A 7×7 grid board model with orthogonal movement + legal-move validation
- Barrier placement by the cop with quota enforcement
- Capture / end-condition detection and the scoring table

**Explicitly out of scope (later phases — do not build here):**
- Any networking / FastMCP / process separation logic (Phase 2)
- Any AI, RL/Q-learning, belief map, scent, or strategy (Phase 3–4)
- Any cryptography / commit-reveal / declarations (Phase 6)
- Any reporting / GUI / replay (Phase 7)
- Series/league aggregation (Phase 8)

Keep this phase completely free of networking and of any AI or strategy logic.
All numeric values come from `docs/PARAMETERS.md` — invent none.

</domain>

<decisions>
## Implementation Decisions

### Scaffolding (locked by the canonical directive — carried forward, not re-asked)
- **D-01:** uv project. `pyproject.toml` with ruff config (line-length 100, target
  py310, `select = E,F,W,I,N,UP,B,C4,SIM`, `ignore = E501`) and coverage config
  (`source = src`, omit `main.py`/tests/gui, `fail_under = 85`). Generate `uv.lock`.
- **D-02:** Layout `src/pursuit/{sdk,services,shared,constants.py}`,
  `tests/{unit,integration}`, `config/police/`, `config/thief/`, `.env-example`
  (dummy values). `src/pursuit/shared/version.py` starts at **1.00**.
- **D-03:** Reuse the existing line-limit gate `scripts/check_line_limit.sh`
  (already wired as a pre-commit hook via `core.hooksPath=scripts/hooks` and in CI).
  Do not re-create it; ensure it is runnable as a standalone gate for this phase.

### Package name
- **D-04:** The Python package is **`pursuit`** — `src/pursuit/…`. Short, neutral,
  usable by both the cop and thief repos when they split in Phase 8.

### Config vs constants split
- **D-05:** **Every numeric game parameter** (board size, start positions, movement
  rule, barrier quota, move ceiling, survival threshold, all scoring values) lives in
  a **`game_params.json`** config file — NOT in `constants.py`. Rationale: Appendix F
  §2 rule 1 requires *every team to define all values in its configuration file*, and
  rule 11 locks that file byte-for-byte / cryptographically (Phase 6). Numbers in code
  could not be verified or per-game-attached.
- **D-06:** `game_params.json` is **duplicated byte-for-byte** in `config/police/` and
  `config/thief/` — one canonical copy per side, so the Phase-2 byte-for-byte identity
  check (rule 11 / NET-09) has two files to compare. A small **per-side role/identity
  file** (e.g. `role.json` → `"police"` / `"thief"`) sits alongside it; that file is the
  *only* legitimate difference between the two config dirs.
- **D-07:** `constants.py` / `Enum` hold **non-numeric structural values only** —
  directions (the 4 orthogonal steps + stay), cell states (empty / barrier / agent),
  `Outcome` labels, config keys. Zero game numbers hardcoded (BASE-08, QUAL-11).

### Barrier mechanics
- **D-08:** A barrier makes a cell **impassable** — no agent may move onto or through
  a barriered cell. (Required for capture-type 3 "no legal move" to be reachable.)
- **D-09:** Each turn the cop may **move AND place one barrier in the same turn**
  (not either/or). Confirmed by the turn model in D-12.
- **D-10:** A barrier may be placed on **any empty in-bounds cell**. Placing on the
  thief's current cell → **capture** (rule 46). Placing on the cop's own cell or on an
  already-barriered/occupied cell → **rejected**, and a rejected placement does **not**
  consume quota. No adjacency/range restriction — such a restriction would require a
  "placement radius" number that does not exist in `docs/PARAMETERS.md`, and inventing
  one violates project rule 1. (Adjacency could only be added by explicit opponent
  agreement with a documented parameter.)
- **D-11:** Quota is **14** (minimum, from PARAMETERS Table 15). A placement request
  beyond the quota is rejected (BASE-02); rejected/over-quota placements never mutate
  the board.

### Turn order & capture-check timing
- **D-12:** Phase 1 has no orchestrator (that's Phase 2). It exposes **pure functions**
  (legal-move generation, `detect_capture(state)`, apply-action, scoring) whose tested
  turn convention is:
  1. Cop acts: move (orthogonal step or stay) and/or place one barrier
  2. Check capture: **cop-on-thief** overlap, then **barrier-on-thief**
  3. Thief's turn: **first** check *no legal move* (→ captured), else thief moves
  4. Increment turn counter
- **D-13:** "No legal move" is evaluated at the **start of the thief's turn**, over the
  thief's current legal-move set (orthogonal steps within bounds onto non-barriered,
  non-out-of-bounds cells; "stay" counts as a legal move unless the thief's own cell is
  the capture condition). Being surrounded by barriers/edges with no move → captured
  (rule 47 / BASE-05).

### End-states Phase 1 produces
- **D-14:** The `Outcome` enum defines **all four** outcomes — `CAPTURE`, `SURVIVAL`,
  `TIE`, `TECHNICAL_LOSS` — and the scoring table in config carries **all** their values
  (capture 20/5, survival 5/10, tie 2/2, technical-loss 0/0) so BASE-07 is fully
  traceable now.
- **D-15:** The Phase-1 **engine only ever produces `CAPTURE` or `SURVIVAL`.** A single
  game is always decisive (at the move ceiling the thief either was caught or survived —
  survival → thief win 10/5). `TIE` is a *series* aggregate across sub-games vs one
  opponent (Phase 8); `TECHNICAL_LOSS` is triggered only by the crypto audit / false
  declaration machinery (Phase 6–7). Neither event can fire in Phase 1, so no producer
  code is written for them (avoids untriggerable dead code and premature build-order
  skipping). **No** early tie-aggregation function this phase.
- **D-16:** `move_ceiling` and `survival_threshold` both default to **35** (minimum).
  Reaching turn 35 without a capture = thief survives = `SURVIVAL` (10/5). They are read
  as two independent config values even though the pilot defaults coincide.

### Claude's Discretion
- Internal data-model shape (e.g. immutable state snapshot vs mutable object, barriers
  as a `frozenset` of cells, coordinate type) — Claude decides, subject to: no shared
  *mutable* game state that could later leak between cop and thief (rule 2), and the
  board-rules library is a **pure/stateless shared** module both sides import.
- Exact file split within `src/pursuit/` to respect the ≤150-line limit (the roadmap
  suggests: board+movement, barrier+quota, capture+end-condition+scoring).
- Test structure under `tests/unit` / `tests/integration` (TDD, happy + error path per
  public function).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The binding directive (read first)
- `docs/KHALED_PERSONAL_PLAN.md` §"PHASE 1 — Base logic" (lines ~217–263) — the
  canonical Phase-1 spec: scaffolding list, exact ruff/coverage config, all game
  numbers, the three capture types, config separation. This is the seed for this phase.

### Numeric truth (invent nothing)
- `docs/PARAMETERS.md` Table 13 (board 7×7, origin top-left, thief (3,3), cop (0,0)),
  Table 15 (movement fixed, quota 14, move ceiling 35, survival threshold 35),
  Table 17 (scoring — capture 20/5, survival 5/10, tie 2, technical loss 0/0).
  Also Appendix F §2 rule 1 (all params in the config file) and rule 11 (byte-for-byte lock).

### Game rules
- `docs/RULES.md` rules 13–16 (orthogonal-only movement, barrier declaration/quota),
  rules 46–48 (barrier-on-thief capture, no-legal-move capture, scoring table).

### Requirements this phase must satisfy
- `.planning/REQUIREMENTS.md` — BASE-01…BASE-08 (Phase 1) and the cross-cutting
  QUAL-01…QUAL-13 code-quality gate.

### Engineering standard (enforced gate)
- `docs/SEGAL_GUIDELINES.md` §19.1 Table 5 — ≤150-line files, ruff 0, coverage ≥85%,
  no hardcoded values, no secrets, uv-only, SDK layer, TDD, versioning at 1.00.

### Project & phase documentation
- `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` — project triplet; keep `docs/TODO.md`
  current as Phase 1 work lands (DOC-01).
- `docs/phases/_TEMPLATE/{PRD,PLAN,TODO}.md` — skeletons to copy into
  `docs/phases/phase-1/{PRD,PLAN,TODO}.md` at plan-phase (per CLAUDE.md per-phase triplet).

### Existing asset to reuse (do not re-create)
- `scripts/check_line_limit.sh` — the ≤150-line gate (pre-commit hook + CI).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/check_line_limit.sh` + `scripts/hooks/` — line-limit enforcement already
  exists and is wired (`core.hooksPath=scripts/hooks`). Phase 1 wires nothing new here,
  just conforms to it.

### Established Patterns
- **No `src/` yet** — this is greenfield. Phase 1 establishes the canonical layout
  (`src/pursuit/{sdk,services,shared,constants.py}`) that every later phase extends.
- **SDK-layer rule (QUAL-01):** all game logic behind `src/pursuit/sdk` / `services`;
  any CLI/harness stays a thin shell.
- **`.gitattributes`** already forces LF on shell scripts (recent commit) — keep new
  config/JSON and shell files LF-clean.

### Integration Points
- The pure board-rules library in `src/pursuit/shared` is the shared module Phase 2's
  two processes will both import (allowed shared *library*, never shared *live state*).
- `game_params.json` shape defined here becomes the config the Phase-2 byte-for-byte
  verifier (NET-09) and the Phase-6 cryptographic lock consume unchanged.

</code_context>

<specifics>
## Specific Ideas

- Package name is a hard choice, not a placeholder: **`pursuit`**.
- The only legitimate difference between `config/police/` and `config/thief/` is the
  per-side role/identity file; `game_params.json` must be identical across both.
- All four outcomes are *named/scored* now, but only CAPTURE and SURVIVAL are *produced*
  by Phase-1 logic — this was an explicit, reasoned decision (see D-14/D-15), not an
  omission.

</specifics>

<deferred>
## Deferred Ideas

- **Adjacency/range-restricted barrier placement** — would need a "placement radius"
  parameter absent from PARAMETERS.md; only viable by explicit opponent agreement with a
  documented value. Not built; noted if a future opponent negotiation requires it.
- **Tie-aggregation function** (level-score detection across sub-games → 2/2) — belongs
  with series/league logic in **Phase 8**, not Phase 1.
- **Technical-loss production path** — triggered by commit-reveal audit / false
  declaration; belongs in **Phase 6–7**.

</deferred>

---

*Phase: 1-Base Logic*
*Context gathered: 2026-07-27*
