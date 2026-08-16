# Phase 5 deferred items

Out-of-scope discoveries logged during execution, per CLAUDE.md's SCOPE BOUNDARY
rule (only auto-fix issues directly caused by the current task's changes).

---

## 1. `httpx.ConnectError` escapes `call_with_retry` and kills the process on the way out

> **CLOSED by 05-09** (2026-08-14, commit `f31ece5` plus the Task-2 commit that carries this
> file — a hash cannot be embedded in the object that defines it; both are listed in
> 05-09-SUMMARY.md). Re-measured on the same
> `late_peer_round(linger=False)` sequence that reproduced it: the late peer now ends
> `game_over` → `audit_incomplete` → `message_received` → `audit_verdict{matched: true}`,
> `peer_error is None`, and **zero `technical_win` records on either side**. `dev_launch.py`
> still exits 0 with both sides on `audit_verdict matched=true`.
>
> One correction to the diagnosis below, found by measurement: the tuple widening this item
> suggested is **necessary but not sufficient**. `httpx.ConnectError` is the raw shape only when
> the fault lands on an ALREADY-OPEN session; on the CONNECT path — which is how every outgoing
> envelope here starts — fastmcp 3.4.5 re-raises it as
> `RuntimeError(f"Client failed to connect: {exc}") from exc` (`client/client.py:616-624`).
> With the tuple alone the artifact still reproduced verbatim. See 05-09-SUMMARY.md deviation 3.
>
> Residual, examined and accepted: item **#5** below.

**Found:** 05-04 Task 2, while measuring the no-linger baseline on plain loopback.
**Not introduced by this plan** — present at `HEAD = 8f35721` and before.
**Severity:** major. **Owner:** a follow-up plan; needs a decision on `deadline.py`'s
exception taxonomy, which is deliberate and documented (Rule 4 territory).

### Measured

`uv run python scripts/dev_launch.py` at HEAD with Task 2 reverted (no linger),
4 runs, all identical:

- `exit=1`, wall clock 14.4–14.7 s;
- police log ends `game_over(capture)` → `audit_verdict(matched=true)`;
- thief log ends `game_over(capture)` and **nothing after it** — no
  `audit_incomplete`, no `technical_win`, no `audit_verdict`;
- thief stderr ends in an unhandled
  `httpx.ConnectError: All connection attempts failed`, raised from
  `push_final_reveal` → `client.call_tool` → `httpx._transports.default`.

### Why it escapes

`deadline.RETRYABLE_TRANSPORT_ERRORS` is exactly `(McpError, DeadlineExpired)`, and
`call_with_retry` has no catch-all by design (that module's docstring is explicit
about why). `httpx.ConnectError` is neither, so it is not retried, not converted to
a `TechnicalWin`, and not contained by `agent_entrypoint`'s `except ToolError`. It
propagates out of `run_agent` into `main.py` and terminates the process.

Consequence when it fires: **we** become the side that published no nonces (rule 36),
and our own log carries no verdict at all — the exact artifact machine B produced on
2026-08-13.

### Relationship to 05-04

05-04 Task 2's linger closes the loopback occurrence completely (measured: with the
linger the same command exits 0 and BOTH sides record `audit_verdict matched=true`).
It does not close the general case: a peer more than one `backoff_seconds` late than
our linger allows would still hit a closed socket and still crash us rather than
recording a contained verdict.

### Not fixed here, deliberately

- `deadline.py` is not in 05-04's `files_modified`, and its no-retry contract was
  reviewed and affirmed in 06-06.
- 05-04's own critical constraints forbid folding new failure classes into
  `agent_entrypoint`'s `except ToolError` branch, which must stay accusatory and
  ToolError-specific.
- Choosing between "add the transport error class to the retry ladder" and "contain
  it at the audit boundary with its own non-accusatory verdict" is a design decision,
  not a mechanical fix.

### Suggested shape for the follow-up

