# Phase 3: Blind Strategy Module (RL policy) — Research

**Researched:** 2026-07-31 · **Scope:** narrow — only the three STRAT-06 training-harness questions.
**User constraints:** locked in `03-CONTEXT.md` (tabular Q-learning, dict+JSON, no framework, no NumPy,
per-role tables, BrainBase seam, BFS oracle, knobs in config). Not repeated here, per directive.

## 1. The sparring opponent's interface — `rmisegal/Game-P2P-Cop-Chase`

**Repo is public and usable.** Default branch is **`master`, not `main`** (raw URLs on `main` 404). v3.0.0,
pushed 2026-07-12.

### It is drivable IN-PROCESS. This is the decisive finding.

The brains are pure synchronous Python — no I/O, no MCP, no asyncio, no subprocess. Verified by reading the
full source of the five files below at `master`:

| File | Provides |
|---|---|
| `src/police_thief/constants.py` | `Role`, `MoveType{MOVE,BARRIER,HOLD}`, `Direction` (8 king dirs), `DELTAS`, `ORTHOGONAL`, `directions_from_move_set()` |
| `src/police_thief/domain/board.py` | `Board(size, moves=None)` — `legal_moves`, `step`, `distance`, `neighbors` |
| `src/police_thief/domain/own_state.py` | `OwnGameState(role, start, board_size, move_set=None)` — `.position`, `.barriers`, `.my_barriers`, `apply_move(move_type, direction, barriers_max) -> bool` |
| `src/police_thief/domain/belief.py` | `BeliefGrid(board_size, smell_trust=4.0, orthogonal=False)` — `observe_smell`, `diffuse`, `exclude`, `most_likely()` |
| `src/police_thief/domain/brains.py` | `BrainBase`, `PoliceBrain`, `ThiefBrain`, `Decision` |

**That subgraph is stdlib-only** (`logging`, `random`, `time`, `dataclasses`, `enum`) — **no fastmcp, no
third-party anything.** Verified line by line.

```python
brain = PoliceBrain(llm=None, rng=random.Random(seed), trash=_DUMMY)   # trash must be non-None
move_type, direction = brain._decide_move(state, belief, barriers_max)  # pure, sync, microseconds
state.apply_move(move_type, direction, barriers_max)
```
Do **not** call `brain.decide(...)` — it invokes `TrashTalk` (the LLM/banter path). A non-`None` `trash` also
suppresses the lazy `strategy.trash_talk` import, so `strategy/`, `peer/`, `infra/` never load.

### Four adapter translations the plan must budget for (each verified from source)

1. **Move set.** `Board(size, moves=None)` falls back to **8-direction king** movement. Construct
   `OwnGameState(..., move_set=["N","S","E","W"])` or the reference agent emits diagonals our 5-action engine
   rejects. `directions_from_move_set` drops `STAY`/`HOLD` itself.
2. **Belief seeding.** `BeliefGrid` starts uniform and `most_likely()` returns the first argmax = `(0,0)`, so
   a raw reference agent walks to the corner. Phase 3's contract is a *known* target: seed with
   `belief.observe_smell({f"{r},{c}": 1.0})` (scales that cell ×5, then normalizes → argmax).
3. **Barrier semantics.** `MoveType.BARRIER` **replaces** the move that turn and walls the neighbour cell in
   `direction`; `PoliceBrain.barrier_chance = 0.15` is a hardcoded class attribute. Our engine must match, or
   the adapter translates.
4. **Strength calibration.** `Board.distance` is Manhattan/Chebyshev and **barrier-blind**; `PoliceBrain`
   argmins over it, so the reference cop routes into barrier pockets. It is a *sibling* of our
   `HeuristicBrain`, not a strong opponent — do not over-invest in this adapter.

### `uv add` is impossible; the license forbids vendoring

Theirs: `requires-python = ">=3.13"`, `fastmcp>=3.4.3`. Ours: `>=3.10`, `fastmcp>=3.4.5` (ours satisfies
theirs). **`uv add` can never resolve `>=3.13` against our `>=3.10`.** Their `constants.py` uses `StrEnum`
(**needs ≥3.11**), so the code *runs* on 3.11/3.12 despite the 3.13 metadata but `ImportError`s on 3.10.

