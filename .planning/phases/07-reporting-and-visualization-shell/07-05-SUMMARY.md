---
phase: 07-reporting-and-visualization-shell
plan: "05"
subsystem: services/reporting-log-artifact
tags: [D-59, D-61, D-64, D-67, D-73, D7-3, D7-8, D7-13, D7-14, REPORT-06, REPORT-09, rule-18, rule-20, rule-38, SEC-04, canonical-json]
one_liner: "log_<game_id>_g<NN>.json joined on LOCAL turn truth -- 5/5 turns re-hash on both seats of a real game with both source files deleted; re-keying on the peer's envelope turn loses a pair and invents two phantom turns, and even an honest peer disagrees on 5-6 records of every real game; zero internal state, by allow-list, with the nonce boundary enforced as a scan rather than recorded as a grep"
requires:
  - "07-02: artifact_header / artifact_digest / write_artifact (D7-1's logs/ refusal) / log_filename"
  - "06-05: agent_audit_observed.observed's local-turn key discipline -- reused, not re-derived"
  - "06-01/06-02: commit_pack.verify_reveal and CommitLedger's {turn, h_commit, payload} record"
provides:
  - "services/reporting/log_read.py: read_tolerating_partial_tail + CorruptLogError -- a crashed game still yields an artifact"
  - "services/reporting/log_join.py: local_turn / peer_claimed_turn / JoinedGame / join_game"
  - "services/reporting/log_turn_fields.py: TurnField, the rules 8-9 allow-list, build_turn_record"
  - "services/reporting/log_artifact_fields.py: LogArtifactField, SEALED_FIELDS, sealed_body"
  - "services/reporting/artifact_log.py: build/verify/write + verify_log_turns (07-08's entry)"
  - "network/turn_commit_ledger.ledger_path_for: D-64's sibling convention over a PATH"
  - "docs/PRD_log_artifact.md: the per-mechanism PRD (CLAUDE.md Sec2.3)"
affects:
  - "07-07 owns the game-end call site; it must pass ctx.game_uid (the NEGOTIATED id) -- see D7-13"
  - "07-08 recomputes hashes with verify_log_turns and MUST check committed > 0 before reporting a ratio"
  - "07-08 inherits D7-8: the artifact carries no belief_argmax at all, so there is nothing to accidentally render"
tech-stack:
  added: []
  patterns:
    - "A second reader beside a deliberately fail-loud one, when two callers want opposite things from the same corruption"
    - "Copy by ALLOW-LIST, never by deny-list, when the source record is owned by another plan that may add fields"
    - "A reachability GATE that runs every suite, watching both the module-path and the re-exported-NAME import form"
    - "Carrying a peer's or a predecessor's claim verbatim as evidence while never using it as a key"
key-files:
  created:
    - src/pursuit/services/reporting/log_read.py
    - src/pursuit/services/reporting/log_join.py
    - src/pursuit/services/reporting/log_turn_fields.py
    - src/pursuit/services/reporting/log_artifact_fields.py
    - src/pursuit/services/reporting/artifact_log.py
    - docs/PRD_log_artifact.md
    - tests/unit/artifact_log_fixtures.py
    - tests/unit/artifact_log_games.py
    - tests/unit/test_artifact_log.py
    - tests/unit/test_artifact_log_redaction.py
    - tests/unit/test_artifact_log_edges.py
    - tests/unit/test_log_artifact_reachability.py
    - tests/integration/test_log_artifact_roundtrip.py
  modified:
    - src/pursuit/network/turn_commit_ledger.py
    - src/pursuit/services/reporting/__init__.py
    - docs/phases/phase-7/TODO.md
    - .planning/phases/07-reporting-and-visualization-shell/deferred-items.md
