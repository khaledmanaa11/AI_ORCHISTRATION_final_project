---
phase: 08-submission-and-league-operations
plan: 07
subsystem: documentation
tags: [mermaid, c4, architecture, deployment, iso-25010, extension-points, contract-tests, segal-17]

# Dependency graph
requires:
  - phase: 08-submission-and-league-operations
    provides: "08-01's scripts/check_submission.py -- the 86-row audit that registers G1-13, G6-01, G6-02 and G6-05 and judges each individually"
  - phase: 08-submission-and-league-operations
    provides: "08-01's submission_common.py (tracked-set reads, the 0/1/2 exit contract) and tests/unit/submission_gate_helpers.load, reused rather than re-implemented"
  - phase: 07-reporting-shell
    provides: "D-76's separate-process GUI and D-74's read model, which the container diagram has to depict correctly or it depicts a disqualification"
provides:
  - "docs/ARCHITECTURE.md -- the repository's first rendered diagrams: C4 x4, a deployment view, the four-phase commit-reveal sequence, plus Sec5.1 deployment instructions"
  - "docs/QUALITY-25010.md -- eight ISO/IEC 25010 characteristics, each in its own section with its own repo evidence"
  - "docs/EXTENSION-POINTS.md -- five real seams with contract, registration site, config key and the test that proves each swaps"
  - "scripts/check_diagrams.py + diagram_parse.py + diagram_graph.py -- a mermaid gate with the 0/1/2 exit contract"
  - "the container diagram read AS A GRAPH, so symmetric peers / rule-2 process separation / D-76's separate GUI are machine-checked rather than asserted"
  - "tests/unit/doc_citation_helpers.py -- a backticked path in these documents is a claim that the path exists NOW, and the suite holds it to that"