Contain it where 06-06 contained `ToolError` — at the audit boundary — but route it
to `record_audit_incomplete` (05-04's non-accusatory path), never to a technical win:
failing to CONNECT to a peer that has already torn down is evidence about the
connection, not about the peer's honesty.

---

## 2. `agent_lifecycle.py` has two lines of headroom left (148/150)

**Found:** 05-05 Task 1, measured after landing `default_context`'s `GameIdentity`.
**Not a violation** — the gate passes. Logged so the NEXT change to that file starts
by splitting rather than discovering this at commit time.

`default_context` grew by 4 code lines (build the identity, hand it to both sinks,
attach it to the returned context). 05-04 left the file at 144; it is now **148/150**.
`agent_wiring.py` came the other way, 148 → **122**, because this plan relocated the
two JSONL sink closures out of it into `game_identity.py`.

**Suggested shape when the room is next needed:** move `stop_watchdog` / `stop_runtime`
/ `shutdown_cleanly` into the existing `agent_teardown.py` (which already owns
`linger_for_peer`) and re-export them, the same relocate-and-re-export move
`secret_wiring.py` (05-02) and `game_identity.py` (05-05) both made. That is a
coherent seam — one module owning teardown — worth ~10 code lines, and every caller
resolves unchanged. Not done here: it is outside this plan's `files_modified` and
this plan's own instruction was to split only if a file landed OVER the limit.

### 2026-08-14, 05-10: still open, and re-measured alongside three new splits

`agent_lifecycle.py` is **unchanged at 148/150** — 05-10 did not touch it, and the suggested
`agent_teardown.py` relocation above is still the move when the room is next needed.

Recorded here because 05-10 hit the same wall three times in one plan and took the split each
time rather than logging a fourth instance of this item. Measured after:

| File | Before | After | Split taken |
|---|---|---|---|
| `security/audit.py` | 131 | **142** | `audit_record.py` (`AuditRecord`/`all_matched`, re-exported) — it landed at exactly 150/150 first, which is 148/150 one line worse |
| `network/deadline_errors.py` | 141 | **140** | `deadline_status.py` took the status policy AND inherited the `httpx.HTTPError` paragraph, which is its subject matter |
| `network/deadline.py` | 139 | **134** | `deadline_wait.py` (`bounded`/`wait_for_opponent`, re-exported) — it BREACHED at 152 first |

The general lesson worth keeping: prose relocates to the module that owns the argument, code
relocates behind a re-export, and neither is ever compressed to fit. A file left at exactly the
limit is a worse outcome than this item describes, not a passing one.

---

## 3. `commit_pack.verify_reveal(h, **payload)` is shape-fragile against peer data

**Found:** 05-05 Task 3, while writing the malformed-state case the plan asked for.
**Contained, not left open** — recorded because the containment is local, not general.

`verify_reveal` takes `state`/`move`/`intent`/`nonce` as required keyword arguments,
so ANY other payload shape from a peer (a missing key, an extra key, `state` not a
dict) raises `TypeError` rather than returning False. `agent_entrypoint`'s guard is
`except ToolError`, which does not catch it, so a peer's malformed FINAL_REVEAL would
kill the process before any verdict was recorded — making **us** the side that
published no nonces (rule 36), the same failure class 06-06 fixed for `ToolError`.

**Contained in this plan** at `audit._audit_one`, the ONLY production call site that
sees peer-supplied payloads (grep-confirmed; the other caller,
`scripts/gate6_tamper.py`, operates on records it built itself): the call is wrapped
and a malformed payload becomes a named `AuditRecord` mismatch — evidence — instead
of an exception.

**Left for a future plan:** whether `commit_pack` itself should validate-and-report
rather than raise. That is a security-module contract change, `commit_pack.py` is not
in this plan's `files_modified`, and D-59 deliberately makes that module strict. The
containment above means nothing is exposed today.

### CORRECTION, 2026-08-14 (05-10). The last sentence above was wrong.

The original text is left standing verbatim -- this is an append-only record, not a
rewrite -- but its closing claim, *"The containment above means nothing is exposed
today"*, was an **over-claim**, and 05-VERIFICATION refuted it by probe. It was true of
the `verify_reveal(...)` CALL and of nothing else. Three sites in the same module read
peer structure **before** that try/except was ever reached, and all three raised:
`entry["turn"]` in `_audit_one`, the `{entry["turn"] for entry in peer_records}`
comprehension in `_missing_turns`, and the final numeric `records.sort(...)`.

Two further facts the original note could not have known:

- the containment was also **too narrow for the call it wrapped**.
  `commit_pack.build_commit_payload` raises **`ValueError`** -- not `TypeError` -- for a
  peer-controlled `intent` outside `{truth, lie}` and for an empty `nonce`, and
  `except (TypeError, KeyError)` did not catch either. Measured:
  `ValueError: build_commit_payload: intent must be one of ['lie', 'truth'], got 'maybe'`;
- the note's framing ("the containment is local, not general") was the right instinct
  and the right thing to record. What it got wrong was the confidence of the conclusion
  drawn from it.

**Status: CLOSED by 05-10.** `audit.py` is now total over peer input (see item 7), the
catch is widened to `(TypeError, KeyError, ValueError)`, and the boundary rule is stated
once in `audit.py`'s own source naming every instance found. The genuinely open part is
unchanged and still deferred: whether `commit_pack` itself should validate-and-report
rather than raise. D-59 deliberately makes that module strict, and no caller depends on
it raising, so this stays a design question rather than a defect.

---

## 4. `test_late_peer_teardown.py`'s non-vacuity test is load-sensitive and flakes

**Found:** 05-06 verification, running the full suite while the parallel 05-05 executor
was also running pytest on the same box.
**Not caused by 05-06** — measured below. **Severity:** minor (a flaky gate, not a
product defect). **Owner:** whoever next touches `late_peer_harness.py` (05-04's file,
outside 05-06's `files_modified`).

### The failure

```
FAILED tests/integration/test_late_peer_teardown.py::test_without_the_linger_the_late_peers_own_push_is_cut_off
E   AssertionError: the late peer's push succeeded WITHOUT a linger -- harness proves nothing
```

The test pins 05-04's non-vacuity probe: with `linger=False`, B's own FINAL_REVEAL push
must NOT land. That is a genuine race — the harness starts B's audit `_LATE_SECONDS =
0.3` after A's and then tears A down — so under enough CPU/socket contention B
occasionally wins it and the premise stops holding.

### Measured (attribution, not assumed)

| Tree | Command | Runs | Result |
|---|---|---|---|
| `f5372e2` (pre-05-06 baseline, separate worktree) | the file alone | 6 | 6/6 pass |
| `f5372e2` | whole `tests/integration` (49 tests) | 4 | 4/4 pass |
| HEAD (05-06 landed) | the file alone | 1 | pass |
| HEAD | whole `tests/integration` **minus** `test_hint_delivery.py` | 3 | 3/3 pass |
| HEAD | whole `tests/integration` (55 tests) | 4 | 4/4 pass |
| HEAD | full `tests/` re-run | 1 | 1293 passed |

Both observed failures fell inside the window where a second pytest process (05-05's
executor) was running concurrently; nothing reproduced once the box was quiet. A
targeted probe that disabled 05-06's `outcome is None` compose guard and re-ran the
audit-heavy integration files 4× was clean **with and without** the guard, so the
production change is not the trigger either.

### Suggested shape

Make the premise deterministic instead of racy: have `late_peer_round(linger=False)`
await A's `stop_runtime` before creating B's audit task, so B is unambiguously late
rather than 0.3 s late. That STRENGTHENS the probe (B pushes into a demonstrably closed
listener) instead of widening any assertion. Not done here: `late_peer_harness.py` is
05-04's file and the `linger=True` path must keep B arriving DURING the grace window,
so the two paths need designing together, by the plan that owns them.

**05-09 note:** re-run alone on a quiet box, 3/3 pass (26.4 s, then 33.3 s once the
containment made the failing push walk the whole ladder instead of dying on attempt 1).
Not reproduced; not relaxed.

### 2026-08-16, 05-16: it now reproduces ALONE, and the trigger is sharper than "load"

Re-attributed by paired measurement rather than assumed. **Not caused by 05-16** — the same
pattern appears with this plan's source changes stashed:

| Tree | Runs of the file alone | Result |
|---|---|---|
| `a010a55` (tests only, no 05-16 source change) | 3 | **1 failed, 2 passed** |
| `a010a55` + the 05-16 fix | 3 | **1 failed, 2 passed** |

Identical, and the failure is the item's own message verbatim (`AssertionError: the late peer's
push succeeded WITHOUT a linger -- harness proves nothing`). Two things worth carrying forward:

1. **It reproduces on a QUIET box now**, which the 05-09 note could not. The 0.3 s race has
   simply drifted onto the wrong side of this machine's timing.
2. **The failing run is reliably the FIRST run after a source file changes**, and the two runs
   after it pass. The plausible mechanism is bytecode recompilation slowing A's teardown enough
   for B's push to land — which is the same race, arriving through a schedulable trigger rather
   than through ambient load. That makes the suggested fix (sequence the harness so B is
   unambiguously late, rather than 0.3 s late) more urgent, not less.

Still **NOT fixed here**: `late_peer_harness.py` is 05-04's file, outside this plan's scope, and
the only quick repair is to widen a timing constant — which is weakening the probe, exactly what
this item says must not happen.

---

## 5. An in-game ladder exhaustion accuses the peer even when the fault was OURS

**Found:** 05-09 Task 2, while writing the two-boundary proof.
**EXAMINED AND ACCEPTED — this is not a new defect.** Logged so a later reader does not
rediscover it as one, and so the one honest way to narrow it is on record.

### The residual

`call_with_retry` cannot tell "the peer is down" from "we cannot reach the peer". If our
own uplink drops, our ngrok agent dies, or DNS fails, all four attempts fail, the ladder
exhausts, and `TechnicalWinReason.OPPONENT_UNRESPONSIVE` names the peer for a fault that
was entirely ours. *Unreachable by us* is not *unresponsive*.

### Why it is accepted rather than fixed

- **It is PRE-EXISTING NET-06 policy, not something 05-09 invents.** `deadline.py`'s own
  docstring has documented `McpError` as covering transport failure since 02-07, and 06-06
  reviewed and affirmed that contract. `McpError` already carries the identical ambiguity:
  a client-side timeout against our own dead uplink has always produced this accusation.
  05-09 makes an accidental GAP consistent with that shipped policy — it does not widen the
  policy's reach.
- **The pre-05-09 alternative is strictly worse.** This failure did not become an accusation
  before; it became a CRASH, which publishes no nonces at all and loses under rule 36 with
  no verdict in our own log. A possibly-misattributed technical win beats a guaranteed
  rule-36 sanction against us.
- **Both non-accusatory boundaries are already correct.** At the audit boundary with a board
  outcome standing, the same failure records `audit_incomplete` and accuses nobody (05-04);
  and our own deterministic faults (`LocalProtocolError`/`UnsupportedProtocol`, wrapped or
  not) are raised rather than laundered into an accusation (05-09).

### The one honest narrowing, for whoever wants it

`TunnelManager.ensure_connected` (05-01) is a LOCAL signal about our own side of the link.
A future plan could consult it after the ladder exhausts and, when our own tunnel is down,
record evidence about US — the existing `record_audit_incomplete` shape — instead of a
technical win. Deliberately not done in 05-09: it is a new cross-module dependency from
`deadline.py`'s pure, FastMCP-free retry ladder into tunnel state, and this plan's scope was
the exception taxonomy.

### 2026-08-14, 05-10: the 429 residual belongs HERE, not in a new item

05-10 makes **429 Too Many Requests** retryable (`deadline_status.RETRYABLE_STATUS_CODES`).
An EXHAUSTED 429 ladder therefore accuses the peer for a rate limit that **our own request
volume may have tripped** -- ngrok's free tier meters the tunnel, not the opponent. That is
identical IN KIND to the ours-versus-theirs ambiguity examined and accepted above, so it is
recorded as a widening of this item rather than as a seventh entry pretending to be new.

RETRYING a 429 is nonetheless correct, and is not the residual: it is transient by definition
and conventionally carries `Retry-After`, so a backoff is exactly the right answer. Only the
EXHAUSTION case is ambiguous, and the one honest narrowing named above applies to it unchanged
-- consult our own local `TunnelManager` state before naming the peer.

---

## 6. A 5xx/429 from the peer or the tunnel is an uncaught `HTTPStatusError` mid-game

> **CLOSED by 05-10** (2026-08-14, commit `49b58ac`). Implemented as the "suggested shape"
> below almost verbatim: a named `RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503,
> 504})` consulted by a `retryable_status` predicate, with everything else -- 403 included --
> still propagating. It landed in a NEW sibling `deadline_status.py` rather than in
> `deadline_errors.py`: that file was at 141/150 and this change needed ~20, so the status
> policy took the split and inherited the `httpx.HTTPError`-is-not-the-class paragraph, which
> is its subject matter. `deadline.py` then breached at 152 and was split in turn
> (`deadline_wait.py`, `bounded`/`wait_for_opponent` re-exported), landing at 134.
>
> One correction to the suggested shape, found while writing it: the set must be **enumerated,
> never "any 5xx or 429"**. A range sweeps in **501** and **505** -- deterministic refusals
> that fail identically on all four attempts, burn `3 x backoff_seconds`, and end in a durable
> `TechnicalWin(OPPONENT_UNRESPONSIVE)` against a peer that answered honestly (rules 16/22).
> That is the mirror image of the `LocalProtocolError` shape 05-09 subtracted for the same
> reason. `tests/unit/test_transport_status_containment.py` carries 501/505 as the control:
> written against an any-5xx rule it FAILS (probe recorded in 05-10-SUMMARY.md).
>
> The suggestion to anchor on a real socket was NOT followed, deliberately. The exception is
> built by driving httpx's own `Response.raise_for_status()`, so the class, the status and the
> message text are all the library's own rather than invented -- and the paired 403/404 cases
> then run through the same `call_with_retry` ladder the 502 does, which a stub ASGI app would
> not have exercised any better. The live socket anchor already exists and still passes
> unedited: `tests/integration/test_secret_channel.py`, 3/3.
>
> Residual, examined and accepted: the 429 half of item **#5** above.

**Found:** 05-09, while establishing the `TransportError`-not-`HTTPError` boundary.
**Not introduced by this plan** — `HTTPStatusError` was uncaught before it too, and 05-09
deliberately keeps it that way for the 403. **Severity:** major, but unmeasured on real
hardware. **Owner:** a follow-up plan; needs a status-code policy decision.

### The shape

`mcp/client/streamable_http.py` calls `response.raise_for_status()` at five sites, so ANY
non-2xx becomes `httpx.HTTPStatusError` — and fastmcp's connect path explicitly PRESERVES
that class unwrapped (`client/client.py:620`). It is not under `TransportError`, matches no
clause in `call_with_retry`, and is not caught by `agent_entrypoint`'s `except ToolError`, so
it propagates out of `run_agent` and kills the process: the same rule-36 artifact 05-09 just
closed for connection failures, arriving through a different door.

For **403** that is correct and deliberate: a wrong shared secret is an application answer
about our own credentials, it fires at the handshake before any game exists, and failing
loudly on bad config is this codebase's house style.
`test_secret_channel.py::test_wrong_secret_fails_every_call` pins that shape, and 05-09 added
two more controls that would fail if it were swept into the ladder.

For **429 / 500 / 502 / 503** it is not correct, and those ARE reachable mid-game: ngrok
answers 502 when the upstream local server is momentarily down, and 429 when a free-tier rate
limit trips. Those are transient, and a backoff is exactly the right answer.

### Why it is not fixed here

Splitting `HTTPStatusError` by `response.status_code` is a genuine policy decision (which
codes are transient? does any 4xx other than 429 deserve a retry?), it would be the first
place this codebase branches on an HTTP status at all, and 05-09's own constraints are
explicit that the retryable class is `TransportError` and that `HTTPStatusError` must not be
swept in wholesale. Doing it by status code needs its own plan and its own paired controls —
the 403 control must stay green.

### Suggested shape

A named `RETRYABLE_STATUS_CODES` frozenset in `deadline_errors.py` (429, 500, 502, 503, 504),
consulted by a predicate beside `unwraps_to_retryable`; everything else, 403 included, keeps
propagating. Anchor it on a real socket the way `test_connect_failure_containment.py` does —
a stub ASGI app returning 502 — never on a constructed exception alone.

---

## 7. `audit_peer_records` raises on a malformed peer FINAL_REVEAL

> **CLOSED by 05-10** (2026-08-14, commit `ab4951b`). Written into this file for the first
> time by that plan: 05-VERIFICATION recorded item 7 in its own frontmatter and in its
> anti-patterns table, but never added it here, so a reader following the pointer found
> nothing. It is recorded in full below, closure included, rather than left as a dangling
> reference.

**Found:** 05-VERIFICATION (2026-08-14), by probing the shipped function directly.
**Not introduced by any plan** — present since the function existed. **Severity:** major, and
a blocker for league day rather than for this phase's own gaps: it is not a false-accusation
path and not one of G1–G5.

### Measured, before

```
records-is-a-string   -> TypeError: string indices must be integers, not 'str'
entry-is-a-string     -> TypeError: string indices must be integers, not 'str'
entry-missing-turn    -> KeyError: 'turn'
turn-is-a-string      -> TypeError: '<' not supported between instances of 'int' and 'str'
turn-is-None          -> TypeError: '<' not supported between instances of 'int' and 'NoneType'
turn-is-a-list        -> TypeError: unhashable type: 'list'
mixed valid+malformed -> KeyError: 'turn'
intent-is-'maybe'     -> ValueError: build_commit_payload: intent must be one of [...]
nonce-is-''           -> ValueError: build_commit_payload: nonce must be a non-empty str
```

All of them sit OUTSIDE 05-05's `verify_reveal` try/except (item 3), or — the last two — inside
it but outside the classes it named. `agent_entrypoint`'s guard is `except ToolError`, so each
killed the process before any verdict was written: rule 36 against **us**, the exact artifact
05-04 and 05-09 exist to prevent, through the last uncontained door in the same corridor. A
foreign league implementation whose record shape merely DIFFERS was enough to trigger it.

### Measured, after

Every one of those shapes now returns a named `AuditRecord` mismatch and still LOSES; the
honest peer is untouched. The full before/after table is in 05-10-SUMMARY.md.

### The one thing that had to be got right

The `turn` test is **join-key USABILITY**, never `isinstance(turn, int)`. An honest peer whose
`turn` arrives as the float `3.0` was audited correctly and returned `matched` BEFORE the fix
(measured: `0.0 in {0: h}` is True, `{0} - {0.0}` is empty, the sort is numeric), and JSON has
no int/float distinction. A type check would have converted that honest peer into a technical
loss — this phase's own recurring defect arriving through the FIX instead of the bug (rules
16/22). Integral floats normalise via `int()` and proceed; a paired control pins it and FAILS
against an isinstance rule.

Equally: `_missing_turns` SKIPS an unparseable entry rather than bailing on the whole check. A
bail would have let a peer append one garbage record and silently delete the rule-36 coverage
check for every valid turn — the `{"records": []}` evasion re-opened through a side door.

### The sixth instance, found while closing this one

`handshake_step0._step0_verified` raised `AttributeError: 'str' object has no attribute 'get'`
on a peer `step0_declaration` that was not an object — measured on str/list/int. `evaluate`'s
try/except wraps the DECODE block only, and `respond_to_handshake`'s docstring claims it "never
raises". On the outbound half it escaped `perform_handshake` into `run_agent` and killed us at
the handshake, before move 1. Closed in the same commit, resolving to the EXISTING digest-only
outcome (there is no content to verify, and a peer wanting that outcome can already have it by
sending no declaration — so a hard abort would only add a false-accusation path).

**Nothing is left open here.** The boundary rule now lives in `src/pursuit/security/audit.py`
as a module comment naming all six instances, so a seventh is a review failure rather than a
discovery.

---

## 8. `.planning/ROADMAP.md`'s progress-summary table is stale for every phase but 5

**Found:** 05-08 Task 3 (2026-08-16), while correcting the Phase-5 row of that table.
**Status:** OPEN — logged, not fixed (CLAUDE.md SCOPE BOUNDARY: only Phase 5's row is this
plan's business).

The table at the bottom of `ROADMAP.md` disagrees with the per-phase sections above it:

| Row | Table says | Actually |
|---|---|---|
| 3. Blind Strategy Module | `0/5 · Not started` | its own plan list above is `[x]` on all seven rows (03-01…03-99) — a straight internal contradiction inside one file |
| 2. FastMCP Infrastructure | `0/5 · Not started` | plan checkboxes are also unticked, but `src/pursuit/network/` ships the transport that Phases 5 and 6 measure live over a real tunnel — the tracker under-reports completed work rather than contradicting itself |
| 4. Language and Scent | `13/14 · In Progress` | matches its list (04-14 GATE-4-vs-live-API is genuinely open), so this row is fine |
| 6. Security and Cryptography | `Executed … verify-work pending` | `/gsd:verify-work 6` ran 2026-08-09, UAT 11/11, recorded in `STATE.md` and `docs/phases/phase-6/` |

Only the Phase-5 row was corrected here (`11/15`, GATE-5 MET). **Why it is worth fixing
anyway:** this table is the first thing a grader reads, and rule 38 is about the trackers
telling the truth, not only the capture declarations. Under-reporting is not the
disqualifying direction — but it is the same drift, and it reads as carelessness about
exactly the discipline this project claims. Natural home: a tracker-wide pass in Phase 8's
submission work, or the next `verify-work` that already touches `ROADMAP.md`.

---

## 9. The belief per-turn budget test still fails in full-suite runs after the CPU-time fix

**Found:** 05-08 verification (2026-08-16), running the plan's own `pytest tests/ --cov`.
**Status:** OPEN — logged, **deliberately not fixed** (this plan changes no source, and the
one-line "fix" available is to weaken a budget assertion, which is exactly what must never
be done to make a gate green).

`tests/integration/test_belief_policy.py::test_belief_enabled_completes_within_the_per_turn_time_budget`
failed in **both** full-suite runs (1373 passed / 1 failed / 96.54% coverage, twice) and
**passed alone in 0.21 s**. The failure, verbatim:

```
    assert max(thief_ms) < thief_params.max_decision_ms