key-decisions:
  - "The join keys on the record's OWN top-level turn (06-05's discipline reused verbatim); the peer's envelope turn is carried in peer_claimed_turns as evidence and is never a key"
  - "log_read.py is a SECOND reader rather than a change to read_all/_read_log: the audit must stop on unreadable evidence, a replay artifact must not"
  - "The language_turn record is copied by ALLOW-LIST (intent + text only) -- a deny-list silently ships whatever a future plan adds"
  - "Hints come from BOTH the language record's broadcast half and the wire HINT envelopes, kept separate and labelled; the decoder's incoming outcome/reason is internal inference and is excluded"
  - "truncated_tail and prior_game_uids live INSIDE the seal -- both are provenance, and a marker outside the seal can be flipped without breaking it"
  - "write_log_artifact re-reads the FILE and refuses to ship an artifact whose seal OR whose own turns fail to re-hash: a FAILED verdict on the grader's screen must never be our transcription bug wearing the opponent's name"
  - "D-61: the caller's negotiated game_uid must appear SOMEWHERE in the log, not be the first record's -- otherwise the thief is refused an artifact in every game"
metrics:
  tasks: 3
  commits: 7
  tests_added: 55
  suite: "1919 -> 1974 passed, 0 failed"
  coverage: "97.02% -> 97.12%"
  completed: 2026-08-17
status: complete
---

# Phase 7 Plan 05: The `log_` Artifact Summary

Rule 20 makes a **verifying** replay viewer a threshold condition for approving the
project. This plan builds the file that viewer verifies: `log_<game_id>_g<NN>.json`,
derived by joining this side's wire JSONL to its own nonce ledger, on local turn truth,
carrying wire truth and nothing else.

---

## 1. The headline measurements, on a real game

`uv run python scripts/dev_launch.py` → exit 0, game `521519a78f96c255`, both seats:

| | police | thief |
|---|---|---|
| turn entries | 6 | 6 |
| committed turns (carry an `h_commit`) | 5 | 5 |
| **re-hashed through `commit_pack.verify_reveal`** | **5 / 5 = 100.0%** | **5 / 5 = 100.0%** |
| seal re-verified off the FILE | `True` | `True` |
| outcome | `capture` @ turn 5 | `capture` @ turn 5 |
| `audit_verdict` | `matched: true` @ 5 | `matched: true` @ 5 |
| `truncated_tail` | `{log: false, ledger: false}` | `{log: false, ledger: false}` |
| `prior_game_uids` | `[]` | `['3c0c5fd8f6705a3b']` — see §5 |
| hints carried with the rule-25 intent flag | 5 | 4 |
| peer claims carried verbatim | 14 | 16 |
| …of which **disagree** with local turn | 1 | **5** |
| rules 8–9 internal fields present | **`[]`** | **`[]`** |
| bytes | 6964 | 6888 |

**Self-containment, on the same real cross-process game, thief seat:** the artifact was
built, then `<uid>.jsonl` and `<uid>.ledger.jsonl` were **deleted** (`list(dir) == []`),
and only then verified: **seal OK, re-hash 5/5 = 100.0%**. The integration test does the
same on a fresh in-harness game, in the plan's order and no other.

Rule 20's threshold is met with the sources gone, which is the only version of that claim
worth anything.

## 2. Task 1 — the join, and the counter-control that is the point

The key is the record's **own top-level `turn`**. This is not re-derived:
`agent_audit_observed.observed` already writes down why, and 06-05 measured the cost of
the alternative. The peer's `envelope.turn` is carried into `peer_claimed_turns` as
evidence and is never a key.

**The adversarial fixture** (`tests/unit/artifact_log_games.py`, `disjoint=True`) has the
peer stamp its COMMIT envelope turn **99** and its REVEAL envelope turn **7** while this
side logs both under local turn **3** — the 06-05 attack, verbatim. Measured:

| | turn entries | peer COMMIT+REVEAL pairs | turn keys |
|---|---|---|---|
| **local turn truth** (shipped) | 5 | **4** | `[0, 1, 2, 3, 4]` |
| re-keyed on `envelope.turn` | **7** | **3** | `[0, 1, 2, 3, 4, 7, 99]` |
| honest fixture, either key | 5 | 4 | `[0, 1, 2, 3, 4]` |

The wrong key **loses one pair and invents two turns the peer named out of thin air.** The
honest row is why a happy path alone proves nothing: on an honest peer the two keys are
indistinguishable, so a test that never runs the adversarial case measures nothing.

**And it is not only an adversary.** Scanned all 20 recorded games in `logs/`: **every
single one carries 5–6 `message_received` records whose local turn differs from the peer's
stamped envelope turn** — every incoming HINT, because a hint arrives one turn late:

```
logs/thief/f2df446f6c75d39c.jsonl: received=16 disagreeing=5
   [(1,0,'hint'), (2,1,'hint'), (3,2,'hint'), (4,3,'hint'), (5,4,'hint')]
```

A builder keyed on the peer's number would misfile **every hint of every honest game** by
one turn. That is measured, not argued.

**The tail.** `event_log.append_event` writes, flushes and `fsync`s per line, so an
interrupted process leaves a partial LAST line. `log_read.py` drops it and reports
`truncated_tail`; a malformed line anywhere else raises `CorruptLogError` — a distinct
class, asserted with `type(exc) is CorruptLogError` because `json.JSONDecodeError` is
itself a `ValueError` and a looser assertion would have passed on the tail case too.
**Neither `read_all` nor `_read_log` is touched**: they are the audit path and their
fail-loud contract is correct there.

## 3. Task 2 — the artifact, and what it refuses to carry

Every turn carries the seven `docs/PARAMETERS.md:167` names, with the five
`verify_reveal` inputs (`hash`, `nonce`, `intent`, `state`, `move`) at the **top level**,
so a reader re-hashes with no unpacking rule to guess.

**No internal state, and the mechanism is an allow-list.** `outgoing_hint` copies exactly
`("intent", "text")`, never `**record` minus a deny-list — an allow-list stays correct when
a future plan adds a field to `language_turn_record`. `LANGUAGE_INTERNAL_FIELDS` names the
six excluded fields; the scan for all six over both real artifacts returned `[]`, and the
**counter-control** (the same scan over a payload that does carry `belief_argmax`) finds
it. This matters because **D7-8 records that the cop's true argmax is still written into
every `language_turn` JSONL record** — correctly, since that log is the rule-38 audit
record — and this artifact is emailed off the machine.

`write_log_artifact` re-reads the file and enforces **both** promises: the seal, and that
every committed turn re-hashes. The second is a builder self-check —
`commit_own_action` computed each `h_commit` from the very payload copied here, so a
mismatch is our corruption, not evidence about the game, and shipping it would put a
`FAILED` verdict on the grader's screen with the opponent's name on it.

## 4. Task 3 — nonce separation, enforced rather than recorded

D-64 keeps the ledger off the wire path; rule 18 keeps nonces secret while the game is
live; only SEC-04's end-of-game publication makes the ledger readable.

`tests/unit/test_log_artifact_reachability.py` re-runs the scan on **173 `src/` files**
every suite run, floored at 100 with a control that finds a real import:

```
importers of the log_ builder outside services/reporting          []
turn-loop modules (network/turn_*, orchestrator) reaching it      []
CommitLedger.read_all() production call sites                     ['network/agent_audit_wiring.py']
   and agent_entrypoint calls it only AFTER run_turn_loop returns (index-ordered assertion)
the four log_ modules binding CommitLedger or calling read_all    none
every src/ importer of security.ledger, named                     6, pinned by exact list
```

**The gate's first version was wrong and a probe proved it.** It watched module paths only.
Adding `from pursuit.services.reporting import artifact_log` to `network/turn_actions.py`
— a turn-loop module importing the builder — **passed 6/6**. The package re-exports, so
that name form is the one 07-07 is most likely to write. The scan now watches both forms;
probes 16, 16b and 16c each fail 2.

## 5. D-61 — one log can carry two `game_uid`s, found on a real game

The `game_uid` cross-check was written to catch "this artifact is named for one game and
filled from another's log." It fired on the **thief's own honest log**:

```
logs/thief/521519a78f96c255.jsonl   42 records, uids ['3c0c5fd8f6705a3b', '521519a78f96c255']
   the ONE pre-negotiation illegal_transition   -> 3c0c5fd8f6705a3b
   the other 41 records (and the filename)      -> 521519a78f96c255
logs/police/521519a78f96c255.jsonl  43 records, uids ['521519a78f96c255']
```

