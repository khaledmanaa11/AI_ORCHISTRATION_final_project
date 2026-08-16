# Remote round runbook — GATE-5 criterion 2

**Purpose:** close the one item in this project that no script in this repository can
produce. Everything else is measurable solo; this is not.

> **Success Criteria** (book milestone gate, §10.4), quoted from `.planning/ROADMAP.md`
> Phase 5:
>
> 2. An agent on a remote machine connects through the tunnel and plays a full round
>    against the local agent

Criterion 1 (public reachability) already PASSED live on 2026-08-09 —
[`gate5_smoke_evidence.json`](gate5_smoke_evidence.json). This runbook is criterion 2 only.
The measurement record it closes is [`GATE-5-MEASUREMENT.md`](GATE-5-MEASUREMENT.md).

> **Status, 2026-08-16: criterion 2 is CLOSED** by remote-round **attempt 4** — two full
> rounds, agreeing `capture` verdicts and `audit_verdict matched=true` on both machines
> ([`remote-round-2026-08-16-attempt4/`](remote-round-2026-08-16-attempt4/)).
> **This file is not retired.** It is the durable operator procedure for league day, and it
> is amended below with what attempts 1–4 each cost to learn: attempt 1 lost a day to
> unretained consoles and a 72 s clock skew, attempt 2 died to a tunnel drop no one could
> attribute, attempt 3 played a whole round on template hints because a key was never
> exported, and attempt 4 still went out with only one machine's console. Every item marked
> **learned the hard way** below is there because a round already paid for it.

Running it **after** Phase 6 is deliberate and better evidence: the round exercises the
commit-reveal protocol (Phase 6) and the live LLM hint layer (Phase 4) over a real network
at the same time.

---

## 1. The shape of the test

| | Machine A | Machine B |
|---|---|---|
| Role | `police` | `thief` |
| Config dir | `config/police` | `config/thief` |
| Local port | 8001 | 8002 |
| Network | e.g. home wifi | **a different network** — phone hotspot, campus, elsewhere |

**Both machines need a public URL.** This surprises people: each peer is simultaneously an
MCP server and an MCP client, and pushes envelopes to the *other* side's tools
(`receive_commit`, `receive_ack`, `receive_reveal`, `receive_final_reveal`). There is no
polling path anywhere in `src/`, so a peer that cannot be reached inbound cannot play, and
one tunnel is not enough for two agents.

The network boundary is the point of the criterion. Two machines on the same LAN does not
close it. The cheapest genuine boundary: leave A on wifi, put B on a phone hotspot.

---

## 2. Machine B's tunnel — pick one path

ngrok's free plan allows **3 concurrent agents** but only **1 static domain per account**,
and machine A has already claimed this account's domain. Machine B therefore needs its own
endpoint. `tunnel_wiring.build_tunnel_manager` only starts a tunnel when
`PURSUIT_NGROK_DOMAIN` is set, so an ephemeral random ngrok URL is not a drop-in
substitute.

### Path A — a second free ngrok account (recommended)

Sign up with a different email address you own (a university address is the natural
second), claim that account's free static domain, and copy its authtoken. Machine B then
runs exactly like machine A and `scripts/gate5_tunnel_smoke.py` works on it unchanged,
giving B an independent reachability proof before the joint session.

### Path C — standalone ngrok CLI on machine B (proven 2026-08-16)

Used in attempt 2, forced by Windows **Smart App Control**: SAC blocks the unsigned binary
pyngrok downloads (`OSError: [WinError 4556] An Application Control policy has blocked this
file`) and removes it, so every run re-downloads and re-fails. The signed Microsoft-Store
ngrok runs fine — but its App Execution Alias is a zero-byte reparse point that cannot be
copied into pyngrok's expected path. So: run ngrok **by hand** and run the agent
**tunnel-off**, keeping B's static domain (unlike Path B's random URLs, nothing on machine
A changes).

```
winget install --id ngrok.ngrok -e
ngrok config add-authtoken <B's token>
ngrok http 8002 --domain=<B's reserved domain>        # window 1, leave running
```

In window 2, start the agent with **`PURSUIT_NGROK_DOMAIN` unset** (the tunnel-off signal —
`build_tunnel_manager` returns `None` and pyngrok is never touched). `PURSUIT_TUNNEL_SECRET`
still applies — the secret is independent of who runs the tunnel. **Start order changes:**
A spends seconds inside pyngrok before binding; B binds instantly. Start A first, count to
five, then start B — starting together makes B's handshake fire into A's not-yet-open
listener. Note the trade: on this path B is outside the 05-11 in-process tunnel watch; a
mid-game drop of B's tunnel is repaired only by the standalone agent's own reconnect.

### Path B — Localtonet on machine B (fallback, D-57)

