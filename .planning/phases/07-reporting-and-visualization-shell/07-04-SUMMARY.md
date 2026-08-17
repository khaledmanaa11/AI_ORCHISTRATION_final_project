---
phase: 07-reporting-and-visualization-shell
plan: "04"
subsystem: services/reporting-mail-transport
tags: [D-70, D7-3, D7-10, D7-11, D7-12, REPORT-01, REPORT-04, REPORT-05, OQ-3, OQ-4, rule-28, rule-30, rule-33, rule-34, rule-38, rule-39, rule-40]
one_liner: "The mandatory report leaves as an attached application/json part with a fixed boilerplate body -- asserted by re-parsing the rendered bytes, not the builder -- through GmailSink, the one module in src/ that imports google-*, which RAISES on 429 rather than sleeping so the wait stays in the single gatekeeper's ladder at the mail instance's 30 s; send-only scope is enforced twice, on what is requested and on what the token actually granted."
requires:
  - "07-01: ReportingChain, QuotaManager, DosDetector, load_reporting_config, the shipped reporting.json"
  - "07-02: result_filename and write_artifact (the D7-1 logs/ refusal the .eml now inherits)"
provides:
  - "services/reporting/message.py: build_report_message / render_message / report_filename -- the ONE MIME shape (rules 33-34)"
  - "services/reporting/sink.py: MailSink protocol, SendReceipt, DryRunSink (.json + .eml, transmits nothing)"
  - "services/reporting/gmail_sink.py: GmailSink, GmailRetryableError, GmailScopeError, GmailCredentialsError, require_send_only_scope, load_send_only_credentials, build_gmail_transport"
  - "services/reporting/artifacts.py: write_artifact_bytes behind the same D7-1 gate as write_artifact"
  - "shared/durable_write.py: durable_write_bytes -- THE crash-safe write scheme, extracted at its second payload shape"
  - "tests/unit/gmail_fixtures.py: FakeGmailTransport / FakeCredentials / FakeInstalledAppFlow / build_mail_chain"
affects:
  - "07-07 (end-of-game) constructs a sink and calls ReportingChain.send -- it owns WHEN, this plan owns HOW"
  - "07-09 measures criterion 1's dry_run half against DryRunSink; 07-10 runs build_gmail_transport for the one live send"
tech-stack:
  added:
    - "google-api-python-client>=2.198.0"
    - "google-auth>=2.56.3"
    - "google-auth-oauthlib>=1.4.0"
  patterns:
    - "Vendor isolation with a DELIBERATE non-re-export: unlike services/llm, the package __init__ does not pull GmailSink, because nothing here needs a register_provider side effect and every shipped config is dry_run"
    - "A rule enforced at both ends of the same pipe -- requested scopes and granted scopes -- because only one of them is what actually authorises the call"
    - "Anti-vacuity by AST identifier scan rather than text search, so a docstring that legitimately names the forbidden thing cannot move the result"
key-files:
  created:
    - src/pursuit/services/reporting/message.py
    - src/pursuit/services/reporting/sink.py
    - src/pursuit/services/reporting/gmail_sink.py
    - tests/unit/test_mail_message.py
    - tests/unit/test_mail_sink_dry_run.py
    - tests/unit/test_gmail_sink.py
    - tests/unit/test_gmail_scope.py
    - tests/unit/test_gmail_credentials.py
    - tests/unit/gmail_fixtures.py
  modified:
    - src/pursuit/services/reporting/artifacts.py
    - src/pursuit/services/reporting/__init__.py
    - src/pursuit/shared/durable_write.py
    - .env-example
    - pyproject.toml
    - uv.lock
    - docs/phases/phase-7/TODO.md
    - .planning/phases/07-reporting-and-visualization-shell/deferred-items.md
key-decisions:
  - "GmailSink RAISES GmailRetryableError on 429 and never sleeps -- a second backoff would be a second gatekeeper and would make the backoff test pass for the wrong reason"
  - "The backoff assertion uses a TRANSCRIBED literal 30, not params.wait_after_error_seconds, so lowering the config cannot keep the test green"
  - "No From header and no address literal in src/ -- the Gmail API fills From from the authenticated account, and a fixed destination a module can default to is one a typo can change"
  - "GmailSink is NOT re-exported from the package __init__, the one departure from services/llm's convention, reasoned in the docstring"
  - "durable_write_bytes extracted rather than a second write-and-rotate sequence written; byte-neutrality measured, not assumed"
