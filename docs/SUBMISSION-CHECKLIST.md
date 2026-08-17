# Submission Checklist — the §17 + Table-5 gap register

**Version:** 1.00 · **Owner:** 08-01 · **Measured:** 2026-08-17 (re-measured after 08-08) ·
**Status:** 8 GAP / 65 PASS / 13 UNJUDGED

> **This file is a report, not a source.** Every number in it comes from
> `uv run python scripts/check_submission.py`, which re-derives all 86 rows from the tree on
> each run. Run the gate, do not edit the counts here by hand.
>
> ```bash
> uv run python scripts/check_submission.py                    # 0 all-pass · 1 any GAP · 2 judged nothing
> uv run python scripts/check_submission.py --run-suite        # also runs pytest --cov (T5-10)
> uv run python scripts/check_submission.py --json out.json    # full evidence
> uv run python scripts/check_submission.py --empty-probe      # must exit 2, never 0
> ```

## Why this is a script and not a list

A prose checklist cannot fail, cannot be re-run after a fix, and cannot notice a regression.
This one exits **1** on any gap and **2** when its evidence set judged *nothing* — the exit
contract `scripts/measure_gate7.py` established, and D-82's requirement. Three separate gates
in this repository have now been caught reporting OK for having looked at nothing, and one of
them was protecting a disqualification rule.

**`UNJUDGED` is not a pass.** §17 names items no script can see — "TDD, tests written
before/with the code", "OOP with no duplication", "0 hardcoded values". Table 5's own
*Enforced by* column marks those `Code review` and `Work process`. Scoring them PASS because
a file exists is precisely the dishonesty the gate is built to refuse, so they are counted
in their own column and never folded into the pass count.

## Measured state at HEAD

| Group | PASS | GAP | UNJUDGED | GAP was (08-06) | GAP was (08-03) | GAP was (08-01) |
|---|---:|---:|---:|---:|---:|---:|
| 1. Structure & documentation | 26 | 2 | 0 | 6 | 15 | 16 |
| 2. Architecture & code | 7 | 0 | 3 | 0 | 0 | 2 |
| 3. Testing & quality | 4 | 0 | 3 | 0 | 0 | 1 |
| 4. Configuration & security | 15 | 0 | 0 | 0 | 0 | 3 |
| 5. Research & visualization | 1 | 4 | 0 | 4 | 4 | 4 |
| 6. Extensibility & standards | 5 | 1 | 2 | 4 | 4 | 5 |
| T5. Table 5 (§19.1) | 7 | 1 | 5 | 1 | 1 | 1 |
| **Total (86 rows, 73 judged)** | **65** | **8** | **13** | **15** | **24** | **32** |

Evidence JSON: [`docs/phases/phase-8/submission_audit_evidence.json`](phases/phase-8/submission_audit_evidence.json).

### What moved, row by row — 08-03, 2026-08-17

**32 GAP → 24 GAP. Eight rows, and exactly the eight 08-03 owned.** No other row changed
verdict in either direction, which is the counter-control: a hygiene plan that moved a row
it did not own would have changed something it did not measure.

| Row | Was | Now | What actually changed |
|---|---|---|---|
| **G1-15** | GAP | PASS | `docs/RULES.md:97` rule 48 now writes `survival 5/10`, cop-first, agreeing with Table 17 rows 3–4. **No fixed value was touched** — both numbers were already on the line; the *order* was wrong, and the order is what says whose number it is. Recorded in RULES.md's new "Corrections to this extract" section with both citations |
| **G2-05** | GAP | PASS | all **11 of 11** packages declare `__all__` (was 4 of 11). The seven that import nothing declare their submodule inventory — 10/6/54/10/9/3/36 names — derived from `git ls-files` by `tests/unit/test_package_exports.py`, so it cannot decay into decoration |
| **G2-06** | GAP | PASS | `src/pursuit/__init__.py` re-exports `__version__` from `shared/version.py`. Re-exported, never re-typed: `tests/unit/test_package_version.py` refuses any version literal in that file |
| **G3-03** | GAP | PASS | the CI job now runs `--cov-report=xml --junitxml=reports/junit.xml` and stores both with `upload-artifact`, `if: always()`. Proven by running the identical command locally: 2321 passed, 97.44%, `coverage.xml` 290597 B and `reports/junit.xml` 309353 B |
| **G4-06** | GAP | PASS | `git check-ignore -q graph.json` → **exit 0** (was 1) |
| **G4-07** | GAP | PASS | `git check-ignore -q graph.html` → **exit 0** (was 1). Both anchored `/graph.json`, `/graph.html`, so a subdirectory's own file cannot be hidden |
| **G4-21** | GAP | PASS | **28 of 28** tracked config JSONs carry `version` (was 24 of 28). Neither `resolution.json` nor `role.json` feeds a peer-compared digest — `config_digest` is taken over `game_params.json` only — so rule 11 is untouched |
| **G6-03** | GAP | PASS | `LICENSE` exists, and `pyproject.toml` declares `license` and `authors`. **Structurally closed, legally open** — see the licence block below |

