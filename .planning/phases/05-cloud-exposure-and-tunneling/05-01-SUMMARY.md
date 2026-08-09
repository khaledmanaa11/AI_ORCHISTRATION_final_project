---
phase: 05-cloud-exposure-and-tunneling
plan: "01"
subsystem: infra
tags: [pyngrok, ngrok, tunnel, di, config-loader, pep562]

# Dependency graph
requires:
  - phase: 04-language-and-scent
    provides: the Phase-4 config-pair convention (byte-identical role
      files, a *Key enum beside its own loader) that tunnel_config.py
      extends as the tenth config block
provides:
  - "pyngrok>=8.1.2 as a declared dependency (D-54)"
  - "config/{police,thief}/tunnel.json -- byte-identical, five string
    fields (provider, secret_header, authtoken_env, domain_env,
    secret_env), zero numeric leaf (D-55)"
  - "src/pursuit/shared/tunnel_config.py -- TunnelKey, TunnelParams,
    load_tunnel_config(), require_env()"
  - "src/pursuit/network/tunnel_manager.py -- TunnelManager(params,
    network_params, *, connect, disconnect, kill, get_process, sleep,
    clock): start()/healthy()/ensure_connected()/stop(), every pyngrok
    call injected, real pyngrok defaults bound in one place"
  - "src/pursuit/network/tunnel_wiring.py -- build_tunnel_manager(),
    exchange_block(), run_with_tunnel()"
  - "src/pursuit/network/agent_entrypoint.py -- run_agent(), now wrapped
    end-to-end in run_with_tunnel; re-exported from agent_lifecycle.py
    via PEP 562 __getattr__"
affects: [05-02, 05-03]

# Tech tracking
tech-stack:
  added: [pyngrok 8.1.2]
  patterns:
    - "TunnelManager DI: every pyngrok call (connect/disconnect/kill/
      get_process) plus sleep/clock injected as constructor defaults,
      matching Gatekeeper (clock/sleep) and Watchdog (clock/sleeper/
      exit_action)"
    - "Opt-in-by-env-presence: tunnel.json carries no boolean; the
      domain env var's presence IS the enable signal, so every existing
      test/dev flow (which never sets it) stays tunnel-off by
      construction, not by an explicit flag"
    - "PEP 562 module __getattr__ for a one-directional split-module
      dependency (2nd use in this codebase, after orchestrator.py/
      turn_actions.py) -- agent_entrypoint.py imports FROM
      agent_lifecycle.py, so agent_lifecycle.py resolves run_agent back
      lazily instead of an eager, circular import"

key-files:
  created:
    - src/pursuit/shared/tunnel_config.py
    - src/pursuit/network/tunnel_manager.py
    - src/pursuit/network/tunnel_wiring.py
    - src/pursuit/network/agent_entrypoint.py
    - config/police/tunnel.json
    - config/thief/tunnel.json
    - tests/unit/test_tunnel_config.py
    - tests/unit/test_tunnel_manager.py
    - tests/unit/test_tunnel_manager_reconnect.py
    - tests/unit/test_tunnel_wiring.py
    - tests/unit/test_agent_entrypoint.py
  modified:
    - pyproject.toml
    - uv.lock
    - src/pursuit/network/agent_lifecycle.py

key-decisions:
  - "D-54: pyngrok (8.1.2), never ngrok-python -- ngrok-python 1.7.0
    requires Python >=3.12, this project runs 3.11.9"
  - "D-55: zero new numeric parameters -- tunnel.json is five strings;
    reconnect retry_count/backoff_seconds and the liveness cadence are
    reused straight from NetworkParams (Table 19 + the D-18 precedent)"
  - "Tunnel-on/off is decided by the static-domain env var's presence,
    not a tunnel.json boolean -- keeps D-55's 'strings only' contract
    literal and makes tunnel-off the structural default for every test"
  - "run_agent moved out of agent_lifecycle.py entirely (not just
    edited in place) once wrapping it in the tunnel pushed the file
    over the 150-code-line gate; re-exported via the same PEP 562
    __getattr__ fix already proven by orchestrator.py/turn_actions.py"

patterns-established:
  - "Env-var-presence-as-opt-in: a feature whose config block always
    exists but whose activation is gated on an env var no test sets,
    so the feature is exercised only when a real operator opts in"

# Metrics
duration: ~50min
completed: 2026-08-09
---

# Phase 5 Plan 01: Tunnel Lifecycle Summary

**`pyngrok`-driven `TunnelManager` (start/healthy/ensure_connected/stop, every pyngrok call injected) wired into `run_agent` so a peer starts with a stable public ngrok URL, reconnects to the same domain on drop using Table 19's existing retry numbers, and prints a paste-ready exchange block -- zero new numeric parameters, zero secret values anywhere in source or tests.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-08-09
- **Tasks:** 3 of 3
- **Files:** 11 created, 3 modified