metrics:
  tasks: 3
  commits: 3
  tests_added: 73
  suite: "1846 -> 1919 passed, 0 failed"
  coverage: "96.95% -> 97.02%"
  completed: 2026-08-17
status: complete
---

# Phase 7 Plan 04: Mail Transport Summary

Rule 34 makes a free-text report a **zero score** and rule 30 makes a broad OAuth scope a
**disqualification**. Both are now pinned by tests that run before a credential exists, and
neither can be satisfied by the sink that only writes to disk.

## The vacuity this plan was written to avoid, and what was done about it

`DryRunSink` writes a file and returns success. It would make every send assertion in the
phase green whether or not `GmailSink` works. So the split is enforced rather than
intended:

- `tests/unit/test_mail_sink_dry_run.py` asserts only what a disk write can honestly
  assert — both files exist, the `.eml` re-parses to the message `message.py` built, the
  `.json` equals the report — and names neither 429, nor a scope, nor a backoff;
- `tests/unit/test_gmail_credentials.py` **checks that absence with an AST identifier
  scan**, not a text search, because the dry-run file's docstring legitimately *names* 429
  and scope while explaining that it asserts neither. Paired with a control that runs the
  same scan over `test_gmail_sink.py` and requires it to find something;
- every REPORT-04 / REPORT-05 assertion runs against `GmailSink` through the real 07-01
  `ReportingChain`, with a fake transport that raises real `googleapiclient` `HttpError`s.

## Task 1 — rules 33-34, asserted against the bytes that would be sent