Full install-through-use procedure: [`LOCALTONET-FALLBACK.md`](LOCALTONET-FALLBACK.md).
Point its HTTP tunnel at `127.0.0.1:8002` and read the assigned public URL from the
dashboard.

On this path machine B leaves **`PURSUIT_NGROK_DOMAIN` unset** — the agent runs tunnel-off
and simply binds its local port, while Localtonet forwards to it from outside. The shared
secret still applies in both directions: `secret_wiring.resolve_shared_secret` keys off
`PURSUIT_TUNNEL_SECRET` alone and is deliberately independent of whether any tunnel is
active. `gate5_tunnel_smoke.py` is pyngrok-specific and does **not** apply here; prove
reachability with a manual request to `https://<B's localtonet url>/mcp` carrying the
`X-Pursuit-Secret` header instead.

### The shared secret

One value, used by **both** sides, delivered out-of-band (a message, a call). Never
committed, never in `config/`, never in a file in this repo — `os.environ.get()` only
(rules 39–40). A mismatch makes every call 403.

---

## 3. Machine B setup

Both machines must be on the **same commit**: the handshake compares SHA-256 digests of the
shared config, and any drift aborts with `CONFIG_MISMATCH` before move 1.

```
git clone https://github.com/khaledmanaa11/AI_ORCHISTRATION_final_project.git
cd AI_ORCHISTRATION_final_project
git checkout <the commit machine A is on>
uv sync
```

**Verify the digests rather than assuming.** On machine B:

```
uv run python -c "from pursuit.network.config_hash import config_digest; from pursuit.shared.scent_config import load_scent_model, scent_digest; print('game_params:', config_digest('config/thief/game_params.json')); print('scent:', scent_digest(load_scent_model('config/thief/scent.json')))"
```

Re-measured on machine A at commit `330e450` and **unchanged** since `0427137`, where they
were first recorded (identical across both role directories — recompute if
`game_params.json` or `scent.json` ever change):

| Digest | Value |
|---|---|
| `game_params` | `23f86a93589131ae3558a4a697fc2105aa878809fa5ed62a11a28a528f25c975` |
| `scent` | `c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e` |

A mismatch is information, not something to edit away. Editing config to force agreement
defeats the check.

**Both machines must be on the same *post-fix* commit — write the hash into the evidence.**
Equal digests are necessary but not sufficient: `game_params.json` and `scent.json` are the
only files hashed, so two machines can agree on every digest while running months-apart
`src/`. Record `git rev-parse --short HEAD` from **both** machines alongside the digests.
For reference, each attempt's commit: attempt 1 `384da44`, attempt 2 `9bda33a`,
attempts 3 and 4 `0632e04`.

**Prove the environment before involving the network:** `uv run ruff check` (0 violations),
`uv run pytest -q` (all green), then one full local loopback game with
`uv run python scripts/dev_launch.py`. Expect `config/*/games_played.json` to change —
that is the Step-0 counter, it is not part of any exchanged digest. Nothing on machine B
gets committed.

---

## 4. The joint run

Set the environment in the shell that will run the agent — there is no dotenv loader in
this project, so a `.env` file is not read.

**Machine A** (PowerShell):

```powershell
$env:NGROK_AUTHTOKEN       = "<A's ngrok token>"
$env:PURSUIT_NGROK_DOMAIN  = "<A's reserved domain>"
$env:PURSUIT_TUNNEL_SECRET = "<the shared secret>"
$env:PURSUIT_OPPONENT_URL  = "https://<B's public host>/mcp"
$env:ANTHROPIC_API_KEY     = "<key — optional, makes the language layer live>"
uv run python -m pursuit.main --config-dir config/police
```

**Machine B** (PowerShell, Path A; on Path B omit `PURSUIT_NGROK_DOMAIN`):

```powershell
$env:NGROK_AUTHTOKEN       = "<B's ngrok token>"
$env:PURSUIT_NGROK_DOMAIN  = "<B's reserved domain>"
$env:PURSUIT_TUNNEL_SECRET = "<the same shared secret>"
$env:PURSUIT_OPPONENT_URL  = "https://<A's public host>/mcp"
$env:ANTHROPIC_API_KEY     = "<key — optional>"
uv run python -m pursuit.main --config-dir config/thief
```

Because both domains are *reserved and static*, both sides can be wired before either
process starts — there is no chicken-and-egg wait for a URL. Sanity-check the wiring first
on each side with `--check-config`, which prints the resolved role, listen address and
opponent URL without starting a server; `opponent_url` must show the peer's **public**
host, not `127.0.0.1`.

### Pre-flight — five recordings, each paid for by a previous attempt

Do all five **before** either process starts. None takes a minute; each one cost a whole
round to learn.