affects: [08-08, 08-09, 08-10, 08-11, 08-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "documents given stable, addressable identity by an HTML-comment marker (`<!-- diagram: NAME -->`) the way 08-01 gave rows path-based ids"
    - "structural checker paired with a one-off run of the REAL renderer, and the checker's own findings shown to correspond to renderer failures"
    - "prose citation as a testable claim: a backticked repo path must be in git ls-files"
key-files:
  created:
    - docs/ARCHITECTURE.md
    - docs/QUALITY-25010.md
    - docs/EXTENSION-POINTS.md
    - scripts/check_diagrams.py
    - scripts/diagram_parse.py
    - scripts/diagram_graph.py
    - tests/unit/test_diagram_parse.py
    - tests/unit/test_architecture_contract.py
    - tests/unit/test_quality_docs_contract.py
    - tests/unit/doc_citation_helpers.py
  modified:
    - docs/SUBMISSION-CHECKLIST.md
    - docs/phases/phase-8/TODO.md
    - .planning/graphs/GRAPH_REPORT.md

decisions:
  - "Diagrams are identified by an HTML-comment marker, not by position. 08-01's probe 11 already paid for the positional lesson: inserting one item renumbered every id after it."
  - "The mermaid checker is structural and says so. It is paired with ONE out-of-tree run of the real renderer rather than wired into CI, because mermaid-cli needs a headless Chromium and this suite is offline by rule."
  - "The three binding architectural facts are asserted about the drawn GRAPH -- identical module sets plus an edge each way, no node id in both subgraphs, the gui node outside both -- because a caption saying 'symmetric peers' cannot fail."
  - "A backticked repository path in these documents is a claim that the path exists now; a deleted file is referenced unbackticked. The convention is written into the document it governs."

metrics:
  duration: "~2h"
  completed: 2026-08-17
---

# Phase 8 Plan 07: Architecture Documentation Summary

Six rendered mermaid diagrams — the repository's first — with the container view read back as
a graph so symmetry, rule-2 process separation and D-76's separate GUI process are machine-checked;
plus the ISO/IEC 25010 map and the extension-points register §17 names.

**No `08-07-PLAN.md` exists.** The phase directory holds only `08-CONTEXT.md` and
`08-PLAN-OUTLINE.md`, so this plan was executed from the outline's §9 08-07 entry, and every
finding it predicted was re-derived at HEAD rather than inherited.

## What landed

**Three commits, each atomic.**

| Commit | What |
|---|---|
| `acc5913` | `scripts/diagram_parse.py`, `diagram_graph.py`, `check_diagrams.py` and 15 counter-controls. At this commit the gate exits **2** — there was nothing to judge |
| `072d61d` | `docs/ARCHITECTURE.md` (six diagrams + deployment instructions), `tests/unit/test_architecture_contract.py`, `tests/unit/doc_citation_helpers.py` |
| `5687c39` | `docs/QUALITY-25010.md`, `docs/EXTENSION-POINTS.md`, `tests/unit/test_quality_docs_contract.py` |

### The six diagrams

| Marker | Kind | What it carries |
|---|---|---|
| `c4-context` | flowchart | two agent processes, the opponent, the ngrok edge, the LLM and Gmail. **The LLM node has no edge into any decision path** — rule 25 drawn rather than captioned |
| `c4-container` | flowchart | two subgraphs with **identical** module sets, an MCP edge in each direction, and `gui` / `replay` / `artifacts` / `mail` / `llm` outside both |
| `c4-component` | flowchart | the decision pipeline: hint decode → belief → policy → bluff → commit pack. **The bluff edge leaves the brain; it does not enter it** |
| `c4-code` | classDiagram | the `BrainBase` seam and the three registered brains. The withdrawn `QLearningBrain` is absent on purpose, with the reason written beside it |
| `deployment` | flowchart | two machines, two tunnels, the shared-secret middleware, and the Gmail path marked `dry_run` |
| `commit-reveal` | sequenceDiagram | COMMIT → ACK → REVEAL → FINAL_REVEAL, with the nonce shown only as local until final reveal |

### Accuracy, checked rather than intended

The outline is explicit that depicting these wrongly depicts a disqualification. Each is an
assertion in `tests/unit/test_architecture_contract.py`:

| Binding fact | How the drawing carries it |
|---|---|
| symmetric peers, each server **and** client | the two subgraphs name an identical `src/pursuit` module set; an edge runs POLICE→THIEF **and** THIEF→POLICE; both contain `tools.py` and `peer_runtime.py` |
| no shared runtime state (rule 2) | **no node id is declared inside both subgraphs** |
| the GUI is a separate process (D-76) | the `gui` node belongs to neither subgraph, and neither subgraph names `gui/live_app.py` |
| commit-reveal's four phases | `COMMIT`, `ACK`, `REVEAL`, `FINAL_REVEAL` present **and in order**; any line mentioning a nonce before FINAL_REVEAL must say it stays local |

## Proof the new assertions fail on the old documents

**Run, not asserted.** With the three documents absent (the tree at `aa75852`), the two new
contract files were executed:

```
uv run pytest tests/unit/test_architecture_contract.py tests/unit/test_quality_docs_contract.py
16 failed, 4 passed
```

The four that passed are honestly vacuous — `unresolved_citations` over an empty document is
`[]`, and `QLearningBrain` is absent from a file that does not exist. They are guards, not
regressions, and each is bracketed by a row that **did** fail:
`test_both_documents_are_tracked` and `test_the_citation_scan_is_not_vacuous`.

`scripts/check_diagrams.py` at the same point printed
`rendered mermaid blocks: 0` and **exited 2** — `EMPTY EVIDENCE`, never 0.

For 08-08's contract the same discipline: `5 failed / 6 passed` before the register moved.

## Proof the checker fails on a malformed diagram — and that its findings are real

The parser has 15 counter-controls, each feeding it a block malformed in exactly one way
(unclosed fence, unknown kind, unbalanced bracket, odd quote count, empty block, a one-way
peer edge, asymmetric peers, a node inside both processes, a GUI inside an agent, a missing
subgraph). All 15 pass.

**That the checker fires is not the same as the finding being real, so the real renderer was
run.** `@mermaid-js/mermaid-cli` 11.16.0, installed out of tree in the scratchpad:

| Input | Result |
|---|---|
| all six blocks as committed | **RENDERED** — SVGs of 22 931 / 25 874 / 27 649 / 33 241 / 37 800 / 57 123 bytes, and `grep "Syntax error"` over them returns nothing |
| `flowchart` → `flowhcart` (the unknown-kind mutation) | **REJECTED**: `UnknownDiagramError: No diagram type detected` |
| a dropped `]` (the unbalanced-bracket mutation) | **REJECTED**: `Error: Parse error on line 3` |

The container and sequence diagrams were additionally rendered to PNG and read back visually:
two separated subgraphs with mirrored contents, edges crossing both ways, the GUI outside both,
and the four phases in order.

This run is **not** in CI and the document says so: mermaid-cli needs a headless Chromium
(it only ran at all with `--no-sandbox`), and CLAUDE.md requires the suite to be offline.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 — Bug] Three fabricated or unresolvable path citations in this plan's own first
draft of `ARCHITECTURE.md`**
- **Found during:** the new `test_the_prose_around_the_diagrams_cites_only_paths_that_exist`, on its first run
- **Issue:** `scripts/check_no_llm_in_move.py` **does not exist** — the real gate is
  `scripts/check_no_llm_in_strategy.py`. `src/pursuit/...` was written as a backticked path
  when it is a pattern. `training/plot_curves.py` was backticked while being referenced *as a
  deleted file*.
