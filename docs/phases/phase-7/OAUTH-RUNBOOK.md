# OAuth runbook — GATE-7 criterion 1's live half, and the two README assets

**Purpose:** close the one item in Phase 7 that no script in this repository can produce.
Everything else is measured solo by `scripts/measure_gate7.py`; this is not.

> **Success Criteria** (book milestone gate, §10.4), quoted from `.planning/ROADMAP.md`
> Phase 7:
>
> 1. A game summary is sent by mail (send-only OAuth, through the gatekeeper; attached JSON,
>    never free text)
> 2. The live GUI displays state — only local truth, never the full objective board
> 3. The replay app reconstructs a recorded round and shows `Verified OK`

Criteria **2 and 3 already PASS**, measured with zero credentials —
[`GATE-7-MEASUREMENT.md`](GATE-7-MEASUREMENT.md) and
[`gate7_measurement_evidence.json`](gate7_measurement_evidence.json). Criterion 1's dry-run
half also passes there. **This runbook is criterion 1's live half plus the two
presentation assets, and nothing else.**

---

## 0. What Claude does, and what only a human may do

**Claude must not enter credentials and must not click consent.** Not "should not" — the
consent screen is an authentication act performed by the account holder, and a coding agent
typing an account password or approving a scope on someone's behalf is out of bounds
regardless of what it is asked to do. The same line applies to Google's account chooser, any
2FA prompt, and the browser window `run_local_server()` opens.

| Step | Who |
|---|---|
| Create the Google Cloud project + OAuth client, restrict it to `gmail.send` | **human only** |
| Sign in, click through the consent screen, approve the scope | **human only** |
| Place the two files on disk and export the two environment variable paths | **human only** |
| Read a screenshot, judge whether it is presentation-grade | **human only** |
| Decide OQ-5's games-played value | **human only** (it is a rule-38 declaration) |
| Everything else below — running commands, checking output, re-running the gate | either |

**No credential, token, client id, client secret, path or account name goes into git, into a
commit message, into a chat transcript, or into any file in this repository.** Rules 39–40:
pushing a secret is a severe security failure and project failure. This document names
environment variable **NAMES** and never a value; so does `config/*/reporting.json`
(`credentials_env_var`, `token_env_var`) and so does `.env-example`.

---

## 1. What a PASS looks like — stated BEFORE the run

Write these down before starting, so the session cannot be graded by how it felt:

| # | Item | PASS looks like |
|---|---|---|
| 1 | OQ-5 decision | a written decision in [`GAMES-PLAYED-RECONSTRUCTION.md`](GAMES-PLAYED-RECONSTRUCTION.md) §8, all five boxes ticked, **before** step 4 |
| 2 | OAuth client scope | the consent screen shows **one** permission, "Send email on your behalf" — nothing about reading mail |
| 3 | Live send | the Gmail API returns a message **id**, and `SendReceipt.mode` is `live` |
| 4 | Arrival | the message is in the mandatory recipient's mailbox with `result_<game_id>.json` **attached**, and the body is the fixed boilerplate |
| 5 | Restore | `git diff config/` is EMPTY afterwards and both `reporting.json` files read `dry_run` again |
| 6 | Live GUI asset | a screenshot showing this seat's own cell, belief and scent — and **no** opponent true position |
| 7 | Replay asset | a screenshot whose banner reads `Verified OK` |
| 8 | Counters | `config/*/games_played.json` advanced by exactly **+1** each, for exactly one real game |

If any of items 3–5 fails, **record the failure and stop**; do not retry into a second live
send until the cause is understood. Rule 32 wants the report sent; rule 38 wants the record
honest, and an unexplained second attempt is how a record stops being one.

---

## 2. Step 0 — decide OQ-5 first, in writing

The Step-0 declaration this game sends carries the games-played number (rule 37), and a
false one is an **absolute disqualification** (rule 38, [`RULES.md:79`](../../RULES.md)).
The value on disk is known to be wrong — plan 07-00 fixed the *mechanism* and deliberately
did not repair the *value*.

1. Read [`GAMES-PLAYED-RECONSTRUCTION.md`](GAMES-PLAYED-RECONSTRUCTION.md) §6 (options A, B,
   C) and §5 (per-team vs per-agent).
2. Choose. Record the reading, the reasoning and the resulting number in §8, and tick its
   five boxes.
3. Set `config/police/games_played.json` and `config/thief/games_played.json` **by hand** to
   the chosen value.
