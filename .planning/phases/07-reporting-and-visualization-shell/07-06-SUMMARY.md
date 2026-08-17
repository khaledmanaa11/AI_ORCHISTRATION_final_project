---
phase: 07-reporting-and-visualization-shell
plan: "06"
subsystem: gui/live-dashboard
tags: [D-74, D-76, OQ-6, D7-6, D7-7, D7-9, D7-15, D7-16, REPORT-08, QUAL-02, QUAL-11, NET-02, rule-8, rule-9, rule-22, rule-38]
one_liner: "A Tk dashboard in a SEPARATE PROCESS fed by a published LocalView snapshot -- which cannot hold the true joint position at all -- plus the render-layer leak the numbers could not have found: quantisation, where a heat ramp that rounds small probabilities to the background draws a support smaller than display.min_support_cells guards, and a five-cell drawn plus names its centre."
requires:
  - "07-03: sdk/local_view.py, sdk/view_builder.py, scripts/check_local_truth.py -- consumed, not re-modelled"
  - "07-11: strategy/display_belief.py -- the FIXED view is what is published; nothing here reaches around it"
provides:
  - "sdk/view_publish.py: publish_view -- one best-effort snapshot per resolved turn, never raises into the turn loop"
  - "sdk/view_snapshot.py: read_snapshot/decode_view -- the GUI process's only input, total over a half-written file"
  - "sdk/view_render.py: every colour, shade, pixel bound and grid position (100% covered)"
  - "sdk/view_text.py: every sidebar string including the newline join (100% covered)"
  - "gui/{__init__,widgets,live_panels,live_sidebar,live_app}.py: 200 code lines of pure widget construction"
  - "scripts/local_truth_ast.py: the hardened AST half of the rules 8-9 gate (alias, getattr, subscript, .pyw, package-marker vacuity)"
  - "network/watchdog.Watchdog.idle_seconds: the read-only freeze reading 07-03 recorded as missing"
  - "network/agent_context.AgentContext.view_history: the per-instance hint accumulator (NET-02)"
affects:
  - "07-09 records the scripted-launch exit code; 07-10 records the --refresh-ms value used for the screenshot (OQ-6)"
  - "07-08's replay viewer inherits the same rule: sdk/local_view.py is the only shape a live panel may consume (D7-8)"
  - "D7-6, D7-7 and D7-9 are all CLOSED here"
tech-stack:
  added: []
  patterns:
    - "A separate PROCESS as a rules-9 mitigation: a viewer that cannot hold the objective board state beats one that merely does not read it"
    - "A colour ramp whose background is reserved for exactly zero, so the DRAWN support provably equals the published support and a numeric floor carries through to the picture"
    - "A gate hardened in the same commit that turns it green, with every blind spot MEASURED OPEN first"
    - "A coverage-omitted directory made safe by moving every derivation out of it, then enforced structurally (zero arithmetic BinOps, zero string building)"
key-files:
  created:
    - src/pursuit/sdk/view_publish.py
    - src/pursuit/sdk/view_snapshot.py
    - src/pursuit/sdk/view_render.py
    - src/pursuit/sdk/view_text.py
    - src/pursuit/gui/__init__.py
    - src/pursuit/gui/widgets.py
    - src/pursuit/gui/live_panels.py
    - src/pursuit/gui/live_sidebar.py
    - src/pursuit/gui/live_app.py
    - scripts/local_truth_ast.py
    - tests/unit/test_view_publish.py
    - tests/unit/test_view_snapshot.py
    - tests/unit/test_view_render.py
    - tests/unit/test_view_text.py
    - tests/unit/test_gui_recovery.py
    - tests/unit/test_gui_structural.py
  modified:
    - src/pursuit/network/turn_resolve.py
    - src/pursuit/network/agent_context.py
    - src/pursuit/network/watchdog.py
    - src/pursuit/network/turn_language_io.py
    - scripts/check_local_truth.py
    - scripts/check_local_truth.sh
    - docs/phases/phase-7/TODO.md
    - .planning/phases/07-reporting-and-visualization-shell/deferred-items.md