- **Fix:** the script name corrected to the one that exists (and its behaviour described from
  its own docstring); the pattern rephrased; the deleted file de-backticked, with the
  convention — **a backticked path claims the path exists now** — written into the document.
- **Commit:** `072d61d`

**2. [Rule 1 — Bug] A fourth fabricated script name in `QUALITY-25010.md`**
- **Found during:** `test_the_quality_model_cites_only_paths_that_exist`
- **Issue:** `scripts/check_publication_safety.py` never existed. The 08 outline *predicted*
  that filename for 08-03; 08-03 shipped the scan as `scripts/submission_scan.py` instead.
  Citing the outline's prediction as if it were the tree is exactly the drift this phase exists
  to close.
- **Fix:** the security section now cites `scripts/submission_scan.py`, quotes its measured
  numbers (886 tracked text files, 0 provider-shape hits), and adds
  `tests/unit/test_publication_ignore_rules.py`.
- **Commit:** `5687c39`

**3. [Rule 3 — Blocking] The citation helper rejected a legitimate directory citation**
- **Issue:** `` `src/pursuit/strategy/` `` (trailing slash) resolved as neither file nor
  directory.
- **Fix:** `cited_paths` normalises a trailing slash away. Recorded because the alternative —
  editing the documents to avoid the checker — is the failure mode.
- **Commit:** `072d61d`

**4. [Rule 1 — Bug] One of my own counter-controls did not fire**
- **Issue:** the odd-quote mutation replaced `a["engine` with `a[engine"`, which leaves an
  **even** number of quotes on the line. The test failed, correctly.
- **Fix:** the mutation now drops the opening quote, producing a genuinely odd count. Found by
  running the controls rather than by reading them.
- **Commit:** `acc5913`

**5. [Rule 2 — Missing critical functionality] `c4-code`'s class bodies were written in a
form mermaid parses loosely**
- **Issue:** free-text members containing commas are a plausible red-error-box source.
- **Fix:** rewritten as conventional stereotype + typed-member syntax, using **only real
  method names read out of `base.py`, `valuebrain.py` and `naive.py`** — then rendered to
  prove it.
- **Commit:** `072d61d`

**6. [Rule 3 — Blocking] mermaid-cli crashed on launch**
- **Issue:** `ConnectionClosedError: Connection closed` — the bundled Chromium would not start
  under this environment's sandbox.
- **Fix:** a puppeteer config with `--no-sandbox`. Out of tree, in the scratchpad; nothing was
  added to `pyproject.toml`, `package.json` or CI.

### Scope boundary

`docs/PLAN.md`'s existing ASCII diagrams were **not** converted. `ARCHITECTURE.md` is a new
document that links to `PLAN.md` as the text design; rewriting `PLAN.md` is not this plan's,
and G1-11 (which judges `PLAN.md`) already passes and did not move.

## Gates

