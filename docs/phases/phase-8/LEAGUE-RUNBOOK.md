# League runbook — playing and reporting the scored games

**Owner:** 08-11 (written) · **Run by:** a human, at **08-13** · **Blocked on:** 08-12
(published repositories) **and 07-10** (the authorised mail credential).

> **What Claude cannot do.** No agent may **arrange an opponent team**, **enter credentials**,
> **click Google's OAuth consent screen**, **send mail**, or **decide the games-played value**.
> Every step marked **HUMAN** below is one of those. Steps marked **CHECK** are local commands.
> **No agent has played a real league game**, and none has flipped a `reporting.mode` to `live`.

Rule 35 is the reason this runbook is careful rather than brisk: **when either team fails to
report, or the two reports contradict each other, BOTH teams score zero.** A league day mistake
here costs an innocent opponent as much as it costs us.

---

## 0. Preconditions — CHECK, all of them, before contacting anyone

| Precondition | Command / where | Must read |
|---|---|---|
| Both repositories published, tagged | [`PUBLISH-RUNBOOK.md`](PUBLISH-RUNBOOK.md) done | `v1.00` visible on both |
| The mail path is authorised | [`../phase-7/OAUTH-RUNBOOK.md`](../phase-7/OAUTH-RUNBOOK.md), 07-10 | one live send already delivered |
| The suite is green on this commit | `uv run pytest --cov` | 0 failed, coverage ≥ 85% |
| The audit gate | `uv run python scripts/check_submission.py` | no **new** GAP |
| The tunnel works to a second machine | [`../phase-5/REMOTE-ROUND-RUNBOOK.md`](../phase-5/REMOTE-ROUND-RUNBOOK.md) | a full round completed |
| Both counters noted | `config/police/games_played.json`, `config/thief/games_played.json` — **gitignored, local to this machine, and absent from both published repositories** (D-77) | write the two numbers down **before** the day starts |

**Both machines must be on the same commit as each other's expectations only through the
handshake**, not by agreement: Step-0 compares SHA-256 digests of the shared config and aborts
with `CONFIG_MISMATCH` before move 1. Do not "fix" a mismatch by editing config to match theirs.

## 1. The bounds — fixed values, not preferences

| Bound | Value | Status | Source |
|---|---|---|---|
| Minimum scored games, against **different** teams | **2** | fixed | Table 18 row 3 |
| Maximum games per team | **10** | **fixed** | Table 18 row 5 |
| Scoring games per opponent | **exactly 1** | rule 52 | unscored warm-ups are permitted |
| Token budget per series | ~200,000 | **negotiable** | agreed with the lead team, then written into `league.json` |

`src/pursuit/services/reporting/league_ledger_bounds.py` refuses to record an eleventh game and
refuses a second **scored** game against an opponent already scored. It refuses rather than
warns, because both of those are rule violations and neither is recoverable after the fact.

## 2. Per opponent — HUMAN arranges, CHECK runs

1. **HUMAN.** Agree with the opponent: who is cop and who is thief, the two tunnel URLs, the
   shared secret (out of band — never in a repository, never in mail with the config), the
   negotiated resolution rules, and the token ceiling.
2. Write their two repository URLs into `league.repo_urls.opponent_cop` /
   `opponent_thief` and their MCP address into `league.mcp_server_addresses.opponent`, in
   **both** `config/police/league.json` and `config/thief/league.json`. The loader **refuses a
   null or placeholder when `reporting.mode = live`** — that refusal is the check, so do not
   work around it.
3. **Play one unscored connectivity warm-up.** Rule 52 permits it and every remote round in this
   project's history has needed it. Leave `reporting.mode = dry_run` for the warm-up.
4. Record the warm-up in the ledger as `scored=false`:
   `record_league_game(..., scored=False, ...)`. `scored` has no default — omitting it raises.

## 3. The one scoring game — HUMAN

1. Flip **only for this game**: `config/<role>/reporting.json` → `"mode": "live"`.
2. Start the two agents (two terminals, or two machines):
   ```bash
   uv run python -m pursuit.main --config-dir config/police
   uv run python -m pursuit.main --config-dir config/thief
   ```
   `scripts/dev_launch.py` is a convenience that spawns exactly these two commands; on league
   day the two agents are usually on two machines and it is not used.
3. Play to a real outcome — capture, survival, tie, or a technical result. Not a partial
   handshake.
4. **Flip `reporting.mode` back to `dry_run` immediately afterwards** and confirm with
   `git diff config/`.
5. Record it: `record_league_game(..., scored=True, opponent=<their team code>,
   commit_hash=<the hash the game ran on>, ...)`. The hash is the one the game **ran under** and
   is reused, never re-derived later.

## 4. Confirm the report actually arrived — HUMAN

Rule 35 turns "we sent it" into a claim that must be checked, not assumed.

- The message went to `rmisegal+uoh26finalgame@gmail.com`.
- The game summary is an **attachment** (`application/json`), not pasted into the body.
- The attached JSON carries the **commit hash** the game ran on
  (`declarations.own.declaration.commit_hash` in `declaration_<game_id>.json`; rule 53).
- Both teams' verdicts agree — or the disagreement is **reported as a disagreement**.

> **The league-day temptation, named so it can be refused.** If their report and ours disagree,
> the cheap move is to edit ours to match and keep the points. That is rules 16, 22 and 38
> territory — a false capture declaration, a false barrier declaration, a misreported count —
> and every one of them is an absolute disqualification. **Report the disagreement.**

## 5. Retain the four artifacts — CHECK

Per game, per seat, under `game_artifacts/<role>/`:

| Artifact | What it is |
|---|---|
| `log_<game_id>.json` | wire log × nonce ledger, joined on local turn truth |
| `result_<game_id>.json` | the per-series result, both token totals |
| `declaration_<game_id>.json` | rule 49's four links, MCP addresses, token ceiling, both signed Step-0 envelopes, the commit hash |
| the ledger | `config/police/league_ledger.json` / `config/thief/league_ledger.json` — written on league day; absent until the first game is recorded |

Commit each game's artifacts under their per-game names (SUB-12). `game_artifacts/` is untracked
scratch for development runs; league-day artifacts are evidence and are committed deliberately,
one directory per game.

## 6. After the last game — CHECK

```bash
uv run python scripts/measure_gate8.py
```

Criterion 3 must move from `MACHINERY PASS; GAMES PENDING` to a games count the ledger derives.
Then check the counters against the two numbers written down in step 0 and carry the difference
into [`SUBMISSION-RUNBOOK.md`](SUBMISSION-RUNBOOK.md) step 3 — the games-played value is decided
there, from `../phase-7/GAMES-PLAYED-RECONSTRUCTION.md`, and **not by an agent**.

---

## Done when

- **≥ 2 scored games against different teams**, ≤ 10 total, one scoring game per opponent.
- The ledger's derived count equals what went on the wire.
- Every scored game's report is confirmed **received**, with the commit hash inside it.
- Verdicts agree, or a disagreement is on the record as a disagreement.
- `reporting.mode` is back to `dry_run` in both roles and `git diff config/` shows it.
