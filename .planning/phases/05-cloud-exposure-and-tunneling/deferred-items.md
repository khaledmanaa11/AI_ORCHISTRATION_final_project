# Phase 5 deferred items

Out-of-scope discoveries logged during execution, per CLAUDE.md's SCOPE BOUNDARY
rule (only auto-fix issues directly caused by the current task's changes).

---

## 1. `httpx.ConnectError` escapes `call_with_retry` and kills the process on the way out

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
