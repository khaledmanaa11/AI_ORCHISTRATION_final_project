---
phase: 07-reporting-and-visualization-shell
plan: "02"
subsystem: services/reporting-artifacts
tags: [D-71, D-72, D7-1, D7-3, D7-4, D7-5, REPORT-06, REPORT-01, rule-11, rule-50, rule-38, appendix-F, canonical-json, step0]
one_liner: "The four PARAMETERS artifact names, the per-game_id <NN> index and one canonical seal in a single spine; config_<game_id>_g<NN>.json proven digest-equal to the handshake wire and byte-identical across both roles; the D-71 declaration wrapper completes the Step-0 payload without touching one byte of it -- and D7-1 is resolved by moving the artifact, not by narrowing the ignore rule."
requires:
  - "Nothing. Wave 1, depends_on: []. Reads 07-01's artifact_dir DECISION but imports no 07-01 code."
provides:
  - "services/reporting/artifact_names.py: the four docs/PARAMETERS.md:165-168 filenames and next_sub_game_index (per-game_id, 01-based)"
  - "services/reporting/artifacts.py: artifact_header (the game_uid join), artifact_digest / artifact_digest_matches (the ONE seal, over config_hash.canonical_json), write_artifact (D7-1's logs/ refusal)"
  - "services/reporting/artifact_config.py: build/write/verify_config_artifact -- config_<game_id>_g<NN>.json"
  - "services/reporting/artifact_declaration.py + artifact_declaration_fields.py: the D-71 wrapper, DeclarationContext, verify_embedded_declarations"
  - "game_artifacts/README.md: where the four artifacts live and why not logs/"
affects:
  - "07-05 (log_ builder) consumes log_filename + next_sub_game_index + write_artifact"
  - "07-07 (end-of-game + result_) consumes result_filename, write_declaration_artifact and DeclarationContext -- it owns the end time, which is why nothing here is wired yet"
  - "07-04 (mail transport) attaches these artifacts"
tech-stack:
  added: []
  patterns:
    - "One spine module owning names + index + join + seal, with the naming half split into a dependency-free leaf and re-exported -- so callers keep one import path (the gatekeeper_types.py precedent)"
    - "A write gate that REFUSES a forbidden destination, rather than a convention every caller must remember"
    - "Post-write re-verification: read the file back and re-check its own seal / signatures before returning a path"
key-files:
  created:
    - src/pursuit/services/reporting/artifacts.py
    - src/pursuit/services/reporting/artifact_names.py
    - src/pursuit/services/reporting/artifact_config.py
    - src/pursuit/services/reporting/artifact_declaration.py
    - src/pursuit/services/reporting/artifact_declaration_fields.py
    - tests/unit/test_artifact_{names,spine,config,config_seal,declaration,declaration_peer}.py
    - tests/unit/{artifact_config_fixtures,artifact_declaration_fixtures}.py
    - game_artifacts/README.md
  modified:
    - src/pursuit/services/reporting/__init__.py
    - .gitignore
    - .planning/phases/07-reporting-and-visualization-shell/deferred-items.md
key-decisions:
  - "D7-1 resolved by MOVING the artifact, not narrowing the logs/ ignore rule -- git cannot re-include under an excluded directory, and logs/ holds the bulky per-run wire logs and nonce ledgers"
  - "The logs/<role>/declaration_<game_id>.json file is the handshake-time PRECURSOR, not the artifact, and could never have been the artifact -- it is written before move 1 and the artifact carries the end time"
  - "config_ embeds game_params + scent + language and excludes network.json, role.json, reporting.json and every policy file, each exclusion reasoned in the module docstring"
  - "handshake_digests carries ONLY the two digests actually exchanged; language.json gets none, because claiming one would assert an agreement never made"
  - "ENVELOPE_DECLARATION_KEY is named locally rather than added to SignKey, to keep the D-71 git-diff control empty (filed as D7-4)"
metrics:
  tasks: 3
  commits: 5
  tests_added: 105
  suite: "1689 -> 1794 passed, 0 failed"
  coverage: "96.80% -> 96.90%"
  completed: 2026-08-17
