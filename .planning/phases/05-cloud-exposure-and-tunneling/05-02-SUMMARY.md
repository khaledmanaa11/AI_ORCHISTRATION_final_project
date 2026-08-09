---
phase: 05-cloud-exposure-and-tunneling
plan: "02"
subsystem: infra
tags: [asgi-middleware, starlette, fastmcp, secrets, shared-secret, streamable-http]

# Dependency graph
requires:
  - phase: 05-cloud-exposure-and-tunneling
    provides: "05-01's TunnelParams.secret_header/secret_env (tunnel.json's
      one config owner) and the tunnel-off-by-env-presence pattern this
      plan's secret-off-by-env-presence pattern mirrors"
provides:
  - "SharedSecretMiddleware (src/pursuit/network/secret_guard.py) -- a pure
    ASGI callable, secrets.compare_digest, 403 before any FastMCP session/
    tool dispatch, rejection logged by fact only (D-56)"
  - "PeerRuntime(..., shared_secret=(header_name, value)) -- server side
    wires the middleware into the same run_async() call that already
    passes sockets=; client side always builds an explicit
    StreamableHttpTransport carrying ngrok-skip-browser-warning
    unconditionally plus the secret header when configured"
  - "secret_wiring.resolve_shared_secret(config_dir) -- reads tunnel.json's
    secret_header + os.environ[secret_env], the factory-function seam
    agent_lifecycle.default_context calls"
  - "tests/integration/test_secret_channel.py -- two real loopback
    PeerRuntimes proving correct-secret/missing-header/wrong-secret over
    actual HTTP sockets, offline"
  - ".env-example: NGROK_AUTHTOKEN, PURSUIT_NGROK_DOMAIN,
    PURSUIT_TUNNEL_SECRET (dummy values)"
affects: [05-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ASGI-boundary middleware (starlette.middleware.Middleware wrapping a
      pure __call__(scope, receive, send) class) attached via
      run_async(middleware=[...]) -- the outer seam, never a check inside
      an @mcp.tool handler"
    - "Explicit transport construction (StreamableHttpTransport(url,
      headers=...)) at every fastmcp.Client() call site instead of a bare
      URL string, which silently infers headers={}"
    - "Secret-shape logic (build_middleware/client_headers) centralized in
      ONE module (secret_guard.py) that both the server call site
      (_run_http) and the client call site (client()) import from, rather
      than duplicated inline at each -- the same QUAL-02 instinct as
      config_hash.py's digests_match"

key-files:
  created:
    - src/pursuit/network/secret_guard.py
    - src/pursuit/network/secret_wiring.py
    - tests/unit/test_secret_guard.py
    - tests/unit/test_secret_wiring.py
    - tests/unit/test_peer_runtime_secret.py
    - tests/integration/test_secret_channel.py
  modified:
    - src/pursuit/network/peer_runtime.py
    - src/pursuit/network/agent_lifecycle.py
    - tests/unit/test_peer_runtime.py
    - .env-example
    - .gitignore

key-decisions:
  - "D-56 implemented exactly as 05-PLAN-OUTLINE.md/05-RESEARCH.md
    specified: ASGI middleware on run_async, explicit
    StreamableHttpTransport on client(), secrets.compare_digest, secret
    VALUE from os.environ only, header NAME from tunnel.json"
  - "resolve_shared_secret landed in a NEW module (secret_wiring.py, beside
    tunnel_wiring.py) instead of agent_wiring.py as the plan's file list
    named -- agent_wiring.py was already at 135/150 code lines with no
    room, and secret_guard.py's Task-1 scope is the middleware itself, not
    env/config resolution. Matches 05-01's own precedent for the identical
    situation (agent_entrypoint.py/tunnel_wiring.py split out of
    agent_lifecycle.py)"
  - "build_middleware()/client_headers() factories live in secret_guard.py,
    not inlined in peer_runtime.py -- peer_runtime.py had no room left at
    its own 150-line ceiling once both the server and client wiring were
    added in place"
  - ".gitignore's broad *_secret*/*-secret* rule-4 guard silently dropped
    every D-56 test file whose NAME contains \"secret\" (test_secret_guard.py,
    test_secret_wiring.py, test_peer_runtime_secret.py,
    test_secret_channel.py) -- fixed with explicit negations, the same
    precedent as the existing !.env-example line, not a rule-4 exception"

patterns-established:
  - "Env-var-presence-as-opt-in, second use (D-56 mirrors D-55's
    tunnel-on/off pattern): the secret_env var's presence is the enable
    signal, no boolean anywhere, so tunnel-off and secret-off are two
    INDEPENDENT opt-ins -- a direct LAN connection can require the header
    with no ngrok process running at all"

# Metrics
duration: ~30min
completed: 2026-08-09
---

# Phase 5 Plan 02: Shared-Secret Channel Summary