`LICENSE` is an **Educational Use EULA** (© Dr. Yoram Segal / GTAI). §4c forbids "redistributing,
sublicensing, publishing, or sharing the Software with any third party" who is not an enrolled Segal student;
§5 requires written consent to "modify, distribute, or adapt". Phase 8 ships **two public repos** — copying
their files in would republish the instructor's EULA'd code inside a graded project. **Vendoring: no.
Submodule: legally safer (stores a URL + SHA, not code) but forces every cloner, incl. the grader, to pull an
EULA'd repo.** **Recommendation (autonomous judgment call): opt-in local clone + path injection.** Config
`[training] reference_impl_path = ""` (empty default), gitignored; the adapter does a guarded `sys.path`
insert + import and, on empty path or `ImportError`, drops the reference opponent and **renormalizes the pool
weights** with a logged warning. Tests use `pytest.importorskip`/`skipif` so CI and the ≥85% coverage gate
stay green without it. Zero redistribution, zero runtime dep, zero resolver conflict.

**Impact on the plan:** the reference partner costs **one small module** (`training/sparring_reference.py`),
not a network/MCP adapter — cheap in-process episodes are available, so the harness keeps its simple shape.
The planner must (a) make it optional and import-guarded with weight renormalization, (b) record an ADR
forbidding vendoring and submodules, (c) add explicit tasks for the four translations, and (d) treat it as a
peer of `HeuristicBrain`, not a strong opponent.

## 2. Past-self checkpointing and pool sampling

**Sample once per episode, never per turn** — mid-episode swaps break the stationarity the Q-target assumes.
The sampled opponent is **frozen, read-only** for the episode; only the learner's table updates (this also
satisfies project rule 2: no shared live table object). **Pool weights** (config `[training] pool_weights`):
heuristic **0.30** / past-self **0.50** / reference **0.20**, renormalized when the reference is absent.

> **Methodological catch worth acting on:** `HeuristicBrain` is *also* the eval opponent (CONTEXT success
> bar). Weighting it much above ~1/3 is training on the test set. The eval set must use **held-out
> start-position seeds** disjoint from training, or "beats the baseline" proves nothing.

**Past-self sampling: δ-uniform** (Bansal et al., ICLR 2018) — sample uniformly from the newest δ fraction of
checkpoint history. δ=1.0 → latest only; δ=0.0 → uniform over all history; **δ=0.5** was best in their
competitive humanoid setting, δ=0.0 best for the simpler ant. Start at **δ=0.5**, config `selfplay_delta`.
Their motivation matches our AI-SPEC failure mode exactly: training only against the most recent opponent
lets one side run away in skill and the other never recovers.

**Cadence and retention:** snapshot every `checkpoint_interval = 10_000` episodes (→ 20–50 snapshots over a
200k–500k run); retain a **ring buffer of the newest 10** (`pool_size`) plus **one pinned early/anchor
snapshot**, so the pool always holds a weak opponent and cannot drift wholesale into one degenerate
equilibrium. (Our heuristic + reference brains are the cheap version of AlphaStar's explicit exploiters;
OpenAI Five used ~80% current self / 20% past — ours is more conservative because the pool already contains
two fixed non-learning anchors.)

**Third anti-collapse lever: decay α, not just ε.** Under a non-stationary opponent a fixed large learning
rate makes Q oscillate rather than converge — add an `alpha` schedule beside the `epsilon` schedule.
**Role asymmetry:** cop and thief will not converge at the same rate. Alternate which role learns per episode
and log **two separate curves and win-rates** — one shared threshold marks one role done while the other is
still random.

**Impact on the plan:** config gains `pool_weights`, `selfplay_delta`, `checkpoint_interval`, `pool_size`, and
an alpha schedule. `training/sparring.py` needs episode-level sampling, a frozen read-only opponent table, and
a ring buffer with a pinned anchor. The eval harness needs held-out seeds.

## 3. Resumable, reproducible overnight runs on Windows/OneDrive

**Checkpoint the run, not just the table.** One `run_state.json`: episode index, both Q-tables + visit counts
(or paths), current ε and α, **RNG state**, seed, config hash, CSV row count. Resuming from a bare Q-table
silently restarts ε and makes the curve unreproducible.

**RNG:** use an *instance* `random.Random(seed)` — never module-level `random.*`, whose global state any
library call can perturb. Exact resume: `rng.getstate()` → `(version, tuple[625 ints], gauss_next)`; persist
as `{"version":3,"keys":[...],"gauss_next":null}`, restore with
`rng.setstate((version, tuple(keys), gauss_next))`. Log the seed in the manifest and the CSV header.