status: complete
---

# Phase 7 Plan 02: Artifact Spine Summary

`docs/PARAMETERS.md` fixes four filenames a grader will diff character by character, and
one of them sits a single field away from aborting every game at the handshake. This plan
pins the names to the document, produces the two artifacts that need no completed game, and
resolves the contradiction 07-01 refused to inherit.

## D7-1 — the decision, and why it is that one

The contradiction 07-01 filed: `.gitignore:82-85` carried a comment stating *"the four
required JSON artifacts (declaration_/config_/log_/result_) MUST be committed per rule 50
and Appendix F rule 4 — keep them out of this ignore list"*, and the very next line ignored
`logs/` wholesale — while `agent_step0_wiring.write_declaration` writes
`declaration_<game_id>.json` into `logs/<role>/`.

**Decided: move the artifact. The ignore rule is NOT narrowed.**

Narrowing was rejected on two grounds that are not preferences:

1. **Git cannot re-include a file whose parent directory is excluded.** `logs/` excludes the
   directory itself, so `!logs/**/declaration_*.json` beneath it is a silent no-op.
   Narrowing genuinely means restructuring into `logs/**` plus a chain of negations that the
   next editor can break with no signal — returning the repository to *exactly this bug,
   unnoticed*. That is the failure mode, not a hypothetical.
2. **`logs/` is deliberately bulky.** It holds the per-run wire logs (`<uid>.jsonl`) and
   nonce ledgers (`<uid>.ledger.jsonl`), plus `*.log`. Checked before touching anything:
   un-ignoring anything inside it puts those one careless `git add` away from the tree.

**And the precursor could never have been the artifact.** `write_declaration` runs at
handshake time, before move 1. `docs/PARAMETERS.md:165` requires
`declaration_<game_id>.json` to carry the **end time**, plus both teams' repo URLs, MCP
server addresses and the agreed token ceiling. So `logs/<role>/declaration_<game_id>.json`
is the immediately-durable **precursor** of the signed payload — valuable precisely because
it lands before a crash can — and the deliverable is this plan's D-71 wrapper, a strict
superset of it, written to `game_artifacts/`.

**What actually changed in the tree, so this is a resolution and not a note:**

| # | Change | Effect |
|---|---|---|
| 1 | `artifacts.write_artifact` raises `ValueError` on any path with a `logs` component | Enforcement at the one write site. Both artifact writers route through it. |
| 2 | The `.gitignore` **comment** corrected | **Zero ignore patterns changed** — verified by diffing both versions with comments stripped: `IDENTICAL`. |
| 3 | `game_artifacts/README.md` | The four names, `<NN>`'s meaning, and why not `logs/`, where a grader will look. |

Correcting the comment is item 2 and not cosmetic: a document certifying a wrong fact is
what let this survive a whole phase. 07-01 set the precedent (`language_model_config.py`).

**Phase-5 retained evidence — verified, not assumed:**

```
git ls-files docs/phases/phase-5/remote-round-*            42 files, all still tracked
19 declaration_*.json among them                           all "tracked-and-not-ignored"
git status --untracked-files=all logs/                     EMPTY (no log newly visible)
git check-ignore game_artifacts/declaration_x.json         exit 1 (not ignored)
```

Those files live under `docs/`, never under `logs/`, and no pattern moved — so neither
resolution could have touched them, and the check confirms it rather than reasoning it.

After the real game below, `logs/police/declaration_4b6f019a96265cd6.json` was written and
`git check-ignore` reports it **IGNORED — as designed.** It is the precursor.

## Task 1 — the names, pinned to the document

`artifact_names.py` holds the four builders, `sub_game_suffix` and `next_sub_game_index`;
`artifacts.py` holds the join, the seal and the write gate. **The combined module measured
167/150**, so it was split on the seam its own subject list already named — the naming half
is the dependency-free leaf, importing nothing from `pursuit`. Nothing compressed.

