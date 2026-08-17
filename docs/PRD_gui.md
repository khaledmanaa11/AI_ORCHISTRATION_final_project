# PRD — The `gui/` package (live dashboard and replay viewer)

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-08-17
**Requirements:** REPORT-02, REPORT-08, QUAL-01, QUAL-11
**Rules:** **8, 9** (local truth only — absolute disqualification), 42
**Phase:** 7 (plans 07-03, 07-06, 07-08, 07-11) · **Related:**
[PRD_display_belief.md](PRD_display_belief.md), [PRD_log_artifact.md](PRD_log_artifact.md)

> **Read §2 before editing anything in `src/pursuit/gui/`.** This package once displayed the
> opponent's exact position while passing every check that existed, and the fix is not
> self-evident from the code. The trap is documented here on purpose.

---

## 1. Mechanism and scope

Two Tk applications, both **thin shells**:

| Module | Code lines | Role |
|---|---:|---|
| `live_app.py` | 83 | the live dashboard entry point |
| `live_panels.py` | 29 | board + heatmap widgets |
| `live_sidebar.py` | 27 | turn/state/timer readouts |
| `replay_app.py` | 132 | the replay viewer entry point |
| `replay_panels.py` | 49 | step-through widgets |
| `widgets.py` | 38 | shared widget constants |
| `__init__.py` | 27 | exports |

**In scope:** widget construction, layout, event wiring, and reading an already-published
snapshot. **Out of scope — deliberately:** every derivation, redaction, verification and
verdict. Those live in `src/pursuit/sdk/` (`local_view.py`, `view_builder.py`, `view_publish.py`,
`view_snapshot.py`, `view_render.py`, `view_text.py`) and in
`services/reporting/replay_verify.py`.

### 1.1 Why the logic is not here

`pyproject.toml` **omits `*/gui/*` from coverage**. Any logic placed in this package is invisible
to the coverage gate — it can be wrong in ways no test measures. That is the entire reason for the
split, and it is enforced by `tests/unit/test_gui_structural.py`, not by good intentions.

The same reasoning bars `scripts/`: `scripts/check_line_limit.sh:18` scans `src/**`, `tests/**`
and `training/**` only, so logic parked in `scripts/` escapes **both** the coverage gate and the
150-line gate. Neither package is a place to put thinking.

---

## 2. The rules 8–9 firewall — including the defect that got past it

Rules 8–9 make displaying the true objective board an **absolute disqualification**. CLAUDE.md
lists it among the cheapest ways to score zero and names it "the tempting debugging shortcut".

### 2.1 What went wrong (07-11, reproduced end to end)

`turn_language.py:57` returns `ctx.state.thief` — the engine's ground truth — as `known_cell` on
every turn after the first. `beliefadapter.py:126-128` fed it to **both**
`observe_exact(known_cell)` and `emit_opponent(known_cell)`, and `belief.py:57` set a hard
1.0/0.0 delta on that cell.

So the cop's "belief map" was not a belief. Measured, with the real `config/police/*.json`:

```
ctx.state.thief (engine truth): (5, 3)
known_opponent_cell returned  : (5, 3)      identical: True
published belief.argmax       : (5, 3)      entropy: 1.88   support: 5 of 49
geometric inversion           : [(5, 3)] == truth? True
scent.opponent argmax         : (5, 3) at 0.9  == scent.json "source" exactly
sealed thief (2 of 14 barriers): one lit cell, P=1.0, entropy -0.0
```

Visible in production logs, not only fixtures — cop `belief_entropy` across a real game read
`5.6108, 1.8800, 1.8800, 1.8800, 1.7159` while the thief's read `5.6131, 5.6100, 5.5183, 5.4697`.
A panel drawing only *pinned, legal* `LocalView` fields displayed the thief's exact cell.

### 2.2 The trap — measured, not theorised

**Deleting `BeliefView.argmax` makes the syntactic scanner return `[]` while the leak survives
intact.** The true cell stays recoverable from `belief.rows` **by geometry**: `observe_exact`
gives a delta, `belief_motion.spread:52-66` disperses it only over that cell's legal
destinations, and `belief.py:80` multiplies pointwise so a zeroed cell never reopens — leaving a
published support that is exactly the legal-move *plus* centred on the true pre-move cell. The
centre of a plus is uniquely recoverable.

> **Any fix here must be validated by a GEOMETRIC recovery test, never a coordinate-absence
> test.** A coordinate-absence test passes against a scanner that is blind — proven by mutating
> `coordinate_hits` to always return clean: the absence test stayed green while three
> counter-controls went red.

### 2.3 Why nobody owned it

`beliefadapter.py:120-123` states in its own docstring that state keeps carrying the true joint
position because *"rule 3's 'local truth' is a display-layer concern, not this one's"*. The
strategy layer explicitly delegated rule 9 to the display layer; the display layer then published
the value unredacted. Each behaved reasonably and the rule fell through the gap.

