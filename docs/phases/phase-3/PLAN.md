# Phase 3 PLAN — Blind Strategy Module (RL policy)

**Version:** 1.00 · **Updated:** 2026-07-31

> Phase-scoped architecture. Inherits the project [PLAN.md](../../PLAN.md); captures only
> the design specific to Phase 3. Mechanism detail lives in
> [PRD_rl_strategy.md](../../PRD_rl_strategy.md). The AI design contract
> (framework decision, failure modes, evaluation strategy) is
> `.planning/phases/03-blind-strategy-module-rl-policy/03-AI-SPEC.md`.

## Components & files

| Module / file (≤150 lines each) | Responsibility |
|---|---|
| `config/{police,thief}/strategy.json` | `[strategy]` + `[training]` sections: brain class, α, γ, ε schedule, `min_visits`, turn buckets, episode counts, eval bar. The per-role file that legitimately differs per side |
| `src/pursuit/shared/strategy_config.py` | `StrategyParams` + `load_strategy_config()`; reuses `loader_helpers._require_key`/`_require_int` (QUAL-02), fail-loud, env-overridable |
| `src/pursuit/strategy/base.py` | `BrainBase` ABC (`_pick_move`, `_decide_move`) + frozen `Observation` / `Decision` dataclasses — the whole seam the network layer sees (STRAT-03) |
| `src/pursuit/strategy/registry.py` | Resolves `police_class` / `thief_class` strings to brain classes; unknown name fails loud. The only place a brain is constructed |
| `src/pursuit/strategy/pathfind.py` | BFS over the barrier-aware grid → `(distance, next_step)`. The single distance oracle (QUAL-02) — consumed by the fallback *and* the barrier sub-policy (STRAT-04) |
| `src/pursuit/strategy/prior.py` | Bayes motion model: uniform prior spread each turn by the opponent's legal moves. Prediction step only — Phase 4 plugs scent/hint evidence into this same update |
| `src/pursuit/strategy/fallback.py` | Chooses a move by BFS distance over the prior's argmax cell. Never raw Manhattan (STRAT-02) |
| `src/pursuit/strategy/heuristic.py` | `HeuristicBrain` — fully playable, and the baseline `QLearningBrain` must beat (GATE-4) |
| `src/pursuit/strategy/encoding.py` | Canonical state key: (own cell, believed target cell, blocked bitmask, barriers used, turn bucket) + bucketing helper |
| `src/pursuit/strategy/qtable.py` | `get` / `set` / `visits` / `best_action`, JSON load+save with per-key visit counts; fail-loud on a corrupt table |
| `src/pursuit/strategy/qlearning.py` | `QLearningBrain` — ε-greedy selection, the `min_visits` fallback trigger, the Q-update rule (STRAT-01) |
| `src/pursuit/strategy/barriers.py` | Cop-only barrier sub-policy: runs after `_pick_move`, blocks the thief's best escape corridor, respects the 14 quota (STRAT-05) |
| `training/harness.py` | Episode loop stepping `pursuit.sdk.engine` directly — **no network, no sockets** (see ADR P3-2) |
| `training/sparring.py` | Opponent pool + sampling rule: heuristic / past-self checkpoints / reference implementation (STRAT-06) |
| `training/checkpoint.py` | Atomic Q-table write (temp file + `os.replace`), seed logging, resume-from-latest |
| `src/pursuit/shared/durable_write.py` | Temp→fsync→rotate `.prev`→`os.replace` with WinError-32 retry, plus validate-with-fallback load. Shared by the Q-table and the training checkpoint (`os.replace` is not atomic on Windows) |
| `training/curves.py` | CSV append per episode: `episode, epsilon, alpha, mean_reward, winrate_vs_baseline, fallback_rate, role` (rule 42) |
| `training/plot_curves.py` | matplotlib → README PNGs. The only matplotlib importer in the repo |
| `artifacts/qtable_{police,thief}.json` | The shipped trained tables — human-readable and diffable, never pickle |

## Interfaces & contracts

```python
# strategy/base.py
@dataclass(frozen=True)
class Observation:
    own_cell: tuple[int, int]
    target_cell: tuple[int, int]   # Phase 3: known target. Phase 4: belief argmax. SAME contract.
    blocked_mask: int              # agent-relative blocked directions
    barriers_used: int
    turn_index: int

@dataclass(frozen=True)
class Decision:
    move: tuple[int, int]
    source: MoveSource                       # QTABLE | FALLBACK | HEURISTIC — provenance is
                                             # a field, not an inference (AI-SPEC E2, E3)
    barrier: tuple[int, int] | None = None   # cop-only; the thief's is always None

class BrainBase(ABC):
    # Both take the GameState explicitly: Observation is the encoded Q-key input and
    # deliberately carries no board, but bfs/fallback/choose_barrier all need the real one.
    def _pick_move(self, obs: Observation, state: GameState) -> Decision: ...
    def _decide_move(self, obs: Observation, state: GameState) -> Decision: ...

# constants.py — the canonical action space; order is FROZEN (renumbering invalidates
# every trained table while still loading successfully)
class Action(IntEnum): NORTH; SOUTH; EAST; WEST; STAY
cell_for(action, own_cell) -> tuple[int, int]
action_for(own_cell, dest) -> Action

# strategy/registry.py
build_brain(role, params) -> BrainBase        # role: "cop" | "thief"; unknown class name raises

# strategy/pathfind.py
bfs(state, start, goal, agent, params) -> tuple[int, tuple[int, int] | None]
                                              # (optimal distance, next step) — barrier-aware.
                                              # Unreachable goal returns (UNREACHABLE, None)

# strategy/prior.py
spread(prior, state, agent, params) -> dict[tuple[int, int], float]   # prediction step, no evidence
argmax_cell(prior) -> tuple[int, int]

# strategy/encoding.py
encode_state(obs, params) -> str              # canonical string — JSON keys must be strings
turn_bucket(turn_index, params) -> int        # early | mid | late, boundaries from config

# strategy/qtable.py
class QTable:
    get(key, action) -> float ; set(key, action, value) -> None
    visits(key) -> int ; best_action(key) -> int
    load(path) -> QTable ; save(path) -> None          # fail-loud on corrupt input

# training/harness.py
run_episode(cop_brain, thief_brain, params, rng) -> EpisodeResult   # steps sdk.engine only
```

