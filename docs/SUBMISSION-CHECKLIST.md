# Submission Checklist — the §17 + Table-5 gap register

**Version:** 1.00 · **Owner:** 08-01 · **Measured:** 2026-08-17 · **Status:** 32 GAP / 41 PASS / 13 UNJUDGED

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

| Group | PASS | GAP | UNJUDGED |
|---|---:|---:|---:|
| 1. Structure & documentation | 12 | 16 | 0 |
| 2. Architecture & code | 5 | 2 | 3 |
| 3. Testing & quality | 3 | 1 | 3 |
| 4. Configuration & security | 12 | 3 | 0 |
| 5. Research & visualization | 1 | 4 | 0 |
| 6. Extensibility & standards | 1 | 5 | 2 |
| T5. Table 5 (§19.1) | 7 | 1 | 5 |
| **Total (86 rows, 73 judged)** | **41** | **32** | **13** |

Evidence JSON: [`docs/phases/phase-8/submission_audit_evidence.json`](phases/phase-8/submission_audit_evidence.json).

---

## Group 1 — Structure & documentation · 16 GAP

### The root README describes a system this repository does not ship

**Rows G1-08, G1-09. This is an honesty defect under rule 42, not a copy-edit.**

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

### The README fails all seven of §2.1's user-manual items

**Rows G1-01 … G1-07, plus G1-03b.** Each is judged on its own — a "README.md exists" check
would pass this file today.

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

**Owner: 08-06** (G1-01…G1-07, G1-03b screenshots from 07-10) · **08-03** (`CONTRIBUTING.md`,
`LICENSE` for G1-05/G1-06).

### Three central mechanisms have no per-mechanism PRD

**Rows G1-M[src/pursuit/gui], G1-M[src/pursuit/sdk], G1-M-TUNNEL.** §2.3 calls this a
"critical requirement". Thirteen PRDs exist; the inventory is walked from `git ls-files`
(10 packages) and answered from `docs/mechanism-prd-map.json`, so a package added later and
not answered for becomes a new GAP row by itself.

- **`src/pursuit/sdk/`** — Table 5's first row and §4's mandated single entry point, 11
  modules, no PRD. → `docs/PRD_sdk.md`
- **`src/pursuit/gui/`** — 7 modules, no PRD. `docs/PRD_display_belief.md` is **not** coverage:
  it governs what a view may *contain* (rules 8–9), not how the six `gui/` files render or
  replay. Reading it as coverage would close this row with a document answering a different
  question. → `docs/PRD_gui.md`
- **the tunnel** — `src/pursuit/network/tunnel_manager.py` is tracked, and
  `docs/PRD_mcp_transport.md:28` puts "ngrok/Localtonet tunneling" **out of scope in as many
  words**, so `network/`'s own PRD provably does not cover it. → `docs/PRD_tunnel.md`

**Owner: 08-08.**

### Zero rendered diagrams anywhere in `docs/`

**Row G1-13.** `grep -rl '```mermaid' docs/` now returns one file —
`docs/phases/phase-8/TODO.md` — and that hit is the *grep command quoted inside a table
cell*, not a diagram. The gate counts a block only when its opening fence owns the whole
line, and finds **0 rendered mermaid blocks across every tracked doc**. Every diagram in
`docs/PLAN.md` is ASCII art in a plain code fence.
`tests/unit/test_submission_judges.py::test_the_real_trap_file_is_not_counted_as_a_diagram`
pins this discrimination end to end, and asserts the trap file still contains the string
first so the test cannot pass by losing its subject.

**Owner: 08-07.**

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
Correcting the extract against the book is a separate decision; this row registers the
disagreement. **Owner: 08-02 records it; the extract edit needs the book.**

---

## Group 2 — Architecture & code · 2 GAP

**PASS:** SDK layer (11 modules) · gatekeeper with rate limits in config · `ruff check .` **0
violations** · every source and test file ≤ 150 code lines over **488 enumerated files** (the
row refuses a zero count, because `check_line_limit.sh`'s no-argument form enumerates via
`git ls-files` and exits 0 vacuously on an empty list — the vacuity already on record in
`05-18-SUMMARY.md`) · a module docstring on all **195** `src/` modules.

| Row | Gap | Evidence | Fix lands in |
|---|---|---|---|
| G2-05 | 7 of 11 packages declare no `__all__` | only `strategy/` and the three child packages do; `src/pursuit/`, `gui/`, `network/`, `sdk/`, `security/`, `services/`, `shared/` do not | `src/pursuit/*/__init__.py` |
| G2-06 | `__version__` is declared in **0** `__init__.py` files | it exists only as `VERSION` in `shared/version.py` | `src/pursuit/__init__.py` |

§14 "professional Python packaging". **Owner: 08-03.**