key-decisions:
  - "D-76: the live GUI is a SEPARATE PROCESS fed by a published snapshot, not Tk driven by after() off the turn loop. Three measured reasons, all from this tree"
  - "OQ-6: the refresh interval has NO source in any document and is therefore written NOWHERE in src/ -- required argparse argument, required keyword-only constructor argument, no default in either"
  - "The heat ramp reserves its background for exactly zero. This is a rules 8-9 decision: quantisation can shrink the drawn support below the floor that keeps the geometric inversion empty"
  - "The snapshot path is DERIVED from the log path (<uid>.jsonl -> <uid>.view.json), following ledger_path_for. No config leaf, no env var"
  - "The publisher is contained on capture_declaration's model: never raises, never returns a verdict, never touches ctx.state -- since 06-05 a non-zero exit code MEANS an audit mismatch"
  - "gui/ is coverage-omitted, so it holds ZERO derivation -- enforced structurally, not by intention"
  - "The gate was HARDENED in the same commit that turned it green, and all three of D7-9's blind spots were measured open before being closed"
metrics:
  tasks: 3
  commits: 5
  tests_added: 73
  suite: "1974 -> 2047 passed, 0 failed"
  coverage: "97.12% -> 97.19%"
  probes: 18
  completed: 2026-08-17
status: complete
---

# Phase 7 Plan 06: The Live GUI Summary

**Commits:** `56e4d96` (publish) -> `840636b` (the dashboard) -> `ad46940` (the gate, green by code)
-> `dea2a60` (self-audit) -> the docs commit below.

Rule 9 makes displaying the objective board state in the live interface a **project
disqualification**. 07-03 built the read model, 07-11 found and fixed the leak inside it. This
plan is the first thing that actually *draws*, and it answers one question the two of them
structurally could not: **can the true cell be recovered from what a panel PAINTS?**

---

## 1. D-76 — a separate process, and the three measurements behind it

`07-PLAN-OUTLINE.md` Sec7 left this open: *"Drive Tk with `after()` off the turn loop, or run it
in a separate process — decide in the plan, not in the executor."* Decided: **separate process.**

| # | Measurement | Consequence |
|---|---|---|
| 1 | `tk.mainloop()` blocks its calling thread; `Watchdog` is a daemon thread polling `clock() - _last_activity` against `watchdog_threshold` = 60 (`config/*/network.json`) whose action is `os._exit(WatchdogExit.FREEZE)` | Blocking the asyncio loop stops every `touch()` and **kills the agent mid-game**; the peer then declares us `opponent_unresponsive` |
| 2 | Tk is not thread-safe | "Run it in a thread" is not an alternative — and a polling thread could additionally sample the pure 1.0/0.0 delta window between `observe_exact` and `predict` **inside** `decide()` |
| 3 | A separate process **cannot hold the true joint position at all** | D-74's type-level firewall becomes a **PROCESS-level** one — the strongest available answer to rule 9 |

Cost: one snapshot file per agent. **Not shared runtime state** (CLAUDE.md rule 2): each process
writes only its own view to its own path and nothing ever reads the other side's.

The agent's entire contribution is one line at one place — `publish_view(ctx, ctx.view_history)`
at the end of `turn_resolve.maybe_resolve`, the single point at which a joint turn has actually
resolved (the same reason `ScentField.advance` is called there). It runs on the agent's own event
loop: `decide()` is synchronous, so nothing can interleave.

**Containment**, copied from `capture_declaration.send_capture_declaration`: never raises, never
returns a verdict, never touches `ctx.state`. Since 06-05 a non-zero process exit code **means an
audit mismatch** (`main.py:25-29`), so an exception escaping a cosmetic write would forge a
technical-loss signal. `BaseException` is deliberately not caught.

**Measured on a real game** (`dev_launch`, `2db6cc8b039c82e7`): exit 0, both seats
`"matched":true`, outcome `capture`, **zero `technical_win`, zero `watchdog_incident`**, and a
snapshot written on both sides.

## 2. OQ-6 — the refresh interval, raised and resolved without inventing a number

