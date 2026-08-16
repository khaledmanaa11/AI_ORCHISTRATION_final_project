---
phase: 05-cloud-exposure-and-tunneling
plan: "15"
subsystem: network/declarations
tags: [gap-closure, G10, rules-15-16, rules-21-22, dead-code, false-accusation, DOC-01, LANG-03, QUAL-11]
one_liner: "The dead declare_truthfully is gone with the rules-15/16 reasoning quoted in its place, the stale PRD line carries a dated superseded-by note, and the cop now sends its rule-21 Capture Claim on the GAME_OVER envelope that already existed -- which is what exposed a PRE-EXISTING false-accusation path in the final-reveal wait."
requires:
  - "06-02 (D-66/SEC-07): the barrier declared inside the committed action, which is why rules 15/16 need nothing here"
  - "05-13 (G6): the per-bounded-attempt watchdog touch on the receive leg, preserved byte for byte"
  - "05-04 (G1): board_outcome-driven non-accusation policy in run_final_audit, unchanged"
provides:
  - "network/capture_declaration.py: the cop's rule-21 Capture Claim on the existing MessageType.GAME_OVER, driven by the resolved Outcome"
  - "receive_final_reveal: an envelope-TYPE check, closing a false-accusation path against an honest peer (rules 16/22)"
  - "network/agent_audit_observed.py: observed()/_read_log split verbatim at the 150-line gate"
  - "docs/PRD_deception.md Sec2.1.1: the rules 15/16/21/22 satisfaction table with the rule text quoted verbatim"
  - "docs/PRD_mcp_transport.md: a dated superseded-by note on the receive_barrier row"
affects:
  - "src/pursuit/strategy/deception.py, services/llm/bluff_prompt.py, services/llm/hintbank_templates.py"
  - "src/pursuit/network/orchestrator.py, agent_audit_exchange.py"
  - "docs/PRD_deception.md, docs/PRD_mcp_transport.md"
tech-stack:
  added: []
  patterns:
    - "Split at the 150-line gate, never compress (agent_audit_exchange.py 153 -> 115 + 68; test_agent_audit_exchange.py 152 -> 62 + 113)"
    - "Deferred import in run_turn_loop for the one-directional capture_declaration -> orchestrator edge (the turn_actions.py precedent)"
    - "Assert two facts as ONE tuple when the first would shadow the second"
key-files:
  created:
    - src/pursuit/network/capture_declaration.py
    - src/pursuit/network/agent_audit_observed.py
    - tests/unit/test_capture_declaration.py
    - tests/unit/test_agent_audit_receive.py
  modified:
    - src/pursuit/strategy/deception.py
    - src/pursuit/services/llm/bluff_prompt.py
    - src/pursuit/services/llm/hintbank_templates.py
    - src/pursuit/network/orchestrator.py
    - src/pursuit/network/agent_audit_exchange.py
    - docs/PRD_deception.md
    - docs/PRD_mcp_transport.md
    - tests/unit/strategy/test_deception.py
    - tests/unit/services/test_bluff.py
    - tests/unit/services/test_bluff_prompt.py
    - tests/unit/services/test_bluff_property.py
    - tests/unit/services/test_hintbank.py
    - tests/unit/test_agent_audit_exchange.py
    - tests/integration/test_commit_reveal_protocol.py
decisions:
  - "declare_truthfully is DELETED, on recorded grep evidence: src/ contained only its own definition and its own error string, and a dynamic/getattr/config-string sweep returned zero."
  - "The BARRIER/CAPTURE template rows and prompt arms are KEPT, against the plan's stated preference, on a measurement: deleting them fails 4 tests, one a KeyError escaping bluff.compose(), whose contract is having no failure mode. They are documented as reserved-and-total-by-design instead."
  - "The Capture Claim reuses MessageType.GAME_OVER and the Phase-2 game_over tool. No new message type, no new tool, no new number, no new payload vocabulary."
  - "Only the COP declares, and only on a resolved CAPTURE -- book Sec3.5 p.22 Table 2. The payload is read off the SAME Outcome object the ledger record commits, in two adjacent statements."
  - "The declaration is best-effort and swallows ToolError: a peer rejecting our claim on the way out must never convert a resolved capture into a technical loss."
  - "receive_final_reveal now loops until an actual FINAL_REVEAL. Returning a verdict for a stray envelope instead (the 'defensive' fix) was probed and refused -- it is the same false accusation through a different door."
metrics:
  duration: "~2h"
  tasks: 3
  commits: 5
  completed: 2026-08-16
---

# Phase 05 Plan 15: The Declaration Story, Settled and Written Down — Summary