`tests/unit/test_artifact_names.py` transcribes `docs/PARAMETERS.md:165-168` as **literals**
and asserts the table still has four rows, so a thinned table fails rather than skipping.
`_g<NN>` is asserted PRESENT on `config_`/`log_` and ABSENT on `declaration_`/`result_`,
**with both negative halves** — adding `_g01` to an unindexed name and dropping it from an
indexed one must each fail the same assertion, or the check is shape-only.

`<NN>` is derived from what exists for that `game_id` in the artifact directory and from
nothing else. **`games_played.json` is neither read nor written** by this module or anything
it calls (D-72); the width `2` and base `1` are read off `<NN>` and "the match number" and
are cited as structural in a comment, not invented.

## Task 2 — the config artifact, measured on both roles

```
police  game_params recomputed = 23f86a93589131ae3558a4a697fc2105aa878809fa5ed62a11a28a528f25c975
police  game_params on-the-wire = 23f86a93589131ae3558a4a697fc2105aa878809fa5ed62a11a28a528f25c975  EQUAL
police  scent       recomputed = c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e
police  scent       on-the-wire = c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e  EQUAL
thief   (all four identical to police, character for character)
config seal (both roles)        = eafd7c72900df5dfb52759650b90cdb9238da6501bab3f3b71318983da9162b9
serialized bytes (both roles)   = 1526
```

The `game_params` digest is the exact string `agent_entrypoint.py:80` puts on the handshake
wire. Byte identity is proved by **writing both files and diffing the bytes**, not by
asserting the builder is careful.

**What is in, and every exclusion reasoned:** `game_params.json` (Tables 13/15/17),
`scent.json` (Table 16), `language.json` (Tables 14/19). Out: `network.json` — Table 18, and
`config_hash.py:13-16` states hashing it *"would abort every game"* (D-04); `role.json`;
`reporting.json`'s **second** Table-19 instance, which governs our outgoing mail rather than
the game and whose OQ-3 `wait_after_error_seconds: 30` beside language.json's 5 would read
as a contradiction; and every policy file.

`handshake_digests` carries **only** the two digests actually exchanged before move 1.
`language.json` deliberately has none — claiming one would assert an agreement never made.

## Task 3 — the declaration completed without being touched

The wrapper embeds **both** signed envelopes by reference, unaltered and unreordered, and
adds PARAMETERS' remaining content strictly at the top level.
`write_declaration_artifact` re-verifies every embedded signature through the real
`step0_sign.verify_declaration` **before** writing, and refuses to ship one that fails. A
digest-only peer gets `peer: null` and a stated reason — never a fabricated empty
declaration.

**The D-71 gate:**

```
git diff HEAD -- src/pursuit/security/step0_collect.py src/pursuit/security/step0_sign.py \
                 src/pursuit/network/agent_step0_wiring.py src/pursuit/network/handshake_evaluate.py
   (empty)
git diff HEAD -- src/pursuit/security/ src/pursuit/network/
   (empty)
```

Every Phase-6 Step-0 / handshake test passes **unmodified**, and `dev_launch.py` logs zero
`STEP0_MISMATCH` on both sides.

## Revert probes — eighteen, with real counts

Every behaviour was reverted and measured. No probe is a shape check.

| # | Mutation | Result |
|---|---|---|
| 1 | `_g<NN>` added to `result_filename` | **2 failed, 44 passed** |
| 2 | zero-padding width 2 → 1 | **4 failed, 42 passed** |
| 3 | `<NN>` never advances | **4 failed, 42 passed** |
| 4 | `bool` guard removed from the index | **3 failed, 43 passed** |
| 5 | `game_id` not `re.escape`d | **1 failed, 29 passed** *(was 0 failed — see below)* |
| 6 | D7-1 `logs/` guard removed | **5 failed, 41 passed** |
| 7 | `network.json` embedded in `config_` | **5 failed, 13 passed** |
| 8 | embedded object re-shaped (`version` dropped) | **4 failed, 14 passed** |
| 9 | scent digest wired to the wrong file | **2 failed, 16 passed** |
| 10 | seal taken over the wrong object | **1 failed, 17 passed** |
| 11 | wrapper adds a field **inside** the signature | **7 failed, 30 passed** |
| 12 | writer's signature self-check removed | **2 failed, 35 passed** |
| 13 | empty peer declaration fabricated instead of a null | **6 failed, 31 passed** |
| 14 | peer-boundary shape guards removed | **3 failed, 34 passed** |
| 15 | `bool` guard removed from `token_ceiling` | **1 failed, 36 passed** |
| 16 | post-write seal check removed | **1 failed, 21 passed** |
| 17 | seal check reads a fresh build, not the FILE | **1 failed, 21 passed** |
| 18 | header carries `sub_game_index` unconditionally | **4 failed, 12 passed** |

