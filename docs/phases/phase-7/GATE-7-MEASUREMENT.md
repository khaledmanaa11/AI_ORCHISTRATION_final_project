# GATE-7 measurement — Phase 7, book §10.4 milestone 7

**Status:** Criterion 2 **PASS** · Criterion 3 **PASS** · Criterion 1 **dry-run PASS, live
half PENDING**. Measured 2026-08-17T10:00:23Z on localhost with **zero credentials and zero
environment variables**; evidence in
[`gate7_measurement_evidence.json`](gate7_measurement_evidence.json).

**Date:** 2026-08-17 · **Plan:** 07-09 · **Method:** `scripts/measure_gate7.py`, one command,
driving the real shipped `config/police` + `config/thief` — the production
`build_reporting_chain`, the production `check_local_truth` gate, the production
`open_replay`, and both shipped GUI entry points as subprocesses. Never a synthetic override
and never a parallel reimplementation.

> **Criterion 1 is NOT closed by this document, and must not be read as if it were.**
> §10.4 criterion 1 requires a game summary **sent by mail**. Everything up to the send is
> measured below with zero credentials. The one live send needs a human at Google's OAuth
> consent screen and belongs to plan 07-10
> ([`OAUTH-RUNBOOK.md`](OAUTH-RUNBOOK.md)). A gate document that read PASS without the
> delivered-message evidence is the failure mode rule 38 exists for.
> [`GATE-5-MEASUREMENT.md`](../phase-5/GATE-5-MEASUREMENT.md)'s retained PENDING record —
> which stayed PENDING across three failed attempts before a human closed it on the fourth —
> is this project's own precedent for how to write this honestly.

Per rule 38 and this plan's own must_haves: every claim below points at a named field in the
evidence JSON a human can re-open. Had a check come back FAIL, this document would say FAIL
and the underlying plan would need fixing, not this report's wording.

---

## The three criteria — quoted verbatim from `.planning/ROADMAP.md` Phase 7 (not ours to edit)

> **Success Criteria** (book milestone gate, §10.4):
>
> 1. A game summary is sent by mail (send-only OAuth, through the gatekeeper; attached JSON,
>    never free text)
> 2. The live GUI displays state — only local truth, never the full objective board
> 3. The replay app reconstructs a recorded round and shows `Verified OK`

---

## Criterion 1 — a game summary is sent by mail · **DRY-RUN PASS + LIVE PENDING**

**Method.** `gate7_mail.py` + `gate7_mail_live.py`. One report through the whole production
chain — `QuotaManager → Gatekeeper.submit (token bucket, semaphore, retry ladder) →
DosDetector → sink` — composed by the shipped
`services/reporting/end_of_game_chain.build_reporting_chain` from the shipped
`config/police/reporting.json`. The dry-run half uses the sink that config selects
(`DryRunSink`, which writes to disk and transmits nothing); the live-path proofs drive the
shipped `GmailSink` with an injected `FakeGmailTransport` that raises a **real**
`googleapiclient.errors.HttpError`. Only the transport and the gatekeeper's own `sleep` seam
are replaced.

**Run it:**

```
uv run python scripts/measure_gate7.py
```

**What a PASS looks like — the dry-run half** (fields under
`criterion_1_game_summary_sent_by_mail`):