**G10 closed.** Three tasks, five atomic commits. The plan's rules-first finding held up
under attack: rules 15/16 were already satisfied and there was nothing to fix there. The
two things that were actually wrong got fixed, the third (the capture Claim) got built —
and **building it surfaced a pre-existing false-accusation path that would have cost an
honest peer the game.** That is the headline.

---

## Task-by-task

### Task 1 — `4acee3b` (refactor): the dead constructor, and the reasoning in its place

`declare_truthfully` is gone. **Recorded grep evidence, taken before anything moved:**

```
$ grep -rn "declare_truthfully" src/ --include=*.py
src/pursuit/strategy/deception.py:73:def declare_truthfully(kind: ClaimKind) -> DeceptionPlan:
src/pursuit/strategy/deception.py:90:            f"declare_truthfully is only for {sorted(...)}, "

$ grep -rn "declare_truthfully" src/ --include=*.py | grep -v "strategy/deception.py" | wc -l
0

$ grep -rn "getattr[^)]*declare\|import_module.*deception\|\"declare_truthfully\"\|'declare_truthfully'" src/ scripts/ config/ tests/ | wc -l
0
```

Only its own definition and its own error string. No dynamic reference, no config string,
no `__all__` export. Every caller was a test.

**The plan named three call-site test files. There are FIVE.** `test_hintbank.py:16` and
`test_deception.py:21` also import the symbol at module level. Measured as **probe P1** —
the function deleted, the tests untouched:

```
ERROR tests/unit/services/test_bluff.py
ERROR tests/unit/services/test_bluff_prompt.py
ERROR tests/unit/services/test_bluff_property.py
ERROR tests/unit/services/test_hintbank.py
ERROR tests/unit/strategy/test_deception.py
!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!
5 errors in 1.27s
```

Both directories interrupted, **zero tests run** — the exact blast radius the plan
sequenced against, one file family wider than it knew. All five were edited in the same
commit.

**The three `declare_truthfully` tests were re-specified, never dropped:**

| Deleted test | What it pinned | Where that fact lives now |
|---|---|---|
| `..._builds_the_always_true_kinds` | a barrier/capture claim exists as TRUTH and is never a lie | `test_an_always_true_declaration_is_built_through_the_constructor_itself` — same parametrisation, built through `DeceptionPlan` (the actual gate) |
| `..._refuses_a_policy_kind` | a LOCATION/HEADING claim carries content and comes from a policy | `test_a_policy_kind_always_carries_its_own_content` — pinned against the **live policies** over 50 draws, strictly stronger than an error-message match |
| `..._takes_no_intent_argument` | "there is nowhere to pass the wrong flag" | `test_the_dispatcher_exposes_no_always_true_shortcut` — the module exposes no shortcut **and can no longer name an always-true kind**, so re-adding one needs an import this test fails on. Carries a `plan_deception in public` control so the introspection cannot pass by reading the wrong object |

**The rules reasoning is recorded with the rule text QUOTED**, in
`strategy/deception.py`'s module docstring and in a new `docs/PRD_deception.md` §2.1.1
table:

| Rule (verbatim from `docs/RULES.md`) | Satisfied where |
|---|---|
| 15 — **MUST** "Declare every barrier placement openly" · "Board forgery and automatic loss at audit" | the committed action, `PRD_commit_reveal.md` §2.2 (D-66/SEC-07) — the sanction is *audit-shaped*, which is the shape that design answers |
| 16 — **FORBIDDEN** "Lie about where a barrier was placed" · "Severe disqualification cause" | same: the declared barrier **is** the hashed one; a different placement fails the D-67 re-hash |
| 21 — **MUST** "Declare the truth **only** at the moment of capturing a thief" · "Immediate disqualification for denying reality" | `network/capture_declaration.py` (Task 3) |
| 22 — **FORBIDDEN** "Make a false capture declaration" · "**Immediate disqualification**, zero score, technical loss, no appeal" | same, and by construction — see Task 3 |

### Task 2 — `1c90869` (docs): the stale PRD line

`docs/PRD_mcp_transport.md:65` promised "Phase 3 consumes it in the strategy loop" for
`receive_barrier`, with nothing in the file recording that D-66/SEC-07 moved the barrier
into the committed action. **Appended, never rewritten** (the `deferred-items.md`
correction style): the stale clause is struck through in place and a dated block names
`PRD_commit_reveal.md` §2.2 as the current spec, quotes rules 15/16, and states why
`MessageType.BARRIER` and the tool are **deliberately retained** — the published tool
surface is a league contract, and `grep -rn "MessageType.BARRIER" src/` returns exactly one
hit, the receiving handler at `tools.py:133`. The `game_over` row is corrected in the other
direction: no longer a Phase-7-only stub.

