# PRD — The `sdk/` layer (the mandated single entry point, and the rules 8–9 read model)

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-08-17
**Requirements:** QUAL-01 (SDK architecture, Table 5 row 1), QUAL-11, REPORT-02, REPORT-08
**Rules:** **8, 9** (local truth only — absolute disqualification), **2** (no shared runtime
state), 42 · **Phases:** 3 (game logic), 7 (the view half) · **Related:**
[PRD_gui.md](PRD_gui.md), [PRD_display_belief.md](PRD_display_belief.md),
[ARCHITECTURE.md](ARCHITECTURE.md), [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md) §4

> Per-mechanism PRD required by CLAUDE.md and [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md)
> §2.3, written after the code it describes, mirroring
> [PRD_commit_reveal.md](PRD_commit_reveal.md)'s section order. Every number below is
> either traced to a source or labelled a structural default — **nothing here is invented.**

---

## 1. Mechanism and scope

`src/pursuit/sdk/` is two things that share one rule, and the rule is what makes them one
package: **it is the only layer permitted to turn the engine's true joint state into
anything anyone else may consume.**

| Module | Code lines | Role |
|---|---:|---|
| `engine.py` | 28 | the façade: `legal_moves`, `score`, and the re-exports `make_state` / `resolve_turn` / `cop_actions` / `thief_actions` |
| `actions.py` | 70 | the two action spaces of one simultaneous turn |
| `resolve.py` | 104 | the joint-turn resolver — the single place a turn is applied |
| `terminal.py` | 70 | the six terminal predicates, in evaluation order |
| `local_view.py` | 110 | the closed, frozen read model a live view may render |
| `view_builder.py` | 147 | `AgentContext` → `LocalView`: the ONE module allowed to read `ctx.state` |
| `view_publish.py` | 76 | best-effort snapshot write on the agent's own loop |
| `view_snapshot.py` | 82 | the read half, in the other process |
| `view_render.py` | 135 | every colour, shade and geometry the dashboard draws |
| `view_text.py` | 86 | every line of text the sidebar prints |
| `__init__.py` | 5 | the submodule inventory (§14 packaging) |

**In scope:** the game's rules as callable functions; the projection from true state to a
publishable view; every derivation a GUI would otherwise be tempted to perform.

**Out of scope, deliberately:** the protocol (that is `src/pursuit/network/`), the policy
(that is `src/pursuit/strategy/`), transport, persistence formats, and widget construction.
The SDK holds **no I/O other than `view_publish`/`view_snapshot`'s single snapshot file**,
and it holds no asyncio.

### 1.1 What "all business logic behind the SDK" means here — precisely

Table 5's first row and §4 require a single entry point with GUI and CLI as thin shells.
This project satisfies that on the axis it is stated: **anything that computes a game fact
for display or for a rules decision lives here.** Stated as precisely as the tree supports:

- `src/pursuit/main.py` parses `--config-dir`, loads config, and hands off. It holds no
  rule, no turn logic and no state machine — and it is coverage-omitted (`*/main.py` in
  `pyproject.toml`), which is only defensible **because** it is that thin.
- `src/pursuit/gui/` performs no arithmetic and builds no strings. Every number it draws
  comes from `view_render`; every line it prints comes from `view_text`.
- `src/pursuit/network/` calls into `sdk.engine` for the rules
  (`orchestrator.py`, `turn_resolve.py`, `agent_context.py` are its three importers) rather
  than re-deriving them.

**The limit, stated rather than implied away.** There is no automated proof that a *future*
rule could not be written inside `src/pursuit/network/`. The enforced half is the
GUI-facing one (§4 below); the protocol-facing half is a review property today. Recording
that is the point — §17's Table 5 marks "OOP with no duplication" and "0 hardcoded values"
as `Code review` rows for the same reason, and `docs/SUBMISSION-CHECKLIST.md` prints them
`UNJUDGED` rather than PASS.

---

## 2. Why the view logic is in `sdk/` and not in `gui/` — a measured argument

`pyproject.toml` `[tool.coverage.run]` reads `omit = ["*/main.py", "*/gui/*", "tests/*"]`.
**Any logic placed in `gui/` is invisible to the `fail_under = 85` gate** — it can be wrong
in ways no test measures, while the suite reports a clean pass.

`scripts/check_line_limit.sh:18` enumerates `src/**`, `tests/**` and `training/**`, so
`scripts/` escapes **both** the size gate and coverage. Neither package is a place to put
thinking, and both facts are written into the module docstrings that depend on them
(`view_render.py`, `view_text.py`, `submission_common.py`).