The provenance was always protocol-legitimate — the thief's own honest Reveal, folded in by
`turn_resolve`. **Rule 9 governs the display, not the provenance.**

### 2.4 The fix (07-11)

A **display-only `BeliefMap`**, never fed `ctx.state.thief`, published in place of the strategy
belief. The rejected alternative — publishing only when `observe_exact` did not fire — yields a
permanently blank cop panel, since `known_cell` is returned every turn after the first; it hides
the leak by deleting the feature. `scent.opponent` is redacted on a contaminated view, because it
leaked independently.

Redaction keys on a **contamination flag, never on the role string** `"cop"`, so it still holds if
the thief ever gains exact knowledge. Measured after: argmax `(1,3)`, entropy `5.5469`, support
47/49, P(truth) `0.0223`, inversion `[]`. The thief's published belief is byte-identical before
and after (sha256 `0b046a94…`) — this was a **cop-seat defect**, and the thief's genuinely
multi-modal belief is the panel that is honestly impressive.

### 2.5 Quantisation — a second channel, closed in 07-06

Compliant *numbers* can still be drawn into a leak. A heat ramp that rounds small probabilities to
the background paints a **smaller** support than published, and a five-cell drawn plus names its
centre. `view_render.shade` therefore reserves `BACKGROUND_COLOUR` for exactly zero, and the
load-bearing assertion is an **equality between drawn and published support**, before any
inversion. Measured drawn/published ratios: `scent.own` 22.50, `scent.opponent` 2.66,
**`belief` 1.57** — the near-uniform belief would have hidden the defect behind the very panel it
endangers.

---

## 3. Topology (D-76)

The dashboard is a **separate process** fed by a snapshot the agent publishes, not a widget inside
the agent. Three measured reasons:

1. `tk.mainloop()` blocks the asyncio loop that `Watchdog` (`watchdog.py:116-123`, 60 s,
   `os._exit(1)`) is timing.
2. Tk is not thread-safe, and a polling thread could sample the pure 1.0/0.0 delta window between
   `observe_exact` and `predict`.
3. A separate process **cannot hold `ctx.state` at all** — which promotes the firewall from a
   type-level guarantee to a process-level one.

`live_app.py` imports exactly `sdk.view_snapshot.read_snapshot` and `sdk.view_text` — no
`pursuit.network`, no `ctx`. The publisher runs on the agent's own loop, in
`turn_resolve.maybe_resolve`.

### 3.1 The refresh interval has no source, and is not invented

No document gives one, and reusing `watchdog_poll_seconds` would make one number serve two
purposes. It is a **required keyword-only argument with no default**, supplied by the launcher as
a required `--refresh-ms`; omitting it exits 2. The operator states the number; the repository
states none.

---

## 4. What the CI gate does and does not prove

`scripts/check_local_truth.py` walks `src/pursuit/gui/` for forbidden **imports** and
`<x>.state.{cop,thief,barriers}` **attribute chains**. It exits 2 — never 0 — on an empty scan
set, because a gate that reports OK for having looked at nothing is worse than no gate.

**It is an import/attribute gate, not a disclosure gate.** Run against a synthetic panel that
markers `belief.argmax` and labels the `scent.opponent` peak, it returned `violations: []`,
exit 0. It cannot see §2.2's geometric leak and never will.

> **Do not cite this gate as evidence that a belief or scent panel is safe, and do not let it be
> the only gate a change satisfies.** The runtime proof is
> `tests/unit/test_local_truth_recovery.py`, which builds a production-wired view and *attempts
> recovery*: argmax, scent argmax, geometric inversion, and support/entropy floors.

Known remaining limits, recorded rather than implied away: a parameter named `state`, and a
coordinate that is *drawn* rather than stored.

---

## 5. Interfaces

```python
# src/pursuit/sdk/view_snapshot.py
def read_snapshot(path: Path) -> LocalView | None: ...

# src/pursuit/sdk/view_publish.py   (runs on the agent's loop)
def publish_view(ctx, path: Path) -> None: ...

# src/pursuit/services/reporting/replay_verify.py
def open_replay(path: Path) -> ReplaySession: ...   # .verdict is what the banner renders
```

The replay viewer's three banner states are earned, never assumed — `Verified OK` only when every
hash recomputes **from the artifact alone** (proven with `.jsonl` and `.ledger.jsonl` deleted from
disk), `FAILED` naming the turn, and a distinct `Nothing to verify` so a zero-turn artifact can
never read as OK.

---

## 6. For whoever edits this package next

- Draw only from the **published, redacted** view. Never `ctx.state`, never the strategy belief,
  never `known_cell`. If a panel wants data the published view lacks, that is a finding — not a
  reason to reach further in.
- Put no logic here; coverage cannot see it. Put none in `scripts/` either.
- Validate any firewall change with a **geometric recovery test**. `test_local_truth_recovery.py`
  pins `test_the_argmax_only_fix_would_still_leak` permanently so the fake fix cannot return.
- The local-truth CI job goes green because the code is clean. **Never by softening the gate**
  (D7-6).
