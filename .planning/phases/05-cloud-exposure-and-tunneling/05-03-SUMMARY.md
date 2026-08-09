---
phase: 05-cloud-exposure-and-tunneling
plan: "03"
subsystem: infra
tags: [gate-measurement, ngrok, localtonet, smoke-test, graphify]

# Dependency graph
requires:
  - phase: 05-cloud-exposure-and-tunneling
    provides: "05-01's TunnelManager (start/healthy/ensure_connected/stop)
      and 05-02's SharedSecretMiddleware/client_headers -- this plan drives
      both as shipped, adding zero new production behaviour to either"
provides:
  - "scripts/gate5_tunnel_smoke.py -- the scriptable half of the §10.4
    milestone-5 gate: env-gated (NGROK_AUTHTOKEN/PURSUIT_NGROK_DOMAIN/
    PURSUIT_TUNNEL_SECRET), starts one real peer + tunnel, round-trips an
    authorized and an unauthorized request through the PUBLIC url, writes
    JSON evidence"
  - "scripts/gate5_smoke_checks.py -- missing_env_vars/check_public_url/
    build_evidence/write_evidence, the offline-testable core"
  - "docs/phases/phase-5/GATE-5-MEASUREMENT.md -- both §10.4 criteria
    quoted verbatim; criterion 1 PENDING (smoke script not yet run on this
    machine, no fabricated numbers); criterion 2 PENDING with the full
    human remote-round procedure"
  - "docs/phases/phase-5/LOCALTONET-FALLBACK.md -- the rule-10 fallback
    runbook, documentation-only, no code path (D-57)"
  - "Knowledge graph refreshed (5806 nodes/10476 edges/367 communities);
    TunnelManager and SharedSecretMiddleware both confirmed present"
affects: [06-security-and-cryptography]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "gate4_*-style helper-module split for a manual gate script: the
      offline-testable pure functions (URL check, evidence builder/writer)
      live in a sibling module (gate5_smoke_checks.py) imported by tests
      via the same sys.path-bootstrap idiom scripts/measure_gate4.py uses
      for its own direct execution -- the FIRST time this project actually
      writes offline tests importing FROM scripts/, closing a gap the
      gate4_* precedent itself left open"
    - "Synchronous preflight() / async run_smoke() split inside one script:
      the env-var refusal path is fully unit-testable (no network, no
      pyngrok) while the live network path stays reviewed-logic-only,
      exactly the must_haves' own stated split"

key-files:
  created:
    - scripts/gate5_tunnel_smoke.py
    - scripts/gate5_smoke_checks.py
    - tests/unit/test_gate5_smoke_checks.py
    - tests/unit/test_gate5_tunnel_smoke_preflight.py
    - docs/phases/phase-5/GATE-5-MEASUREMENT.md
    - docs/phases/phase-5/LOCALTONET-FALLBACK.md
  modified:
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "The smoke script's live network path (run_smoke) is reviewed logic,
    not unit-tested -- it needs a real ngrok account this machine does not
    have. Its two testable seams (preflight()'s env refusal, and every
    pure function in gate5_smoke_checks.py) ARE unit-tested offline, per
    the plan's own must_haves wording"
  - "GATE-5-MEASUREMENT.md records BOTH criteria PENDING, not one: unlike
    GATE-4 (mocked numbers existed, only --live was blocked), nothing in
    Phase 5 can run without a real ngrok account on this machine, so
    criterion 1 has no numbers to report yet either -- stated honestly
    rather than filled with a description of what WOULD happen"
  - "Localtonet stays documentation-only (D-57): a second TunnelManager-
    equivalent integration would double the engineering surface for a path
    whose only job is standing by if ngrok is unusable on league day; the
    runbook satisfies rule 10 without that cost"

patterns-established:
  - "A manual gate script's env-preflight is split into its own
    synchronous, dependency-free function specifically so a test can
    assert the refusal message without needing to fake pyngrok, sockets,
    or asyncio at all"

# Metrics
duration: ~35min
completed: 2026-08-09
---

# Phase 5 Plan 03: Gate 5 Measurement Summary

**`scripts/gate5_tunnel_smoke.py` drives the real, shipped `TunnelManager`/`SharedSecretMiddleware` through a public ngrok URL and writes JSON evidence; `GATE-5-MEASUREMENT.md` quotes both §10.4 criteria verbatim and records both PENDING with exact rerun/remote-round procedures; `LOCALTONET-FALLBACK.md` satisfies rule 10's second provider with zero lines of code; the knowledge graph is refreshed.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-08-09
- **Tasks:** 3 of 3
- **Files:** 6 created, 1 modified

## Accomplishments