The split is enforced structurally, not by intention:
`tests/unit/test_gui_structural.py` AST-scans `src/pursuit/gui/` for arithmetic operators,
string building (`join`/`format`) and any import outside `pursuit.sdk` / `pursuit.gui`, and
each scan is paired with a synthetic control proving it can fail.

### 2.1 One measured consequence, kept because it is the argument

`view_render.shade` reserves `BACKGROUND_COLOUR` for **exactly zero** and maps every
strictly positive value to at least the lowest lit stop. A heat ramp that rounded small
probabilities down to the background would draw a **smaller** support than the published
grid carries — and the floor that makes the geometric inversion fail guards the *published*
support, not the *drawn* one. Measured drawn/published support ratios were `scent.own`
22.50, `scent.opponent` 2.66, **`belief` 1.57**. Had that ramp lived in `gui/`, no coverage
number in this repository would have moved.

---

## 3. The read model (D-74) — closed, frozen, and not sufficient on its own

`LocalView` is the whole of what a live view may carry:

```python
# src/pursuit/sdk/local_view.py
@dataclass(frozen=True)
class LocalView:
    role: str; board_size: int; turn: int
    own_cell: Coord                      # rule 8: our own position
    declared_barriers: tuple[Coord, ...] # rule 22: declared, so shared knowledge
    barriers_placed: int
    belief: BeliefView | None            # None when belief is disabled — never a fake uniform
    scent: ScentView | None
    hints: tuple[HintView, ...]
    machine_state: str
    idle_seconds: float | None           # None when the watchdog exposes no reading
    watchdog_threshold_seconds: float
```

**The closed field set is half the mitigation, and until 07-11 the docstring claimed it was
all of it.** A dense probability grid expresses a cell perfectly well without any
coordinate appearing in it: measured through the shipped path, a cop's `belief.argmax` *was*
the engine's `ctx.state.thief`, and the published support was the legal-move plus centred on
the true cell — the centre of a plus is uniquely recoverable. What a view may *contain* is
therefore governed by `src/pursuit/strategy/display_belief.py`
([PRD_display_belief.md](PRD_display_belief.md)); the closed field set only keeps a whole
`GameState` from arriving. The full incident is in [PRD_gui.md](PRD_gui.md) §2.

Two shapes exist for the same reason. **Grids are densified**: `ScentField` keys its dicts
by coordinate, and handing those over would put every cell on the board into the view *as a
value*. **The hint history is an instance the caller owns and passes in** — never a
module-level global and never a class attribute, because two `AgentContext`s in one
interpreter must share no field (rule 2, NET-02).

---

## 4. What is enforced, and by which gate

| Property | Enforced by | Can it fail? |
|---|---|---|
| `view_builder` is the only `sdk/` module that reads `<x>.state.{cop,thief,barriers}` | `tests/unit/test_view_builder.py` — an AST walk over `src/pursuit/sdk/`, asserting the module count is ≥ 5 first | yes — its own counter-control plants a second reader |
| `gui/` imports nothing outside `pursuit.sdk` / `pursuit.gui`, and computes nothing | `tests/unit/test_gui_structural.py`, and the CI job behind `scripts/check_local_truth.py` | yes — four synthetic leaky panels are pinned |
| A live view cannot be inverted back to the true cell | `tests/unit/test_local_truth_recovery.py` — a **geometric** recovery attempt on a production-wired view | yes — `test_the_argmax_only_fix_would_still_leak` is pinned permanently |
| Drawn support equals published support | `tests/unit/test_gui_recovery.py` | yes |
| A snapshot read mid-write degrades to the previous frame | `tests/unit/test_view_snapshot.py` | yes |

**`scripts/check_local_truth.py` is an import/attribute gate, not a disclosure gate.** Run
against a synthetic panel that markers `belief.argmax` and labels the `scent.opponent` peak,
it returned `violations: []`, exit 0. **Do not cite it as evidence that a panel is safe.**
It exits 2 — never 0 — on an empty scan set, because a gate that reports OK for having
looked at nothing is worse than no gate.

**`check_submission.py`'s row G2-01 is weaker still**, and it is worth naming: it counts
tracked modules under `src/pursuit/sdk/` and passes on more than one. That is a presence
check. The real measurement is the table above; the row exists so the layer's *absence*
would be loud, not to certify its contents.

