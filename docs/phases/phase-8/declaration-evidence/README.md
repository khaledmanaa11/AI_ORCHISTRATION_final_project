# The first `declaration_<game_id>.json` a real game ever wrote

**Plan:** 08-04 · **Game:** `397b3503b1bfa996` · **Run:** `uv run python scripts/dev_launch.py`,
exit 0 · **Recorded:** 2026-08-17

## Why these two files are kept

`build_declaration_artifact`, `write_declaration_artifact` and `DeclarationContext` were built by
07-02 and had **zero production callers** — re-derived at HEAD by 08-01. `declaration_<game_id>.json`
is one of rule 50's **four mandatory** artifacts and rule 49 wants four repo links inside it, so
`docs/PARAMETERS.md:165`'s declaration content had **never been written by a game**. 08-04 wired the
first production caller (`services/reporting/end_of_game_declaration.declare_game`, called from
`end_of_game._report`). These are its output, copied verbatim off `game_artifacts/{role}/`.

They are **evidence of a dev-launch smoke game, not league artifacts.** The four committed artifacts
of a scored league game are 08-13's, produced by the same code path against a real opponent.

## What the run measured

| Reading | Before | After |
|---|---:|---:|
| `config/police/games_played.json` | 1922 | **1923** |
| `config/thief/games_played.json` | 1915 | **1916** |

One real game, `+1` on each counter — 07-00's fixed mechanism behaving correctly. The same day's full
`uv run pytest --cov` moved both counters by **zero**.

## The keys, against `docs/PARAMETERS.md:165`

PARAMETERS asks the declaration for *"both teams' identities, repo URLs, MCP server addresses,
hardware spec, language model, agreed token ceiling, start/end times"*.

| PARAMETERS content | Where it is | Value in these files |
|---|---|---|
| both teams' identities · hardware spec · language model | `declarations.own` / `declarations.peer`, the signed Step-0 envelopes, embedded verbatim (D-71) | `role`, `team_code`, `os`, `cpu`, `ram_gb`, `gpu`, `llm_name`, `code_version`, `games_played_so_far`, `commit_hash` — all ten §5.5 keys, both seats |
| repo URLs | `repo_urls` | rule 49's four named slots, each a stated-absence marker naming 08-12 |
| MCP server addresses | `mcp_server_addresses` | `own` / `opponent`, both stated-absent |
| agreed token ceiling | `token_ceiling` | `200000` — `docs/PARAMETERS.md:83` Table 18 row 4, negotiable |
| start/end times | `start_time` / `end_time` | `2026-08-17T12:01:46…` / `…12:01:55…` — the earliest and latest timestamps in each seat's own wire log, measured, not stamped at report time |
| *(not PARAMETERS content — 08-04 adds it)* | `games_played_declared` | `present: false`, naming `GAMES-PLAYED-RECONSTRUCTION.md` |

**Both seats embedded the peer's envelope** (`peer_declaration_status`: *"peer's own signed
declaration embedded verbatim"*), so D-71's both-sides wrap is proven on a real handshake and not
only on a fixture.

## The one number that is deliberately not a declaration

Each file's signed envelope carries `games_played_so_far` — **1922** on the police seat and **1915**
on the thief seat — because rule 37 puts the counter's value in the Step-0 declaration. Those are the
**raw counters**, and 07-00 measured them advancing +14 across one `pytest` run for zero games; they
still disagree by seven for two agents that have only ever played each other.

So the artifact's top level carries `games_played_declared` as a stated absence saying exactly that
and naming `docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md`. The field is **unparameterised** —
no caller can set it — because rule 38 (`docs/RULES.md:79`) makes a false games-played declaration an
**absolute disqualification**. The value is a human's, at 08-14.