Controls restored cleanly each time (46 / 22 / 37 passed).

Probe 11 is the one the plan named: the exact mistake D-71 exists to prevent, caught seven
times over.

## Three holes the self-audit found in my own work

**Probe 5 first returned 46 passed / 0 failed.** My escaping test wrote
`config_a.c_g07.json` and searched for `abc` — but the hazard runs the *other* direction: a
metacharacter `game_id` matching **someone else's** artifact. Rewritten to plant
`config_axc_g07.json` and search for `a.c`, which unescaped returns 8 instead of 1. Probe 5
now fails 1.

**`artifact_digest_matches` had test-only reachability** — dead code by the exact standard
07-01 filed D7-3 for. Fixed rather than excused: `write_config_artifact` now reads the file
back and re-checks the embedded seal, raising rather than returning a path to an artifact it
could not verify. Not a tautology on the in-memory object — it is the round trip through
`durable_write_json` and `json.loads` being checked (probe 17 confirms: pointing it at a
fresh build instead of the file fails 1). That is the config half of the promise the
declaration writer already made for signatures.

**`test_all_four_artifacts_join_on_one_game_uid` was near-tautological** — three headers
built with the same `game_uid`, asserting the set had one element. Replaced by a
name-against-header cross-check across all four artifacts, so a builder that puts
`sub_game_index` on `result_` or drops it from `config_` fails on the disagreement. Probe 18
went from 0 failed to **4 failed**.

**An AST scan over every `parametrize` in this plan's six test files** resolved each
argvalues source and checked for a length guard: 16 parametrize sites, **every named source
GUARDED**, every inline literal non-empty. Collected counts, verified non-zero: 30 / 16 / 17
/ 5 / 16 / 21 = **105**, which equals the suite delta exactly.

## Production reachability, grepped

Every importer of the artifact spine outside its own package is a **test** — nothing in
`src/`, `scripts/`, `training/` or `main.py`. Recorded honestly as an extension of **D7-3**
rather than glossed, because nothing here *could* be wired: `write_declaration_artifact`
needs the **end time**, which exists only at game end (07-07), and `write_config_artifact`
needs the artifact directory from `load_reporting_config`, which no production path loads
yet (07-04/07-07).

Reachability *inside* the spine is complete after the fix above. `next_sub_game_index`,
`log_filename` and `result_filename` are the three public names with no in-package caller —
07-05 and 07-07 own them.

## Zero numbers invented

Every parameter **value** in `config_` is copied from an already-shipped config file; none
is re-typed. `SUB_GAME_INDEX_WIDTH = 2` and `FIRST_SUB_GAME_INDEX = 1` are read off `<NN>`
and "the match number" in `docs/PARAMETERS.md:159-168` and cited as structural. The width is
a **minimum**, not a truncation — a 100th sub-game widens to `_g100` rather than colliding,
and that is tested.

`DeclarationContext` has **no default for `token_ceiling`** — a caller without an agreed
ceiling gets a `TypeError`, which is a gap to report, not a number to choose. `bool` is
rejected explicitly there and in the index, because it is an `int` subclass and would
otherwise ship a ceiling of 1 and a file named `_g01`.

## Gates