### Task 3 — `0930aac` (feat) + `886772d` (fix): the Capture Claim, and what it exposed

**`0930aac`** — `network/capture_declaration.py`. Book §3.5 p.22 Table 2 ("the cop lands on
the thief's cell and declares Capture Claim") was the one genuine residual: capture was
**derived** on both sides and never transmitted. Built at **zero new protocol cost**, as
the plan required:

- `MessageType.GAME_OVER` — since Phase 2, `envelope.py:32`;
- the peer's `game_over` tool — since Phase 2, `tools.py:136`;
- the same `call_with_retry`/`NetworkParams` ladder — D-17, no new number;
- payload `{outcome, reason}` — the shape `PRD_mcp_transport.md`'s own row already specified.

**Rule 22 is the shape of the module, not a comment on it.** The payload is read off the
SAME resolved `Outcome` object `run_turn_loop` writes into its `game_over` ledger record,
in the two adjacent statements, so the transmitted claim and the audited record *cannot*
disagree. Nothing that could choose is near it — no policy, no brain, and above all no
model. `strategy/` is not imported.

**`886772d`** — and here is the finding. Probing task 3a's own risk before shipping it:

```
### PROBE P2 (pre-fix), queue = [GAME_OVER, FINAL_REVEAL]
peer records returned : []
verdict               : None
REAL peer ledger was  : [{'turn': 0, 'nonce': 'abc', 'h_commit': 'deadbeef'}]
SWALLOWED?            : True
```

`receive_final_reveal` read `records` off whatever `next_protocol_message` returned
**first**. Any other envelope arriving ahead of the peer's FINAL_REVEAL therefore produced
`records=[]` with `verdict=None` — byte-indistinguishable from the `{"records": []}`
rule-36 evasion `security/audit.py` exists to punish. Every played turn then fails
`audit_state` as "absent from final reveal", and an **honest peer is declared a technical
loss**. That is a false accusation, rules 16/22.

**It was pre-existing, not introduced here.** `game_over` is a registered tool on our
published league surface, so any peer implementation calling it already triggered it. Task
3a merely made it certain in our own games. The leg now loops until an actual
FINAL_REVEAL — the same shape `turn_commit_wait.py`'s four `wait_for_*` legs have always
had. Termination is unchanged (the ladder still returns a verdict against a silent peer)
and 05-13's per-bounded-attempt watchdog touch is byte-untouched. A capture claim seen on
the way past is **logged as received evidence**; anything else is dropped as tolerated
jitter, identical policy.

---

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 — Blocking] The plan under-counted the call-site test files by two**
- **Found during:** Task 1, before any deletion landed
- **Issue:** the plan named `test_bluff.py`, `test_bluff_prompt.py`, `test_bluff_property.py`. `test_hintbank.py` and `test_deception.py` also import `declare_truthfully` at module level.
- **Fix:** all five edited in the same commit; measured as probe P1 (5 collection errors, both directories interrupted).
- **Files:** `tests/unit/services/test_hintbank.py`, `tests/unit/strategy/test_deception.py`
- **Commit:** `4acee3b`

**2. [Rule 1 — Bug] The plan's PREFERRED removal of the BARRIER/CAPTURE rows is wrong, and the measurement says so**
- **Found during:** Task 1
- **Issue:** the plan says "Prefer removal" of the unreachable rows and arms, on the ground that "the enforcement that matters lives in `DeceptionPlan.__post_init__` and is untouched either way". True of the *wrapper*; **false of the rows.** `DeceptionPlan(intent=TRUTH, kind=BARRIER)` stays perfectly constructible — `__post_init__` refuses only the LIE combination — so `BANK` must remain TOTAL over every pair the gate permits. `HintBank.select`'s own docstring promises it "cannot KeyError for a real `DeceptionPlan`".
- **Measured (probe X — the two `BANK` rows deleted, nothing else changed):** **4 failed / 42 passed** against a 46-passed baseline, the decisive one being `KeyError` escaping `bluff.compose()`, whose entire contract is that it *has* no failure mode (`test_compose_contains_no_raise_statement`). Deleting the rows converts the zero-token fallback into a raising one. `test_every_legal_kind_intent_pair_selects_without_error` — byte-unedited, and named in its own docstring "No KeyError for any DeceptionPlan the constructor allows to exist" — fails on both parametrisations.
- **Fix:** the plan's second sanctioned option taken instead — kept, with both modules and `PRD_deception.md` §2.1.1 stating **plainly** that the rows have no policy caller and are reserved-and-total-by-design, with the probe number recorded. Removing `ClaimKind.BARRIER`/`CAPTURE` from the enum outright was never on the table: `ALWAYS_TRUE_KINDS` is what `__post_init__` iterates, and an empty map makes the rules-15/16/21/22 refusal **vacuous**.
- **Files:** `src/pursuit/services/llm/hintbank_templates.py`, `src/pursuit/services/llm/bluff_prompt.py`, `docs/PRD_deception.md`
- **Commit:** `4acee3b`
- **Consequence for the phase TODO row:** the row asks for "no unreachable BARRIER/CAPTURE branches left". They are still there. They are not *dead*, they are *total*, and the difference is a `KeyError` in production. The row's intent — nothing left that looks live but is not — is met by documentation instead of by deletion.