| Gate | Result |
|---|---|
| `uv run pytest --cov` | **2413 passed / 0 failed** (baseline 2366; +47) |
| coverage | **97.44%** — unchanged. The new code is in `scripts/`, outside the coverage source list, and is measured by tests that load it **by path** |
| `ruff check .` | 0 violations |
| `check_line_limit.sh` | exit 0 tree-wide, and all seven new `.py` files ALSO checked **explicitly by path** (`scripts/` is not enumerated by the no-argument form) |
| `check_diagrams.py` | exit **0** — 6 blocks parse, all **29** labels resolve. Exit **2** before the document existed |
| `check_submission.py` | exit 1 at **62 PASS / 11 GAP / 13 UNJUDGED** after this plan (58/15/13 before) |
| graphify | refreshed — 11 646 nodes / 20 310 edges / 660 communities (was 11 097 / 19 646). `parse_flowchart` resolves at `scripts/diagram_graph.py:70`, degree 4 |

## GAP movement — row by row

**58 PASS / 15 GAP → 62 PASS / 11 GAP. Four rows, and exactly the four 08-07 owned. No other
row changed verdict in either direction** — the same counter-control 08-03 and 08-06 each
passed.

| Row | Was | Now | Why |
|---|---|---|---|
| G1-13 | GAP | PASS | 0 → 6 rendered mermaid blocks across every tracked doc |
| G6-01 | GAP | PASS | `docs/EXTENSION-POINTS.md` exists with five documented seams |
| G6-02 | GAP | PASS | `docs/ARCHITECTURE.md` exists with §5.1 deployment instructions |
| G6-05 | GAP | PASS | `docs/QUALITY-25010.md` names all eight characteristics **and** cites ≥ 8 repo paths |

Group totals: 1 → 22/6 → 23/5; 6 → 2/4 → 5/1. Groups 2, 3, 4, 5 and T5 unmoved.

## Counters (rule 38) — all four numbers

| Measurement | Police | Thief |
|---|---|---|
| full `uv run pytest --cov` | **1926 → 1926** | **1919 → 1919** (delta **0/0**) |
| one real `dev_launch.py` game | **1926 → 1927** | **1919 → 1920** (delta **+1/+1**) |

The game (`game_id` `2582a94c8a5ec618`, exit 0) ended `capture` with `audit_verdict
matched=true` on both seats at turn 5, the thief seat recording `agreed: true`. Its
`games_played_declared` field is `{"present": false, ...}` — **deliberately unset**, naming
`GAMES-PLAYED-RECONSTRUCTION.md`, exactly as rule 38 requires.

`git diff config/` is **empty**: `config/*/games_played*.json` is gitignored at
`.gitignore:90`, so no counter value can be committed.

## What this plan deliberately does not claim

- **Nothing has been mailed.** Every shipped `reporting.json` is `dry_run`; the diagrams and
  the 25010 map both say so at the point where the Gmail path is drawn.
- **No league game has been played**, and the games-played value is unset.
- Phase 4 is `human_needed`; phases 7 and 8 have **no verification pass**. `QUALITY-25010.md`
  states this in its scope paragraph rather than in a footnote.
- The tunnel repair path **has never fired in a live game** — copied from
  `GATE-5-MEASUREMENT.md`, not softened.
- `check_diagrams.py` does **not** execute mermaid, and the document says which run did.

## Nothing pushed

**No `git push`, no tag, no remote command was issued by this plan.** `git tag -l` is empty.

**One finding that is not mine and must not be lost:** `origin/main` moved to `acc5913` —
this plan's own first commit — at 19:10:14, **6 minutes 39 seconds after** it was made. The
only git hook in this repository is `scripts/hooks/pre-commit`, which runs the line-limit and
ruff gates and contains no push. `codex.exe` (PID 21568) is running on this machine, and
CLAUDE.md retires Codex for this user. The reflog shows the same pattern for earlier commits.
**Something outside this agent is pushing to the public remote**, and the user should
investigate it. No corrective remote action was taken — a force-push would itself be touching
the remote.

## Self-Check: PASSED

Ten created paths verified present **and** tracked **and** not gitignored; three commits
verified reachable; the two modified trackers verified changed. Numbers in this summary were
each taken from a command run in this session, and the diagram/label counts (6 blocks, 29
labels) were re-read from `check_diagrams.py`'s own output rather than counted by hand.