```
ruff check .                        All checks passed        (0 violations)
check_line_limit.sh                 exit 0                   (tracked)
check_line_limit.sh <14 new paths>  exit 0                   (explicit -- the no-arg form
                                                              enumerates via git ls-files
                                                              and passes VACUOUSLY on an
                                                              untracked file)
check_no_llm_in_strategy.py         OK
pytest tests/ --cov                 1794 passed, 0 failed    (baseline 1689)
                                    coverage 96.90%          (baseline 96.80%)
git diff -- security/ network/      EMPTY                    (the D-71 control)
dev_launch.py                       exit 0
                                    both sides audit_verdict matched=true (11 turns each)
                                    outcome capture at turn 5
                                    zero technical_win, zero STEP0_MISMATCH
```

Every new module at **100%**: `artifacts.py` · `artifact_names.py` · `artifact_config.py` ·
`artifact_declaration.py` · `artifact_declaration_fields.py` · `__init__.py`.

File sizes, all ≤ 150 code lines:

| File | Lines | | File | Lines |
|---|---|---|---|---|
| `artifacts.py` | 107 | | `test_artifact_names.py` | 104 |
| `artifact_names.py` | 102 | | `test_artifact_spine.py` | 95 |
| `artifact_config.py` | 130 | | `test_artifact_config.py` | 114 |
| `artifact_declaration.py` | 125 | | `test_artifact_config_seal.py` | 54 |
| `artifact_declaration_fields.py` | 58 | | `test_artifact_declaration.py` | 102 |
| `__init__.py` | 68 | | `test_artifact_declaration_peer.py` | 94 |
| `artifact_config_fixtures.py` | 24 | | `artifact_declaration_fixtures.py` | 50 |

## Secrets — rules 39-40

Both artifacts were produced and searched, **with the real values loaded from `.env` so the
search was not vacuous** (the first attempt searched an empty set, because no key was
exported in this shell):

```
.env secret-bearing names searched: ANTHROPIC_API_KEY, NGROK_AUTHTOKEN,
                                    PURSUIT_NGROK_DOMAIN, PURSUIT_TUNNEL_SECRET
config_g_g01.json      1526 bytes   forbidden-token-hits=[]  REAL-secret-value leaks=[]
declaration_g.json      535 bytes   forbidden-token-hits=[]  REAL-secret-value leaks=[]
control (planted NGROK_AUTHTOKEN)   FOUND -- the search can find something
```

No artifact sample is committed. `config_` embeds no `security.json`, so no `team_code`
either — asserted as a leak test with its own counter-control.

## Games-played counters — rule 38

Read directly (the files are gitignored):

```
FULL SUITE     before 1912 / 1905    after 1912 / 1905    DELTA 0 / 0
ONE REAL GAME  before 1912 / 1905    after 1913 / 1906    DELTA 1 / 1
```

07-00's guarantee holds under this plan's changes. The **value** remains deliberately unset
and is the human's at 07-10; nothing here reads it, defaults it, or reads around it.

## Deviations from plan

1. **[Rule 3 — blocking] `artifact_names.py` created.** Not in `files_modified`. The plan's
   own subject list for `artifacts.py` measured **167/150** and CLAUDE.md forbids
   compressing to fit. Split on a meaning boundary — names/index vs join/seal/placement —
   with the naming half a dependency-free leaf. Public import path unchanged; both halves
   re-exported.
2. **[Rule 3 — blocking] `artifact_declaration_fields.py` created.** Same cause at
   **156/150**, following 07-01's `reporting_config_fields.py` and 04-06's
   `language_model_config.py`.
3. **[Rule 3 — blocking] test files split.** The plan named one test file per module; the
   gate forced `test_artifact_spine.py` (out of `test_artifact_names.py`, at 167 combined),
   `test_artifact_config_seal.py` (out of `test_artifact_config.py`, at 153) and
   `test_artifact_declaration_peer.py` (out of `test_artifact_declaration.py`, at 154).
4. **[Rule 3 — blocking] two test fixture modules created.** `artifact_config_fixtures.py`
   and `artifact_declaration_fixtures.py`, extracted at the second consumer of each builder
   set rather than duplicated (CLAUDE.md Table 5: no duplication). Not named `test_*`, so
   pytest collects nothing from them — the `late_peer_harness.py` precedent.
