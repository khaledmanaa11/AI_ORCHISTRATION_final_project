# `game_artifacts/` — the four required JSON artifacts

This directory holds the four artifacts `docs/PARAMETERS.md` ("Required JSON artifacts",
lines 157–168) requires, which rule 50 and Appendix F rule 4 require to be **committed**:

| File | Written by | Plan |
|---|---|---|
| `declaration_<game_id>.json` | `services/reporting/artifact_declaration.py` | 07-02 |
| `config_<game_id>_g<NN>.json` | `services/reporting/artifact_config.py` | 07-02 |
| `log_<game_id>_g<NN>.json` | `services/reporting/artifact_log.py` | 07-05 |
| `result_<game_id>.json` | `services/reporting/artifact_result.py` | 07-07 |

`_g<NN>` is a **per-`game_id` sub-game index** — 01-based, derived from what already exists
here for that `game_id`. It is **not** the rule-37/38 games-played counter, which lives in
`config/{police,thief}/games_played.json` and is never read by the artifact spine (D-72).

## Why not `logs/` — D7-1

`.gitignore` ignores `logs/` **wholesale**, and `agent_step0_wiring.write_declaration`
writes its handshake-time declaration **precursor** into `logs/<role>/`. That precursor is
not this artifact and cannot be: it is written before move 1, and
`declaration_<game_id>.json` must carry the game's **end time**.

So the deliverables land here — the `artifact_dir` set in `config/*/reporting.json`,
verified not ignored — and `services/reporting/artifacts.write_artifact` **refuses** any
path under `logs/`. The `logs/` ignore rule itself is deliberately left byte-unchanged:
git cannot re-include a file whose parent directory is excluded, so narrowing it would
require a `logs/**`-plus-negations restructure that the next editor can silently break,
and it would put the bulky per-run wire logs and nonce ledgers one careless `git add`
away from the repository.

## Staging rule — never `git add -A` here (D7-19)

Every `scripts/dev_launch.py` run leaves untracked files in this directory, from a
throwaway local game. **Stage league evidence by explicit path.** A blanket sweep would
commit a development game under filenames a grader reads as league evidence, and rule 38
territory is one directory away.

Two patterns that can never be one of the four required artifacts are ignored as of plan
07-09, so a careless sweep is that much less harmful:

| Pattern | What it is | Why it is safe to ignore |
|---|---|---|
| `game_artifacts/**/*.eml` | the rendered RFC 5322 message a **dry run** writes beside the report | not JSON, and not one of the four names |
| `game_artifacts/**/*.prev.json` | `durable_write_json`'s rotation generation | `.prev` is not a name `docs/PARAMETERS.md:165-168` gives |

**The four required names are NOT ignored and must never be.**
`tests/unit/test_artifact_dir_hygiene.py` asserts both halves — that those two patterns are
ignored *and* that all four required names are not — so narrowing this further fails a test
rather than quietly hiding evidence.

Which of the remaining files are real league evidence and which are debris is a judgement
only the operator running the game can make; plan 07-10 owns it
(`docs/phases/phase-7/OAUTH-RUNBOOK.md` §6).