4. If any doubt remains, **ask the lecturer before the first league game.** A question is far
   cheaper than rule 38's sanction.

Do not proceed to step 4 until this is written down. Nothing in this runbook decides it, and
nothing in this runbook may pre-empt any of the three options.

## 3. Step 1 — the OAuth client, restricted to `gmail.send`

1. In Google Cloud Console, create (or reuse) a project and **enable the Gmail API**.
2. Configure the OAuth consent screen as an **External** app in **Testing**, and add the
   sending account as a test user. Testing mode is enough for one supervised send and avoids
   a verification review.
3. Add exactly **one** scope: `https://www.googleapis.com/auth/gmail.send`.
   *A scope wider than send-only is "a security breach that disqualifies the code"* —
   rule 30, [`RULES.md:66`](../../RULES.md). The code refuses a wider scope twice
   (`gmail_sink.require_send_only_scope`, at the **requested** scopes and again at the
   scopes the loaded token was **granted**), so a leftover broader `token.json` fails loudly
   rather than sailing through.
4. Create an **OAuth client ID** of type *Desktop app* and download its JSON.
5. Put that file **outside the repository** — anywhere git cannot see it. `.gitignore`
   already carries `credentials.json`, `client_secret*.json`, `token.json`, `token.pickle`
   and `*.token`, but a path outside the working tree is the belt to that suspenders.
6. Export the two environment variables whose NAMES `config/*/reporting.json` gives. Do not
   write the values into any file in the repository:

   ```sh
   export PURSUIT_GMAIL_CREDENTIALS_PATH=<path to the downloaded client JSON>
   export PURSUIT_GMAIL_TOKEN_PATH=<path where the token cache may be written>
   ```

   The token file does not exist yet; the consent flow writes it. Point it outside the repo
   too. `.env-example` carries both names with dummy values and is the committed reference.

7. Complete consent, **as a human**, at a moment of your choosing. The flow that opens the
   browser is `InstalledAppFlow.run_local_server()`, reached through
   `gmail_sink.build_gmail_transport`. The consent screen must list **one** permission. If it
   lists more, stop: the client is misconfigured, and the code will refuse the token anyway.

Once the token file exists, the automated path never opens a browser again — it loads the
cached token, refreshes it if expired, and re-checks the granted scope before every send.

## 4. Step 2 — one live send, then flip back

**One config, one game, then restore.** Every `reporting.json` this repository ships reads
`dry_run`, which writes the report to disk and transmits nothing. This is the only step that
changes that, and it changes it back.

1. Confirm the starting state:

   ```sh
   git diff config/            # must be EMPTY
   grep -h '"mode"' config/police/reporting.json config/thief/reporting.json
   ```

2. Flip **one** file — the seat that will send — to `"mode": "live"`. Leave the other at
   `dry_run`. (Rule 35 asks each team to send its own report; one live seat is what a
   supervised single send means here, and the second seat's `dry_run` `.eml` on disk is a
   useful side-by-side control.)
3. Record the shipped `game_artifacts/` state before the run, so debris and evidence can be
   told apart afterwards:

   ```sh
   git status --short game_artifacts/
   ```

4. Run **one** game and keep the full console — stdout **and** stderr — of both seats:

   ```sh
   uv run python scripts/dev_launch.py > consoleA_oauth.txt 2>&1
   ```

   *Learned the hard way in Phase 5:* attempt 1 of the remote round kept one console and the
   other side of the teardown is permanently unreconstructable
   ([`REMOTE-ROUND-RUNBOOK.md`](../phase-5/REMOTE-ROUND-RUNBOOK.md) §5). Keep both.

5. Confirm the send. The live seat's `SendReceipt` carries `mode = live` and a
   `message_id`; the `result_<game_id>.json` and `result_<game_id>.eml` under
   `game_artifacts/<role>/` are the same report and the same rendered message. Then open the
   mandatory recipient's mailbox and confirm **arrival with the JSON ATTACHED**. A report
   sent as free text is rejected in processing and scores zero (rule 34,
   [`RULES.md:75`](../../RULES.md)) — so the check is not "an email arrived", it is "an
   email arrived carrying a `result_<game_id>.json` attachment, with a boilerplate body".
6. **Flip the config BACK to `dry_run`** and prove it:

   ```sh
   git diff config/            # must be EMPTY again
   ```