**Atomic write:** temp file **in the same directory** → `flush()` → `os.fsync(fd)` → `os.replace(tmp, final)`.
Three Windows caveats, all of which change the code:
- `os.replace` maps to `MoveFileEx(MOVEFILE_REPLACE_EXISTING)`, **not guaranteed atomic** and can fall back to
  a copy [MEDIUM — python-atomicwrites#25, Go issue 8914]. **Do not rely on replace alone**: rotate
  `run_state.json` → `run_state.prev.json` before replacing, and validate on load (`json.load` + schema
  assert) with fallback to the previous generation.
- **Directory fsync is unavailable on Windows** (cannot open a directory fd) — the prev-generation copy is the
  real protection, not fsync.
- `os.replace` raises `PermissionError [WinError 32]` when the destination is held open by another process
  (OneDrive, Defender, an editor) → bounded retry with backoff.

**OneDrive is the largest concrete hazard.** This repo lives under `C:\Users\Hp\OneDrive\Desktop\...`.
Rewriting a multi-MB Q-table every N episodes inside a synced folder means OneDrive holds the file open to
upload (→ WinError 32 on the next replace), `-DESKTOP-XXXX` conflict copies, flooded version history, and
Files-On-Demand dehydrating a checkpoint into a placeholder that stalls a later read. → **Default
`training.artifacts_dir` to a non-OneDrive path** (e.g. `os.environ.get("LOCALAPPDATA")` + `\pursuit\training\`,
config-overridable, no hardcoded path in `src/`), gitignored. Copy only the final blessed
`qtable_police.json` / `qtable_thief.json` + curve CSV/PNGs into the repo at run end.

**Other Windows long-run gotchas:** **Console QuickEdit** — clicking in a cmd/PowerShell window selects text
and *suspends the process* until Enter; the single most common "the overnight run just stopped" cause, so
redirect output to a file or disable QuickEdit. **Sleep/hibernate** kills the run: `powercfg /change
standby-timeout-ac 0`, or call `ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)` at
harness start behind a `sys.platform == "win32"` guard. **Defender real-time scan** on every checkpoint
rewrite adds latency — exclude the artifacts dir (operator step, not code). **No SIGTERM on Windows**: catch
`KeyboardInterrupt`, write a final checkpoint in `try/finally`, `atexit` as backstop.

**Curves:** append + `flush()` per row (not fsync — too slow). **On resume, truncate rows with
episode > checkpoint episode**, or the curve has a duplicated/rewound segment and the rule-42 README PNG is
wrong. Dump the big table with `separators=(",", ":")` and no `indent`; measure one dump and pick
`checkpoint_interval` so checkpointing stays under ~1% of wall clock.

**Impact on the plan:** add `training/checkpoint.py` (atomic write + prev-generation rotation + WinError-32
retry + validate-with-fallback on load) and `training/runstate.py` (episode/ε/α/RNG-state/seed manifest).
Config gains `artifacts_dir` defaulting **outside OneDrive**. The harness needs a `try/finally` final
checkpoint, CSV truncate-on-resume, and a win32-guarded `SetThreadExecutionState`. Operator steps (output
redirection, QuickEdit, Defender exclusion) belong in `docs/phases/phase-3/TODO.md`.

## Confidence

**HIGH** — Q1 interface/deps/license (full raw source of the 5 modules + `pyproject.toml` + `LICENSE` +
`tests/unit/test_brains.py` at `master`; metadata via `api.github.com`); Q2 δ-uniform and δ=0.5 (Bansal et al.,
*Emergent Complexity via Multi-Agent Competition*, ICLR 2018, arXiv:1710.03748); Q3 RNG-state, CSV and
checkpoint contents (documented CPython `random`/`os` behaviour).
**MEDIUM** — the vendoring recommendation (EULA text verified, the choice is my judgment call); Q2 pool weights
and retention numbers (standard practice scaled to our setting; starting proposals, all config-tunable); Q3
Windows/OneDrive hazards (community reports + documented behaviour, not reproduced experimentally here).
**Not verified:** whether their `sdk/series.py` offers a headless multi-game driver — not needed, since
`_decide_move` is directly callable and cheaper than any driver they ship.