**`SharedSecretMiddleware` (pure ASGI, `secrets.compare_digest`, 403 before any FastMCP dispatch) wired into `PeerRuntime`'s `run_async(middleware=...)` and an explicit `StreamableHttpTransport(url, headers=...)` on every outgoing client call -- opt-in per environment via `PURSUIT_TUNNEL_SECRET`, invisible to loopback dev and every existing test.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-08-09T04:55:00Z (approx.)
- **Completed:** 2026-08-09T05:25:43Z
- **Tasks:** 3 of 3
- **Files:** 6 created, 5 modified

## Accomplishments

- `src/pursuit/network/secret_guard.py`: `SharedSecretMiddleware`, a pure
  ASGI callable -- non-`http` scopes pass through untouched; an `http`
  scope missing the header, or carrying a value that fails
  `secrets.compare_digest`, gets a plain `403 Forbidden` and never reaches
  the wrapped FastMCP app. The rejection is logged at `warning` with the
  remote address and the missing/mismatched FACT only, never the expected
  value. Also owns `build_middleware()`/`client_headers()`, the two small
  factories both `PeerRuntime` call sites use, kept in ONE place.
- `PeerRuntime` gains an optional `shared_secret: tuple[str, str] | None`
  constructor kwarg. Server side: `_run_http()` passes
  `middleware=build_middleware(...)` into the SAME `run_async()` call that
  already passes `sockets=`, with a D-57 comment at that call site
  (`host_origin_protection` stays off -- fastmcp's own default, verified
  by reading `fastmcp.settings.http_host_origin_protection` directly:
  `False`). Client side: `client()` now ALWAYS constructs an explicit
  `StreamableHttpTransport` (never a bare URL string -- confirmed by
  direct probe that `Client(url_string)` yields `headers={}`), carrying
  `ngrok-skip-browser-warning: true` unconditionally plus the secret
  header when configured.
- `src/pursuit/network/secret_wiring.py` (new): `resolve_shared_secret(config_dir)`
  reads `tunnel.json`'s `secret_header` + `os.environ[secret_env]`, wired
  into `agent_lifecycle.default_context`'s one `PeerRuntime(...)`
  construction site.
- `tests/integration/test_secret_channel.py`: two REAL loopback
  `PeerRuntime`s (actual sockets, actual middleware, actual HTTP -- not
  the in-memory transport `two_peer_game.py` uses, which bypasses the ASGI
  layer entirely) proving all three cases offline.
- `.env-example` gains `NGROK_AUTHTOKEN`, `PURSUIT_NGROK_DOMAIN`,
  `PURSUIT_TUNNEL_SECRET` with dummy values, closing 05-01's deferred
  documentation.

## Task Commits

1. **Task 1: the middleware** - `5971846` (feat)
2. **Task 2: wire both sides of PeerRuntime** - `70f57e5` (feat)
3. **Task 3: prove it end-to-end in-process** - `b21cf9a` (test)

**Plan metadata:** pending (this commit)

## Files Created/Modified

- `src/pursuit/network/secret_guard.py` - `SharedSecretMiddleware`,
  `build_middleware()`, `client_headers()`
- `src/pursuit/network/secret_wiring.py` - `resolve_shared_secret(config_dir)`
- `src/pursuit/network/peer_runtime.py` - `shared_secret` constructor kwarg;
  `_run_http()` wires `middleware=`; `client()` builds an explicit
  `StreamableHttpTransport`
- `src/pursuit/network/agent_lifecycle.py` - `default_context()` resolves
  and threads `shared_secret` into the one `PeerRuntime(...)` call
- `tests/unit/test_secret_guard.py` - middleware unit tests (httpx.ASGITransport,
  no server)
- `tests/unit/test_secret_wiring.py` - `resolve_shared_secret` unit tests
- `tests/unit/test_peer_runtime.py` / `test_peer_runtime_secret.py` (new,
  split at the 150-line gate) - client-header and `run_async(middleware=)`
  wiring tests
- `tests/integration/test_secret_channel.py` - real-socket end-to-end proof
- `.env-example` - three new dummy env vars
- `.gitignore` - explicit negations for the D-56 test files whose names
  contain "secret"

## Decisions Made

See frontmatter `key-decisions`. Headline: two file-location deviations
from the plan's literal `files_modified` list (`secret_wiring.py` instead
of `agent_wiring.py`; `build_middleware`/`client_headers` in
`secret_guard.py` instead of inline in `peer_runtime.py`), both forced by
the 150-code-line gate and both landing in files that are still exactly
"the two places the channel belongs" the plan's own `<done>` text names --
server-side wiring and client-side wiring -- just split one file further
than the plan anticipated, mirroring 05-01's own precedent for the
identical constraint.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `agent_wiring.py` had no room for the tunnel-secret
resolver; split into a new `secret_wiring.py` module instead**
- **Found during:** Task 2
- **Issue:** The plan's Task 2 text says "`agent_wiring` threads the tunnel
  params through" and lists `agent_wiring.py` in `files_modified`, but that
  file was already at 135 of its 150 code lines; adding
  `resolve_shared_secret` (plus its `os`/`tunnel_config` imports) pushed it
  to 155.