**3. [Rule 1 — Bug, pre-existing] `receive_final_reveal` falsely accused an honest peer**
- **Found during:** Task 3, by probing 3a's own risk rather than by reading
- **Issue/measurement/fix:** see Task 3 above. `[GAME_OVER, FINAL_REVEAL]` → `records=[]`, `verdict=None`, peer's ledger discarded → AUDIT_HASH_MISMATCH → TECHNICAL_LOSS against a peer that did everything right.
- **Files:** `src/pursuit/network/agent_audit_exchange.py`
- **Commit:** `886772d`

**4. [Rule 3 — Blocking] Two 150-line gate breaches, both SPLIT, never compressed**
- `agent_audit_exchange.py` reached **153** once the receive-leg loop landed → `observed()`/`_read_log` moved **verbatim** into `agent_audit_observed.py` (115 + 68), along the seam that file's own docstring already named ("how to push/receive one FINAL_REVEAL envelope" **and** "how to read this side's own observed history"). Code byte-identical, verified by diff; only the docstring gained a paragraph. Re-exported, so `agent_audit_wiring.py`, the gate scripts and the suite all resolve it unchanged.
- `test_agent_audit_exchange.py` reached **152** → the four receive-leg cases moved to `test_agent_audit_receive.py` (62 + 113). **Every surviving test body is byte-unedited** (`git diff` shows only the module docstring), so the silent-peer rule-36 fairness control passes without a character touched.
- **Commit:** `886772d`

**5. [Rule 1 — Bug] An existing integration test failed, and its own docstring said why**
- **Found during:** Task 3, full integration run
- **Issue:** `test_toggle_off_is_byte_equivalent_to_pre_phase_6` asserts `types <= _ALLOWED_TYPES_OFF = {"handshake", "move", "hint"}`; the new declaration made it `{'game_over', 'hint', 'move'}`.
- **Fix:** `game_over` admitted — **a correction, not a relaxation.** That test's docstring has always read "only handshake/move/hint/**game_over** types"; the constant simply reflected the fact that nothing had ever *sent* one. The claim it actually makes (`not ({"commit","ack","reveal"} & types)`) is byte-unchanged. The admission is **paid for** with a positive pin added in the same edit: the cop declares exactly once, the thief never, and the payload equals the resolved outcome.
- **Files:** `tests/integration/test_commit_reveal_protocol.py`
- **Commit:** `0930aac`

### Self-audit finding: a shadowed assertion in my own control

`test_a_capture_claim_ahead_of_the_final_reveal_does_not_swallow_it` originally asserted
`records == _PEER_LEDGER` and then `verdict is None` as two statements. **The first
shadows the second**: under both wrong fixes the records assertion fired and the verdict
assertion never ran at all — it could not fail, which is the vacuous shape 05-13 and 05-14
each caught in their own controls. Measured:

```
### P6 failure MODE (no fix -- the swallow):
E   AssertionError: assert [] == [{'turn': 0, ...: 'deadbeef'}]
### P7 failure MODE (the WRONG fix -- the accusation):
E   AssertionError: assert [] == [{'turn': 0, ...: 'deadbeef'}]     <- IDENTICAL
```

Re-pinned as one tuple, and a **sharper wrong fix** built specifically to defeat a
records-only check — probe **P8**, which returns the peer's ledger *correctly* but attaches
an accusatory verdict because a stray envelope was seen. It now fails, reported as:

```
E   AssertionError: assert ([{'turn': 0,...ay envelope')) == ([{'turn': 0,...beef'}], None)
E     At index 1 diff: TechnicalWin(reason=<TechnicalWinReason.PEER_PROTOCOL_ERROR ...>) != None
```

Found by *running* the wrong fix, the same lesson 05-13 and 05-14 both recorded.

---

## Revert probes