| Field | Must be | Measured |
|---|---|---|
| `shipped_modes.{police,thief}` | `dry_run`, both | `dry_run`, `dry_run` |
| `recipient_is_the_mandatory_address` | `true` (PARAMETERS.md:176) | `true` — `rmisegal+uoh26finalgame@gmail.com` |
| `dry_run_end_to_end.sent` / `.refusal` / `.pending_after_send` | `true` / `null` / `0` | `true` / `null` / `0` |
| `dry_run_end_to_end.files_written` | the report, its `.eml`, and the quota counter | `["reporting_quota.json", "result_gate7mail.eml", "result_gate7mail.json"]` |
| `dry_run_end_to_end.watchdog_touches` | `> 0` (touch per bounded attempt) | `2` — entry and `finally`, one attempt |
| `dry_run_end_to_end.attachment.is_attachment` | `true` (rule 34) | `true` |
| `.attachment.content_type` | `application/json` (rule 33) | `application/json` |
| `.attachment.filename` | `result_<game_id>.json` (PARAMETERS.md:168) | `result_gate7mail.json` |
| `.attachment.reparses_to_the_report` | `true` — the bytes decode back to the exact report | `true` |
| `.body.is_the_fixed_boilerplate` | `true` | `true` |
| `.body.carries_no_report_content` | `true` — a distinctive `game_uid` is absent from the body | `true` |
| `.body.line_ending_is_crlf` | `true` | `true` |
| `.from_header_absent` | `true` — the Gmail API fills it from `userId="me"` | `true` |
| `backoff_ladder.attempts` / `.sleeps_seconds` | `3` / two waits equal to config | `3` / `[30, 30]`, config `wait_after_error_seconds = 30` |
| `backoff_ladder.sent` | `true` — 429, 429, 200 recovers | `true` |
| `scope_gate.extra_scope_rejected` / `.empty_scope_rejected` | `true` (rule 30) | `true`, `true` |
| `scope_gate.scope_checked_before_any_credential_is_read` | `true` | `true` |
| `scope_gate.guard_call_sites` | both call sites, by AST | `["the granted OAuth token", "the requested OAuth scopes"]` |
| `queue_and_drain.queued` / `.pending_after_send` | `true` / `1` | `true` / `1` |
| `queue_and_drain.attempts_before_recovery` | `retries_before_failure + 1` | `4`, config `retries_before_failure = 3` |
| `queue_and_drain.drained_outcomes_sent` / `.pending_after_drain` | `[true]` / `0` | `[true]` / `0` |

`dry_run_verdict = "PASS"`.

### The live half — **PENDING**, and exactly what would close it

`live_send_verdict = "PENDING"`. The criterion-level `verdict` field is the string
`"DRY_RUN PASS; LIVE PENDING (07-10)"`, deliberately: a grep for `"verdict": "PASS"` over the
evidence JSON returns criteria 2 and 3 and **cannot** return criterion 1.