---

## 5. Interfaces

```python
# src/pursuit/sdk/engine.py — the façade
def legal_moves(state: GameState, agent: str, params: GameParams) -> list[Coord]: ...
def score(outcome: Outcome, params: GameParams) -> tuple[int, int]: ...
# re-exported unchanged: make_state, resolve_turn, cop_actions, thief_actions

# src/pursuit/sdk/resolve.py — the ONE place a turn is applied
def resolve_turn(
    state: GameState, cop_action: CopAction, thief_move: Coord,
    params: GameParams, rules: ResolutionRules,
) -> tuple: ...                                    # (new_state, outcome | None)

# src/pursuit/sdk/terminal.py
def terminal_outcome(
    pre: GameState, post: GameState, barrier: Coord | None, raced: bool,
    params: GameParams, rules: ResolutionRules,
) -> Outcome | None: ...
def is_walled_in(cell: Coord, barriers: frozenset, board_size: int) -> bool: ...

# src/pursuit/sdk/view_builder.py — the ONE reader of ctx.state
def build_local_view(
    ctx: AgentContext, history: HintHistory, *, idle_seconds: float | None = None,
) -> LocalView: ...

# src/pursuit/sdk/view_publish.py — runs on the agent's own loop, best-effort
def publish_view(ctx, path: Path) -> None: ...

# src/pursuit/sdk/view_snapshot.py — runs in the GUI process
def read_snapshot(path: Path | str) -> LocalView | None: ...   # None on a half-written file
```

`resolve_turn` replaced the sequential `apply_cop_action` + `apply_thief_move` pair, which
could not be reordered into simultaneity: every turn passed through an intermediate state
in which exactly one agent had moved, destroying the pre-turn positions a swap detector
needs. It also closed three defects that pair carried — an `apply_move` that validated
nothing (a thief could be placed on a barrier), a thief that could step onto the cop
uncaptured, and a rejected barrier signalled by returning the same object, which made an
invalid placement indistinguishable from a deliberately wasted turn.

---

## 6. Parameters and their sources

Every number this mechanism uses, with its status — none invented.

| Parameter | Value | Status | Source |
|---|---|---|---|
| Movement set | four orthogonal + stay | **fixed** | Book §3.4 p.21; `docs/PARAMETERS.md` Table 15. A diagonal is a technical loss (rules 13/14), so no generator may emit one |
| Board size, barrier quota, scores | from `config/police/game_params.json` | **fixed** | `docs/PARAMETERS.md` Tables 16–17 — read from config, never a literal |
| The two negotiated terminal predicates | `config/police/resolution.json` | negotiated | `docs/phases/phase-3/RULES-RESOLUTION.md` §5 |
| `min_support_cells`, belief publication floor | the `display` block of `config/police/belief.json`, loaded by `src/pursuit/shared/display_config.py` | engineering | 07-11; specified in [PRD_display_belief.md](PRD_display_belief.md). The loader **refuses** a floor at or below one cell's legal-destination count, so the value cannot be set to a number that would let the geometric inversion succeed |
| Heat ramp buckets | `len(HEAT_RAMP)` | structural | presentation; never restated as a literal anywhere it is used |
| Cell geometry (26 px, 1 px gap) | `view_render.py` constants | structural | presentation defaults, named so `gui/` performs no arithmetic |
| Snapshot refresh interval | **none** | — | **No document states one.** `--refresh-ms` is required with no default; the operator states the number and this repository states none (OQ-6) |

---

## 7. Acceptance criteria for this mechanism

1. `resolve_turn` applies both actions from the **same** pre-turn state and advances the
   turn counter by exactly one; the six terminal predicates run in the fixed order, capture
   before survival — `tests/integration/test_game_loop.py`,
   `tests/integration/test_turn_lifecycle.py`.
2. Exactly one module in `src/pursuit/sdk/` reads the true joint position, and the AST scan
   that says so refuses to run against fewer than five modules.
3. A production-wired `LocalView` survives a **geometric** recovery attempt: argmax, scent
   argmax, inversion, and support/entropy floors — `tests/unit/test_local_truth_recovery.py`.
4. `src/pursuit/gui/` contains no arithmetic, no string building and no foreign import.
5. `read_snapshot` is total over a half-written file and returns `None` rather than raising.

**OPEN:** the protocol-facing half of §1.1 — no automated check prevents game logic from
being written into `src/pursuit/network/` in future. Recorded, not closed.