## Phase ADRs

| # | Decision | Rationale | Alternative / trade-off |
|---|----------|-----------|-------------------------|
| P3-1 | No RL framework — stdlib `dict` + JSON | 5 actions and a bounded state key make this a tabular problem; a framework adds a torch dependency and makes the policy opaque, against the ≤150-line and grader-readability standards | Gymnasium/SB3/RLlib: rejected — see 03-AI-SPEC.md §2 |
| P3-2 | Training steps `sdk.engine` directly, never the network layer | The Phase-1 SDK is pure and synchronous, so episodes run in-process at full speed; routing training through FastMCP would make hundreds of thousands of episodes impossible and couple the learner to transport | Train over MCP: rejected — orders of magnitude slower, and a network flake would corrupt a run |
| P3-3 | Barriers enter the state key as an **agent-relative blocked-direction bitmask**, never the full board bitmap | The full 7×7 bitmap explodes the state space so every key stays unvisited — the policy would be the fallback in disguise | Full bitmap: rejected — never converges |
| P3-4 | Absolute (own cell, target cell) pair as the positional core | 49×49 is affordable, and edge/corner effects are *learned* — which is the essence of cornering play | Relative offset only: loses the board-edge information cornering depends on |
| P3-5 | Turn enters as a bucketed phase, not a raw index | Lets the thief learn end-game stalling toward the 35-turn survival threshold without a 35× table blow-up | Raw turn: 35× sparser for almost no extra signal |
| P3-6 | Fallback triggers on **visit count**, not just key absence | A key seen twice carries noise, not policy; acting on it looks trained and plays worse than the heuristic | Absence-only trigger: ships confident nonsense on the sparse tail |
| P3-7 | Fallback distance is BFS, not Manhattan | Manhattan walks into barrier pockets — precisely the situations the cop creates on purpose. The name "Bayes + Manhattan" is kept for STRAT-02 traceability; the metric is barrier-aware | Raw Manhattan: fails GATE-1's pocket case |
| P3-8 | Separate Q-table per role, loaded per process | Project rule 2 — a shared live table or state object is an information-leak disqualification, and it also keeps the Phase-8 repo split clean | Shared table: disqualification |
| P3-9 | Q-table persists as JSON, never pickle | Diffable, grader-openable, and no arbitrary-code-execution on load | Pickle: rejected in CONTEXT |
| P3-10 | Two fully playable brains behind `BrainBase` | `HeuristicBrain` is both the fallback's logic home and the objective baseline for GATE-4 — without a playable baseline, "the RL learned something" is unfalsifiable | Q-only: no way to prove the phase goal |
| P3-11 | `random` (seeded) for ε-greedy, `secrets` reserved for Phase 6 nonces | Training must be reproducible, which is exactly what `secrets` prevents; conflating them would either break reproducibility or weaken the crypto | One shared RNG helper: blurs a security boundary |
| P3-12 | Matplotlib is dev/training-only | Keeps the shipped agent's runtime dependency list at `fastmcp` alone; nothing on the decision path imports it | Runtime dep: unnecessary weight on the league agent |

## Test plan (TDD)

- **Unit:** `tests/unit/strategy/` — one file per module, happy path + error case per public
  function. Every brain test injects a seeded RNG and explicit params, so selection is
  deterministic. Q-table tests cover the save→load round-trip and the corrupt-table failure.
- **Gate tests:** `tests/integration/` —
  `test_shortest_path.py` (GATE-1, including the barrier-pocket case that breaks Manhattan),
  `test_policy_fallback.py` (GATE-2, including the `min_visits` boundary itself),
  `test_strategy_pluggable.py` (GATE-3, config-only swap + a structural assertion that the
  decision path reaches no LLM), and `test_beats_baseline.py` (GATE-4, the head-to-head run
  over the fixed scenario set).
- **No test trains a real policy.** Gate tests load a small fixture Q-table; the overnight
  training run is an operator task, not a test. `test_beats_baseline.py` runs the shipped
  table against the baseline over the configured game count with fixed seeds.
- **Coverage target:** ≥85% (`fail_under=85`). `training/` is exercised by unit tests on the
  episode loop, sparring sampler and checkpoint atomicity — it is not exempt.

## Per-mechanism PRDs written this phase

- [`docs/PRD_rl_strategy.md`](../../PRD_rl_strategy.md) — the Q-learning policy (DOC-02).
  Written in Wave 1, **before** the policy code it describes, per SEGAL §2.5 step 5.

## Known limitation

Phase 3 plays blind against a *known* target cell — that is the Stage-3 gate, not the final
game. The belief map that replaces it arrives in Phase 4. The input contract
(`Observation.target_cell` = "a believed target cell") is fixed now precisely so Phase 4
swaps the source of that cell without retraining the table. Until then, GATE-4's
"beats the baseline" result is measured under full target knowledge and will need
re-measuring once belief noise is introduced; that re-measurement is Phase 4 scope and is
recorded here so the number is not later mistaken for a blind-play result.