- `scripts/gate5_tunnel_smoke.py`: one command
  (`uv run python scripts/gate5_tunnel_smoke.py [--config-dir config/police]`)
  that starts one real `PeerRuntime` + the real `TunnelManager`, brings the
  tunnel up, makes an authorized round trip (secret header, expects the
  five D-05 tool names) and an unauthorized one (no header, expects 403)
  **through the public URL**, tears both down, and writes JSON evidence to
  `docs/phases/phase-5/gate5_smoke_evidence.json`. Reuses `TunnelManager`,
  `SharedSecretMiddleware`/`client_headers`, `resolve_shared_secret`, and
  `PeerRuntime` exactly as 05-01/05-02 shipped them -- zero parallel
  reimplementation.
- `scripts/gate5_smoke_checks.py`: `missing_env_vars`, `check_public_url`,
  `build_evidence`, `write_evidence` -- the pure, offline-testable core the
  must_haves specifically demand, split out at the gate4_* helper-module
  precedent.
- `preflight()` (inside `gate5_tunnel_smoke.py`) loads `tunnel.json`,
  resolves the three env-var NAMES it declares
  (`authtoken_env`/`domain_env`/`secret_env`), and raises `SystemExit`
  naming every missing one -- before touching pyngrok, `PeerRuntime`, or
  the network at all. This is the entire offline-safe half of `main()`.
- **11 new tests**, all offline, zero env vars set, zero network:
  `tests/unit/test_gate5_smoke_checks.py` (8 tests: env-var reporting,
  URL-pattern accept/reject-http/reject-mismatch, evidence PASS/FAIL,
  evidence file round-trip) and
  `tests/unit/test_gate5_tunnel_smoke_preflight.py` (3 tests: names every
  missing var, names only the actually-missing ones, returns real params
  when everything is set) -- imported from `scripts/` via the same
  sys.path-bootstrap idiom `scripts/measure_gate4.py` already established
  for its own direct execution.
- `docs/phases/phase-5/GATE-5-MEASUREMENT.md`: both §10.4 criteria quoted
  verbatim from `.planning/ROADMAP.md`. Criterion 1 (reachability) is
  **PENDING** -- honestly, since this machine has none of
  `NGROK_AUTHTOKEN`/`PURSUIT_NGROK_DOMAIN`/`PURSUIT_TUNNEL_SECRET` set and
  no smoke run has happened -- with a field-by-field description of what a
  `PASS` verdict in the evidence JSON must show, and the exact rerun
  command. Criterion 2 (the genuine remote round, CLOUD-02) is **PENDING**
  with the full seven-step human procedure (start agent, read the exchange
  block, deliver URL+secret out-of-band, remote `PURSUIT_OPPONENT_URL`
  paste, play one full round, retain both event logs + verdicts, note the
  machine/network pair) and an explicit paragraph on why this criterion
  cannot be scripted from this repo alone (it requires an actual second
  machine on an actual different network -- not a mocking gap).
- `docs/phases/phase-5/LOCALTONET-FALLBACK.md`: install (exe or Microsoft
  Store), `--authtoken`, dashboard port mapping to
  `127.0.0.1:<agent's local port>` (the exact host/port
  `PeerRuntime._run_http` already binds), `--install-service`/
  `--start-service`, the 30-minute free-tier timeout stated plainly as the
  reason ngrok is primary (D-57), and the league-day re-establish-per-window
  note including that the free-tier public URL changes on every restart.
  States explicitly that no Localtonet code path exists anywhere in the
  repo and why that satisfies rule 10 without doubling the engineering
  surface.