`build_report_message` produces a multipart message whose report is a
`Content-Disposition: attachment` part of type `application/json`, named by 07-02's
`result_filename` (`docs/PARAMETERS.md:168` — "the mandatory report emailed to the
lecturer"). The body is `BODY_TEXT`, a constant with no interpolation and no
caller-supplied text.

Every assertion re-parses `render_message(...)` with the stdlib parser. `_attachments()`
filters on `get_content_disposition() == "attachment"` rather than trusting
`iter_attachments()`, which yields every non-body part whatever its disposition — measured:
without that filter, sending the JSON **inline** failed only 1 test instead of 4.

The leak check comes in a **triple**: a positive assertion that `game_uid` appears in no
header and in no body part, plus two controls that plant it in the body and in the Subject
and require the check to FAIL.

`canonical_json` is reused rather than a second `json.dumps(sort_keys=True, ...)`
(QUAL-02, D-46). `render_message` uses `email.policy.SMTP`, so the `.eml` a dry run leaves
on disk is byte-for-byte the message a live run sends.

## Task 2 — the protocol, the disk sink, and one extraction

`MailSink` is a `runtime_checkable` Protocol with one `async send(report) -> SendReceipt`.
`SendReceipt` is never a bare bool: a dry run's evidence is the two paths it wrote, a live
send's is the API's message id.

`DryRunSink` writes both files through `artifacts.write_artifact*`, so the `.eml` inherits
D7-1's `logs/` refusal and the crash-safe rotate scheme instead of a hand-rolled
`Path.write_bytes` that no rule governs. That needed a bytes primitive, so
`durable_write_bytes` was **extracted** in `shared/durable_write.py` and
`durable_write_json` now calls it — a second write-and-rotate sequence would have been a
second crash-safety scheme (CLAUDE.md Table 5).

**The extraction was proven byte-neutral, not assumed.** The old text-mode `json.dump` and
the new `json.dumps(...).encode()` produce **98 identical bytes** for a payload carrying a
newline, a tab and Hebrew, because `json.dumps` escapes newlines and defaults to ASCII —
so Windows' text-mode newline translation had nothing to act on. Binary mode matters for
the `.eml`, and that is measured too: probe E turned the CRLF into `\r\r\n` on disk.

## Task 3 — the live path, proven without a credential

`gmail_sink.py` is the **only** module in `src/` importing `google-*`:

```
$ grep -rn "googleapiclient\|google\.oauth2\|google_auth\|google\.auth" src/
src/pursuit/services/reporting/gmail_sink.py:36  from google.auth.transport.requests import Request
src/pursuit/services/reporting/gmail_sink.py:37  from google.oauth2.credentials import Credentials
src/pursuit/services/reporting/gmail_sink.py:38  from google_auth_oauthlib.flow import InstalledAppFlow
src/pursuit/services/reporting/gmail_sink.py:39  from googleapiclient.discovery import build
src/pursuit/services/reporting/gmail_sink.py:40  from googleapiclient.errors import HttpError
```

**It does not sleep.** On 429 it raises `GmailRetryableError`; the wait is
`Gatekeeper._call_with_retry`'s, at the mail instance's OQ-3 value. Observed, with the
gatekeeper's injected `sleep` seam recording:

```
statuses [429, 429, 200]   ->  sent=True   attempts=3   sleeps=[30, 30]
statuses [429] (always)    ->  sent=False  attempts=4   sleeps=[30, 30, 30]
                               refusal=SEND_FAILED  queued=True  pending=1
                               then statuses=[200] + drain() -> sent=True, pending=0
                               the recovered attachment == the original report dict
```

Four attempts is `retries_before_failure + 1` = 4, read from the shipped `reporting.json`.
The queue assertion is **recoverability**, not "nothing raised": the same report reaches
the wire on `drain()` and is compared after a round trip through base64, MIME and
`json.loads`.

**Rule 30 is enforced twice**, and the second one is the one that matters: a `token.json`
left over from a broader consent is what actually authorises the call, and it never appears
in the list of scopes we asked for. Six forbidden scope sets are refused —
send+`gmail.readonly`, send+`https://mail.google.com/`, `gmail.modify`, `gmail.compose`,
`https://mail.google.com/` alone, and the empty set. The gate is a **set equality**, so
"contains `gmail.send`" cannot pass.

The blocking API call runs under `asyncio.to_thread`, off the loop the freeze watchdog
guards; asserted by thread id, and probed.

## Revert probes — eight, with real counts

Every behaviour was reverted and measured. No probe is a shape check; each was confirmed
wired (`assert old in source`) before the run, because the recurring failure mode in this
project is a probe that returns 0 failures because the mutation never landed.

| # | Mutation | Result |
|---|---|---|
| A | report content interpolated into the body | **2 failed, 15 passed** |
| B | JSON sent `inline` instead of as an attachment | **4 failed, 13 passed** |
| C | attachment renamed off 07-02's `result_filename` | **2 failed, 15 passed** |
| D | dry run writes the `.json` only, no `.eml` | **3 failed, 6 passed** |
| E | `durable_write_bytes` reverted to text mode | **2 failed** (`\r\r\n` observed on disk) |
| i | `GmailSink` SWALLOWS 429 instead of raising | **3 failed, 41 passed** |
| ii | mail backoff lowered to Table 19's bare 5 s | **3 failed, 8 passed** |
| vi | scope gate weakened to `GMAIL_SEND_SCOPE in scopes` | **4 failed, 11 passed** |
| iii | granted-token scope check removed | **1 failed, 14 passed** |
| iv | scope gate moved BELOW the credential read | **7 failed, 8 passed** |
| vii | `asyncio.to_thread` removed | **1 failed, 11 passed** |
| viii | a test file named `*_secret*` added | **1 failed, 19 passed** |

Controls restored cleanly each time (17 / 9 / 44 / 20 passed).

Probes **i** and **ii** are the two the plan named. Probe ii is the reason the backoff
assertion transcribes the literal `30` instead of reading `params.wait_after_error_seconds`
back: written the obvious way, `sleeps == [params.wait_after_error_seconds] * 2` would have
stayed green with the config lowered to 5.

Probe iv's seven failures are the ordering property: with the gate moved below the
credential read, all six forbidden-scope cases stop raising `GmailScopeError` first.

## The hole the self-audit found in my own work

**`tests/unit/test_gmail_credentials.py` shipped first as `test_gmail_secrets.py`, and
`.gitignore:26`'s `*_secret*` swallowed it silently.** `git status` never listed it. Eighteen
passing tests — including every rules 39-40 assertion in this plan — that git would have
refused to track, CI would never have run, and the grader would never have seen. It was
caught only because `git status --short` before the commit did not show a file I had just
written.

Fixed by **renaming, not by weakening the pattern** (`*_secret*` is a correct rules-39-40
guard). And the class of mistake is now checked rather than remembered:
`test_no_source_or_test_file_is_swallowed_by_gitignore` runs `git check-ignore -z --stdin`
over every `.py` under `src/`, `tests/`, `training/` and `scripts/`. It **fails rather than
skips** without git (D7-6's standard: a gate reporting OK for having looked at nothing is
worse than no gate), carries an anti-vacuity floor of `> 100` files scanned, and is paired
with a control asserting the scan does find `.env`. Measured while fixing it: **no other
`.py` in the repository is ignored.**

One more thing that check taught: `subprocess.run(..., text=True)` on Windows writes CRLF
into the child's stdin, so `git check-ignore --stdin` saw every path with a trailing `\r`
and reported **five false positives**. The helper passes bytes with `-z`, and says why.

## Anti-vacuity scans

**Every `parametrize` in this plan's five test files is guarded.** Four parametrize sites,
each over a module-level tuple, each with a companion test asserting the tuple's length —
`FORBIDDEN_SCOPE_SETS` (6), `SHIPPED_ROLES` (2, twice), `OAUTH_IGNORE_ENTRIES` (6). An
emptied table would otherwise **skip silently**, which is how 07-01 nearly lost its single
most important control.

**Collected counts, verified non-zero:** 17 / 9 / 12 / 15 / 20 = **73 tests**, against a
suite delta of 1846 → 1919 = **+73**. They agree exactly.

## Zero network, and it is enforced rather than promised

`test_gmail_sink.py` carries an autouse fixture that fails any test attempting a
non-loopback `connect` or **any** DNS lookup. Two control tests prove both halves fire:
`connect(("93.184.216.34", 80))` and `getaddrinfo("gmail.googleapis.com", 443)` each raise.

The guard is narrowed to *non-loopback* deliberately and the reason is in its docstring:
asyncio's Windows proactor loop builds its own self-pipe over a loopback socketpair, so a
blanket refusal fails at event-loop construction — measured, 8 fixture ERRORs — and would
have had to be deleted, which is how this kind of guard usually dies.

No test constructs a real credential: `build_gmail_transport` takes its loader as a seam,
and `load_send_only_credentials` is driven with `Credentials`, `InstalledAppFlow` and
`Request` monkeypatched on the `gmail_sink` module.

## Secrets — rules 39-40

`.env-example` gains `PURSUIT_GMAIL_CREDENTIALS_PATH` and `PURSUIT_GMAIL_TOKEN_PATH` —
the NAMES `config/*/reporting.json` already carried — with `your-...-here` dummy values in
the existing house style. A test asserts, for **both** shipped roles, that every env-var
name the config names has an entry in `.env-example` and that its value matches the dummy
shape; another asserts the six OAuth ignore entries (`credentials.json`,
`client_secret*.json`, `token.json`, `token.pickle`, `*.token`, `.env`) survive this plan,
since they were written into `.gitignore` before the OAuth code existed.

Scanned with the **real** values exported from `.env`, so the search was not vacuous:

```
real secret values loaded: ANTHROPIC_API_KEY 108 chars · NGROK_AUTHTOKEN 49 ·
                           PURSUIT_NGROK_DOMAIN 50 · PURSUIT_TUNNEL_SECRET 32
11 files scanned (.env-example, pyproject.toml, 3 src modules, 6 test files)
REAL-value leaks: []        KEY-SHAPED hits: []
controls: planted `sk-AAAA...` DETECTED · planted real authtoken DETECTED
```

`git diff config/` is **empty** — both `reporting.json` files still read
`"mode": "dry_run"`, asserted per role by a test that reads the raw JSON rather than the
loader's enum.

## OQ-3 and the Phase-4 control

The mail instance backs off **30 s**; Phase 4's LLM instance still backs off **5 s**. Both
are pinned in one test in this plan, reading the shipped files, so neither can be
harmonised into the other:

```
load_reporting_config(config/police/reporting.json).wait_after_error_seconds == 30
load_language_config(config/police/language.json).wait_after_error_seconds  ==  5
```

07-01's 22/22 effective-parameter control (`tests/unit/test_gatekeeper_llm_unchanged.py`,
26 tests) passes **unmodified**, and `git diff config/*/language.json` is empty. This plan
edited no gatekeeper, built no second one and added no backoff.