`docs/PARAMETERS.md` Table 19 has no UI row. `network.json`'s `watchdog_poll_seconds` = 1 is the
watchdog's own D-18 engineering default, and reusing it would be one number serving two purposes —
the practice `language_wiring.py:43-47` explicitly refuses.

**Resolution, structural, zero numbers in `src/`:** `--refresh-ms` is `required=True` with **no
`default=`**, and `LiveDashboard.__init__` takes `refresh_ms` as a **required keyword-only
argument with no default**, the pattern `Watchdog.__init__` and `TokenBucket.__init__` already use
(QUAL-11). The operator states the number at launch; the repository states none. 07-10 records the
value used for the README screenshot.

```
$ uv run python -m pursuit.gui.live_app --help          -> exit 0
usage: pursuit.gui.live_app [-h] --snapshot SNAPSHOT --refresh-ms REFRESH_MS [--once]

$ uv run python -m pursuit.gui.live_app --snapshot foo.json
pursuit.gui.live_app: error: the following arguments are required: --refresh-ms   (exit 2)
```

## 3. The finding: **quantisation is a new way to leak**

This is the part 07-11 could not have tested, because it is created by rendering.

`display.min_support_cells` = 6 keeps the published support larger than any one cell's step
neighbourhood, which is what makes the geometric inversion return `[]`. **That floor guards the
published grid, not the drawn one.** A heat ramp that rounded small probabilities down to the
background would paint a *smaller* support than the grid carries — and a five-cell drawn plus
names its centre exactly as loudly as a printed coordinate, off numbers that were themselves
compliant.

So `view_render.shade` reserves `BACKGROUND_COLOUR` for **exactly zero**: every strictly positive
value maps to at least `HEAT_RAMP[0]`. The load-bearing assertion in
`tests/unit/test_gui_recovery.py` is therefore an **equality** between the drawn support and the
published one, asserted before any inversion is attempted.

**And it is not hypothetical, measured on the production view:**

| Grid | support | min | max | max/min |
|---|---|---|---|---|
| `belief.rows` | 47 | 0.01667 | 0.02624 | **1.57** |
| `scent.own` | 9 | 0.08 | 1.8 | **22.50** |
| `scent.opponent` | 49 | 0.05793 | 0.15414 | **2.66** |

The belief posterior is near-uniform, so a dropped bucket would **not** show there — the defect
would hide behind the very panel it endangers. The scent panels, at ratio 22.5, lose cells
immediately. Both halves are asserted, and probe 1 confirms it (**4 failed** when the lowest
bucket is sent to the background).

The same near-uniformity produced a second, smaller correction in my own first draft: I asserted
that the brightest heat stop must not *contain* the true cell, and it **failed** — the top stop
holds 20-odd cells of 49 because `ceil(v/peak * 6)` puts most of a near-uniform board in the last
bucket, and the true cell was among them by arithmetic, not by disclosure. The assertion was
wrong-shaped, not the code: what would be a leak is the top stop **naming** a cell, so it is now
a geometric inversion over the brightest set, with a non-empty guard.

## 4. Rules 8-9, asked at runtime over what the panels paint

`tests/unit/test_gui_recovery.py` drives the whole production chain — real
`decide(known_cell=ctx.state.thief)` -> `publish_view` -> **the file on disk** -> `read_snapshot`
-> the exact `view_render` / `view_text` calls `gui/` makes — and then attacks the result.

**Both counter-controls are present and both fire**, because without them the file proves nothing:

| Control | Result |
|---|---|
| A **leaky panel** (07-11's monkeypatched `DisplayBelief`, i.e. HEAD's leak restored) | drawn support inverts to **`[(5, 3)]`**; the scent's brightest set is **`[(5, 3)]`**; the sidebar prints the peak cell |
| The **argmax-only fake fix** (the peak-cell line deleted from the caption) | the coordinate scan returns **`[]` — a clean verdict** — while the heatmap still inverts to `[(5, 3)]` |
| `lit_cells` neutered to always return `[]` | **6 failed** — the drawn-support reader is proven not inert |
| The sidebar scan asked for a cell the sidebar legitimately prints | **finds it** — the scan is not a no-op |