- **Fix:** Created `src/pursuit/network/secret_wiring.py` (beside 05-01's
  own `tunnel_wiring.py`) holding `resolve_shared_secret(config_dir)`, and
  left `agent_wiring.py` byte-unmodified. `agent_lifecycle.py` imports the
  new function directly, matching `make_handshake_responder`'s own
  factory-function injection style the plan asked for.
- **Files modified:** `src/pursuit/network/secret_wiring.py` (new),
  `src/pursuit/network/agent_lifecycle.py`
- **Verification:** `bash scripts/check_line_limit.sh` clean on both
  `agent_wiring.py` (unchanged, 135) and `secret_wiring.py` (new, well
  under 150); `test_secret_wiring.py` (4 tests) covers it at 100%.
- **Committed in:** `70f57e5` (Task 2 commit)

**2. [Rule 3 - Blocking] `peer_runtime.py` had no room for the middleware/
header-building logic inline; moved the two factories into `secret_guard.py`**
- **Found during:** Task 2
- **Issue:** Building `Middleware(SharedSecretMiddleware, ...)` and the
  client headers dict inline in `peer_runtime.py` (as the RESEARCH doc's
  own snippets show it) pushed that file to 157 code lines.
- **Fix:** Added `build_middleware(shared_secret)` and
  `client_headers(shared_secret)` to `secret_guard.py` (already the single
  owner of the shared-secret shape from Task 1); `peer_runtime.py` calls
  both, one line each, at its two seams.
- **Files modified:** `src/pursuit/network/secret_guard.py`,
  `src/pursuit/network/peer_runtime.py`
- **Verification:** `bash scripts/check_line_limit.sh` clean on both files;
  the two factories are covered at 100% via `test_secret_guard.py`'s
  direct wiring assertions plus `test_peer_runtime_secret.py`'s call-site
  assertions.
- **Committed in:** `70f57e5` (Task 2 commit)

**3. [Rule 3 - Blocking] `.gitignore`'s broad secret-name guard silently
dropped every D-56 test file**
- **Found during:** Task 1 (`git add` on `test_secret_guard.py` reported
  "ignored by .gitignore")
- **Issue:** `.gitignore`'s deliberate `*_secret*`/`*-secret*` rule-4 guard
  (protects against ever committing a file that holds a real secret value)
  matches any FILENAME containing "secret" as a substring, including test
  files that merely test the D-56 feature and hold only placeholder
  literals local to the test (`test_secret_guard.py`,
  `test_secret_wiring.py`, `test_peer_runtime_secret.py`,
  `test_secret_channel.py`).
- **Fix:** Added four explicit `!path` negations under a comment, the same
  precedent the file already uses for `!.env-example`. No value in any of
  the four files is a real secret; each was inspected before adding its
  negation.
- **Files modified:** `.gitignore`
- **Verification:** `git check-ignore -v` / `git add -n` confirm all four
  paths are now trackable; `git status --short` after each task's `git add`
  shows them staged, not silently dropped.
- **Committed in:** `5971846` (Task 1), `70f57e5` (Task 2)

---

**Total deviations:** 3 auto-fixed, all Rule 3 (blocking). **Impact on
plan:** All three are mechanical consequences of the 150-code-line gate and
a pre-existing `.gitignore` rule intersecting with this plan's natural file
names -- no scope creep, no change to the plan's `must_haves`, `D-56`
contract, or the D-57 comment placement. Every file the plan's own `<done>`
criteria describe ("both halves of the channel exist in the two places they
belong") still exists exactly where described; the split modules are
narrowly-scoped satellites of those two places, not a redesign.

## Issues Encountered

None. The one open question going in -- what exception a wrong-secret
`fastmcp.Client` call actually raises through a real HTTP 403 -- was
resolved by direct probe (a throwaway script in the scratchpad, discarded
after use, never committed): `httpx.HTTPStatusError` with `"403 Forbidden"`
in the message, asserted directly in `test_wrong_secret_fails_every_call`.

## User Setup Required

None for this plan's automated tests. A real league-day operator sets
`PURSUIT_TUNNEL_SECRET` (the header's VALUE) and exchanges it with the
opponent team out-of-band alongside 05-01's `tunnel.json`-sourced header
NAME (`secret_header`) -- `.env-example` now documents the variable name;
05-03's runbook is the next place this gets a full operator-facing
walkthrough.

## Next Phase Readiness

Ready for 05-03 (Gate 5: smoke script, `GATE-5-MEASUREMENT.md`, Localtonet
runbook, D-57's full documentation, graph refresh). 05-03 can reuse this
plan's exact three-case shape (`test_secret_channel.py`) as the in-process
proof its own smoke script repeats through the real tunnel, and can quote
`SharedSecretMiddleware`, `PeerRuntime(shared_secret=...)`, and
`resolve_shared_secret` verbatim by name. No blockers.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-09*

## Self-Check: PASSED

All 6 created files confirmed on disk (`[ -f ]`); all 3 task commits
(`5971846`, `70f57e5`, `b21cf9a`) confirmed present in `git log`.