- Knowledge graph refreshed (`graphify update .`): 5806 nodes / 10476
  edges / 367 communities. `TunnelManager` and `SharedSecretMiddleware`
  both confirmed present by grep against the committed report.
  `graph.html` was skipped this pass (5806 nodes exceeds graphify's
  5000-node HTML viz limit, same as 04-12's own pass); `graph.json`/
  `graph.html` stay gitignored per the existing rule.

## Task Commits

1. **Task 1: the smoke script** - `09b0eb3` (feat)
2. **Task 2: the measurement document and the remote-round procedure** - `c45aa71` (docs)
3. **Task 3: the Localtonet runbook and the graph refresh** - `2d3cbcd` (docs)

**Plan metadata:** pending (this commit)

## Files Created/Modified

- `scripts/gate5_tunnel_smoke.py` - `preflight()`, `run_smoke()`, `main()`
- `scripts/gate5_smoke_checks.py` - `missing_env_vars()`,
  `check_public_url()`, `build_evidence()`, `write_evidence()`
- `tests/unit/test_gate5_smoke_checks.py` - 8 offline tests
- `tests/unit/test_gate5_tunnel_smoke_preflight.py` - 3 offline tests
- `docs/phases/phase-5/GATE-5-MEASUREMENT.md` - both §10.4 criteria, both
  PENDING with exact procedures
- `docs/phases/phase-5/LOCALTONET-FALLBACK.md` - the D-57 fallback runbook
- `.planning/graphs/GRAPH_REPORT.md` - refreshed (05-96)

## Decisions Made

See frontmatter `key-decisions`. Headline: `GATE-5-MEASUREMENT.md` records
**both** criteria PENDING (not one PASS-mocked/one-PENDING-live like
GATE-4), because nothing in this phase can execute without a real ngrok
account on this machine -- there is no mocked path to fall back to, and
none was invented.

## Deviations from Plan

None — the plan's three tasks, `must_haves`, and file-content boundaries
(the offline-testable core, both PENDING criteria, the Localtonet
documentation-only scope, the graph refresh) were followed exactly. No
Rule 1-4 triggers encountered.

**Total deviations:** 0.

## Issues Encountered

None. `pyngrok`'s own import (via `TunnelManager`) is confirmed safe at
module-import time (no binary download, per 05-01's own docstring finding)
by the fact that `scripts/gate5_tunnel_smoke.py` imports cleanly and its
11 new tests collect and pass with zero env vars set and zero network
access.

## Verification (plan's own block, run in full)

1. `uv run ruff check .` → **0 violations**. `uv run pytest tests/ --cov`
   → **1116 passed, 95.70% coverage, fully offline** (baseline before this
   plan: 1105 passed, 95.70%; +11 tests, 0 regressions, 0 failures;
   coverage unchanged because `scripts/` is outside
   `[tool.coverage.run] source = ["src", "training"]`, matching the
   gate4_* precedent).
2. `bash scripts/check_line_limit.sh` → **clean**, both for the explicit
   new files and the full tracked-file sweep (`scripts/gate5_tunnel_smoke.py`
   125 code lines, `scripts/gate5_smoke_checks.py` 58, both well under 150;
   the two new test files 66/40).
3. `docs/phases/phase-5/GATE-5-MEASUREMENT.md` quotes both criteria
   verbatim and marks **both** criterion 1 and criterion 2 PENDING, each
   with its own procedure (criterion 2's the full remote-round steps).
4. `grep -n "^\- \[x\]\|^\- \[X\]"` against `.planning/ROADMAP.md`,
   `docs/phases/phase-5/TODO.md`, `docs/TODO.md`, filtered to `05-` rows →
   **zero matches**. Nothing ticked anywhere.
5. `git status --short` after the graph refresh → **empty** (clean tree);
   `graph.json`/`graph.html` never appeared in `git status` at any point
   (gitignored, confirmed).

Additionally (not in the plan's own block, run for completeness per this
task's success criteria): `uv run python scripts/check_no_llm_in_strategy.py`
→ clean ("OK: no forbidden imports").

## User Setup Required

**Two human-pending items remain for Phase 5**, both documented with exact
procedures rather than left implicit:

1. **The smoke run** (criterion 1) — needs `NGROK_AUTHTOKEN`,
   `PURSUIT_NGROK_DOMAIN`, `PURSUIT_TUNNEL_SECRET` set on a machine with a
   real ngrok account, then:
   ```
   NGROK_AUTHTOKEN=<token> PURSUIT_NGROK_DOMAIN=<your-claimed-domain>.ngrok-free.app \
   PURSUIT_TUNNEL_SECRET=<shared-secret> \
   uv run python scripts/gate5_tunnel_smoke.py
   ```
2. **The genuine remote round** (criterion 2, CLOUD-02) — needs a second
   machine on a different network and a human operator; the full seven-step
   procedure is in `docs/phases/phase-5/GATE-5-MEASUREMENT.md`.

Neither is fabricated or approximated here; both are recorded as exactly
what they are — PENDING — per rule 38.

## Next Phase Readiness

Phase 5's three plans are all code-and-test complete
(05-01/05-02/05-03), and the gate's scriptable half plus the full
human-pending procedures are documented. **The phase is NOT yet verified**
(`/gsd:verify-work 5` must not tick GATE-5) until a human runs the smoke
script and the genuine remote round and updates
`GATE-5-MEASUREMENT.md`'s two PENDING sections with real evidence — the
same standing gap Phase 4 already carries for its own live API run. Phase
6 (Security and Cryptography) can begin planning independently of these
two pending items, since Phase 6 depends on Phase 5's CODE (the tunnel +
shared-secret transport layer, both shipped and tested), not on the gate's
own measurement being closed.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-09*

## Self-Check: PASSED

All 7 created/modified files confirmed on disk (`[ -f ]`); all 3 task
commits (`09b0eb3`, `c45aa71`, `2d3cbcd`) confirmed present in `git log`.
