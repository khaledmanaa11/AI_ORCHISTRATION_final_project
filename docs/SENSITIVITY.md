# Sensitivity analysis

**Which parameters actually move the outcome, measured.** Segal §17 ("systematic experiments,
sensitivity analysis"). Closes `docs/SUBMISSION-CHECKLIST.md` row **G5-02**.

Reproduce every number on this page, offline, with no API key:

```
uv run python scripts/sensitivity_sweep.py        # -> artifacts/sensitivity/sweep.json
uv run python scripts/sensitivity_report.py       # -> the tables below, verbatim
uv run python scripts/sensitivity_reconcile.py    # -> artifacts/sensitivity/reconcile.json
```

`tests/unit/test_research_docs.py` re-renders both generated blocks from the committed
artifacts and compares them against this file, so a figure edited in by hand fails the suite
instead of reaching a grader.

---

## Read these limits first

* **No league game has ever been played.** Nothing here is a competitive result. The
  opponents are the two hand-written archetypes in `src/pursuit/strategy/naive.py`
  (`ChaserCop`, `GreedyEvader`), and a knob that helps against a chaser may do nothing
  against a team that plays differently.
* **The cop matchup is saturated.** `cop vs greedy evader` sits at **200/200** at the
  baseline, so every knob reads `+0.0%` there. That is a ceiling, not a finding, and the
  effect ranking refuses to rank a knob on a saturated matchup at all.
* **One factor at a time, from the shipped configuration.** No interaction between two knobs
  is measured. A full factorial over six knobs is 216 cells and would not answer *which knob
  matters* any better at this sample size.
* **Separability is deliberately conservative.** A row is marked separable only when its 95%
  Wilson interval does not **overlap** the baseline's — stricter than a two-proportion
  z-test, so "SIGNIFICANT" here is not an artefact of the test choice. Most rows are not
  separable, and that is reported rather than smoothed over.
* **n = 200 games per matchup per configuration.** At a 30% base rate the interval is roughly
  ±6.5 points, so an effect under about 10 points is not resolvable here.

---

## What the sweep is allowed to vary, and what it is not

Every number in `docs/PARAMETERS.md` carries a Status. **fixed** deviations disqualify the
team; **minimum** values may be negotiated upward and *never* downward; **negotiable** values
may be agreed freely.

The grid does not get to decide which is which. `scripts/sensitivity_status.py` parses the
Status column out of the extract and `refuse_fixed` fails the sweep when a knob's declared
status disagrees, when it names a row that does not exist, or when it targets a **fixed**
row at all. `refuse_downward` separately fails a `minimum` knob swept below the value this
repository ships. The full list of untouched fixed parameters is printed at the foot of the
generated block below — derived, not typed. Both refusals live in
`scripts/sensitivity_status.py` and are probed in `tests/unit/test_sensitivity_grid.py`.

Two knobs are not Appendix F rows at all and are labelled **engineering default**; each must
cite its source in the grid or `refuse_fixed` rejects it:

| Knob | Not a game parameter because | Source |
|---|---|---|
| `equilibrium_iterations` | regret-matching iteration count, ours to choose | `src/pursuit/strategy/valuebrain.py:29-32` |
| `resolution_rules` | negotiated per pair of teams; deliberately kept **out** of `game_params.json` so rule 11's byte-identity handshake is untouched | `src/pursuit/shared/resolution.py:1-13` |
| `weights` | a fitted artefact, not a rule | `artifacts/run2/weights.json` |

<!-- BEGIN GENERATED: sensitivity -->

Sweep: **13 configurations**, **200 games per matchup**, eval seed `90210`, wall time 755.6s.

Baseline (the shipped configuration): `barrier_quota`=14, `board_size`=7, `cop_start`=[0, 0], `equilibrium_iterations`=200, `horizon`=35/35, `resolution_rules`=race=true,swap=false, `thief_start`=[3, 3], `weights`=run2.

### Effect ranking

| Knob | Largest effect | At | On matchup | 95% separable |
|---|---:|---|---|---|
| `board_size` | +35.0% | 11 | thief vs chaser cop (no seals) | **yes** |
| `horizon` | -29.0% | 70/70 | thief vs chaser cop (seals) | **yes** |
| `resolution_rules` | -25.0% | race=false,swap=true | thief vs chaser cop (no seals) | **yes** |
| `weights` | -18.0% | prior | thief vs chaser cop (no seals) | **yes** |
| `equilibrium_iterations` | -6.0% | 800 | thief vs chaser cop (seals) | no |
| `barrier_quota` | -3.0% | 28 | thief vs chaser cop (no seals) | no |

### Per-matchup detail

**cop vs greedy evader** -- baseline 200/200 = 100.0% [98.1%, 100.0%]  **SATURATED: no upward effect is observable here**

| Knob | Value | Wins | Rate | 95% Wilson | delta | 95% separable |
|---|---|---:|---:|---|---:|---|
| `board_size` | 9 | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `board_size` | 11 | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `barrier_quota` | 21 | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `barrier_quota` | 28 | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `horizon` | 50/50 | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `horizon` | 70/70 | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `equilibrium_iterations` | 50 | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `equilibrium_iterations` | 800 | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `resolution_rules` | race=false,swap=false | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `resolution_rules` | race=false,swap=true | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `resolution_rules` | race=true,swap=true | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |
| `weights` | prior | 200/200 | 100.0% | [98.1%, 100.0%] | +0.0% | no |

**thief vs chaser cop (no seals)** -- baseline 65/200 = 32.5% [26.4%, 39.3%]

| Knob | Value | Wins | Rate | 95% Wilson | delta | 95% separable |
|---|---|---:|---:|---|---:|---|
| `board_size` | 9 | 100/200 | 50.0% | [43.1%, 56.9%] | +17.5% | **yes** |
| `board_size` | 11 | 135/200 | 67.5% | [60.7%, 73.6%] | +35.0% | **yes** |
| `barrier_quota` | 21 | 63/200 | 31.5% | [25.5%, 38.2%] | -1.0% | no |
| `barrier_quota` | 28 | 59/200 | 29.5% | [23.6%, 36.2%] | -3.0% | no |
| `horizon` | 50/50 | 47/200 | 23.5% | [18.2%, 29.8%] | -9.0% | no |
| `horizon` | 70/70 | 50/200 | 25.0% | [19.5%, 31.4%] | -7.5% | no |
| `equilibrium_iterations` | 50 | 55/200 | 27.5% | [21.8%, 34.1%] | -5.0% | no |
| `equilibrium_iterations` | 800 | 61/200 | 30.5% | [24.5%, 37.2%] | -2.0% | no |
| `resolution_rules` | race=false,swap=false | 64/200 | 32.0% | [25.9%, 38.8%] | -0.5% | no |
| `resolution_rules` | race=false,swap=true | 15/200 | 7.5% | [4.6%, 12.0%] | -25.0% | **yes** |
| `resolution_rules` | race=true,swap=true | 16/200 | 8.0% | [5.0%, 12.6%] | -24.5% | **yes** |
| `weights` | prior | 29/200 | 14.5% | [10.3%, 20.0%] | -18.0% | **yes** |

**thief vs chaser cop (seals)** -- baseline 116/200 = 58.0% [51.1%, 64.6%]

| Knob | Value | Wins | Rate | 95% Wilson | delta | 95% separable |
|---|---|---:|---:|---|---:|---|
| `board_size` | 9 | 137/200 | 68.5% | [61.8%, 74.5%] | +10.5% | no |
| `board_size` | 11 | 173/200 | 86.5% | [81.1%, 90.6%] | +28.5% | **yes** |
| `barrier_quota` | 21 | 114/200 | 57.0% | [50.1%, 63.7%] | -1.0% | no |
| `barrier_quota` | 28 | 113/200 | 56.5% | [49.6%, 63.2%] | -1.5% | no |
| `horizon` | 50/50 | 82/200 | 41.0% | [34.4%, 47.9%] | -17.0% | **yes** |
| `horizon` | 70/70 | 58/200 | 29.0% | [23.2%, 35.6%] | -29.0% | **yes** |
| `equilibrium_iterations` | 50 | 109/200 | 54.5% | [47.6%, 61.3%] | -3.5% | no |
| `equilibrium_iterations` | 800 | 104/200 | 52.0% | [45.1%, 58.8%] | -6.0% | no |
| `resolution_rules` | race=false,swap=false | 125/200 | 62.5% | [55.6%, 68.9%] | +4.5% | no |
| `resolution_rules` | race=false,swap=true | 120/200 | 60.0% | [53.1%, 66.5%] | +2.0% | no |
| `resolution_rules` | race=true,swap=true | 111/200 | 55.5% | [48.6%, 62.2%] | -2.5% | no |
| `weights` | prior | 87/200 | 43.5% | [36.8%, 50.4%] | -14.5% | **yes** |

### Fixed parameters the sweep did NOT vary

Derived from `docs/PARAMETERS.md`'s Status column, not typed here; `scripts/sensitivity_status.py`'s `refuse_fixed` fails the sweep if any of them reaches the grid.

- `[number of agents]`
- `[movement range]`
- `[scent strength at source]`
- `[scent decay rate]`
- `[scent field size]`
- `[capture score – cop]`
- `[capture score – thief]`
- `[survival score – cop]`
- `[survival score – thief]`
- `[tie score]`
- `[number of opponents]`
- `[diversity reward]`
- `[minimum games]`
- `[max games per team]`

<!-- END GENERATED: sensitivity -->

---

## What the numbers say

**1. Board size is the single largest lever, and it favours the thief.** Growing the board
from the 7×7 minimum to 11×11 moves thief survival from 32.5% to 67.5% against a barrier-blind
chaser (+35.0 points, separable) and from 58.0% to 86.5% against a sealing one (+28.5,
separable). Both are the strongest separable effects in the sweep. The mechanism is not
mysterious — more cells to hide in, the same 35-turn clock — but it has a direct negotiation
consequence: **board size is a `minimum`, so an opponent may propose a larger board, and
agreeing to one measurably helps our thief seat and costs our cop seat nothing measurable
here.** The cop matchup is saturated, so "costs nothing" is a ceiling statement, not proof.

**2. A longer game is the strongest lever against us.** Raising the move ceiling and survival
threshold together from 35 to 70 drops thief survival against a sealing chaser from 58.0% to
29.0% (−29.0, separable); 50 turns already costs 17.0 points (separable). Both are `minimum`
parameters, so an opponent may legitimately propose a longer game, and this is the one such
proposal that should be resisted. Against a barrier-blind chaser the same change is −7.5 and
−9.0 and is **not** separable, which is itself informative: the extra turns only hurt when the
cop is actually sealing.

**3. Extra barriers beyond the 14-barrier minimum buy the cop almost nothing.** Raising the
quota to 21 or 28 moves the thief's survival by −1.0 to −3.0 points, separable in no matchup.
The shipped quota already exceeds what this cop archetype can use inside 35 turns. Treat a
proposal to raise it as close to free.

**4. The trained vector is worth roughly 15 points of thief survival.** Swapping the run-2
weights for the hand-written `PRIOR` costs 18.0 points against a barrier-blind chaser and
14.5 against a sealing one, both separable. This is the sweep independently reproducing
Phase 3's own claim that the training run mattered — measured here on the negotiated opening
at n=200, not remembered from the training session.

**5. Search depth is not a lever.** Quadrupling the regret-matching iterations to 800, or
cutting them to 50, moves nothing separably (−2.0 to −6.0). `valuebrain.py`'s docstring calls
200 "comfortably converged"; that claim now has a measurement behind it, and the 800-iteration
run cost roughly four times the wall time for no separable gain.

**6. The swap predicate is the one negotiated rule with a large effect.** Agreeing that a
swap counts as a capture costs the thief seat 25.0 points against a barrier-blind chaser
(separable), whether or not the barrier race is also on. The barrier race alone is worth
−0.5 / +4.5 and is separable nowhere. **This confirms the direction of the decision already
shipped in `shared/resolution.py`'s `PREFERRED`** — propose the barrier race, decline the
swap. It does not confirm the magnitude that decision was recorded with; see below.

---

## A contradiction this sweep found, and did not resolve

`docs/phases/phase-3/ENGINEERING-LOG.md` Act 4.3 records the swap decision as costing thief
survival **89% → 1%** against a barrier-blind chaser, and that pair is quoted onward into
`docs/phases/phase-3/PRD.md`, `PLAN.md` and `src/pursuit/shared/resolution.py`'s `PREFERRED`
docstring. This sweep measures the same matchup at **32.0% → 7.5%**.

The direction agrees and the magnitude does not. `scripts/sensitivity_reconcile.py` re-measures
every combination of the two variables that could plausibly explain it — the weight vector
(Act 4.3 predates Act 5's run-2 fit) and the opening (negotiated versus randomised starts).
Both percentages are **parsed out of the log**, not typed into the script, so the comparison
cannot drift from the document it checks.

<!-- BEGIN GENERATED: reconcile -->

`docs/phases/phase-3/ENGINEERING-LOG.md Act 4.3` records **89%** survival book-only and **1%** with the swap. Re-measured at n=200 per arm, every combination of the two variables that could explain the gap:

| weights / rules / opening | Survival | 95% Wilson |
|---|---:|---|
| `prior/book_only/negotiated` | 28/200 = 14.0% | [9.9%, 19.5%] |
| `prior/book_only/randomised` | 90/200 = 45.0% | [38.3%, 51.9%] |
| `prior/swap/negotiated` | 10/200 = 5.0% | [2.7%, 9.0%] |
| `prior/swap/randomised` | 64/200 = 32.0% | [25.9%, 38.8%] |
| `run2/book_only/negotiated` | 64/200 = 32.0% | [25.9%, 38.8%] |
| `run2/book_only/randomised` | 105/200 = 52.5% | [45.6%, 59.3%] |
| `run2/swap/negotiated` | 15/200 = 7.5% | [4.6%, 12.0%] |
| `run2/swap/randomised` | 64/200 = 32.0% | [25.9%, 38.8%] |

The highest arm is `run2/book_only/randomised` at **52.5%** -- still far below the recorded 89%, and no arm approaches 1%. **The cause was not established.**

<!-- END GENERATED: reconcile -->

**What this does and does not license.** The shipped decision is unchanged and needs no
change: declining the swap is still worth ~25 points of thief survival, and the cop seat is
at 100% under all four rule combinations, so the swap still buys the cop nothing. What is
*not* safe is quoting "89% to 1%" as a current measurement. The engine has moved through
Phases 4–6 since Act 4.3 and the archetypes, the resolver and the weights have all changed;
this analysis did **not** re-derive which change is responsible, and says so rather than
guessing. Correcting the three documents that quote the pair is out of 08-09's scope and is
recorded in `docs/SUBMISSION-CHECKLIST.md` as a follow-up.

---

## Negotiable parameters this sweep could not measure

Named here because a sensitivity analysis that quietly omits half the negotiable surface
reads as though the omitted half was tested and found irrelevant.

| Parameter | Status | Why it is not in the grid |
|---|---|---|
| `[hint word limit]` | negotiable | The sweep runs the offline arena, which has no language layer. Its cost side is measured instead in `docs/TOKEN-COST.md`; its *tactical* value would need games with a live model and is the one thing this project cannot do offline. |
| `[game arena]` | negotiable | Same — it only enters the two system prompts. Its prompt-size effect is measured in `docs/TOKEN-COST.md`. |
| `[axis origin]`, `[axis start index]` | negotiable | Presentation of coordinates, not board geometry. They cannot change a game's outcome, only how a cell is named. |
| `[response timeout]`, `[watchdog threshold]` | negotiable | Network-layer deadlines. Nothing in the offline arena waits on a socket, so a sweep here would return a flat line by construction. |
| `[requests per minute]`, `[parallel requests]`, `[wait after error]`, `[retries before failure]`, `[queue depth]` | minimum | Gatekeeper limits. Same reason: no calls are made. |
| `[token budget per series]` | negotiable | Measured in `docs/TOKEN-COST.md` against the recorded live spend, which is the only honest way to move it. |
| `[start position – thief]`, `[start position – cop]` | negotiable | Moved *only* as a dependent of `board_size` — the cop stays in its corner and the thief is re-centred, because Table 13 rows 5–6 describe those seats by position name. Sweeping them independently is a reasonable future experiment and was not run. |

---

## Related

* `docs/TOKEN-COST.md` — the language layer's cost surface
* `notebooks/analysis.ipynb` — these results plotted, offline
* `docs/phases/phase-3/ENGINEERING-LOG.md` — the training runs these weights came from
* `docs/PARAMETERS.md` — the Status column every refusal above is derived from