**UNJUDGED (3):** G2-08 OOP/no duplication · G2-09 consistent style and descriptive names ·
G2-10 zero hardcoded values. All three are `Code review` rows in Table 5.

---

## Group 3 — Testing & quality · 1 GAP

**PASS:** `fail_under` wired in `pyproject.toml` · CI runs `ruff check` **and** `pytest --cov`
· the tracked test suite exists.

| Row | Gap | Evidence | Fix lands in |
|---|---|---|---|
| G3-03 | no automated test-report artifact is produced or stored | no tracked `coverage.xml`, `junit.xml`, `test-results.xml` or `htmlcov/`; the workflow carries no `--cov-report=xml`, `--junitxml` or `upload-artifact` directive | `.github/workflows/quality-gate.yml` |

§17 names "automated test reports" explicitly. **Owner: 08-03.**

**UNJUDGED (3):** G3-05 measured coverage (run `--run-suite`, or the standing
`uv run pytest --cov`) · G3-06 TDD · G3-07 edge-case documentation.

---

## Group 4 — Configuration & security · 3 GAP

**PASS (12):** `.env-example` with 12 placeholder key lines and no real credential shape ·
**886 tracked text files scanned** for credentials with **0 provider-shape hits and 0
unexempted generic hits**, both positive controls firing · `.env`, `.venv/`, `logs/`,
`.planning/graphs/graph.json`, `.planning/graphs/graph.html`, `graphify-out/`, `run.log`,
`.coverage` and `police_thief_p2p.pdf` each proven ignored by its **own** `git check-ignore`
call · `uv.lock` + `pyproject.toml` present with no `requirements.txt`.

| Row | Gap | Evidence | Fix lands in |
|---|---|---|---|
| G4-06 | root-level `graph.json` is **not** ignored | `git check-ignore -q graph.json` → exit 1. `.gitignore:151-152` covers only `.planning/graphs/graph.json`. CLAUDE.md states these are gitignored build artifacts; at the repo root they are not | `.gitignore` |
| G4-07 | root-level `graph.html` is **not** ignored | `git check-ignore -q graph.html` → exit 1, same cause | `.gitignore` |
| G4-21 | 4 of 26 tracked config JSON files carry no `version` field | `config/{police,thief}/resolution.json` and `config/{police,thief}/role.json`. The two `games_played*.json` counters are excluded **by name and visibly in the row's evidence** — they are live rule-37 state, not configuration | `config/` |

**Owner: 08-03.**

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
| G5-04 | no screenshots of the running system | 3 tracked images, **0** of them not a training curve. A learning curve satisfies rule 42 and §9.4.2 item 4; it is not a screenshot, and counting it as one would answer a different question | `docs/assets/` |
| G5-05 | no token-cost analysis or optimization strategy | `docs/TOKEN-COST.md` absent, though `TokenBudget.report()` already produces the data | `docs/TOKEN-COST.md` |

**Owner: 08-09** (G5-02, G5-03, G5-05) · **08-06 with 07-10's screenshots** (G5-04).

---

## Group 6 — Extensibility & standards · 5 GAP

**PASS:** git history — **100%** of the last 200 commits carry a conventional prefix.

| Row | Gap | Evidence | Fix lands in |
|---|---|---|---|
| G6-01 | no documented extension points | `docs/EXTENSION-POINTS.md` absent, though `BrainBase`, `MailSink` and the provider registry are real seams | `docs/EXTENSION-POINTS.md` |
| G6-02 | no deployment instructions / architecture document | `docs/ARCHITECTURE.md` absent; deployment is one ASCII topology diagram in `docs/PLAN.md` | `docs/ARCHITECTURE.md` |
| G6-03 | **no licence file** | `LICENSE` absent; `pyproject.toml` declares neither `license` nor `authors`. Blocked on **OQ8-5** — publishing a licence is a legal declaration, so the human names it | `LICENSE` |
| G6-05 | ISO/IEC 25010 is not mapped | the eight characteristic names are parsed out of `docs/SEGAL_GUIDELINES.md` §13 by the gate; **no** tracked document names all eight *and* cites at least eight repo paths. The whole repo has one line of content, `docs/PRD.md:94` | `docs/QUALITY-25010.md` |
| G6-08 | no Git tag | `git tag -l` → empty. Rule 41. **The tag is cut in 08-11 and pushed by a HUMAN in 08-12 — this gate never creates or pushes one** | `docs/phases/phase-8/SUBMISSION-RUNBOOK.md` |

**Owner: 08-07** (G6-01, G6-02, G6-05) · **08-03 pending OQ8-5** (G6-03) · **08-11/08-12** (G6-08).

**UNJUDGED (2):** G6-04 thread safety · G6-07 building-block design.

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
by this plan. **Owner: 08-05**, which must either close both with a revert probe or accept
both against shipped-config evidence **re-measured at HEAD**.

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