**What is proven, offline, with zero credentials.** The MIME shape a live send would put on
the wire (re-parsed from the rendered bytes, not asserted against the builder's intentions);
the attachment and its type and filename; the boilerplate body; the mandatory recipient read
from config; the rule-30 scope gate at both call sites and its ordering ahead of any
credential read; the 429 → backoff → 429 → backoff → 200 ladder with the wait taken from
config by the gatekeeper and never by the sink; and the queue-and-drain behaviour of a report
that a permanently-failing server refused.

**What is NOT proven, and no amount of offline work can prove it.** That a message was
delivered. Nothing in this repository has transmitted anything: `measure_gate7.py` clears
`PURSUIT_GMAIL_CREDENTIALS_PATH` and `PURSUIT_GMAIL_TOKEN_PATH` (and `ANTHROPIC_API_KEY`) at
import time, so it **cannot** have sent, and both shipped `reporting.json` files still read
`dry_run` with `git diff config/` empty.

**07-10 must attach, to flip this row** (`live_send.evidence_07_10_must_attach`):

1. the Gmail message id returned by the API for the one supervised send;
2. a screenshot of the delivered message at the mandatory recipient showing the
   `result_<game_id>.json` **attachment** (rules 33–34);
3. the `git diff config/` output proving `reporting.mode` was flipped to `live` and flipped
   **back**;
4. the OQ-5 games-played decision recorded in writing **before** the send
   ([`GAMES-PLAYED-RECONSTRUCTION.md`](GAMES-PLAYED-RECONSTRUCTION.md) §8).

**Do not flip this row on the strength of a dry run.**

---

## Criterion 2 — the live GUI displays state, only local truth · **PASS**

**Method.** `gate7_localtruth.py`, three independent measurements, none sufficient alone:

1. the rules 8-9 CI gate (`scripts/check_local_truth.py`, loaded by file path — the same
   loader the pytest suite uses, so the suite, the CI job and this measurement run ONE copy
   of the logic) over the real shipped `src/pursuit/gui/`;
2. the **published snapshot** of a real game, on both seats, scanned for the three field
   names that would carry the objective board. The GUI process is fed by that file and by
   nothing else (D-76), so the file is the attack surface;
3. both shipped entry points launched as **subprocesses** with `--once`, exit codes recorded.

**What a PASS looks like** (fields under `criterion_2_live_gui_local_truth_only`):

| Field | Must be | Measured |
|---|---|---|
| `structural_gate.modules_scanned` | `> 0` — **a zero/zero result is a FAIL, not a PASS** | `7` |
| `structural_gate.module_names` | the real package | `__init__.py`, `live_app.py`, `live_panels.py`, `live_sidebar.py`, `replay_app.py`, `replay_panels.py`, `widgets.py` |
| `structural_gate.violation_count` / `.exit_code` | `0` / `0` | `0` / `0` |
| `structural_gate.allowed_service_modules` | non-empty, and exactly the one read path | `["pursuit.services.reporting.replay_verify"]` |
| `empty_scan_control.missing_root_exit_code` | `2` | `2` |
| `empty_scan_control.package_marker_only_exit_code` | `2` | `2` |
| `published_snapshot.{police,thief}.published` | `true` | `true`, `true` |
| `published_snapshot.{police,thief}.true_position_fields_present` | `[]` — none of `cop`/`thief`/`barriers` appears as a key anywhere in the tree | `[]`, `[]` |
| `published_snapshot.police.top_level_keys` | the closed `LocalView` field set | `barriers_placed, belief, board_size, declared_barriers, hints, idle_seconds, machine_state, own_cell, role, scent, turn, watchdog_threshold_seconds` |
| `published_snapshot.{police,thief}.own_cell` | this seat's own cell only | `[2, 2]` (police), `[2, 4]` (thief) |
| `live_app_launch.{police,thief}.returncode` | `0` | `0`, `0` (at `--refresh-ms 500`) |

**Verdict:** `criterion_2_live_gui_local_truth_only.verdict = "PASS"`.

### What is machine-verified here, and what is a human judgement — stated apart

**Machine-verified:** that no `gui/` module can reach the objective board (imports, attribute
chains, dynamic accessor keys); that the published snapshot carries no key naming the
opponent's true position; that both apps render and exit 0 against a real game's data.

**A human aesthetic call, and 07-10's:** whether the screenshot is *presentation-grade* —
legible, framed, showing what a grader needs to see. No script can answer that, and none
here pretends to.

**Deliberately NOT claimed by this gate, and it matters.** The structural gate is an
import/attribute gate: it sees a coordinate that is **named**, never one that is **drawn**.
Whether a human could *invert* the true cell out of what a panel paints is a different
question, asked by `tests/unit/test_gui_recovery.py` and
`tests/unit/test_local_truth_recovery.py` — 07-11's runtime recovery work, which found and
closed a real leak (`belief.argmax` on the JSONL) and 07-06's quantisation channel. Those two
files and this gate do not replace each other; the evidence records that in
`not_measured_here`.

---

## Criterion 3 — the replay app shows `Verified OK` · **PASS**

**Method.** `gate7_replay.py`, on ONE real two-peer game played on the shipped configs
(`game_uid: gate7measure`, outcome `capture` on both seats, `outcomes_agree: true`) — the
SAME game criterion 2 measured, joined by `game_uid`. The game is played, the final audit
runs, `write_log_artifact` builds `log_gate7measure_g01.json`, and then **both sources are
deleted from disk** before any verdict is taken.

Every verdict goes through `open_replay(path).verdict` — the exact value
`gui/replay_app.main` renders. There is deliberately no `verdict_for(artifact)` wrapper in
`src/` (07-08 wrote one, found it reachable from tests only, and removed it), because a
measurement taken through a parallel helper would be evidence about the helper.

**What a PASS looks like** (fields under `criterion_3_replay_shows_verified_ok`):

| Field | Must be | Measured |
|---|---|---|
| `sources_existed_before_deletion` | `true` — the deletion is not vacuous | `true` |
| `sources_deleted_before_verifying.{wire_log,ledger}` | `true`, `true` | `true`, `true` |
| `verified_ok.banner` / `.state` | `Verified OK` / `ok` | `Verified OK` / `ok` |
| `verified_ok.committed` | `> 0` — **a zero-turn `Verified OK` proves nothing** | `5` |
| `verified_ok.verified` / `.detail` | `== committed` | `5`, `"5/5 committed turns re-hash"` |
| `verified_ok.turn_count` | `> committed` — the trailing game-over turn is present and uncounted | `6` |
| `failed.state` / `.banner` | `failed` / names the tampered turn | `failed` / `FAILED -- turn 4: re-hash does not match h_commit` |
| `failed.banner_names_the_tampered_turn` | `true` | `true` (`tampered_turn: 4`, field `move`) |
| `failed.banner_does_not_name_turn_zero` | `true` — it named the RIGHT turn, not the first | `true` (`first_committed_turn: 0`) |
| `failed.verified` / `.committed` | `committed - 1` | `4` / `5` |
| `nothing_to_verify.banner` / `.state` / `.committed` | `Nothing to verify` / `nothing_to_verify` / `0` | exactly that |
| `app_launch.returncode` | `0` | `0` (at `--step-ms 400`) |
| `live_log_refused_by_name.returncode` | `2` | `2` |
| `live_log_refused_by_name.message_names_rule_18` | `true` | `true` |

**Verdict:** `criterion_3_replay_shows_verified_ok.verdict = "PASS"`.

**Three verdicts, not one, and the third is the point.** A run that can only ever show
`Verified OK` proves nothing about the screen. The tamper is a single legal-for-legal `move`
swap on ONE committed turn, **resealed** afterwards, so the FAILED verdict is earned by the
per-turn re-hash and not by the artifact seal. The zero-turn case is the vacuity that
`security/audit_record.all_matched([])` is honest about ("vacuously True for an empty list")
and that would be a lie on a screen — `verdict_from`'s non-zero guard runs before any
aggregate, and dropping it makes an empty artifact read `Verified OK` (measured; see the
mutation probes below).

---

## Zero environment variables, and nothing transmitted

`env_vars_required: []`. `gate7_common.py` clears `ANTHROPIC_API_KEY`,
`PURSUIT_GMAIL_CREDENTIALS_PATH` and `PURSUIT_GMAIL_TOKEN_PATH` unconditionally at import
time, so a grader's own shell can never turn a measurement into a live API call or a live
send. The whole flow plays through the language layer's existing no-key fallback (04-12), and
the console says so twice per run.

## The rule-37/38 counters are read before and after, and reported

`games_played_counter` in the evidence JSON:

| File | Before | After |
|---|---|---|
| `police/games_played.json` | `1921` | `1921` |
| `thief/games_played.json` | `1914` | `1914` |

`unchanged_by_this_measurement: true`. This matters because this script plays a **real** game:
GATE-6's own measurement script used to advance these counters, and
[`GATE-6-MEASUREMENT.md`](../phase-6/GATE-6-MEASUREMENT.md) certified that as correct
behaviour until 07-00 proved it was a defect. GATE-7 measures the counters rather than
assuming them.

**The counters' numeric VALUE is not repaired here and must not be read from this document.**
It is reconstructed and set by a human before any live send —
[`GAMES-PLAYED-RECONSTRUCTION.md`](GAMES-PLAYED-RECONSTRUCTION.md), OQ-5, 07-10.

## Does this gate measure anything? — five mutation probes, each reverted

A gate script that prints PASS while measuring nothing is this plan's central vacuity risk.
Each probe below broke the criterion's real subject in `src/`, ran the whole gate, and was
reverted with `git checkout --` (`git diff` clean after every one).

| # | Mutation | Result |
|---|---|---|
| 1a | `message.ATTACHMENT_SUBTYPE` `json` → `octet-stream` | criterion 1 **DRY_RUN FAIL**, gate exit 1; `attachment.content_type` recorded `application/octet-stream` |
| 1b | `require_send_only_scope` weakened from *"is exactly `gmail.send`"* to *"contains `gmail.send`"* — rule 30's actual hazard | criterion 1 **DRY_RUN FAIL**, exit 1; `extra_scope_rejected: false` and `scope_checked_before_any_credential_is_read: false` |
| 2 | `from pursuit.shared.state import GameState` planted in `gui/widgets.py` | criterion 2 **FAIL**, exit 1; `violation_count: 2`, both messages naming rules 8-9 |
| 3 | the non-zero-committed guard removed from `verdict_from` | criterion 3 **FAIL**, exit 1; **the EMPTY artifact read `"banner": "Verified OK"` at 0/0** — the exact bug the guard exists for |
| 4 | the per-turn re-hash removed from `check_turn` (a present hash accepted without verifying it) | criterion 3 **FAIL**, exit 1; **the TAMPERED artifact read `Verified OK` at 5/5** |

And two probes of the report builder itself, on real evidence:

| # | Mutation | Result |
|---|---|---|
| 5 | `modules_scanned` zeroed / `verified_ok.committed` zeroed / attachment count, ladder attempts and guard call sites zeroed | **FAIL** in every case; the zeroed local-truth scan exits **2** (`EMPTY_EVIDENCE`), matching 07-03's own empty-scan convention |
| 6 | the counter snapshot reduced to ONE file | exit **2** — see the finding below |

**Probe 6 is a defect this gate found in itself.** `counter_snapshot` originally keyed on
`path.name`, so both roles collapsed onto the single key `games_played.json` and the evidence
silently reported ONE counter — thief's, because it was written last — while claiming to
watch both. Found by reading the first evidence file rather than by a test. Fixed to key on
`<role>/<filename>`, and `exit_code` now refuses a snapshot holding fewer than two entries,
so the same shortfall can never again read as `unchanged: true`.

## Idempotence — what is identical across runs, and what is not

Two consecutive runs produce a **byte-identical GATE-7 summary block** and an evidence JSON
**identical apart from `generated_at`**. Every game plays inside its own throwaway temp
directory under a fixed `game_uid` (never the real `logs/` tree), and only
`gate7_measurement_evidence.json` is written, overwritten in place.

Two honest caveats, recorded rather than smoothed:

- The replay app's refusal message echoes the path it was handed, which is a fresh temp
  directory each run. The evidence field is therefore
  `stdout_tail_tmp_dir_redacted` — the temp directory is replaced with `<tmp>` and the field
  name says so. Nothing about the refusal is edited, and the redaction also keeps a local
  username out of a file destined for a public submission repo (rule 49).
- The **console** is not byte-identical: the local-truth gate's own two `ERROR:` lines from
  the empty-scan control name the throwaway directory they scanned. Those are the gate under
  test being loud, which is the behaviour being measured; only the summary block is compared.

## Open findings routed by this plan, not left silent

| Finding | Decision |
|---|---|
| **D7-17** — `game_id` is minted per GAME while PARAMETERS.md:159 reads it as the SERIES id | **Not decidable from the book. Routed to 07-10 / Phase 8 with the options laid out** — see below. |
| **D7-18** — the shipped-config write guard covered one writer, not the rule | **CLOSED by 07-09.** All six `durable_write_json` bindings are now guarded (five importers plus the defining module), enumerated by AST so a seventh fails the test. |
| **D7-19** — untracked `game_artifacts/` debris one `git add -A` from becoming league evidence | **Partially closed, and documented where it will be seen.** `*.eml` and `*.prev.json` under `game_artifacts/` are now ignored (neither is ever one of rule 50's four artifacts); the four JSON names stay un-ignored and a test proves it. The remaining discipline is written into `game_artifacts/README.md` and [`OAUTH-RUNBOOK.md`](OAUTH-RUNBOOK.md) §6. |
| `check_no_llm_in_strategy.sh` absent from CI since 03-10 | **CLOSED by 07-09** — wired into `.github/workflows/quality-gate.yml` as its own job. |

### D7-17 in full — why it is not ours to decide

`docs/PARAMETERS.md:157-159` reads the two filename parts as *series* and *match within it*:
all four artifacts "carry a shared `game_uid`, and each filename embeds the game identifier
`game_id` plus the match number `<NN>`", and `result_<game_id>.json` (line 168) is the "final
results summary **across all sub-games**". `docs/PARAMETERS.md:72` then settles ties on the
"aggregate score across all sub-games against one opponent", so the aggregation is
score-bearing.

But `agent_entrypoint.run_agent` mints `secrets.token_hex(8)` per game and then adopts the
peer's negotiated value (D-61), so today's `game_id` identifies ONE game: a production series
file holds exactly one sub-game and `<NN>` is `01` on both seats. The accumulator itself is
correct and proven over two sub-games sharing a `game_id`
(`test_the_series_total_is_the_sum_of_two_sub_games`, and proven wrong when the accumulation
is removed). What is missing is a series-scoped identifier to key on.

**The book does not settle it, and this is the reasoning, not a shrug.** Two book facts pull
against each other. `docs/PARAMETERS.md:86` — *"Against each opponent there is **one scoring
game only** — no rematches for points"* (rule 52) — means a scored series against one
opponent contains exactly one scoring game, which is what production produces today and is
**correct, understating nothing**. Table 17 row 5's tie rule and PARAMETERS' "across all
sub-games" wording only bind if warm-up games (rule 52 permits and encourages them) are meant
to share the scored game's `game_id`. Nothing in either document says whether they should.

And `game_id` is **negotiated with the peer at handshake** (D-61): redefining it as a
series-scoped value is a change to what two independently-written agents agree on, which is a
protocol decision, not an artifact-writer decision. 07-07 refused to invent an id scheme for
exactly this reason and this plan does not overturn that refusal — inventing one here would
be a numeric/protocol invention of precisely the kind [CLAUDE.md](../../CLAUDE.md) rule 1
forbids.

**Routed to 07-10 / Phase 8's league runner, with three options and their costs:**

- **(a) Leave it.** One scored game per opponent (rule 52) means one sub-game per series, and
  the artifact is already correct for that. Cost: if a lead team asks for an aggregated
  multi-sub-game result, we have no id to aggregate on.
- **(b) Reuse one `game_id` across every game against the same opponent**, agreed with that
  opponent at the first handshake. Cost: it must be agreed with a team we do not control, and
  a peer that mints a fresh id per game (as we do today) would break it silently.
- **(c) Add a separate series id** to the artifact beside `game_id`, purely local, and key the
  accumulator on it. Cost: a field `docs/PARAMETERS.md` does not name, in a grader-facing
  artifact whose four names and fields the document fixes.
- **The cheapest correct move before choosing: ask the lecturer.** Rule 38 territory is one
  misreported aggregate away, and the question costs a message.

## Re-run command

```
uv run python scripts/measure_gate7.py
```

Exit 0 when criteria 2 and 3 PASS and criterion 1's dry-run half passes; 1 on any FAIL; **2
on an evidence set that judged nothing.** The live half is PENDING by design and does not
make the exit code non-zero — this document carries that, not the exit code.

---

*Phase: 07-reporting-and-visualization-shell*
*Plan: 07-09 · Criterion 1's live half: 07-10*
