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

Measured on machine A at commit `0427137` (identical across both role directories —
recompute if `game_params.json` or `scent.json` ever change):

| Digest | Value |
|---|---|
| `game_params` | `23f86a93589131ae3558a4a697fc2105aa878809fa5ed62a11a28a528f25c975` |
| `scent` | `c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e` |

A mismatch is information, not something to edit away. Editing config to force agreement
defeats the check.

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

## 6. What closes afterwards

- Fill in the Criterion 2 section of [`GATE-5-MEASUREMENT.md`](GATE-5-MEASUREMENT.md) with
  the retained paths, both verdicts, and the machine/network note.
- Tick both §10.4 boxes and rows 05-01…05-99 in [`TODO.md`](TODO.md).
- Tick the matching Phase-5 rows in the root [`docs/TODO.md`](../../TODO.md).
- Re-run `/gsd:verify-work 5`; the phase moves from `human_needed` to `passed`.

---

*Phase: 05-cloud-exposure-and-tunneling · closes GATE-5 criterion 2 (CLOUD-02)*