| # | What was broken | Result |
|---|---|---|
| **P1** | `declare_truthfully` deleted, the five call-site tests unedited | **5 collection ERRORS**, both directories interrupted, 0 tests run |
| **X** | the two `BANK` rows for BARRIER/CAPTURE deleted (the plan's preference) | **4 fail / 42 pass**, incl. `KeyError` escaping `bluff.compose()` |
| **P2** | *(pre-fix measurement)* `receive_final_reveal` on `[GAME_OVER, FINAL_REVEAL]` | `records=[]`, `verdict=None`, peer ledger discarded |
| **P3** | the `run_turn_loop` call site removed | **2 fail** |
| **P4** | the role guard removed — the thief declares too | **2 fail** |
| **P5** | the outcome guard relaxed to "any outcome" (**rule 22**) | **4 fail** |
| **P6** | receive leg reverted to pre-05-15 | **3 fail** |
| **P7** | wrong fix #1 — a non-FINAL_REVEAL treated as a peer protocol failure | **3 fail** |
| **P8** | wrong fix #2, the *defensive* one — ledger returned correctly, stray envelope still accuses | **2 fail** (the discrimination this plan owed) |
| **P9** | `message_sent` written unconditionally (log claims a declaration that never landed) | **2 fail** |
| **P10** | the `ToolError` swallow removed | **1 fail** |

---

## Measurements

**Live two-process loopback game** (`scripts/dev_launch.py`, exit 0, live `claude-haiku-4-5`,
ngrok tunnel up), one shared uid `6ee059af51c508f5`:

| | police (cop) | thief |
|---|---|---|
| `game_over` envelope | **`message_sent` turn=6** | **`message_received` turn=6** |
| payload | `{'outcome': 'capture', 'reason': "cop landed on the thief's cell; capture resolved by the engine"}` | *byte-identical* |
| `game_over` ledger record | `capture`, turn 6 | `capture`, turn 6 |
| `audit_verdict` | `matched: True` | `matched: True` |
| `technical_win` / `watchdog_incident` | **0 / 0** | **0 / 0** |

The claim, the ledger record and the audit agree on both sides across a real round trip —
and the thief's `message_received` line only exists because `record_received_declaration`
fires inside the fixed receive leg.

**Two-peer harness, both toggle paths:** police sends one `game_over` (turn 5 with
commit-reveal on, turn 16 off), thief sends none, payload `outcome='capture'` both times.

**GATE-6** (`uv run python scripts/measure_gate6.py`, exit 0) — all three §10.4 criteria
**PASS**, evidence RESTORED not committed. Diff against the committed evidence is
**3 timestamp/mtime lines plus exactly two new counter lines** — `"game_over": 1` under
`police_sent` and `"game_over": 1` under `thief_received`, and nowhere else. All **32**
verdict/boolean fields byte-identical.

**Suite:** `1507 passed / 0 failed`, coverage **96.62%** (baseline 1491 / 96.59%) — **+16
tests, +0.03pp**. All four new/changed network modules at **100%**
(`capture_declaration.py` 37/37, `agent_audit_observed.py` 28/28,
`agent_audit_exchange.py` 29/29), `deception.py` / `bluff_prompt.py` /
`hintbank_templates.py` at 100%. `test_late_peer_teardown` (deferred #4) did not fire.

**Gates:** `ruff check src/ tests/` → **All checks passed**; `scripts/check_line_limit.sh` →
**exit 0**; `scripts/check_no_llm_in_strategy.py` → **OK: no forbidden imports under
src/pursuit/strategy** (this plan touched `deception.py`, `bluff_prompt.py` and
`hintbank_templates.py` — the model's own text surface — and the algorithm still decides).
Knowledge graph refreshed: **7719 nodes / 13861 edges / 482 communities** (was 7656 /
13731 / 465).

**Nothing weakened, nothing skipped, no `--no-verify`.**

---

## Deferred

**#14 (new).** `next_protocol_message`'s callers each re-enter the full
`(retry_count+1) × response_timeout` ladder per *dropped* envelope. With the receive leg
now looping, a peer that sends many strays could stretch the audit wait by one ladder each.
Bounded in practice (an honest peer sends at most one declaration) and identical in shape
to the four `wait_for_*` legs that have always worked this way; a per-leg total budget is a
parameter decision needing its own plan and **must not** be closed by widening
`watchdog_threshold`.

**#15 (new).** `tests/unit/services/test_bluff.py` is at **147/150** with the shared
`declaration()` helper in it. Next change there should move the shared fakes into a
`_bluff_fixtures.py` (the `_hint_decode_fixtures.py` precedent), not compress.

Pre-existing #2–#5, #8–#13 unchanged.

## Self-Check: PASSED