## Zero numbers invented

`TOO_MANY_REQUESTS = 429` is RFC 6585's status code and is what rule 28 names. `200` and
`500` are HTTP statuses in a test fixture. `GMAIL_API_VERSION = "v1"` is Google's. Every
limit in the chain comes from the shipped `reporting.json`, whose `_sources` object cites
each leaf. `MAIL_BACKOFF_SECONDS = 30` / `LLM_BACKOFF_SECONDS = 5` in the test file are
transcriptions of two config values, deliberately duplicated there so the test can disagree
with the config.

## Gates

```
ruff check .                        All checks passed        (0 violations)
check_line_limit.sh                 exit 0                   (tracked)
check_line_limit.sh <12 paths>      exit 0                   (explicit -- the no-arg form
                                                              enumerates via git ls-files
                                                              and passes VACUOUSLY on an
                                                              untracked file)
check_no_llm_in_strategy.py         OK
pytest tests/ --cov                 1919 passed, 0 failed    (baseline 1846)
                                    coverage 97.02%          (baseline 96.95%)
git diff config/                    EMPTY
uv lock --check                     resolved, current        (no requirements.txt exists)
scripts/dev_launch.py               exit 0
                                    outcome capture, 11 audit_verdict matched=true per side
                                    zero STEP0_MISMATCH, zero technical_win
```