### 4.1 Verified on the LIVE game, not only on fixtures

`logs/police/2db6cc8b039c82e7.view.json`, with the thief's true cell read from the thief's own
snapshot:

```
thief true cell (from the thief's own seat): (2, 3)
police published belief argmax:  (1, 1)      truth? False
police published belief entropy: 5.5587      (log2(49) = 5.6147)
drawn belief support: 49 of 49   == published support? True
  geometric inversion: []
drawn opponent-scent support: 49 == published support? True
  peak: (2, 2)  truth? False    inversion: []
forward pair [2, 3] anywhere in the file: NONE
flat indices 17 / 23 anywhere:           NONE
```

**One scan hit, and it is a false positive worth recording** (filed as **D7-16**): the scanner
reports both `[row, col]` and `[col, row]`, and the police's own cell that turn was `(3, 2)` — the
reversed encoding of the truth. This is exactly the coincidence `local_view_fixtures.py`'s
docstring says its *chosen* coordinates avoid, here on live data. Confirmed a false positive
rather than assumed: the forward pair and both flat indices are absent. The geometric inversion,
which cannot collide this way, returned `[]`.

The live sidebar also shows `idle: 0.00 / 60.00 s` — the **real** `Watchdog.idle_seconds` reading
flowing through, not the `None` a test double produces.

## 5. `gui/` is coverage-omitted, so it contains nothing worth covering

Measured: `pyproject.toml:38` `omit = ["*/main.py", "*/gui/*", "tests/*"]`;
`check_line_limit.sh:18` enumerates `src/** tests/** training/**`, so `scripts/` escapes the size
gate too. Nothing was parked in either.

| `gui/` | lines | | `sdk/` (covered) | lines | coverage |
|---|---|---|---|---|---|
| `__init__.py` | 23 | | `view_publish.py` | 76 | **100%** |
| `widgets.py` | 38 | | `view_snapshot.py` | 82 | **100%** |
| `live_panels.py` | 29 | | `view_render.py` | 135 | **100%** |
| `live_sidebar.py` | 27 | | `view_text.py` | 86 | **100%** |
| `live_app.py` | 83 | | | | |
| **total** | **200** | | **total** | **379** | |

**The omission covers 200 of 579 new `src/` code lines — 34.5%** — and every one of those 200 is
widget construction or an attribute read. `test_gui_structural.py` enforces that structurally
rather than by intention:

* **zero arithmetic `BinOp`s** (annotation `X | None` is a `BitOr` and is deliberately excluded) —
  every pixel bound, grid position and bucket index is computed in `view_render`;
* **zero f-strings, `.join` or `.format`** — even the newline join between sidebar lines is
  `view_text.as_block`;
* **every `pursuit` import under `pursuit.sdk` or `pursuit.gui`**.

Each scan is paired with a control proving it can fail (`f'{n * 2}' + ', '.join(parts)` reports
`Add`, `Mult`, `f-string`, `join`). The plan's own grep is clean **as prose too**: the four
forbidden spellings (`ctx.state`, `GameState`, `engine`, `pursuit.network`) appear nowhere under
`gui/`, docstrings included, so nobody has to read past a comment to decide.

## 6. D7-6 closed by CODE, and D7-9's three holes measured open first

`scripts/check_local_truth.py` now prints `OK: 5 module(s) scanned`, exit 0 — because the modules
pass, never because the gate was softened. It was **hardened in the same commit**, and every
blind spot was measured before it was closed:

| Hole | At HEAD | After |
|---|---|---|
| a root holding one bare `__init__.py` | **`OK: 1 module(s) scanned`, exit 0** | `EmptyScanError`, **exit 2** |
| `panel.pyw` reading `ctx.state.thief` | **never scanned** (`rglob("*.py")`) | scanned and **reported** |
| `s = ctx.state; s.thief` + `getattr(ctx.state, "thief")` + `asdict(s)["cop"]` | **`violations=[]`, exit 0** | **3 violations**, exit 1 |