1. **Both machines' commit hash and config digests** (§3 above) — into the evidence file.
2. **Each machine's UTC clock — learned the hard way.** In attempt 1 the two machines' clocks
   were **≈72 s apart**, and comparing timestamps *across* machines produced a confidently
   wrong causal story that survived hours of analysis. Record both clocks now:

   ```powershell
   Get-Date -AsUTC -Format o     # PowerShell
   ```
   ```
   date -u +"%Y-%m-%dT%H:%M:%SZ"  # sh
   ```

   Then, for the rest of the round: **compare timestamps only WITHIN one machine.** Across
   machines, the ordering evidence is the *content* — a commit hash this side logged as sent
   and that side logged as received — never the clock.
3. **Both consoles redirected, stdout AND stderr, for the whole session — learned the hard
   way, twice.** Attempt 1 kept machine A's console and not B's, so B's side of the teardown
   was unreconstructable; attempt 2 kept **neither**; attempt 4 still shipped with only A's.
   On each machine:

   ```powershell
   uv run python -m pursuit.main --config-dir config/police 2>&1 |
       Tee-Object -FilePath consoleA.txt
   ```

   Two honest notes from attempt 4's retained capture: PowerShell wraps every stderr line in
   a `NativeCommandError` record (harmless — the text is all there), and `Tee-Object` writes
   **UTF-16**, so `grep`/`rg` need `-a` or a conversion afterwards. If your `Tee-Object`
   supports `-Encoding utf8`, pass it and the file stays greppable.
4. **The ngrok agent log on both machines — see §5 item 6.** Set it up now; it cannot be
   recovered afterwards.
5. **Decide the language layer deliberately — learned the hard way.** Attempt 3 played an
   entire clean round on the deterministic template bank because neither machine had
   exported `ANTHROPIC_API_KEY`. That is a *sanctioned* mode, not a bug, and the Step-0
   declaration says so honestly (`llm_name: template-fallback (no LLM calls)`) — but it is
   not the same evidence as a live model. This project reads `os.environ` only and has no
   dotenv loader, so a key sitting in a local `.env` is **not** loaded: export it into the
   launch shell yourself (never commit it, never echo its value). Then confirm at startup —
   the run's own `declaration_<uid>.json` must read `claude-haiku-4-5`, not
   `template-fallback (no LLM calls)`, before you trust the round as a live-LLM round.

**One more, from attempt 4's failed launch:** if a previous ngrok agent is still holding the
reserved domain, the launch dies with `ERR_NGROK_334 — the endpoint ... is already online`
(retained: `remote-round-2026-08-16/consoleA_2026-08-14_failed_launch_ERR_NGROK_334.txt`).
Kill leftover ngrok agents on both machines first.

### Start them together — the handshake does not retry

`perform_handshake` makes **exactly one attempt: no retry, no timeout, no sleep**
(`network/handshake.py`). If one side fires before the other's server is listening it logs
`peer unreachable during handshake` and exits. Count down and start within a second or two
of each other. A failed start is a restart of both, not a hang.

*(League-day note: this is the same coordination the league requires with an opposing team.
A bounded handshake retry would remove the sharp edge — logged here as a known operational
risk, not silently tolerated.)*

Play to a **real outcome** — capture, survival, tie, or technical loss. A partial handshake
does not close the criterion.

### What should look different from attempt 1 — how to spot a regression live

Attempt 1 (2026-08-13) ran a complete 5-turn game to a real capture and still failed the
criterion. Five things were fixed afterwards; each has a signature you can check *during* the
round rather than in the post-mortem. If one of these is missing, stop and say so — do not
re-run until it looks good.

| Check | Attempt 1 | Expected now | Fixed by |
|---|---|---|---|
| One game UID | two different stems (`074fc2b16888899e` on A, `d50ceb00be724b93` on B) | **one** stem shared by both machines' `.jsonl`, `.ledger.jsonl` and `declaration_*` | 05-05 (D-61) |
| Inbound hints logged | **zero** `message_received` + `hint` records on either machine | both sides carry them | 05-06 (rule 20) |
| Hints actually decoded | machine B: five `no_hint` in a row | both sides show ≥1 `incoming_hint` that is **not** `no_hint` in `language_turn` | 05-06 |
| Verdicts | A `capture`; B `capture` **then** a spurious `technical_win {opponent_unresponsive}` | both sides `capture` (or the same real outcome) + `audit_verdict`, **no** `technical_win` against a peer that answered | 05-04 |
| Game end | A cancelled its server and killed its tunnel with zero grace, mid-exchange | a **bounded pause** after the audit before the process exits | 05-04 |