Every new or touched module at **100%**: `message.py` · `sink.py` · `gmail_sink.py` ·
`artifacts.py` · `durable_write.py`.

File sizes, all <= 150 code lines:

| File | Lines | | File | Lines |
|---|---|---|---|---|
| `message.py` | 90 | | `test_mail_message.py` | 117 |
| `sink.py` | 73 | | `test_mail_sink_dry_run.py` | 77 |
| `gmail_sink.py` | 149 | | `test_gmail_sink.py` | 145 |
| `artifacts.py` | 125 | | `test_gmail_scope.py` | 126 |
| `durable_write.py` | 105 | | `test_gmail_credentials.py` | 137 |
| `__init__.py` | 90 | | `gmail_fixtures.py` | 140 |

`gmail_sink.py` at 149/150 is the tightest file in the phase. It was measured before the
`__all__` entry for `load_send_only_credentials` was added and again after; the next plan
to open it splits rather than compresses.

## Games-played counters — rule 38

Read directly (the files are gitignored):

```
FULL SUITE     before 1915 / 1908    after 1915 / 1908    DELTA 0 / 0
ONE REAL GAME  before 1915 / 1908    after 1916 / 1909    DELTA 1 / 1
```

07-00's guarantee holds under this plan's changes. Nothing here reads the value, defaults
it, or reads around it; it remains the human's at 07-10.

## Deviations from plan

1. **[Rule 3 — blocking] Two extra test files.** The plan named
   `tests/unit/test_gmail_sink.py`; the 150-line gate forced `test_gmail_scope.py` (rule
   30) and `test_gmail_credentials.py` (rules 39-40 plus the dry-run purity scan) out of
   it. The 07-01 / 07-02 precedent.
2. **[Rule 3 — blocking] `tests/unit/gmail_fixtures.py` created.** The fake transport, the
   fake credentials and the chain builder are used by two test files; extracted at the
   second consumer rather than duplicated (CLAUDE.md Table 5). Not named `test_*`, so
   pytest collects nothing from it — the `artifact_config_fixtures.py` precedent.
3. **[Rule 2 — missing critical functionality] `artifacts.write_artifact_bytes`.** Not in
   `files_modified`. Without it the `.eml` would have been written by a hand-rolled
   `Path.write_bytes` that bypasses D7-1's `logs/` refusal and the crash-safe rotation. The
   existing guard was extracted to `_permitted_artifact_path` so the two writers cannot
   drift.