E   AssertionError: assert 62.5 < 50
E    +  where 62.5 = max([0.0, 0.0, 0.0, 0.0, 15.625, 0.0, ...])

belief-enabled per-turn decision CPU time over 35 turns -- cop: max=15.625ms mean=2.232ms;
thief: max=62.500ms mean=3.571ms (budget: cop=50ms, thief=50ms)
```

**What the numbers say, and what they do not.** Commit `330e450` re-priced this gate in CPU
time (`time.thread_time`) precisely to stop wall-clock counting OS preemption of other
processes. It did not remove the failure, and the sample above shows why: every measurement
is a multiple of **15.625 ms**, Windows' thread-CPU accounting tick. The decision path is
genuinely fast — mean **3.571 ms** against a 50 ms budget — but a single decision straddling
four ticks is *reported* as 62.5 ms, and `max()` over 35 turns reliably finds one under
full-suite load. So this is a **measurement-resolution defect in the test, not evidence that
the algorithm breaches `max_decision_ms`** — and equally, the test currently cannot tell the
difference, which is the actual problem.

**Do not "fix" it by raising the budget.** `max_decision_ms = 50` lives in
`config/{police,thief}/strategy.json` — checked while writing this: it does **not** appear in
`docs/PARAMETERS.md` under that name or as a decision-time row, so it is a project-chosen
engineering budget rather than a book value. That makes it easier to edit and no more
legitimate to edit *for this reason*: moving a threshold so a red test turns green is
weakening the assertion, and the measurement is what is wrong here, not the threshold.
(Whether this budget belongs in `PARAMETERS.md` at all is a separate, smaller question —
worth asking, not answered here.) The honest repairs are to make the
*measurement* fit the clock's resolution — e.g. time a batch of N decisions and compare the
mean against the budget, so quantization averages out, or assert on a percentile rather than
`max()` while keeping the budget value untouched. Either needs its own plan and a control
that still fails against a genuinely slow brain.

Prior art in this file's own history: this test has been recorded as "the documented
`test_belief_policy` time-budget flake" since 05-09, attributed by measurement each time.
This is the first record of the *mechanism*.

---

## 10. The TURN LOOP still runs its own 135 s wait ladder against a 60 s watchdog

> **CLOSED by 05-16** (2026-08-16, commits `a010a55` measurement, `4e3d42e` fix, `0993b05`
> controls). Closed by the mechanism 05-13 built, not a new one, and **without moving one
> numeric value**.
>
> **Measured before**, on an injected clock in 0.000 s of real time
> (`tests/unit/test_turn_loop_watchdog.py`, `tests/unit/test_turn_push_watchdog.py`):
>
> ```
> config: response_timeout=30 retry_count=3 backoff=5 watchdog_threshold=60
> attempt cost (injected) = 35
> wait attempts=2 elapsed=70.0s touches=0 checks=[False, True] fired=['freeze','exit'] verdict=None
> push attempts=2 elapsed=70.0s touches=0 checks=[False, True] fired=['freeze','exit'] verdict=None
> move attempts=2 elapsed=70.0s touches=0 checks=[False, True] fired=['freeze','exit'] verdict=None
> ```
>
> **After:** `attempts=4 elapsed=140.0s touches=5 checks=[F,F,F,F] fired=[] verdict=TechnicalWin`
> on every leg. 140 s of ladder against a 60 s threshold, zero freeze polls firing, D-13's
> honest verdict recorded.
>
> **One correction to the item's own diagnosis, found by measuring rather than reading.** The
> text below names only the four `wait_for_*` legs. There were **six** unmarked ladders, and
> the ones it missed are the ones a stalled peer hits FIRST: `turn_commit_send.push` sends the
> COMMIT the wait leg is waiting for a reply to, so marking only the waits would have left the
> turn loop dying at exactly the same t=60 s one door earlier. Also unmarked:
> `turn_buffer.await_move` (the toggle-off MOVE wait), `turn_buffer.send_hint`,
> `turn_commit_send.send_move_only`, and 05-15's `capture_declaration` — which runs INSIDE
> `run_turn_loop`, where the watchdog stays armed until `agent_entrypoint:134`, so an unmarked
> ladder there killed us BEFORE `run_final_audit` could publish our nonces. All six are marked
> now; `grep -rn "watchdog\.touch" src/` returns **18** = 12 calls + 5 `on_attempt` hook passes
> + 1 comment (the call-form grep alone returns **12** and undercounts the hooked legs by five).
>
> **Both wrong fixes are refuted by named revert probe**, which is what this item asked for:
> widening `watchdog_threshold` 60 → 150 fails **6 of 8** cases on `assert 140.0 > 150`
> ("a Table-19 NUMBER was moved"), because every ladder case reads the bound from config and
> asserts the ladder outlives it; a blanket `ctx.watchdog.stop()` across the turn loop fails
> **8 of 8**, including `test_a_genuinely_frozen_turn_loop_is_still_killed`
> ("DID NOT RAISE ProcessKilledError") and `test_the_turn_loop_never_disarms_the_watchdog`.
> Six single-leg reverts fail exactly one case each. See 05-16-SUMMARY.md for the full table.

**Found:** 05-13 (2026-08-16), while closing G6. **Severity:** major, unmeasured in the wild.
**Status:** logged, deliberately NOT fixed — out of this plan's scope and a policy decision of
its own.

G6 was written about the AUDIT path. Fixing it made the same shape visible one level up.
`turn_commit_wait.next_protocol_message` touches the watchdog exactly once, AFTER its whole
`call_with_retry` ladder returns — `(retry_count + 1) x response_timeout` plus backoffs =
**135 s** at the shipped Table-19 values, against `watchdog_threshold` = **60 s**. Every
turn-loop wait (`wait_for_opponent_commit`, `wait_for_ack_and_commit`,
`wait_for_reveal_capturing_early_ack`, `wait_for_matching_ack`) inherits it. So an opponent
that goes quiet MID-GAME can still get `os._exit(1)` called on us at t=60 s of a ladder whose
own D-13 verdict would have arrived at t=135 s — we publish no nonces (rule 36 against US)
and write no verdict, which is the same artifact class G6 is about.

05-13 gave `next_protocol_message` an `on_attempt` hook and **deliberately defaulted it to
`None`**, so every turn-loop caller is byte-identical. Passing `ctx.watchdog.touch` there too
is a one-word change and is NOT obviously correct: in-game, a peer that never answers is
exactly the condition NET-07's threshold was chosen to bound, and the turn loop already has a
different, deliberate answer for it (the D-13 technical-win ladder). Deciding which of the two
bounds should win mid-game — and whether `watchdog_threshold` (60) being smaller than one full
ladder (135) is itself the defect — is a parameter-and-policy question, and rule 1 forbids
touching either number without `docs/PARAMETERS.md`. It needs its own plan with a control
proving a genuinely frozen turn loop is still killed.

**Do not close this by widening `watchdog_threshold`.** That is moving a Table-19 value so a
symptom disappears.

---

## 11. Four files are now within six lines of the 150-line gate

**Found:** 05-13 (2026-08-16). **Severity:** minor, mechanical. **Status:** logged.

Measured at `da58bc2` with `scripts/check_line_limit.sh` (exit 0 tree-wide):
`turn_commit_wait.py` **145**, `test_audit_send_failure.py` **148**,
`test_audit_watchdog.py` **146**, `_fakes_agent.py` **144**.

The deferred-item #2 posture applies to each: split BEFORE the next change there, never
compress to fit. `turn_commit_wait.py`'s natural seam is the four `wait_for_*` legs (policy)
away from `next_protocol_message` (the primitive) — the same policy-vs-mechanism split
`handshake.py`/`handshake_wire.py` already uses, and the one its own docstring cites.
`test_audit_send_failure.py`'s is case 5 and the watchdog cases moving to
`test_audit_watchdog.py`, where the fakes already live.

05-13 itself acted on this rather than logging it once: `agent_audit_wiring.py` reached
**exactly 150/150** and was split into `agent_step0_wiring.py` in its own commit (`6920d4d`),
following 05-10's `security/audit.py` precedent of splitting AT the gate rather than at the
breach.

### 2026-08-16, 05-16: two of the four are relieved, and one new file is watched

`test_audit_watchdog.py` went **146 → 142** because its three Table-19 helpers moved to
`_fakes_watchdog.py` at their second copy; every one of its four cases is byte-unedited.
`turn_commit_wait.py` is **unchanged at 145** — 05-16 added only comment lines and inline
keyword arguments there, deliberately, precisely because of this item.

Re-measured at `0993b05`: `turn_commit_wait.py` **145**, `test_audit_send_failure.py` **148**,
`_fakes_agent.py` **144**, `_fakes_watchdog.py` **143** (was 112; it absorbed the three shared
helpers). `test_audit_watchdog.py` is off the list.

05-16 acted rather than logging: `test_turn_loop_watchdog.py` would have reached ~163 with its
NET-07 controls, so the harness went to `_turn_loop_fixtures.py` (74) and the four push legs to
`test_turn_push_watchdog.py` (85), leaving it at **110**. Split, never compressed — no assertion
was shortened to fit.

---

## 12. `push_final_reveal` cannot be driven without a real backoff sleep

**Found:** 05-13 (2026-08-16). **Severity:** minor, test-ergonomics. **Status:** logged.

`deadline.call_with_retry` already has injected `sleep` and `clock` seams — added precisely so
"tests never wait on a real backoff" (its own docstring). Neither `push_final_reveal` nor
`next_protocol_message` plumbs them through, so at production values a four-attempt ladder
costs `3 x backoff_seconds` = **15 s of real wall clock** in any test that drives it.

05-13 worked around it rather than widening a production signature for a test's benefit: the
G6 cases set `backoff_seconds=0` and charge the backoff to the INJECTED watchdog clock
instead, which is the only clock `Watchdog.check_once` reads (see
`test_audit_watchdog._audit_ctx`'s docstring). That is honest for NET-07 — the ladder really
is 140 s from the watchdog's point of view — but it does mean no test anywhere exercises the
real `asyncio.sleep(backoff_seconds)` path at production values. Threading the two seams from
`AgentContext` would remove the workaround; it touches two production signatures, so it wants
its own small plan.

---

## 13. With `commit_reveal=False` the second mover's MOVE envelope is stamped one turn into the future

**Found:** 05-14 (2026-08-16), while building G8's ground truth. **Severity:** major on a
latent path (evidence integrity, rule 20). **Status:** logged, deliberately NOT fixed here.

**Measured**, `scripts`-free probe on `tests/integration/two_peer_game.play_two_peer_game`
with `security.commit_reveal=False` on both sides, one full 16-turn game:

```
police (first mover):  moves=[0..15]  hints=[0..15]   final ctx.state.turn=16
thief  (second mover): moves=[1..16]  hints=[0..14]   final ctx.state.turn=16
```

Turn **16 was never played by anybody**. The hints are correct — that is 05-14 Task 2 — but
`turn_commit_send.send_move_only` reads `ctx.state.turn` (`:119`, `:139`) and is called from
`turn_commit.initiate`, which `take_my_turn` reaches AFTER `record_action` + `maybe_resolve`
(`turn_actions.py:114-117`). On the second mover that `maybe_resolve` fires, so the MOVE
envelope carries N+1 for the action played at N. Exactly the same defect class 05-14 closed
one line away, through a second door.

It is **latent, not active**: shipped config is `commit_reveal: true`, and on that path the
initiator's `maybe_resolve` is genuinely a no-op, so both sides' REVEALs are correct
(`test_hint_delivery.py` pins this, unedited). It costs no game today — the receiver keys its
own record on `ctx.state.turn` (`log_received`'s `local_turn`, 06-UAT Gap 1) and `await_move`
never compares the peer's declared turn — so the damage is confined to what a replay of the
JSONL says the peer claimed.

**Why 05-14 did not fix it.** The repair is to thread the pre-resolve turn into
`turn_commit.initiate` instead of letting it re-read `ctx.state.turn` (`turn_commit.py:67`).
That changes a public entry point's signature, and on the commit-reveal-ON path the same
`turn` value feeds `commit_own_action` — the D-59 hash input and the D-64 ledger join key.
A wrong number there is a rules-19/22 technical loss, not an evidence blemish. That deserves
its own plan with its own tamper tests, not a drive-by inside a hint-channel fix. 05-14's own
tests were built to be independent of it for exactly this reason: the toggle-off case derives
the played turns as `0..N-1` rather than comparing hints against moves, and says so in its
module docstring.

---

## #14 (05-15) -- a dropped envelope costs the final-reveal wait a whole retry ladder

**Logged, not fixed.** `agent_audit_exchange.receive_final_reveal` now loops until an actual
`FINAL_REVEAL` arrives (05-15, the false-accusation fix). Each iteration re-enters
`next_protocol_message`, which is itself bounded by the full
`(retry_count + 1) x response_timeout` + backoff ladder -- 135 s at the shipped Table-19
values. So N stray envelopes ahead of the peer's ledger cost up to N ladders.

Bounded in practice: an honest peer sends at most one Capture Claim, so the realistic worst
case is one extra ladder, and 05-13's per-bounded-attempt watchdog touch is live throughout
(a wedged loop still stops producing attempts and NET-07 still kills us). The shape is
identical to `turn_commit_wait.py`'s four `wait_for_*` legs, which have drained jitter this
way since 06-02.

**Why it was not closed here.** A per-leg total budget is a parameter decision -- it needs a
number that is not in `docs/PARAMETERS.md` today (rule 1), and it interacts with
`watchdog_threshold`. It must **NOT** be closed by widening `watchdog_threshold`, for the
same reason deferred item #10 says so.

---

## #15 (05-15) -- test_bluff.py is at 147/150

`tests/unit/services/test_bluff.py` gained the shared `declaration(kind)` helper (05-15, the
`declare_truthfully` replacement) and now measures 147 code lines. It is already the host of
`FakeProvider`/`_plan`/`_context`/`_result`/`WORD_LIMIT` for two sibling modules.

**The named seam:** move the shared fakes into `tests/unit/services/_bluff_fixtures.py`, the
`_hint_decode_fixtures.py` (05-14) and `_fakes_agent.py` precedent -- a non-`test_*.py`
helper module pytest never collects. Split, never compress.
