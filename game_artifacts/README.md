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