**Group 4 is now 15 PASS / 0 GAP, and group 2 and group 3 are 0 GAP.** The 24 that remained
after 08-03 belonged to 08-06 (README, 9 rows), 08-07 (architecture/25010/extension points,
4), 08-08 (the three per-mechanism PRDs, 3), 08-09 (research and visualization, 4),
08-11/08-12 (the tag and T5-06's version reconciliation, 2), and 08-06+07-10 jointly
(screenshots, 2). **08-06 has since closed its nine**, leaving 15 — see the next section.

Two things 08-03 deliberately did **not** move:

- **G1-05 and G1-06 stay GAP.** They judge the *README's* headings, not the existence of
  `CONTRIBUTING.md` and `LICENSE`. Both files now exist; adding the two headings is part of
  08-06's rewrite of a file whose opening paragraph is still factually wrong about the
  shipped strategy. Closing a README row from a hygiene plan would have meant editing around
  that.
- **T5-06 stays GAP.** `version.py` reads `1.00` and `pyproject.toml` reads `1.00.0`. D-79
  derives the tag name from the reconciled value, so reconciling it is 08-11's, not a
  drive-by in a plan that was editing `pyproject.toml` anyway.

### What moved, row by row — 08-06, 2026-08-17

**24 GAP → 15 GAP. Nine rows, and exactly the nine 08-06 owned.** No other row changed
verdict in either direction — same counter-control as 08-03's pass.

| Row | Was | Now | What actually changed |
|---|---|---|---|
| **G1-01** | GAP | PASS | an `## Installation` section with prerequisites, a five-step block, environment setup and a six-row troubleshooting table. `--check-config` is documented as the install check and its real output is quoted |
| **G1-02** | GAP | PASS | `## Usage — running a game`: the two-terminal league path, `dev_launch.py`, and both GUI processes, each with a flag table |
| **G1-03** | GAP | PASS | `## Examples and screenshots`: an end-to-end run, a one-liner that prints the shipped weight vector, and the artifact inventory |
| **G1-04** | GAP | PASS | `## Configuration guide`: all eleven per-role config files and the three rules that hold across them |
| **G1-05** | GAP | PASS | a `## Contributing` section pointing at `CONTRIBUTING.md` — the row 08-03 deliberately left, closed by the rewrite that owned the file |
| **G1-06** | GAP | PASS | a `## Licence` section stating **prepared, not adopted**, and that the repository is all-rights-reserved until the owner confirms. `**LICENCE STATUS:**` below is untouched |
| **G1-07** | GAP | PASS | `## Credits and acknowledgements`: author and team code, the two source documents, third-party software, and an AI-assistance disclosure |
| **G1-08** | GAP | PASS | **3 unqualified mentions of a superseded mechanism → 0.** The one remaining mention sits on a line that says it was *superseded* and *withdrawn*; the strategy section describes the matrix-game mover over a learned 15-weight evaluation that actually ships |
| **G1-09** | GAP | PASS | the status table is rebuilt from the `NN-VERIFICATION.md` and `GATE-N-MEASUREMENT.md` files. Phase 3 no longer reads "in progress"; phases 4, 7 and 8 read `human_needed` / NOT verified / NOT verified, because that is what their artifacts say |

**Two rows 08-06 could not close, and did not pretend to.**

- **G1-03b and G5-04 stay GAP — the screenshots do not exist.** Both are produced by 07-10,
  which has not run. The README carries two **marked-absent slots** naming the file each will
  occupy and the plan that produces it. A placeholder image would have closed G1-03b with a
  broken icon, so `tests/unit/test_readme_contract.py` now fails the moment any image link in
  the README resolves to nothing — the slot cannot quietly become a fake asset.

**OQ8-8 (README language) is NOT confirmed and is left open.** `08-CONTEXT.md` says English
and instructs that the book be checked for a Hebrew mandate. `police_thief_p2p.pdf` is in
Hebrew and CLAUDE.md's standing instruction is to work from the extracts and surface a gap
rather than re-derive from the book; `docs/SEGAL_GUIDELINES.md`, `docs/RULES.md` and
`docs/PROJECT_GUIDE.md` contain **no** language requirement for §9.4.2. The README is
therefore written in English on `08-CONTEXT.md`'s instruction, and that is recorded as an
assumption rather than as a confirmation — the same treatment 08-03 gave rule 48's ordering.

### What moved, row by row — 08-07, 2026-08-17

**15 GAP → 11 GAP. Four rows, and exactly the four 08-07 owned.** No other row changed
verdict in either direction — the same counter-control 08-03 and 08-06 each passed.

| Row | Was | Now | What actually changed |
|---|---|---|---|
| **G1-13** | GAP | PASS | `docs/ARCHITECTURE.md` carries **six** rendered mermaid blocks — the repository's first. The gate counted **0** across every tracked doc before this, and its one grep hit was a table cell quoting the command |
| **G6-01** | GAP | PASS | `docs/EXTENSION-POINTS.md`: five seams, each with contract, registration site, config key, current implementations and the test that proves it swaps — plus a table of what is deliberately **not** extensible |
| **G6-02** | GAP | PASS | `docs/ARCHITECTURE.md` also carries §5.1 deployment instructions: the local two-process path, the league-day two-machine path, and both GUI processes |
| **G6-05** | GAP | PASS | `docs/QUALITY-25010.md` maps all eight characteristics, **each in its own section with its own repo evidence**. The whole repository held one line on 25010 before this, `docs/PRD.md:94` |

**The diagrams are checked twice, and the second check found the first defects.**
`scripts/check_diagrams.py` parses every block (fence closure, diagram kind, quote-aware
delimiter balance) and resolves every `src/pursuit/...` label against `git ls-files`;
`tests/unit/test_architecture_contract.py` reads the container diagram **as a graph** and
asserts symmetric peers, no node inside both processes, and the GUI outside both. A
backtick-path citation check over the prose then caught **three fabrications in 08-07's own
first draft**, one of them a script name that does not exist
(`scripts/check_no_llm_in_move.py`; the real gate is `scripts/check_no_llm_in_strategy.py`).

**Rendering was verified out of tree and once**, with `@mermaid-js/mermaid-cli` 11.16.0:
all six blocks produced real SVGs and none contained a `Syntax error` box, while the two
mutations the unit tests use — an unknown diagram kind and an unbalanced bracket — were
**rejected by that renderer**. It is not wired into CI: mermaid-cli needs a headless
Chromium and this suite is offline by rule.

### What moved, row by row — 08-08, 2026-08-17

**11 GAP → 8 GAP. Three rows, and exactly the three 08-08 owned.**

| Row | Was | Now | What actually changed |
|---|---|---|---|
| **G1-M[src/pursuit/sdk]** | GAP | PASS | `docs/PRD_sdk.md`, cited from `docs/mechanism-prd-map.json` |
| **G1-M[src/pursuit/gui]** | GAP | PASS | `docs/PRD_gui.md` existed at `aa75852` but the **register still answered `prds: []`**, so the row was still open. `docs/PRD_display_belief.md` is deliberately still not cited |
| **G1-M-TUNNEL** | GAP | PASS | `docs/PRD_tunnel.md`. The row is derived, not asserted: `tunnel_manager.py` has to exist **and** `docs/PRD_mcp_transport.md` has to still declare tunneling out of scope |

`tests/unit/test_mechanism_prd_contract.py` pins what the walk cannot see — no cited PRD
may carry a SUPERSEDED banner, `PRD_rl_strategy.md`'s banner must still be intact and still
point at `PRD_matrix_mover.md`, `PRD_mcp_transport.md` must still exclude the tunnel (the
derivation `PRD_tunnel.md` rests on), and every backticked path in all three PRDs must be in
`git ls-files`. That last rule caught a second fabricated script name
(`scripts/check_publication_safety.py` never existed; the scan is `scripts/submission_scan.py`).

---

## Group 1 — Structure & documentation · 2 GAP  *(was 6; G1-13 closed by 08-07, the three mechanism rows by 08-08)*

### The root README describes a system this repository does not ship

**Rows G1-08, G1-09 — CLOSED by 08-06, 2026-08-17.** The finding below is the state at 08-01
and is retained rather than rewritten: a defect that was found and fixed is evidence, and
deleting its description would leave the fix looking unmotivated.

**This was an honesty defect under rule 42, not a copy-edit.**

`README.md:7` says each agent "decides moves with a trained tabular **Q-learning** policy
(Bayes + BFS fallback)". Phase 3 **withdrew** that mechanism as unsound under the book's
simultaneous turn order (`docs/PRD_rl_strategy.md` carries a `⛔ SUPERSEDED — DO NOT
IMPLEMENT` banner pointing at `docs/PRD_matrix_mover.md`); what ships is a matrix-game mover
over a learned 15-weight evaluation. The gate derives this rather than asserting it: it reads
the superseded PRD's own H1, extracts `Q-Learning`, and finds **3 unqualified mentions** in
the README — line 7, the phase-3 status row, and the documentation link at line 37 which
introduces the superseded file as "the Phase-3 Q-learning mechanism contract".

`README.md:22` also still calls Phase 3 *"in progress"* while
`.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md` reads
`status: passed`. The gate compares the README's status table against every
`NN-VERIFICATION.md` in the tree and reports phases 01/02/03/06 verified, 03 still shown in
progress.

Roughly 90% of the file is a report on the *withdrawn* Q-learning training run.

**Owner: 08-06** (rewrite). 08-01 only registers it.

**CLOSED by 08-06, 2026-08-17.** Both rows PASS. The gate now finds **0** unqualified
mentions, and the status table is derived from the verification and gate documents. Two
further false statements the gate does not judge were found and fixed in the same pass: the
README documented `uv run python training/plot_curves.py`, a file deleted with the run-1
stack in `f3d9847`, and it presented run 1's figures as *the* learning curves. The figures
for the mechanism that ships are now drawn by `scripts/plot_run2_curves.py` from tracked
artefacts, and `tests/unit/test_readme_contract.py` fails on any repo path quoted in a
command block that does not exist.

### The README fails all seven of §2.1's user-manual items

**Rows G1-01 … G1-07, plus G1-03b. G1-01 … G1-07 CLOSED by 08-06; G1-03b remains open on
07-10's screenshots.** Each is judged on its own — a "README.md exists" check would have
passed the file this table measured.

| Row | §2.1 item | What the gate measured |
|---|---|---|
| G1-01 | installation: prerequisites, step-by-step, env setup, troubleshooting | no heading matches `install / prerequisit / getting started / setup`; the body never mentions prerequisites or troubleshooting |
| G1-02 | usage: modes, flags, CLI/GUI, typical workflow | no heading matches `usage / running / how to run / quick start` — and `gui/live_app.py` + `gui/replay_app.py` both ship |
| G1-03 | examples, code samples, screenshots, use-cases | no heading matches `example / screenshot / demo / use case` |
| G1-03b | at least one code sample **and** one non-curve screenshot | fenced code blocks: yes; images: 3, of which **0** are not a training curve |
| G1-04 | configuration guide | no `configuration` heading |
| G1-05 | contribution guidelines | no `contribut` heading |
| G1-06 | license | no `license`/`licence` heading |
| G1-07 | credits | no `credit`/`acknowledg`/`authors` heading |

**Owner: 08-06** (G1-01…G1-07 — all seven now PASS; G1-03b still open, its screenshots come
from 07-10) · **08-03** (`CONTRIBUTING.md`, `LICENSE`, which G1-05/G1-06's new sections link
to).

### Three central mechanisms have no per-mechanism PRD

**Rows G1-M[src/pursuit/gui], G1-M[src/pursuit/sdk], G1-M-TUNNEL.** §2.3 calls this a
"critical requirement". Thirteen PRDs exist; the inventory is walked from `git ls-files`
(10 packages) and answered from `docs/mechanism-prd-map.json`, so a package added later and
not answered for becomes a new GAP row by itself.

- **`src/pursuit/sdk/`** — Table 5's first row and §4's mandated single entry point, 11
  modules, no PRD. → `docs/PRD_sdk.md` — **CLOSED by 08-08.**
- **`src/pursuit/gui/`** — 7 modules, no PRD. `docs/PRD_display_belief.md` is **not** coverage:
  it governs what a view may *contain* (rules 8–9), not how the six `gui/` files render or
  replay. Reading it as coverage would close this row with a document answering a different
  question. → `docs/PRD_gui.md` — **CLOSED by 08-08**, which supplied the register
  entry the PRD's own commit (`aa75852`) had left empty.
- **the tunnel** — `src/pursuit/network/tunnel_manager.py` is tracked, and
  `docs/PRD_mcp_transport.md:28` puts "ngrok/Localtonet tunneling" **out of scope in as many
  words**, so `network/`'s own PRD provably does not cover it. → `docs/PRD_tunnel.md`
  — **CLOSED by 08-08.**

**Owner: 08-08 — all three CLOSED 2026-08-17.**

### Zero rendered diagrams anywhere in `docs/`

**Row G1-13.** `grep -rl '```mermaid' docs/` now returns one file —
`docs/phases/phase-8/TODO.md` — and that hit is the *grep command quoted inside a table
cell*, not a diagram. The gate counts a block only when its opening fence owns the whole
line, and finds **0 rendered mermaid blocks across every tracked doc**. Every diagram in
`docs/PLAN.md` is ASCII art in a plain code fence.
`tests/unit/test_submission_judges.py::test_the_real_trap_file_is_not_counted_as_a_diagram`
pins this discrimination end to end, and asserts the trap file still contains the string
first so the test cannot pass by losing its subject.

**CLOSED by 08-07, 2026-08-17.** `docs/ARCHITECTURE.md` carries six rendered blocks —
C4's four levels, a deployment view and the four-phase commit-reveal sequence — and the
gate now reports **6 blocks in 1 file**. They are held to the tree by
`scripts/check_diagrams.py` (29 distinct `src/pursuit` labels, all resolving) and by
`tests/unit/test_architecture_contract.py`, which reads the container diagram as a graph.

**Owner: 08-07 — CLOSED.**

### No prompt-engineering log

**Row G1-14.** `docs/PROMPT_LOG.md` does not exist. §8.3 requires it and §17 names it.
**Owner: 08-09.**

### A defect in a grader-facing extract — rule 48's survival pair

**Row G1-15.** `docs/RULES.md:97` writes rule 48 as *"capture 20/5, survival **10/5**"*, while
`docs/PARAMETERS.md` Table 17 rows 3–4 give **cop 5 / thief 10** — both **fixed**. Rule 48's
own capture pair is cop-first (`20/5` = cop 20, thief 5), so its survival pair must be
`5/10`. `.planning/REQUIREMENTS.md` BASE-07 already writes `5/10`. Same numbers, contradictory
ordering, in two documents a grader will open.

The gate derives both halves — it parses the pair out of PARAMETERS and out of RULES and
compares them — so **no number is written down here and no fixed value is touched.**

**CLOSED by 08-03, 2026-08-17. `docs/RULES.md:97` now reads `survival 5/10`.** No fixed value
was changed: both numbers were already on that line and still are, and only the *order* was
wrong — which is precisely what says whose number it is. Under the old ordering rule 48
awarded the **cop** 10 for failing to capture and the **thief** 5 for surviving, inverting the
incentive Table 17 sets, on a page a grader reads.

The correction is **recorded, not slipped in**: `docs/RULES.md` gains a
"Corrections to this extract" section carrying entry **C1** with both citations (PARAMETERS
Table 17 rows 3–4; rule 48's own cop-first capture pair `20/5`), the row that found it, and
the honest limit — **the book itself was not re-read.** `police_thief_p2p.pdf` is untracked
and in Hebrew, and CLAUDE.md's instruction is to work from the extracts and *surface* a
contradiction rather than re-derive one. This extract yielded to PARAMETERS because its own
header says it must: *"All numeric values referenced here live in PARAMETERS.md."* If the
book's Appendix F table is ever checked and disagrees, **both** documents move together and
C1 is superseded rather than deleted.

`tests/unit/test_extract_consistency.py` parses both pairs out of both documents and compares
them, so no number is typed into the test and it cannot pass while the two drift together.

---

## Group 2 — Architecture & code · 0 GAP  *(was 2; both closed by 08-03)*

**PASS:** SDK layer (11 modules) · gatekeeper with rate limits in config · `ruff check .` **0
violations** · every source and test file ≤ 150 code lines over **488 enumerated files** (the
row refuses a zero count, because `check_line_limit.sh`'s no-argument form enumerates via
`git ls-files` and exits 0 vacuously on an empty list — the vacuity already on record in
`05-18-SUMMARY.md`) · a module docstring on all **195** `src/` modules.

| Row | Was | Now | Evidence at HEAD |
|---|---|---|---|
| G2-05 | 7 of 11 packages declared no `__all__` | **PASS** | **11 of 11** declare one. The four API packages list exactly the names they import; the seven that import nothing list their submodule inventory (10/6/54/10/9/3/36 names) |
| G2-06 | `__version__` in **0** `__init__.py` files | **PASS** | `src/pursuit/__init__.py` re-exports it from `shared/version.py` — the single source T5-06 reads |

§14 "professional Python packaging". **Owner: 08-03 — CLOSED 2026-08-17.**

Neither row can decay into decoration. `tests/unit/test_package_exports.py` derives each
inventory from `git ls-files` and fails on a module added without being exported *or* a name
exported after its module was deleted; `tests/unit/test_package_version.py` parses
`__init__.py` and refuses any version literal written there, so only a re-export passes.
Adding `__all__` to `gui/__init__.py` correctly made the rules 8–9 firewall start judging
that file; `local_truth_ast.is_package_marker` was widened **by shape, never by filename**
(one `__dunder__` target whose value `ast.literal_eval` accepts), and
`tests/unit/test_package_marker_admission.py` holds eight refusal cases plus a leaky
`__init__.py` that must still be reported as a violation.

**UNJUDGED (3):** G2-08 OOP/no duplication · G2-09 consistent style and descriptive names ·
G2-10 zero hardcoded values. All three are `Code review` rows in Table 5.

---

## Group 3 — Testing & quality · 0 GAP  *(was 1; closed by 08-03)*

**PASS:** `fail_under` wired in `pyproject.toml` · CI runs `ruff check` **and** `pytest --cov`
· the tracked test suite exists.

| Row | Was | Now | Evidence at HEAD |
|---|---|---|---|
| G3-03 | no test-report artifact produced or stored | **PASS** | the `lint-and-test` job runs `uv run pytest --cov --cov-report=term-missing --cov-report=xml --junitxml=reports/junit.xml` and stores both with `actions/upload-artifact`, `if: always()` so a FAILING run's report is kept too |

§17 names "automated test reports" explicitly. **Owner: 08-03 — CLOSED 2026-08-17.**

**Proven by running it, not by writing it.** The identical command was executed locally:
2321 passed, coverage **97.44%**, `coverage.xml` 290597 bytes and `reports/junit.xml` 309353
bytes, and neither file appeared in `git status` — both are anchored gitignore entries,
because a per-run report committed by reflex is the failure on the other side of this row.
`tests/unit/test_test_report_artifacts.py` parses the workflow's **non-comment lines only**:
its first draft grepped the whole file and passed with the flags deleted, because the
explanatory comment quotes them.

**UNJUDGED (3):** G3-05 measured coverage (run `--run-suite`, or the standing
`uv run pytest --cov`) · G3-06 TDD · G3-07 edge-case documentation.

---

## Group 4 — Configuration & security · 0 GAP  *(was 3; all three closed by 08-03)*

**PASS (12):** `.env-example` with 12 placeholder key lines and no real credential shape ·
**886 tracked text files scanned** for credentials with **0 provider-shape hits and 0
unexempted generic hits**, both positive controls firing · `.env`, `.venv/`, `logs/`,
`.planning/graphs/graph.json`, `.planning/graphs/graph.html`, `graphify-out/`, `run.log`,
`.coverage` and `police_thief_p2p.pdf` each proven ignored by its **own** `git check-ignore`
call · `uv.lock` + `pyproject.toml` present with no `requirements.txt`.

| Row | Was | Now | Evidence at HEAD |
|---|---|---|---|
| G4-06 | `git check-ignore -q graph.json` → exit **1** | **PASS** | exit **0**, via an anchored `/graph.json` rule |
| G4-07 | `git check-ignore -q graph.html` → exit **1** | **PASS** | exit **0**, via an anchored `/graph.html` rule |
| G4-21 | 4 of 26 tracked config JSONs carried no `version` | **PASS** | **28 of 28** carry one (the denominator grew by two when 08-04 added `league.json`) |

**Owner: 08-03 — all three CLOSED 2026-08-17.**

**On G4-06/G4-07.** `graphify update .` writes `graphify-out/` *and* drops `graph.json` /
`graph.html` (~2 MB each) at the repository root; only the `graphify-out/` and
`.planning/graphs/` copies were covered, so **CLAUDE.md:178 asserted something that was
false**. The rules are anchored with a leading slash, so they cover exactly those two root
artifacts and cannot hide a `graph.json` a future subdirectory legitimately tracks.
`tests/unit/test_publication_ignore_rules.py` **parses the claim out of CLAUDE.md** and holds
git to it, so the sentence and the ignore file cannot disagree again.

**On G4-21.** Neither `resolution.json` nor `role.json` feeds a peer-compared digest —
`config_hash.config_digest` is taken over `game_params.json` **only**
(`config_hash.py:14-17`) — so rule 11's byte-identity requirement is untouched and no
handshake changed; 97 integration tests pass unmodified. `tests/unit/test_config_versioning.py`
asserts **value**, not just presence: every tracked config version equals
`shared/version.py`'s `VERSION`, with `weights.json`'s `2.00` the one named exception (it is
versioned on its training generation) and a staleness check so a dropped exception cannot
linger.

### The credential allowlist, and why it cannot rot

The scan splits its patterns in two. **Provider shapes** (`sk-ant-`, `AIza`, `ghp_`) are
unconditional and no allowlist entry can suppress them anywhere. The **generic assignment
shape** (`token = "<16+ chars>"`) also matches five synthetic HMAC fixtures in `tests/`, each
named with a reason in [`docs/credential-scan-allowlist.json`](credential-scan-allowlist.json).
An entry whose file no longer produces a generic match is **stale and fails the row**, so a
deleted or rewritten fixture takes its exemption with it. Both properties are probe-proven
(probes 13a and 13b below).

This is **not** a substitute for 08-03's planted-secret control, which proves the scan catches
a secret placed in a real file. It only classifies what the scan already found.

---

## Group 5 — Research & visualization · 4 GAP

**PASS:** `artifacts/curves/{winrate_cop,winrate_thief,mean_reward}.png` + `curves.csv`, with a
McNemar correction discussed in the README — real statistical work, instrumented from
episode 1.

| Row | Gap | Evidence | Fix lands in |
|---|---|---|---|
| G5-02 | no sensitivity analysis | `docs/SENSITIVITY.md` absent | `docs/SENSITIVITY.md` |
| G5-03 | no analysis notebook | **0** tracked `*.ipynb`; no `notebooks/` despite §2.4 | `notebooks/analysis.ipynb` |
| G5-04 | no screenshots of the running system | **5** tracked images (08-06 added the two run-2 curves), **0** of them not a training curve. A learning curve satisfies rule 42 and §9.4.2 item 4; it is not a screenshot, and counting it as one would answer a different question — which is why adding two curves moved the image count and left this row exactly where it was | `docs/assets/` |
| G5-05 | no token-cost analysis or optimization strategy | `docs/TOKEN-COST.md` absent, though `TokenBudget.report()` already produces the data | `docs/TOKEN-COST.md` |

**Owner: 08-09** (G5-02, G5-03, G5-05) · **08-06 with 07-10's screenshots** (G5-04).

---

## Group 6 — Extensibility & standards · 1 GAP  *(was 4; G6-01, G6-02 and G6-05 closed by 08-07)*

**PASS:** git history — **100%** of the last 200 commits carry a conventional prefix.

| Row | Gap | Evidence | Fix lands in |
|---|---|---|---|
| G6-01 | ~~no documented extension points~~ **CLOSED by 08-07** | `docs/EXTENSION-POINTS.md` documents five seams — `BrainBase`, `Provider`, `MailSink`, `ResolutionRules` and the MCP tool surface — each with its contract, registration site, config key and the test that proves it swaps | `docs/EXTENSION-POINTS.md` |
| G6-02 | ~~no deployment instructions / architecture document~~ **CLOSED by 08-07** | `docs/ARCHITECTURE.md` §5 is a deployment diagram plus §5.1's three real command paths — local two-process, league-day two-machine, and both GUI processes | `docs/ARCHITECTURE.md` |
| G6-03 | ~~no licence file~~ **CLOSED by 08-03 — PREPARED, `AWAITING OWNER CONFIRMATION`** | `LICENSE` now exists (MIT, the conventional academic default) and `pyproject.toml` declares `license = { file = "LICENSE" }` and `authors`. See the block below — this row is structurally closed and **legally open** | `LICENSE` |
| G6-05 | ~~ISO/IEC 25010 is not mapped~~ **CLOSED by 08-07** | the eight characteristic names are parsed out of `docs/SEGAL_GUIDELINES.md` §13 by the gate; **now** `docs/QUALITY-25010.md` does, giving each characteristic its **own section with its own repo evidence**; `tests/unit/test_quality_docs_contract.py` parses the eight names out of §13 rather than typing them, and fails on any cited path missing from `git ls-files`. Before 08-07 the whole repo had one line of content, `docs/PRD.md:94` | `docs/QUALITY-25010.md` |
| G6-08 | no Git tag | `git tag -l` → empty. Rule 41. **The tag is cut in 08-11 and pushed by a HUMAN in 08-12 — this gate never creates or pushes one** | `docs/phases/phase-8/SUBMISSION-RUNBOOK.md` |

**Owner: 08-07 (G6-01, G6-02, G6-05) — all three CLOSED 2026-08-17** · **08-03** (G6-03) ·
**08-11/08-12** (G6-08).

**UNJUDGED (2):** G6-04 thread safety · G6-07 building-block design.

### The licence — the owner must confirm it before anything is published

**LICENCE STATUS:** AWAITING_OWNER_CONFIRMATION

**OQ8-5 is NOT closed.** 08-03 drafted `LICENSE` so the §17 structural gap could stop
being open, and drafting is the whole of what an agent may do here: **a licence is a legal
declaration about the repository owner's own coursework, and no agent is entitled to make
one on their behalf.** The file therefore opens with a `PREPARED, NOT ADOPTED` block naming
what the owner must confirm.

**08-12 must not create a public repository until the owner has explicitly confirmed:**

1. **that MIT is the licence they want** — BSD-3-Clause, Apache-2.0 and "all rights
   reserved" are the usual alternatives, and the university may have a policy that overrides
   the personal preference;
2. **that `Copyright (c) 2026 Khaled Manaa` names the holder correctly** — taken from
   `git config user.name`, which is an identity, not an authorisation;
3. **that the year is right.**

This sits in the same class as the two repo URLs (OQ8-6) and the games-played value
(OQ8-2): prepared by a plan, decided by a human, and **visibly flagged rather than slipped
in**. It is trivially reversible today because **nothing has been pushed** — `git tag -l` is
empty and the mono-repo's commits sit unpublished ahead of `origin/main`. It stops being
reversible the moment 08-12 runs.

`tests/unit/test_packaging_metadata.py` holds the two halves together as a
**biconditional** over the single **LICENCE STATUS** field above. While `LICENSE` carries
its `PREPARED, NOT ADOPTED` block the field must read the awaiting-confirmation token;
when the owner confirms and that block is deleted, the field must be changed to the
confirmed token. Neither file can change its story without the other, so the flag cannot be
dropped by tidying — and the test reads **one anchored line**, not a grep over the page,
because its first draft failed against its own explanatory prose.

---

## Table 5 (§19.1) · 1 GAP

Twelve of the thirteen rows **cite** the §17 rows that measure them and take the worst verdict
among them; nothing is measured twice. A cited row that a run does not produce is a **GAP**,
not a shrug — `submission_table5._worst` refuses an empty backing set by name.

| Row | Gap | Evidence | Fix lands in |
|---|---|---|---|
| T5-06 | the two version sources disagree | `src/pursuit/shared/version.py` `VERSION = "1.00"`; `pyproject.toml` `version = "1.00.0"`. D-79 derives the tag name from the reconciled value, so these must agree **before** a tag exists | `pyproject.toml` |

**Owner: 08-11.**

**UNJUDGED (5):** T5-02 OOP · T5-05 overflow handling (judged by the suite, so `--run-suite`)
· T5-07 TDD · T5-10 coverage (`--run-suite`) · T5-11 hardcoded values.

---

## Registered outside the gate's reach

Two findings a path-and-pattern gate cannot express as a row, recorded here so they cannot be
lost.

### The mandatory `declaration_<game_id>.json` has never been written by a real game

`build_declaration_artifact`, `write_declaration_artifact` and `DeclarationContext` have
**zero production callers**. Re-derived at HEAD:

```
$ grep -rn "write_declaration_artifact|build_declaration_artifact|DeclarationContext" \
      src/ scripts/ training/ --include=*.py | grep -v artifact_declaration
src/pursuit/services/reporting/artifact_config.py:151   (a docstring mention)
src/pursuit/services/reporting/__init__.py:31,32,34,103,123,149   (the re-export)
```

Every other reference is a test. `declaration_` is one of rule 50's four mandatory artifacts
and rule 49 wants four repo links inside it, so a wrapper no game calls means the declaration
content `PARAMETERS.md:165` names has never reached the wire. **Owner: 08-04** (the first
production caller). The gate cannot see this: a "dead code" row would need call-graph
reachability, which `scripts/check_local_truth.py`'s AST walk does for imports but not for
call sites.

**CLOSED by 08-04, 2026-08-17.** `services/reporting/end_of_game_declaration.declare_game` is
the production caller, called once from `end_of_game._report` after both sealed artifacts and
before the reporting chain. Re-run the grep at HEAD and it returns that module. A real
`uv run python scripts/dev_launch.py` game (`game_id` `397b3503b1bfa996`, exit 0) wrote
`declaration_397b3503b1bfa996.json` on **both** seats, each carrying `repo_urls`,
`mcp_server_addresses`, `token_ceiling`, `start_time`, `end_time` and both signed Step-0
envelopes embedded verbatim; the two files are kept at
[`docs/phases/phase-8/declaration-evidence/`](phases/phase-8/declaration-evidence/) with their
keys tabled against `PARAMETERS.md:165`.

Since the gate still cannot see call-graph reachability, the guard is a test:
`tests/unit/test_declaration_reachability.py` asserts the shape of the real source, and probe F
of 08-04 replaced the call site with `declaration_path = None` and made **7 tests fail** — five
integration, two structural. Rule 49's four links are carried as stated-absence markers naming
08-12 rather than guessed URLs, and the games-played figure is left explicitly unset.

### Deferred items #13 and #19

Two latent `commit_reveal=False` evidence defects recorded in a phase-5 file. Not re-measured
by 08-01. **Owner: 08-05**, which must either close both with a revert probe or accept both
against shipped-config evidence **re-measured at HEAD**.

**BOTH CLOSED by 08-05, 2026-08-17** — `112e593` (#13) and `12c3a0c` (#19). Neither was
accepted; the shipped config remains `"commit_reveal": true` on both seats, and both repairs
are on the toggle-off path only.

- **#13** — the second mover's MOVE envelope was stamped one turn into the future.
  `send_move_only` now takes the played turn instead of re-reading `ctx.state.turn` after
  `maybe_resolve`. **The shipped commit-reveal-ON path is byte-identical, measured:** a
  nonce-pinned ON-path drive produced the same fingerprint
  `c79f76aff77180…`, the same three pushes at turns `[0, 0, 0]`, the same `h_commit`
  `6a34ee5c…` and the same single ledger record at turn 0, before and after. `turn =
  ctx.state.turn` is textually unmoved, so **the D-59 hash input and the D-64 join key were
  never in the change's path** — pinned structurally by
  `tests/unit/test_shipped_path_turn_source.py`.
- **#19** — `turn_buffer.await_move` had no type test. It now returns only a MOVE, buffers a
  FINAL_REVEAL, and keeps waiting through anything else. `await_move` has exactly **one**
  production caller — `turn_commit.await_and_respond`'s `if not ctx.security.commit_reveal`
  branch — so a commit-reveal-ON game never reaches it.

**The 05-18 bookmark that was supposed to fail on closure did not fail**, and that is the
finding worth keeping: it counted all nine `MessageType` members, and the nine include MOVE,
whose fixture payload is legitimately malformed. Nine = 1 buffered + 1 awaited + **7 foreign**;
all seven are closed, and the test now derives that partition from `MessageType` and pins the
malformed-MOVE row positively so it can never pad the count again.

---

## Proof that this gate can fail

Thirteen probes. Each broke or repaired a real subject, each asserted **the mutation landed**
before the verdict was read, and each was reverted with the tree verified clean afterwards.

| # | Probe | Result |
|---|---|---|
| 1 | `--empty-probe` end to end | **exit 2**, four emptiness reasons printed, never 0 |
| 2 | full 86-row set, `mechanism_count = 0` | **exit 2** — `EMPTY_EVIDENCE` **outranks** the 32 real GAPs |
| 3 | full row set, `readme_count = 0` | **exit 2**, reason named |
| 4 | rows present but every one UNJUDGED | **exit 2**; `judged = 0` |
| 5 | group 1 — unstage `docs/PLAN.md` | **exactly 1** row flipped: G1-11 PASS → GAP |
| 6 | group 2 — plant a `src/` module with no docstring | **exactly 1**: G2-07 PASS → GAP (196 modules parsed under the probe against 195 at HEAD, 1 offender named) |
| 7 | group 3 — unstage the CI workflow | **exactly 1**: G3-02 PASS → GAP |
| 8 | group 4 — unstage `.env-example` | **2**: G4-01 PASS → GAP **and** its Table-5 citation T5-12 followed it |
| 9 | group 5 — unstage 3 of 4 curve artifacts | **exactly 1**: G5-01 PASS → GAP |
| 10 | group 6 — plant a real 25010 map (positive control) | **exactly 1**: G6-05 GAP → **PASS**, then back to GAP on removal |
| 11 | plant an empty `src/pursuit/probe_pkg/` | **exactly 1 new row**, `G1-M[src/pursuit/probe_pkg]` = GAP, "absent from docs/mechanism-prd-map.json" |
| 12 | plant a 161-code-line `src/` file | **2**: G2-03 PASS → GAP **and** T5-08 followed the citation |
| 13a | add a **stale** allowlist entry | G4-02 PASS → GAP, `STALE allowlist entries: 1` |
| 13b | plant a provider key **inside an allowlisted file** | G4-02 PASS → GAP, `provider-shape hits: 1` — the allowlist could not hide it |

**Probe 11 found a defect in this gate's own work.** The mechanism rows were first numbered
`G1-M01`, `G1-M02`, … in walk order, so inserting one package renumbered every row after it
and a stable register row silently changed its own id. Rows are now identified by the path
they judge (`G1-M[src/pursuit/gui]`), and the probe re-run produces exactly one new row.

**Test-mutation A found a second one.** The first version of the mermaid test asserted only
`_FENCE.match(quoted) is None`, which `.match`'s own anchoring satisfies whatever the pattern
says — the test passed under a deliberately weakened regex. It now also asserts `.search`, and
adds an end-to-end row over the real trap file that first asserts the trap still exists.

---

## What this plan did **not** do

- **Nothing was pushed. No tag was created. No remote was touched.** The gate's only git
  calls are `ls-files`, `log`, `tag -l` and `check-ignore` — all local reads.
- No gap was fixed. 08-01 registers; waves 2–3 close.
- No fixed numeric value was changed. G1-15 reports a disagreement between two extracts and
  reads both numbers out of the documents themselves.

---

*Register written by 08-01 · re-generate with `uv run python scripts/check_submission.py`*