## Accomplishments

- `uv add pyngrok` (D-54) -- the only tunnel dependency; `ngrok-python` was
  never viable on this project's Python 3.11.9
- The tenth per-agent config block: `config/{police,thief}/tunnel.json`,
  byte-identical, five string fields, zero numeric leaf (D-55), with a
  fail-loud loader (`load_tunnel_config`) and a separately-tested env-var
  preflight (`require_env`)
- `TunnelManager`: `start()` (preflights NGROK_AUTHTOKEN/domain by name,
  stores `public_url`, propagates connect failures as-is), `healthy()`,
  `ensure_connected()` (bounded reconnect to the SAME domain, reusing
  `NetworkParams.retry_count`/`backoff_seconds`), `stop()` (idempotent
  disconnect-then-kill) -- 100% unit-tested with injected fakes, zero real
  processes or sleeps
- `run_agent` now wraps its entire body in `run_with_tunnel`: tunnel starts
  before the runtime, stops after `shutdown_cleanly`, and a start failure
  aborts before the handshake can even begin. Tunnel-off (the default for
  every existing test) is a transparent no-op
- The league-day exchange block: public URL + which env var the opponent
  sets for the shared secret, never the secret value itself

## Task Commits

1. **Task 1: dependency and the tunnel config block** - `d91d166` (feat)
2. **Task 2: TunnelManager** - `769282b` (feat)
3. **Task 3: lifecycle wiring and the exchange printout** - `7472bb2` (feat)

**Plan metadata:** pending (this commit)

## Files Created/Modified

- `src/pursuit/shared/tunnel_config.py` - `TunnelKey` (enum beside the
  loader, the Phase-4 convention), `TunnelParams`, `load_tunnel_config()`,
  `require_env()`
- `config/police/tunnel.json`, `config/thief/tunnel.json` - byte-identical;
  keys: `version`, `provider`, `secret_header`, `authtoken_env`,
  `domain_env`, `secret_env` (all strings)
- `src/pursuit/network/tunnel_manager.py` - `TunnelManager(params,
  network_params, *, connect=ngrok.connect, disconnect=ngrok.disconnect,
  kill=ngrok.kill, get_process=ngrok.get_ngrok_process, sleep=time.sleep,
  clock=time.monotonic)` with `.start()`, `.healthy()`,
  `.ensure_connected()`, `.stop()`, `.public_url`, `.params`
- `src/pursuit/network/tunnel_wiring.py` - `build_tunnel_manager(config_dir,
  net) -> TunnelManager | None`, `exchange_block(public_url, params) -> str`,
  `run_with_tunnel(tunnel, body) -> T`
- `src/pursuit/network/agent_entrypoint.py` - `run_agent(config_dir, *,
  game_uid=None)`, moved here from `agent_lifecycle.py` at the 150-line
  gate, wrapped in `run_with_tunnel`
- `src/pursuit/network/agent_lifecycle.py` - `run_agent` replaced by a
  PEP 562 `__getattr__` lazy re-export from `agent_entrypoint.py`;
  `default_context`/`start_server`/`shutdown_cleanly` unchanged
- `tests/unit/test_tunnel_config.py`, `test_tunnel_manager.py`,
  `test_tunnel_manager_reconnect.py`, `test_tunnel_wiring.py`,
  `test_agent_entrypoint.py` - full new-module coverage, all with fakes

## Interfaces for 05-02 / 05-03

**`TunnelManager` signature** (`src/pursuit/network/tunnel_manager.py`):

```python
class TunnelManager:
    def __init__(
        self,
        params: TunnelParams,
        network_params: NetworkParams,
        *,
        connect: Callable[..., object] = ngrok.connect,
        disconnect: Callable[[str], None] = ngrok.disconnect,
        kill: Callable[[], None] = ngrok.kill,
        get_process: Callable[[], object] = ngrok.get_ngrok_process,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None: ...
    def start(self) -> None: ...          # sets self.public_url, raises loudly on failure
    def healthy(self) -> bool: ...
    def ensure_connected(self) -> bool: ...  # bounded reconnect to the SAME domain
    def stop(self) -> None: ...            # idempotent disconnect-then-kill
    # public attrs: self.public_url: str | None, self.params: TunnelParams
```

