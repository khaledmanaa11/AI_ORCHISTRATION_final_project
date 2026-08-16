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