**Do not `Ctrl-C` at `game_over`.** That pause is the fix, not a hang: `linger_for_peer`
drains the peer's in-flight exchange, capped by `NetworkParams.response_timeout` with a
`backoff_seconds` quiet interval (Table 19 values — no new number was introduced). Measured
on a clean loopback pair it costs **17.44 s / 17.64 s** of wall clock against **14.44–14.72 s**
without it (`05-04-SUMMARY.md`); over a real tunnel expect more. Killing the process during
that window recreates attempt 1's failure by hand.

One thing this list cannot promise: attempt 2's mid-game tunnel drop is now watched and
repaired on a bounded budget (05-11), but **that repair path has never fired in a live
round** — no drop occurred in attempts 3 or 4. If your tunnel drops, that is new evidence:
keep the ngrok agent log (§5 item 6) whatever the outcome.

---

## 5. Evidence to retain

`logs/` is gitignored, so evidence must be **copied out** to be committed.

1. Both peers' `logs/<role>/<game_uid>.jsonl`.
2. Both sides' final verdict — they must agree (rule 38 honesty applies to this round like
   any other) — and each process's exit code (non-zero means a technical loss was recorded,
   including one the Final-Reveal audit declared).
3. The machine/network pair actually used, in one line: *"machine A: Windows 11, home wifi;
   machine B: `<desc>`, phone hotspot"*. The criterion is about crossing a genuine boundary,
   so which one was crossed is part of the evidence.
4. On Path A, machine B's own `gate5_smoke_evidence.json`, kept as
   `gate5_smoke_evidence_machineB.json` so it does not clobber machine A's.
5. **Both machines' FULL console output — stdout AND stderr — for the whole session**
   (§4 pre-flight item 3), named per machine (`consoleA_<attempt>.txt`,
   `consoleB_<attempt>.txt`) so neither clobbers the other. *Learned the hard way:* attempt 1
   ([`remote-round-2026-08-13/`](remote-round-2026-08-13/) — nine files, **not one console
   and not one ngrok agent log among them**) kept A's console only, so **B's side of the
   teardown is permanently unreconstructable**;
   attempt 2 kept neither and its root cause had to be inferred; attempt 4 closed the gate
   with A's console alone and the gap is recorded in `NEEDED-FROM-MACHINE-B.md`. Retaining
   both is the difference between diagnosing the next attempt in an hour and re-running it.
6. **The ngrok agent log from BOTH machines.** This is the single artifact that would have
   settled attempt 1 — whether machine A's zero-grace teardown or an independent tunnel drop
   killed B's push — and attempt 2, where A's public ingress died mid-game and nothing on
   disk can say why. Two ways to get it; use whichever matches the machine's tunnel path,
   and do not guess a path — ask the tool:
   - **Path A (pyngrok, tunnel-on):** pyngrok surfaces the ngrok agent process's output on
     the *agent's own console*, so the full console redirect of item 5 already captures it.
     Keep it in that file and say so in the evidence notes.
   - **Path C (standalone ngrok CLI):** the CLI's window shows a TUI, not a log. Either run
     it as `ngrok http <port> --domain=<domain> --log=stdout --log-format=json > ngrokB.log`
     (the redirect replaces the TUI with the agent log), **or** set a `log:` path in ngrok's
     own configuration file and retain that file — `ngrok config check` prints where that
     file lives on this machine.
7. **Each machine's recorded UTC clock** from §4 pre-flight item 2, and **any stray or
   aborted session logs.** Do not tidy those away: attempt 4 retained
   `eb55daeefafb4208.jsonl` — machine B launching first, waiting for A, and honestly
   recording its own `watchdog_incident` eight seconds before the real game — and that stray
   is part of why the round reads as honest rather than curated (rule 38).

**Before committing any of it — check for secrets (rules 39–40).** Consoles and ngrok agent
logs are exactly where the shared secret, an `NGROK_AUTHTOKEN` or an `ANTHROPIC_API_KEY`
leaks into a file you are about to make public. Grep the retained directory for each of the
three values before `git add`, and remember the console may be UTF-16 (§4 pre-flight item 3),
which a naive `grep` will silently fail to match.

## 6. What closes afterwards

- Fill in the Criterion 2 section of [`GATE-5-MEASUREMENT.md`](GATE-5-MEASUREMENT.md) with
  the retained paths, both verdicts, and the machine/network note.
- Tick both §10.4 boxes and rows 05-01…05-99 in [`TODO.md`](TODO.md).
- Tick the matching Phase-5 rows in the root [`docs/TODO.md`](../../TODO.md).
- Re-run `/gsd:verify-work 5`; the phase moves from `human_needed` to `passed`.

*All four were carried out for attempt 4 on 2026-08-16 and GATE-5 is met; the section stays
as the procedure for any future round, league day included.*

---

*Phase: 05-cloud-exposure-and-tunneling · closes GATE-5 criterion 2 (CLOUD-02)*