The dynamic-key check is on the **key**, not on what it is applied to, which makes it total over
indirections nobody has thought of yet: a view module has no legitimate reason to key anything on
`cop`, `thief` or `barriers`, however it got hold of the mapping.

The gate reached 198 code lines and was **split** into `scripts/local_truth_ast.py`, loaded by
file path so 07-03's standalone property (never imports `pursuit`, runs from a bare checkout)
survives. Both halves are checked **explicitly by path** against the 150-line gate — 140 and 102.

**What is still open is stated rather than papered over** and is written into the gate's own
docstring: a parameter named `state` (`def render(state): ...`) is beyond a single-module AST
walk, and the gate still cannot see a coordinate that is *drawn*. **It is nowhere cited as
evidence about these panels** — the runtime recovery test is.

## 7. Revert probes — eighteen, every count real

Baseline over the ten affected test files: **103 passed, 0 failed**. Each probe asserts the anchor
is present and that the mutation landed before the run; a probe whose mutation did not land is
reported BROKEN, never counted.

| # | Mutation | Result |
|---|---|---|
| 1 | `shade` drops its lowest bucket to the background (**the quantisation leak**) | **4 failed** |
| 2 | `lit_cells` always returns `[]` — the drawn-support reader is inert | **6 failed** |
| 3 | `publish_view` re-raises into the turn loop | **2 failed** |
| 4 | the snapshot is published before both action slots are known | **1 failed** |
| 5 | `view_history` becomes a shared module-level instance (NET-02) | **1 failed** |
| 6 | the belief panel is fed the **strategy** map again (HEAD's leak) | **14 failed** |
| 7 | an absent belief renders as a **fabricated uniform** panel | **1 failed** |
| 8 | an absent idle reading prints `0.00` instead of `unknown` | **1 failed** |
| 9 | `read_snapshot` lets a half-written file raise | **2 failed** |
| 10 | GATE: the bare-package-marker guard is neutered | **2 failed** |
| 11 | GATE: `.pyw` dropped from the scan globs | **1 failed** |
| 12 | GATE: `state_aliases` returns nothing | **1 failed** |
| 13 | GATE: `accessor_key` always None | **1 failed** |
| 14 | GATE: the direct `.state.<field>` chain dropped from the walk | **5 failed** |
| 15 | `panel_grids` blanks a belief panel that WAS published | **1 failed** |
| 16 | the two scent panels share one scale | **3 failed** |
| 17 | the outgoing hint is never recorded — half a conversation | **2 failed** |
| 18 | the published scent is the RAW field again (07-11's half fix) | **4 failed** |

## 8. Four holes the self-audit found in my own work

1. **`lit_cells()` had TEST-ONLY reachability** — the D7-3 finding, in my own code, found by
   grepping production callers for all 33 new public names. Wired rather than excused:
   `view_text._support` now counts the cells the belief panel **actually lights** instead of
   re-counting the positive values, so the caption and the picture are one fact — and
   `test_the_lit_cell_count_matches_the_published_support`, which counts independently, fails the
   moment a ramp change makes them differ. Every other new name has a production caller.
2. **One unguarded assert-bearing loop**, found by an AST scan over all six of this plan's test
   files: `for row, col in fx.BARRIERS: assert ...` — an emptied source would have skipped the
   body and passed. Rewritten as a set comparison, which **fails** on an empty source.
3. **Both `parametrize` tables were inline literals.** Named (`_IDLE_CASES`, `_NOT_A_VIEW`) and
   floored by their own test, because a thinned table skips silently.
4. **Coverage found the one uncovered branch** — a scent-free view, which
   `view_builder._scent_view` genuinely produces. All four new `sdk/` modules are now at 100%.

The AST scan's own limitation is recorded: it flagged `for name in bound:` as unguarded because
the guard above it is `assert bound` rather than a length comparison. Checked by hand; it is
guarded.

## 9. Deviations from plan

### Auto-fixed / adjusted

**1. [Rule 3 — blocking] Four `sdk/` modules instead of the plan's "add `view_render.py` if
`local_view.py` has no room".** Measured first, as the plan asked: `local_view.py` is 110/150 and
`view_builder.py` 147/150, so neither could absorb anything. The split is along real seams —
`view_publish` (write), `view_snapshot` (read), `view_render` (colour/shade/geometry), `view_text`
(strings) — and `view_render` landed at 135. Split, never compressed.

**2. [Rule 3 — blocking] `AgentContext` gains `view_history`.** `HintHistory` is caller-owned by
07-03's design and must survive a turn (`ctx.incoming_hints` holds only the last hint per sender).
Per NET-02 and rule 2 the only correct home is the context, via `default_factory` so two contexts
in one interpreter still share no field. Probe 5 fails when it is made shared. `agent_context.py`
landed at 145/150.

**3. [Rule 2 — missing critical functionality] `Watchdog.idle_seconds`.** 07-03 recorded that
`LocalView.idle_seconds` had to be caller-supplied "because `Watchdog` exposes no public idle
reading and this plan does not edit `network/`". Without it the freeze-timer panel is a static
number. Added as a read-only property that takes no lock and mutates nothing; the live game shows
it flowing through. A watchdog without the reading publishes `None` — the honest "not measured",
never a fabricated `0.0` (probe 8).

**4. [Rule 2] `HintHistory.record_outgoing` wired** in `turn_language_io.compose_and_send_hint`,
after the hint actually goes out. It had **no caller at all** (D7-7); the sidebar would otherwise
have shown half a conversation. Probe 17: **2 failed**.

**5. [Rule 2 — the plan's own D7-9 debt] the gate hardened and split.** In scope: D7-9 names 07-06
as owner, and the plan's success criteria require that an empty `__init__.py` provably not satisfy
the gate. See §6.

### Out of scope, filed not fixed

* **D7-15** — `snapshot_path_for` and `ledger_path_for` are two spellings of one sibling
  convention. Not folded onto a shared helper: `turn_commit_ledger.py` is the D-64 nonce path
  06-05 certified, and the D7-2/D7-4 precedent in this phase is to leave a certified path alone
  rather than rename through it for a one-expression join. `test_view_publish` asserts the two
  agree on the parent directory and the stem, so they cannot drift silently.
* **D7-16** — the reversed-pair scan collision described in §4.1.
* **D7-5** — the recoverable `handshake -> handshake` transition still fires once per run.
  Pre-existing, unrelated, untouched.
* `check_no_llm_in_strategy.sh` is still absent from `quality-gate.yml`. Pre-existing since 03-10,
  recorded by 07-03, and not something to slip into a commit about a different gate.

### Authentication gates

None.

---

## 10. Verification

| Gate | Result |
|---|---|
| `uv run ruff check .` | **All checks passed** (0 violations) |
| `uv run pytest tests/ --cov` | **2047 passed, 0 failed**; coverage **97.19%** (baseline 1974 / 97.12%) |
| `bash scripts/check_line_limit.sh` | **exit 0**, plus all 21 new/touched files checked **explicitly by path** (the no-arg form enumerates via `git ls-files` and passes VACUOUSLY on an untracked file) |
| `uv run python scripts/check_local_truth.py` | **`OK: 5 module(s) scanned`, exit 0** — non-zero count, by code |
| `bash scripts/check_local_truth.sh` | same, exit 0 (the CI-facing wrapper) |
| `uv run python scripts/check_no_llm_in_strategy.py` | **OK: no forbidden imports under `src/pursuit/strategy`** |
| every new `.py` vs `.gitignore` | **none ignored** (D7-10's guard, checked by hand as well) |
| grep `gui/` for `ctx.state` / `GameState` / `engine` / `pursuit.network` | **no hits**, prose included |
| `uv run python -m pursuit.gui.live_app --help` | **exit 0**, `--refresh-ms` shown as required |
| scripted launch, police snapshot | `--once` built every widget, **exit 0** |
| scripted launch, thief snapshot | `--once` built every widget, **exit 0** |
| `uv run python scripts/dev_launch.py` | **exit 0**, game `2db6cc8b039c82e7`, both seats `"matched":true`, outcome capture, **0 `technical_win`, 0 `watchdog_incident`** |
| graphify | refreshed — **9734 nodes / 17412 edges / 579 communities**; `publish_view` at `view_publish.py:90` (degree 17, edge in from `maybe_resolve`), `LiveDashboard` at `live_app.py:47` |

### Rule-38 counters — all four numbers

| | police | thief |
|---|---|---|
| before full `pytest` | 1918 | 1911 |
| after full `pytest` | **1918** | **1911** |
| **suite delta** | **0** | **0** |
| before `dev_launch.py` | 1917 | 1910 |
| after `dev_launch.py` | **1918** | **1911** |
| **one-real-game delta** | **1** | **1** |

Nothing in this plan reads, writes, defaults or reads around the counter. **Nothing transmits:**
both shipped `reporting.json` files still read `dry_run`, and the only thing this plan sends
anywhere is a JSON file into the agent's own `logs/<role>/` directory, which `.gitignore` already
excludes.

### Zero numbers invented

No game parameter is introduced. `CELL_PIXELS` / `CELL_GAP_PIXELS` / `PANEL_PAD` /
`TEXT_WRAP_PIXELS` / `DECIMALS` / `PANELS_PER_ROW` are presentation constants, named rather than
inline per CLAUDE.md's hardcoded-value rule and expressible as nothing else. The number of heat
buckets is `len(HEAT_RAMP)` everywhere, never restated. **The one number a live GUI genuinely
needs — the refresh interval — is not in the repository at all** (OQ-6).

---

## 11. Commits

| Hash | Message |
|---|---|
| `56e4d96` | `feat(07-06): publish one LocalView snapshot per resolved turn, best-effort` |
| `840636b` | `feat(07-06): the live Tk dashboard -- five thin gui/ files over two sdk read models` |
| `ad46940` | `feat(07-06): turn the local-truth gate green by CODE, and close D7-9's three holes` |
| `dea2a60` | `test(07-06): four holes the self-audit found in my own work` |

## 12. What 07-08, 07-09 and 07-10 must know

* **07-09** records the scripted-launch evidence: `--once` exits 0 on this machine (Tk 8.6),
  against both a synthetic snapshot and both seats of a real game.
* **07-10** must state a `--refresh-ms` value for the screenshot and record it there. The
  repository deliberately holds none (OQ-6).
* **07-08's replay viewer** may not render `belief_argmax` from the JSONL while a game is live
  (D7-8), and `sdk/local_view.py` remains the only shape a live panel may consume. If it renders
  a heatmap, **the quantisation rule in §3 applies to it too**: a ramp whose background swallows
  small probabilities can leak from numbers that are themselves compliant.
* **Do not "simplify" `view_render`/`view_text` into `gui/`.** That directory is coverage-omitted;
  the 100% figures above exist because the logic is outside it, and `test_gui_structural.py` fails
  the moment anything moves in.

---
*Phase: 07-reporting-and-visualization-shell*
*Completed: 2026-08-17*

## Self-Check: PASSED

All 25 claimed paths verified present on disk with `[ -f ]` **and** tracked by git with
`git ls-files --error-unmatch` (`07-06-SUMMARY.md` itself untracked until the final commit
below) — the check that would have caught D7-10. All four claimed commit hashes verified
reachable in `git log --oneline --all`.

Every number in this document was produced by a command run in this session, not carried over
from the plan: the two suite/coverage figures, the four counter readings, the eighteen probe
counts, the three dynamic-range ratios, the live-game recovery values, the graph's node and edge
counts, and all 21 line counts (re-measured with the gate's own `awk` after the last edit). The
`gui/` share of new `src/` lines was recomputed independently at the end — **200 / 579 = 34.5%**,
which is what §5 states.

Production callers were grepped for all 33 new public names; **one had test-only reachability
(`lit_cells`) and was wired rather than excused** (§8). Every remaining name has a caller on a
path that reaches `maybe_resolve` or `live_app.main`.