4. **[Rule 2] `shared/durable_write.durable_write_bytes` extracted.** Same cause, one layer
   down. Byte-neutrality measured (98 bytes both ways). The two older D7-2 copies were
   deliberately **not** folded in — `step0_collect.py` is the rule-38 write path 07-00
   certified, and D7-2's reasoning is unchanged by opening a different function in the same
   module. Restated as **D7-11**.
5. **[Rule 1 — bug] `tests/unit/test_gmail_secrets.py` renamed.** `.gitignore` swallowed
   it. Filed as **D7-10** with the permanent gate. The ignore pattern was not touched.
6. **[Rule 1 — bug] `durable_write.py`'s module docstring corrected.** It said "Crash-safe
   **JSON** write/read sequence shared by QTable and training/checkpoint.py" — no longer
   true of either half after the extraction, and a document certifying a wrong fact is what
   let D7-1 survive a whole phase (07-01's and 07-02's lesson).
7. **[Rule 1 — bug] `test_gmail_sink.py`'s docstring corrected** — it named a control test
   that had been renamed during the fix for the Windows proactor loop.
8. **[Rule 2] `GmailSink` deliberately NOT re-exported from the package `__init__`.** The
   one departure from `services/llm/__init__.py`'s "import from here" convention, with the
   reason written into the docstring: that package must import `anthropic_provider` for its
   `register_provider()` side effect, this one has no such requirement, and re-exporting
   would load `google-*` — measured at 0.265 s — for every `dry_run` importer.

**Total deviations:** 8 auto-fixed (2 blocking splits/extractions, 3 missing-critical, 3
bug/doc corrections). No architectural decision was needed; no checkpoint was reached; no
authentication gate occurred — nothing in this plan authenticates against anything.
`tests/integration/test_belief_policy.py` was not touched and no `git add -A` was used.

## Issues Encountered

- **`socket.socket.connect` cannot be blanket-refused on Windows.** The first network guard
  failed 8 tests at fixture setup, in asyncio's proactor self-pipe. Narrowed to non-loopback
  plus a DNS guard, with both halves controlled.
- **`subprocess.run(text=True)` corrupted the git-ignore scan** with CRLF-terminated paths
  and five false positives (D7-10).
- **`iter_attachments()` is not a disposition filter.** Discovered by probe B failing only
  1 test where it should have failed 4; the helper now filters on
  `get_content_disposition()`.

## Open, for the plans that own it

**D7-10 RESOLVED** here, with the permanent gate · **D7-11** the two un-folded
durable-write copies · **D7-12** nothing in `src/` sends a report yet — D7-3's fourth
occurrence, structural, and 07-07's to close. All three in `deferred-items.md`, with the
in-package reachability of every new name grepped and listed.

## Task Commits

1. **Task 1: the MIME shape** — `86d9547` (feat)
2. **Task 2: the sink protocol and the dry-run sink** — `c196535` (feat)
3. **Task 3: `GmailSink` against an injected fake transport** — `6b686cd` (feat)

---
*Phase: 07-reporting-and-visualization-shell*
*Completed: 2026-08-17*

## Self-Check: PASSED

All 18 claimed paths verified present on disk with `[ -f ]` **and**, for the nine new
source/test files, tracked by git with `git ls-files --error-unmatch` — which is the check
that would have caught D7-10 on its own. All three claimed commit hashes verified reachable
in `git log --oneline --all`. Collected test counts re-read from pytest rather than counted
by hand: **17 / 9 / 12 / 15 / 20 = 73**, equal to the suite delta 1846 → 1919. Every number
in this document was read off a command's output in this session, including the two counter
readings, the twelve line counts and both coverage figures.

## Addendum — `docs/phases/phase-7/TODO.md`

CLAUDE.md requires `/gsd:execute-phase` to keep the phase TODO current as tasks land.
07-04's row is now `☑` with its measured acceptance evidence written into the Definition of
Done column. Row 07-96 (graph refresh) moved to `◐`: the graph was refreshed after this
plan's code landed — 9250 nodes / 16532 edges, and `graphify explain GmailSink` resolves to
`gmail_sink.py:153` — but its Definition of Done also names `gui/`, which 07-06 creates.
Rows 07-05…07-10 are untouched.
