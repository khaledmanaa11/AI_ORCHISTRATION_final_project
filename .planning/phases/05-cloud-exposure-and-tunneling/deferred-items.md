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