`agent_lifecycle` opens the log before the handshake;
`game_identity.adopt_negotiated_game_id` renames it afterwards (D-61, closing 05-UAT G2),
and the record written before the rename keeps its stamp. **A builder that read "the log's
`game_uid`" off the first record would have refused the thief an artifact in every game.**

Fixed by requiring the negotiated id to appear *somewhere*, and carrying every other id in
`prior_game_uids` **inside the seal** — dropping it would hide the very fact 05-UAT G2
exists to make visible. The strict half is kept and tested
(`test_a_log_holding_none_of_the_requested_uid_is_still_refused`). Filed as **D7-13** for
07-07 and 07-08.

## 6. Revert probes — twenty-one, every count real

Anchor asserted present before each mutation and the mutation asserted landed before the
run; source restored and re-compared afterwards (07-04's discipline).

| # | Mutation | Result |
|---|---|---|
| 1 | join re-keyed on the peer's `envelope.turn` | **3 failed, 46 passed** |
| 2 | `peer_claimed_turn` neutered to the local turn | **3 failed, 46 passed** |
| 3 | a partial tail raises, as `read_all` does | **3 failed, 46 passed** |
| 4 | mid-file corruption dropped instead of raised | **4 failed, 45 passed** |
| 5 | `_is_turn`'s `bool` guard removed | **1 failed, 31 passed** |
| 6 | `outgoing_hint` copies the whole language record | **11 failed, 38 passed** |
| 7 | `verify_log_turns` counts uncommitted turns | **8 failed, 41 passed** |
| 8 | the re-hash always returns `True` | **2 failed, 47 passed** |
| 9 | `truncated_tail` dropped out of the seal | **1 failed, 48 passed** |
| 10 | the seal recomputed from a fresh build, not the FILE | **1 failed, 26 passed** |
| 11 | the `game_uid` cross-check removed | **2 failed, 25 passed** |
| 12 | the post-write re-hash check removed | **1 failed, 29 passed** |
| 13 | the outgoing hint never populated | **3 failed, 46 passed** |
| 14 | the `audit_verdict` never carried | **2 failed, 47 passed** |
| 15 | `prior_game_uids` silently dropped | **1 failed, 12 passed** |
| 16 | a turn-loop module imports the builder (module form) | **2 failed, 4 passed** |
| 16b | …imports the **re-exported name** instead | **2 failed, 4 passed** |
| 16c | the orchestrator imports the builder's module | **2 failed, 4 passed** |
| 17 | the join reaches for `CommitLedger` | **1 failed, 5 passed** |
| 18 | a new `src/` module imports `security.ledger` unannounced | **1 failed, 5 passed** |
| 19 | the reachability scanner made blind | **2 failed, 4 passed** |

Probe 1 is the plan's named revert. Probes 8, 19 and the `peer_claimed_turn` neutering
(2) exist because this mechanism's most likely silent failure is a check that never fires.

## 7. Three holes the self-audit found in my own work

**1. Probe 5 first returned 18 passed / 0 failed.** `_is_turn`'s `bool` guard had no test.
It is not cosmetic: `True == 1` and `hash(True) == hash(1)`, so a ledger line stamped
`"turn": true` lands on **turn 1's dict key** and silently replaces its nonce and hash.
`test_a_boolean_turn_cannot_overwrite_turn_one` now plants exactly that; probe 5 fails 1.

**2. Probe 12 first returned 16 passed / 0 failed.** The post-write re-hash check had no
test, because it cannot fire on a healthy builder. Given a real cause — a ledger whose
`h_commit` disagrees with its own payload — it does.
`test_a_ledger_whose_hash_disagrees_with_its_payload_is_refused_at_write` supplies it.

**3. Probe 16 returned 6 passed / 0 failed against a genuine turn-loop import.** §4. The
gate was path-only and the package re-exports. This is the same class of finding as
07-11's vacuous fixtures: a green gate that was green because it was blind.

**Coverage found four more.** `pytest --cov` reported `artifact_log` 98%, `log_join` 98%,
`log_turn_fields` 98% — four untested defensive branches (no envelope, unusable turn,
missing outgoing hint, seal failure after write). Each now has a real input;
`tests/unit/test_artifact_log_edges.py`. **All four new modules are at 100%.**

**AST parametrize scan** over all seven of this plan's test/fixture files: **3 parametrize
sites** — `PARAMETERS_FIELDS` (guarded, `== 7`), `sorted(LANGUAGE_INTERNAL_FIELDS)`
(guarded, `== 6`), one inline 5-element literal (non-empty, with a positive control). **2
assert-bearing loops** — one guarded by `len(turns) > 0`; the other, over
`LOG_ARTIFACT_MODULES`, was **unguarded** and now carries `== 4`.

## 8. Gates

```
uv run ruff check .                       All checks passed         (0 violations)
bash scripts/check_line_limit.sh          exit 0                    (tracked)
  + all 12 new files explicitly by path   exit 0                    (the no-arg form
                                                                     enumerates via
                                                                     git ls-files and
                                                                     passes VACUOUSLY on
                                                                     an untracked file)
uv run python scripts/check_no_llm_in_strategy.py   OK
uv run pytest tests/ --cov                1974 passed, 0 failed     (baseline 1919)
                                          coverage 97.12%           (baseline 97.02%)
uv run python scripts/dev_launch.py       exit 0                    (521519a78f96c255)
                                          both seats matched=true, capture at turn 5
git status                                clean; no artifact staged from a real run
git check-ignore, every new .py           not ignored (D7-10's guard)
graphify update .                         9449 nodes / 16882 edges
                                          write_log_artifact -> artifact_log.py L129, deg 14
                                          join_game -> log_join.py L119, deg 25
```

File sizes, all ≤ 150 code lines:

| File | Lines | | File | Lines |
|---|---|---|---|---|
| `log_join.py` | 147 | | `test_artifact_log.py` | 125 |
| `artifact_log.py` | 137 | | `test_artifact_log_redaction.py` | 105 |
| `log_turn_fields.py` | 118 | | `test_artifact_log_edges.py` | 109 |
| `log_read.py` | 51 | | `test_log_artifact_reachability.py` | 127 |
| `log_artifact_fields.py` | 30 | | `test_log_artifact_roundtrip.py` | 120 |
| `turn_commit_ledger.py` | 75 | | `artifact_log_fixtures.py` / `_games.py` | 82 / 83 |

### Rule-38 counters — all four numbers, read directly (the files are gitignored)

| | police | thief |
|---|---|---|
| before full `pytest` | 1916 | 1909 |
| after full `pytest` | **1916** | **1909** |
| **suite delta** | **0** | **0** |
| before `dev_launch.py` | 1916 | 1909 |
| after `dev_launch.py` | **1917** | **1910** |
| **one-real-game delta** | **1** | **1** |

Nothing in this plan reads, writes, defaults or reads around the counter. Its **value**
stays the human's at 07-10 (OQ-5).

## 9. Deviations from Plan

### Auto-fixed

**1. [Rule 3 — blocking] Three source files split at the 150-code-line gate.**
`log_join.py` measured **175** combined → `log_read.py` (the crash-tolerant reader) split
on the seam its own docstring named. `artifact_log.py` measured **151** twice → first the
rationale moved to `docs/PRD_log_artifact.md` (which CLAUDE.md §2.3 requires for a central
mechanism anyway — the `display_belief.py` precedent), then `log_artifact_fields.py` split
out (the `artifact_declaration_fields.py` precedent). `log_join.py` hit **154** after the
D-61 fix → the D-61 reasoning moved to PRD §7. **Split, never compressed**; every public
name re-exported, so callers keep one import path.

**2. [Rule 3 — blocking] Four test files instead of two.** The plan named
`test_artifact_log.py` and `test_log_artifact_roundtrip.py`; the gate and the audit forced
`test_artifact_log_redaction.py`, `test_artifact_log_edges.py` and
`test_log_artifact_reachability.py`, plus two fixture modules (`artifact_log_fixtures.py`,
`artifact_log_games.py`, not `test_*` so pytest collects nothing — the
`local_view_fixtures.py` precedent).

**3. [Rule 3 — blocking] `ledger_path_for` extracted in `turn_commit_ledger.py`.** The join
has a path, not an `AgentContext`. Copying `f"{stem}.ledger.jsonl"` would have re-created
the two-private-copies situation that file's own docstring records folding in.
Behaviour-preserving; `ledger_path(ctx)` now delegates. Not in the plan's `files_modified`,
and outside its `<non_goals>` (which name `event_log.py`, `ledger.py`,
`agent_audit_observed.py` — all three untouched).

**4. [Rule 1 — bug] D-61: the `game_uid` check refused the thief an artifact.** §5.
Commit `4787e11`.

**5. [Rule 2 — missing critical] `write_log_artifact` re-verifies seal AND turns.** §3.

**6. [Rule 2 — missing critical] The reachability gate widened to name imports.** §4.

**7. [Rule 3] The integration harness runs `run_final_audit`.** `play_two_peer_game` stops
at the turn loop, so there was no `audit_verdict` record to carry. The helper now runs the
audit leg too — the order `agent_entrypoint.run_agent` uses (turn loop → audit → artifact),
which is also the order this builder's D-64 constraint requires.

**8. [Rule 3] One planned integration assertion was replaced, not weakened.** The plan's
"an honest peer still stamps a turn we disagree with" cannot be observed through the
in-memory harness (its hints do not lag; measured 0 disagreements). Replaced by a stronger
one that CAN run there — every received envelope's claimed turn recomputed independently
from the raw events and asserted equal to the artifact's, floored on a non-zero count — and
the lag itself is measured on 20 real logs in §2 instead of asserted on a harness that
cannot produce it.

### Out of scope, filed not fixed

- **D7-13** — one log, two `game_uid`s (D-61). Resolved for `log_`; 07-07/07-08 inherit it.
- **D7-14** — the builder has no production caller yet (D7-3, fifth occurrence). Structural
  **and required**: D-64 forbids one during play. Enforced by scan, not recorded by grep.
- **D7-5** — the recoverable `handshake -> handshake` transition still fires once per run
  (it is the record carrying the pre-negotiation uid in §5). Pre-existing, unclaimed.

### Authentication gates

None.

## 10. Task Commits

| Hash | Message |
|---|---|
| `3f503b2` | `feat(07-05): join the wire log to the nonce ledger on local turn truth` |
| `e6ea7f0` | `feat(07-05): log_<game_id>_g<NN>.json, self-contained and re-hashable` |
| `1d0a47d` | `test(07-05): pin the nonce-separation boundary as a scan, not a grep` |
| `fdb95eb` | `test(07-05): cover the defensive branches, and guard the last loop` |
| `4787e11` | `fix(07-05): one log can carry two game ids -- D-61, found on a real game` |
| `34169fd` | `refactor(07-05): trim log_join to 147/150, off the exact limit` |
| *(this commit)* | `docs(07-05): complete the log_ artifact plan` -- this SUMMARY, STATE.md, the ticked phase TODO row, D7-13/D7-14, and the refreshed graph |

## 11. What 07-07 and 07-08 must know

* **07-07 must pass the NEGOTIATED `game_uid`** (`ctx.game_uid`), not the process-local one.
  `prior_game_uids` will be `[]` on one seat and one entry on the other; that is correct.
* **07-07 must call this at game end only.** The reachability test will fail the moment
  anything under `network/turn_*` or `orchestrator.py` reaches it, in either import form.
* **07-08 must check `committed > 0`** before displaying a ratio. `verify_log_turns` returns
  `(0, 0)` on an empty artifact and `0 == 0` is `True`.
* **07-08 needs neither source file.** Proven by deleting both.
* **There is no `belief_argmax` in this artifact** (D7-8's constraint is satisfied by
  absence, not by discipline at render time).

---
*Phase: 07-reporting-and-visualization-shell*
*Completed: 2026-08-17*

## Self-Check: PASSED

All 19 claimed paths verified present on disk with `[ -f ]` **and** verified TRACKED by git
with `git ls-files --error-unmatch` — the check that would have caught D7-10 on its own. All
six claimed commit hashes verified reachable in `git log --oneline --all`. Every file-size
number in §8 was re-read from the awk counter after the last edit and three of them were
**corrected** rather than left as written (`test_artifact_log.py` 139→125,
`artifact_log_games.py` 88→83, `log_join.py` 150→147). Every measurement quoted in this
document came off a command run in this session.