7. Confirm the counters advanced by exactly one each, for exactly one game:

   ```sh
   cat config/police/games_played.json config/thief/games_played.json
   ```

## 5. Step 3 — the two README assets

Both are required by the academic README (§9.4.2 item 5, rule 42) and both are screenshots a
human takes and judges. Neither app has a default interval, deliberately: **OQ-6 — no
document in this project states a UI interval, so the operator states it and the repository
does not.** Whatever value you use, **record it beside the screenshot**.

1. **The live GUI.** Against a snapshot from a real game (`<log-stem>.view.json` beside the
   wire log), in its own process:

   ```sh
   uv run python -m pursuit.gui.live_app --snapshot <path>.view.json --refresh-ms <N>
   ```

   What the screenshot must show: this seat's own cell, its belief and scent surfaces, and
   the sidebar. What it must **not** show: the opponent's true position, in any form. That is
   rule 9 and it is a project disqualification, not a blemish. The structural half is already
   proven (`scripts/check_local_truth.py`, 7 modules, 0 violations); the *visual* half is
   this judgement, and it is why a human takes the picture.
2. **The replay viewer**, on a real finished game's artifact:

   ```sh
   uv run python -m pursuit.gui.replay_app --artifact game_artifacts/<role>/log_<game_id>_g01.json --step-ms <N>
   ```

   What the screenshot must show: the banner reading **`Verified OK`**, in green, with the
   ratio detail beside it. The three banner colours are pinned by test, so a green banner is
   an OK verdict and not a coincidence. A file the viewer refuses (a `.jsonl` wire log, a
   `.ledger.jsonl`, a `result_` or `declaration_`) exits 2 with a message naming rule 18 and
   never opens a window — so there is no way to photograph an empty banner by accident.
3. Record the two intervals used, in one line each, beside the images.

## 6. Evidence to retain

`logs/` is gitignored, so anything under it must be copied out to be kept.

1. The `result_<game_id>.json` and `result_<game_id>.eml` the live seat produced, and the
   `log_<game_id>_g01.json` beside them.
2. The Gmail **message id** returned for the send (an id, not a credential).
3. Both consoles from step 4, stdout and stderr, named per seat.
4. The two screenshots, each with its interval recorded.
5. The `git diff config/` output from step 4 items 1 and 6 — the proof that the flip happened
   and was reversed.
6. The OQ-5 decision as written into `GAMES-PLAYED-RECONSTRUCTION.md` §8.
7. Anything that did **not** fit the happy path. Do not tidy it away: Phase 5's attempt 4 kept
   a stray aborted session log recording its own `watchdog_incident`, and that stray is part
   of why the round reads as honest rather than curated (rule 38).

**Before committing any of it — scan for secrets (rules 39–40).** Consoles are exactly where
a path, an id or a token leaks into a file about to be made public. Grep the retained
directory for the values of both `PURSUIT_GMAIL_*` variables and for `ANTHROPIC_API_KEY`
before `git add`, and remember a Windows console redirect may be UTF-16, which a naive
`grep` silently fails to match.

**Stage explicit paths — never `git add -A`.** `game_artifacts/` is deliberately not ignored,
because rule 50 requires the four JSON artifacts to be committable; the cost is that every
`dev_launch` leaves untracked files there. A blanket sweep would publish a throwaway local
game under filenames a grader reads as league evidence (deferred item **D7-19**). Compare
against the `git status --short game_artifacts/` you recorded in step 4 item 3, and stage the
real evidence by name. `*.eml` and `*.prev.json` under `game_artifacts/` are ignored as of
07-09 — they are never one of rule 50's four artifacts — but the four JSON names are NOT
ignored and never will be, so the discipline is still yours.

## 7. What closes afterwards

- Fill in criterion 1's **live** row in [`GATE-7-MEASUREMENT.md`](GATE-7-MEASUREMENT.md) with
  the message id, the arrival confirmation and the retained paths. It reads **PENDING** until
  then, and must not be flipped on the strength of a dry run.
- Re-run `uv run python scripts/measure_gate7.py` afterwards, with `dry_run` restored, and
  confirm it still exits 0 — the live send must leave the offline gate exactly as it found it.
- Tick the §10.4 boxes and the 07-* rows in [`TODO.md`](TODO.md), and the matching Phase-7
  rows in the root [`docs/TODO.md`](../../TODO.md).
- Re-run `/gsd:verify-work 7`.