5. **[Rule 2 — missing critical functionality] `write_config_artifact` re-reads and
   re-verifies its own seal.** Found by the self-audit: `artifact_digest_matches` was
   test-only reachable. An artifact that cannot be re-verified must fail rather than ship.
   Commit `042c0ac`, probes 16-17.
6. **[Rule 2 — missing critical functionality] `write_artifact` refuses `logs/`.** This is
   D7-1's enforcement half. The plan asked for a decision; a decision recorded only in prose
   would have left the tree in the state that produced the bug.
7. **[Rule 1 — bug] The `.gitignore` comment corrected.** It asserted the opposite of what
   the next line did. **Zero patterns changed**, verified by a comments-stripped diff.
8. **[Rule 3] The strengthened join test.** `test_all_four_artifacts_join_on_one_game_uid`
   asserted something that could barely fail; replaced by the name-against-header
   cross-check. Commit `e2bb0ee`.

**Total deviations:** 8 auto-fixed (4 blocking splits/extractions, 3 missing-critical or
bug, 1 test strengthening). No architectural decision was needed; no checkpoint was reached;
no authentication gate occurred. Nothing outside the plan's scope was modified: `git diff`
over `src/pursuit/security/` and `src/pursuit/network/` is empty, and
`tests/integration/test_belief_policy.py` was not touched.

## Issues Encountered

- **`docs/PARAMETERS.md` never says what "the agreed configuration" contains file by file.**
  Resolved by mapping Appendix F's tables onto this repo's shipped config and recording every
  inclusion *and* exclusion with its reason in the module docstring, rather than embedding
  everything and hoping. `network.json`'s exclusion is the one that carries a rule (D-04).
- **Probe 15 could not be reverted with `git checkout`** — `artifact_declaration_fields.py`
  was still untracked at that point. Restored by hand and re-verified against a re-read of
  the file, not from memory.

## Open, for the plans that own it

**D7-1 RESOLVED** (recorded in `deferred-items.md` with the reasoning) · **D7-3 extended** —
the artifact spine awaits its 07-05/07-07 wiring, structurally, because 07-07 owns the end
time · **D7-4** `"declaration"` is an inline literal on the signed path with no `SignKey`
member; deliberately not folded in, because the D-71 control *is* the empty git diff over
that file · **D7-5** a pre-existing recoverable `illegal transition handshake -> handshake`
on every `dev_launch.py` run, present in runs predating this plan — logged, not fixed, per
the scope boundary.

## Task Commits

1. **Task 1: the names and the index** — `9ac7fdb` (feat)
2. **Task 2: `config_<game_id>_g<NN>.json`** — `4f90fd7` (feat)
3. **Task 2 self-audit fix: the post-write seal check** — `042c0ac` (fix)
4. **Task 3: the declaration wrapper, and D7-1 resolved** — `7bd0d01` (feat)
5. **Self-audit: the join cross-check, and D7-5 logged** — `e2bb0ee` (test)

---
*Phase: 07-reporting-and-visualization-shell*
*Completed: 2026-08-17*

## Self-Check: PASSED

All 17 claimed paths verified present on disk with `[ -f ]` **and** tracked by git with
`git ls-files --error-unmatch`; all five claimed commit hashes verified reachable in
`git log --oneline --all`. Checked, not recalled — every number quoted in this document was
read off a command's output in this session, including the two counter readings and the
four digests.

## Addendum — `docs/phases/phase-7/TODO.md`

CLAUDE.md requires `/gsd:execute-phase` to keep the phase TODO current as tasks land. 07-02's
row is now `☑` with its measured acceptance evidence written into the Definition of Done
column. **07-01's row was also still `☐`** although that plan is committed and closed with a
passing self-check — a stale row in a grader-facing tracker is the same "document certifying a
wrong fact" problem D7-1 was, so it is ticked too rather than left to look like unfinished
work. Rows 07-03…07-10 are untouched.