**`tunnel.json` key list** (`config/{police,thief}/tunnel.json`, both
byte-identical): `version`, `provider`, `secret_header`, `authtoken_env`,
`domain_env`, `secret_env` -- all strings, D-55 has zero numeric leaves.
`secret_header` is the exact header NAME 05-02's `SharedSecretMiddleware`
and `PeerRuntime.client()`'s explicit `StreamableHttpTransport` will both
read from this same loaded `TunnelParams` object (one config owner, per the
outline's own note). `secret_env` names the env var 05-02 resolves for the
secret's actual VALUE.

## Decisions Made

- D-54/D-55 implemented exactly as `05-PLAN-OUTLINE.md` specified (see
  frontmatter `key-decisions`).
- Tunnel-on/off is decided by the static-domain env var's presence, not a
  boolean in `tunnel.json` -- see frontmatter.
- `run_agent` relocated wholesale to `agent_entrypoint.py` (PEP 562 lazy
  re-export from `agent_lifecycle.py`) once `agent_lifecycle.py` -- already
  sitting at exactly 150 code lines before this plan -- had no room left to
  absorb the tunnel wrapping in place. Mirrors the already-proven
  `orchestrator.py`/`turn_actions.py` fix for the identical problem
  (one-directional split-module dependency, avoiding a load-order circular
  import).

## Deviations from Plan

None — the plan's three tasks, `must_haves`, and file-content boundaries
(D-54, D-55, the DI shape, the tunnel-off default) were followed exactly.
Two additions beyond the plan's literal `files_modified` list were made
under CLAUDE.md's "every module gets a test file" rule (04-03-SUMMARY.md's
own precedent for the identical situation): `tunnel_wiring.py` and
`agent_entrypoint.py` did not exist as named files in the plan (the plan
explicitly authorized "split a helper module if agent_lifecycle.py
approaches its line limit" — it was already AT the limit), and each got its
own test file (`test_tunnel_wiring.py`, `test_agent_entrypoint.py`).

**Total deviations:** 0 rule-triggered. Two file additions were plan-
authorized splits, not unplanned scope.

## Issues Encountered

None blocking. One pre-existing (not introduced by this plan) minor
coverage gap noted for completeness: `agent_lifecycle.py` lines 114 (the
default `log_path` branch in `default_context`) and 144 (`start_server`'s
body) were already uncovered before this plan (confirmed via `git stash` —
baseline was 72% on that file, with the entire old `run_agent` function,
18 lines, ALSO uncovered). This plan's changes improved the file's coverage
from 72% to 90% overall (moving `run_agent` out to a fully-tested
`agent_entrypoint.py`, now 100%); the two remaining pre-existing gaps are
out of this plan's scope per the deviation rules' scope boundary and are
not fixed here.

## Verification (plan's own block, run in full)

1. `uv run ruff check .` → **0 violations**. `uv run pytest tests/ --cov`
   → **1087 passed, 95.64% coverage** (baseline before this plan: 1051
   passed, 95.21%; +36 tests, 0 regressions, 0 failures).
2. `bash scripts/check_line_limit.sh` → **clean** (every touched/created
   file ≤ 150 code lines). `uv run python scripts/check_no_llm_in_strategy.py`
   → **clean** ("OK: no forbidden imports").
3. No test touches a real network, process, or `ngrok.exe` — every pyngrok
   call (`connect`/`disconnect`/`kill`/`get_process`) and every sleep is an
   injected fake in every unit test; the one test that references the real
   `pyngrok.ngrok` functions only compares function IDENTITY, never calls
   them.
4. `grep -rn "authtoken\|ngrok-free" config/ src/` → only key/field NAMES
   and the literal env-var NAME `NGROK_AUTHTOKEN` — zero values, zero
   secrets, confirmed by inspection of every match.
5. `git diff` on `peer_runtime.py`, `envelope.py`, `handshake*.py`,
   `tools.py` → **empty** on all four.

## User Setup Required

None for this plan. `NGROK_AUTHTOKEN`, `PURSUIT_NGROK_DOMAIN`, and
`PURSUIT_TUNNEL_SECRET` are the three env vars a real league-day operator
must set (their NAMES only, per `config/{police,thief}/tunnel.json`) —
05-02/05-03 will document this fully; no test on this machine requires any
of them to be set, and none are.

## Next Phase Readiness

Ready for 05-02 (shared-secret channel: `SharedSecretMiddleware` on the
ASGI boundary, `PeerRuntime.client()`'s explicit `StreamableHttpTransport`
headers, `.env-example`) — 05-02 reads `TunnelParams.secret_header` and
`TunnelParams.secret_env` from this plan's loader, one config owner, as the
outline specified. No blockers.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-09*

## Self-Check: PASSED

All 12 created files confirmed on disk (`[ -f ]`); all 3 task commits
(`d91d166`, `769282b`, `7472bb2`) confirmed present in `git log`.
