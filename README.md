# P2P Cops-and-Robbers — a cop agent and a thief agent

Two autonomous agents — a **cop** and a **thief** — that play a distributed cops-and-robbers
match on a 7×7 grid over a peer-to-peer network with **no central server and no referee**.
Final project for *Orchestration of AI Agents* (University of Haifa).

Each agent is a symmetric [FastMCP](https://gofastmcp.com) peer: it exposes tools with
`@mcp.tool` and calls the opponent's tools over the same protocol. It never sees the board.
It infers where the opponent is from a decaying scent field and from free-text hints that
may be lies, chooses its action by solving a **simultaneous-move matrix game** over a learned
15-weight positional evaluation, and proves it did not change its mind after seeing the
opponent's move by way of a SHA-256 **commit-reveal** protocol with a mutual end-of-game
audit.

This file is both the user manual (engineering standard §2.1) and the academic report
(§9.4.2, rule 42). Every claim in it points at a file you can open. Where something is not
done, it says so and names what would close it — a README that overstates and a README that
understates are the same defect.

---

## What this is

| | |
|---|---|
| **Two processes, no shared state** | `config/police/` and `config/thief/` are two independent agents. They share a *library*, never a live game state — sharing state is instant disqualification for information leakage (rule 2). |
| **No referee** | Neither peer arbitrates. `scripts/dev_launch.py` only spawns the two standalone commands; deleting it changes nothing about how a league game runs. |
| **The algorithm decides** | A language model decodes incoming hints and writes outgoing bluff text. It never chooses a move (rule 25), and `scripts/check_no_llm_in_strategy.py` is a CI job that proves no LLM import is reachable from `strategy/`. |
| **The agent never sees the truth** | The live GUI renders a `LocalView` — this seat's own belief — and cannot reach the joint board. `scripts/check_local_truth.py` enforces it at the AST level over 7 modules (rules 8–9). |
| **Board** | 7×7, orthogonal movement, cop starts `(0,0)`, thief starts `(3,3)`, barrier quota 14, move ceiling 35. Every one of those numbers comes from [`docs/PARAMETERS.md`](docs/PARAMETERS.md); none is invented. |

---

## Status — measured, not asserted

Built in 8 phases mirroring the book's build order (§10.3). The table below is derived from
the verification and gate documents in the repository, **not** from a tracker's own banner.
When they disagree, the artifact wins.

| Phase | What it delivers | State |
|---|---|---|
| 1 | Base game logic — grid, movement, barrier quota, capture | Verified — [`01-VERIFICATION.md`](.planning/phases/01-base-logic/01-VERIFICATION.md) `passed` |
| 2 | FastMCP P2P infrastructure — two processes, localhost | Verified — [`02-VERIFICATION.md`](.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md) `passed` |
| 3 | Blind strategy module — the matrix-game mover | Verified — [`03-VERIFICATION.md`](.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md) `passed`, 3/3 §10.4 criteria |
| 4 | Language and scent — hints, pheromones, deception | **Executed, not verified.** [`04-VERIFICATION.md`](.planning/phases/04-language-and-scent/04-VERIFICATION.md) reads `human_needed`: all three mechanisms verified *mocked*, and a live-API confirmation of GATE-4 is the single open item |
| 5 | Cloud exposure and tunnelling | **Both §10.4 criteria PASS** — [`GATE-5-MEASUREMENT.md`](docs/phases/phase-5/GATE-5-MEASUREMENT.md), closed on the fourth attempt by two full rounds between two machines on two networks. `05-VERIFICATION.md` still reads `human_needed`; its one open item is a tracker scope decision, not a code gap |
| 6 | Security — commit-reveal, nonce, Step-0 | Verified — [`06-VERIFICATION.md`](.planning/phases/06-security-and-cryptography/06-VERIFICATION.md) `passed`, GATE-6 all three criteria PASS |
| 7 | Reporting shell — Gmail, live GUI, replay viewer | **Executed, NOT verified.** 11 of 12 plans have run; **no `07-VERIFICATION.md` exists**. [`GATE-7-MEASUREMENT.md`](docs/phases/phase-7/GATE-7-MEASUREMENT.md): criteria 2 and 3 PASS, criterion 1 **dry-run PASS + live PENDING** |
| 8 | Submission and league operations | **In progress, not verified** — no `08-VERIFICATION.md` exists. [`docs/SUBMISSION-CHECKLIST.md`](docs/SUBMISSION-CHECKLIST.md) is re-derived from the tree on every run of `scripts/check_submission.py` and reports its own remaining gaps |

**Three things this repository does not claim.**

- **No game report has ever been delivered by mail.** Every shipped `config/*/reporting.json`
  reads `"mode": "dry_run"`, which writes the report to disk and transmits nothing. The MIME
  shape, the send-only scope check and the gatekeeper are proven; the live send is PENDING.
- **No league game has been played.** The remote rounds on record are this project's own two
  seats playing each other across two machines, not a match against another team.
- **No games-played figure appears anywhere in this file.** Misreporting it is rule 38, an
  absolute disqualification. The counters are mechanical
  (`config/*/games_played.json`); the *declared* value is a human decision still open, with
  the evidence gathered in
  [`GAMES-PLAYED-RECONSTRUCTION.md`](docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md).

---

## Installation

**Prerequisites**

- **Python ≥ 3.10** (`pyproject.toml` `requires-python`); developed and measured on 3.11.
- **[`uv`](https://docs.astral.sh/uv/)** — the only supported package manager. There is no
  `requirements.txt` and `pip` is never used; `pyproject.toml` + `uv.lock` are the single
  source of dependency truth.
- **Git** ≥ 2.9, for `core.hooksPath`.
- **Tk** for the two GUI processes. It ships with the python.org and `uv`-managed builds; on
  Debian/Ubuntu it is the separate `python3-tk` package.
- No API key is needed to run a game, the test suite, or any quality gate.

**Step by step**

```bash
git clone <this repository>            # see "Companion repository" below
cd final_project
uv sync                                # creates .venv and installs from uv.lock
git config core.hooksPath scripts/hooks # enables the pre-commit 150-line gate
cp .env-example .env                   # then fill in your own values
uv run python -m pursuit.main --config-dir config/police --check-config
```

The last command is the install check. It prints the resolved role and endpoints and exits
without starting a server:

```
role=police
listen=127.0.0.1:8001
opponent_url=http://127.0.0.1:8002/mcp
```

**Environment setup.** `.env-example` is committed with dummy values and documents every
variable the code reads. Secrets are read with `os.environ.get()` only — never a config
field, never a default, never a file in git (rules 39–40). All of them are optional: unset,
the language provider degrades to a template fallback, the tunnel stays off, and no mail can
be sent.

**Troubleshooting**

| Symptom | Cause and fix |
|---|---|
| `uv: command not found` | `uv` is not installed. Install it from the link above; do not fall back to `pip`, which this project does not support. |
| `ModuleNotFoundError: pursuit` | The command was run outside `uv`. Every command in this file starts with `uv run`. |
| `_tkinter.TclError` / `no display name` | Tk is missing or there is no display. The agents themselves need neither — only `pursuit.gui.*` does. Add `--once` to render one frame and exit. |
| Port 8001/8002 already in use | A previous agent did not shut down. Stop it, or change `net.port` and the peer's `net.opponent_url` in `config/<role>/network.json`. |
| An agent exits with status 1 | That is a **technical loss**, deliberately surfaced as a non-zero exit — including one declared by the Final-Reveal audit after catching a forged or withheld reveal. The reason is in `logs/<role>/<game_id>.jsonl`. |
| The pre-commit hook rejects a file | A file exceeds 150 code lines. **Split it; never compress code to fit.** Never `--no-verify`. |

---

## Usage — running a game

**The league path: two terminals, two processes.** This is exactly how a real match runs, and
the only difference between the two commands is the `--config-dir` flag. Start one agent per
terminal; neither process arbitrates the game and neither is a referee. Start both promptly —
a peer that cannot be reached at handshake time is a distinct, recorded outcome
(`HandshakeOutcome.UNREACHABLE`), not a silent hang.

```bash
uv run python -m pursuit.main --config-dir config/police   # terminal 1
uv run python -m pursuit.main --config-dir config/thief    # terminal 2
```

**Flags of `pursuit.main`**

| Flag | Required | Meaning |
|---|---|---|
| `--config-dir` | yes | This agent's own configuration directory. Role, listen address and opponent URL all come from there. It is the only way the two commands differ. |
| `--check-config` | no | Load and print the resolved role and endpoints, then exit without starting a server. |

Exit status `0` is a completed game; `1` is a technical loss.

**Local convenience.** One command spawns both of the above as subprocesses and waits:

```bash
uv run python scripts/dev_launch.py
```

It imports nothing from the agent package, decodes no wire message and holds no board
snapshot — it is not a referee (rule 2, D-01). **It plays a real game**, so it advances both
agents' games-played counters by one each. The test suite never does.

**Watching a game live** (a separate process, fed by this seat's published `LocalView`
snapshot — it cannot reach the true board):

```bash
uv run python -m pursuit.gui.live_app \
  --snapshot logs/police/<game_id>.view.json --refresh-ms 500
```

**Replaying and verifying a finished game** (recomputes every commit hash and shows a
verdict banner):

```bash
uv run python -m pursuit.gui.replay_app \
  --artifact game_artifacts/police/log_<game_id>_g01.json --step-ms 400
```

**Flags of both GUI processes**

| Flag | Required | Meaning |
|---|---|---|
| `--snapshot` (live) | yes | Path to this seat's `<game_id>.view.json`, written beside the wire log. |
| `--artifact` (replay) | yes | Path to a sealed `log_<game_id>_g<NN>.json`. A `.jsonl` path is refused with exit 2 and a message naming rule 18. |
| `--refresh-ms` / `--step-ms` | yes | Redraw interval. **Deliberately has no default**: no document in the project supplies this number, so the operator states it rather than the code inventing one. |
| `--once` | no | Render a single frame and exit — used by the automated checks, and useful without a display. |

---

## Examples and screenshots

**A complete game, end to end, from a clean checkout:**

```bash
uv sync
uv run python scripts/dev_launch.py                 # plays one real game
ls game_artifacts/police                            # the sealed artifacts
uv run python -m pursuit.gui.replay_app --once \
  --artifact game_artifacts/police/log_<game_id>_g01.json --step-ms 400
```

A finished game leaves four kinds of artifact, named and specified in
[`docs/PARAMETERS.md`](docs/PARAMETERS.md) — `declaration_<game_id>.json`,
`config_<game_id>_g<NN>.json`, `log_<game_id>_g<NN>.json` and `result_<game_id>.json`. Each
seat writes its **own** copy from its **own** wire log; nothing is merged.

**Reading the strategy without running anything:**

```bash
uv run python -c "import json; d=json.load(open('config/police/weights.json')); \
print(dict(zip(d['feature_names'], d['weights'])))"
```

**Screenshots — NOT PRESENT.** Two are required by §9.4.2 item 5 and neither exists yet:

| Slot | What it will show | Produced by |
|---|---|---|
| *(absent)* `docs/assets/live-gui-heatmap.png` | The live dashboard's belief heat map during a game — this seat's belief only, never the true position | plan 07-10 |
| *(absent)* `docs/assets/replay-verified-ok.png` | The replay viewer's verdict banner reading `Verified OK` after re-hashing every turn | plan 07-10 |

They are listed as empty slots on purpose. A placeholder image would render as a broken icon
and read as a delivered asset — the same failure mode as a placeholder URL. Until 07-10 runs,
the evidence for both is the machine-checked kind: `GATE-7-MEASUREMENT.md` criterion 3
records the banner text, and records that removing the non-zero-turn guard made an **empty**
artifact print `Verified OK`, which is precisely why that guard exists.

---

## Configuration guide

Every number the agents use is read from JSON under `config/<role>/`, never hardcoded. Each
file carries a `_sources` block citing the document each leaf came from, because JSON has no
comment syntax and an uncited number is indistinguishable from an invented one.

| File | Governs |
|---|---|
| `game_params.json` | Board size, start cells, movement, barrier quota, move ceiling, the scoring table. **Fixed values** — a deviation disqualifies. |
| `role.json` · `network.json` | Which seat this is; listen host/port and the opponent's URL. |
| `strategy.json` · `weights.json` | The brain class per seat, and the 15-weight evaluation vector. |
| `belief.json` · `scent.json` | Bayesian belief priors; the 5×5 emission kernel and decay law (both **fixed**). |
| `language.json` · `deception.json` | LLM provider, gatekeeper limits, hint word ceiling, the truth/lie policy. |
| `security.json` | Commit-reveal on/off, hash and nonce policy, Step-0 declaration fields. |
| `resolution.json` | The negotiated rules block: which optional predicates this seat proposes. |
| `tunnel.json` | Tunnel provider and the **names** of the environment variables holding its secrets. |
| `reporting.json` | Mail mode (`dry_run` in everything shipped), the mandatory recipient, artifact directory, and the gatekeeper's rate limits. |
| `league.json` | Rule 49's four repo URLs, the MCP server addresses and the agreed token ceiling. |
| `games_played.json` | The raw mechanical counter. Not a declaration. |

Rules that hold across all of them: no secret is ever a config value, only the *name* of an
environment variable; the two roles' `game_params.json` and `scent.json` must be identical
and are compared by cryptographic digest during the handshake; and values marked **fixed** in
`docs/PARAMETERS.md` may never be edited, while **minimum** values may only move upward.

---

## The model — a Dec-POMDP

The match is a **decentralised, partially observable Markov game**. Two agents act
simultaneously on a shared state that neither observes directly, and neither may condition
its action on the other's action for the same turn.

- **State** `s = (cop cell, thief cell, barrier set, turn index, barriers remaining)` on the
  7×7 grid. Transitions are deterministic given the joint action.
- **Actions** are enumerated from the *same* pre-turn state for both seats: five moves
  (four orthogonal plus stay) for either agent, and for the cop optionally a barrier
  placement — only the cop may place one, and placing it on the thief's cell is a capture.
- **Observations** are strictly local. A seat sees its own cell, the barriers it knows
  about, the scent field it maintains, and the opponent's free-text hint — which may be a
  lie. A seat never receives the opponent's coordinates: `shared/hint_guard.py` refuses to
  *send* a digit pair or a row/column phrase.
- **Uncertainty** is carried as an explicit belief distribution over the opponent's cell,
  updated by Bayes from two likelihoods — scent intensity and the decoded hint — in
  `strategy/belief.py` and `strategy/belief_hint.py`. It is the only thing the agent has, and
  it is what the live GUI renders.
- **Rewards** are the book's scoring table, taken from `docs/PARAMETERS.md` and never
  invented: capture 20/5, survival 5/10, tie 2/2, technical loss 0/0, cop first.
- **Why it is not an MDP.** Book §5.3.2 p.35 states that the Acknowledge phase *"guarantees
  that the reveal will occur only when both sides have already fixed their moves"*. That
  makes the per-turn problem a matrix game, in which a deterministic best response does not
  exist and the only unexploitable play at contact squares is a mixed one. The consequence
  for the algorithm is in the next-but-one section.

Fuller treatment: [`docs/PRD.md`](docs/PRD.md), [`docs/PLAN.md`](docs/PLAN.md),
[`docs/phases/phase-3/PRD.md`](docs/phases/phase-3/PRD.md).

---

## Orchestration dilemmas

**Turn management under simultaneity.** Both seats must fix their actions before either sees
the other's. A four-phase protocol enforces it — **Commit** (a hash only) → **Acknowledge**
→ **Reveal** (move and hint; the nonce stays hidden) → **Final Reveal / Audit** (all nonces
at game end). The turn resolves *once*, from one joint resolver, so no seat can act on
information from the same turn. Phase 3's post-mortem records what happened before this was
true: the engine resolved cop-then-thief and the thief was effectively choosing with sight
of the cop's new cell.

**Network failure handling.** Every remote call is bounded and every bound is observable. A
freeze watchdog `os._exit`s an agent that stops making progress, rather than hanging a peer
that is waiting on it. An early or out-of-order envelope is **buffered**, never eaten —
discarding a peer's early `FINAL_REVEAL` once created a path to a false accusation of
silence, and that class is now held closed by a guard enumerated over all twelve queue-pull
sites. A dropped tunnel mid-round is on the record too, in `GATE-5-MEASUREMENT.md` attempt 2.

**The Gatekeeper.** One component fronts every external call — language model and mail alike.
Its limits come from config, never from constants in code, and on overflow it **queues and
refuses; it never crashes** (rules 28–29). Contract:
[`docs/PRD_gatekeeper.md`](docs/PRD_gatekeeper.md).

**The Orchestrator.** There isn't one, and that is the design. Each peer is simultaneously a
server and a client; no process arbitrates the game; and the only "launcher" holds no state
and passes no data between the two children. Anything else would be a referee, and a referee
is disqualifying.

---

## The strategy that ships

**Per turn, in four steps** — no language model is on this path at any point:

1. Enumerate both action sets from the same pre-turn state (`sdk/actions.py`).
2. Build the |A_cop| × |A_thief| payoff matrix by one-ply expansion through the *live*
   negotiated rules (`strategy/matrix.py`): `M[i][j]` is the value of the resolved successor.
3. Solve the matrix game (`strategy/equilibrium.py`): a pure saddle point when one exists,
   otherwise regret matching — a **mixed** strategy.
4. Sample this seat's action from a seeded, logged RNG (`strategy/valuebrain.py`).

Leaf values are bounded to `[-1, 1]`: capture `+1.0`, survival `-1.0`, and every
non-terminal position `tanh(w · φ(s))` over a **15-feature** evaluation of the free-cell
graph — distance, reachability, degree, territory, cycle rank, chokepoints, barrier and turn
budgets, parity. The game is zero-sum, so one weight vector serves both seats by negation.

Nothing joint is ever stored: the matrix is rebuilt at the point of use, and only the 15
floats are learned. A decision costs **3.62 ms** cold and 2.14 ms warm, against a negotiated
30-second timeout.

**What was withdrawn, and why it matters here.** Run 1 of this project trained a tabular
Q-learning policy for 300,000 episodes; it was **superseded** and withdrawn, and
[`docs/PRD_rl_strategy.md`](docs/PRD_rl_strategy.md) still carries the ⛔ banner saying so.
The reason is the one above: `max_a' Q(s', a')` is a single-agent quantity with no meaning in
a simultaneous game, and `argmax` over a Q-row is deterministic by construction — this
repository measured a search cop capturing a *deterministic* evader 96% of the time and a
*mixing* one 36%. Earlier revisions of this README described the withdrawn design as what
ships. It did not, and it does not.

Mechanism contract: [`docs/PRD_matrix_mover.md`](docs/PRD_matrix_mover.md). The full history,
including the reversals: [`ENGINEERING-LOG.md`](docs/phases/phase-3/ENGINEERING-LOG.md) and
[`RUN-1-POSTMORTEM.md`](docs/phases/phase-3/RUN-1-POSTMORTEM.md).

---

## Learning curves

Rule 42 and §9.4.2 item 4 make learning curves a graded section. **These are the curves of
the mechanism that ships**, drawn from tracked artefacts, reproducible on a clean checkout
with no training run and no API key:

```bash
uv run python scripts/plot_run2_curves.py
```

**Outcome regression — the optimiser whose vector ships.** 40 generations × 600 games ≈
24,000 games, `seed=1337`, Adagrad on `tanh(w·φ)` against each game's actual result, scored
every generation against *fixed* anchors rather than against self-play — a policy that has
merely learned to beat its own past selves otherwise looks like progress.

![run 2 outcome-regression learning curve](artifacts/curves/run2_selfplay.png)

Cop capture rate against the anchors rises 0.523 → 0.737 and thief survival 0.280 → 0.363,
while the regression loss falls 1.634 → 0.724. The vector at the end of this run is
byte-identical to the shipped `config/police/weights.json` and `config/thief/weights.json`.

**(1+λ)-ES on league points — run to completion, and NOT shipped.**

![run 2 evolution-strategy fitness curve](artifacts/curves/run2_evolution.png)

Best-so-far fitness rises 32.67 → 35.50. Total points came out near-identical to outcome
regression; the *distribution* did not. Held out at n=200 with 95% Wilson intervals:

| Optimiser | thief vs sealing cop | thief vs blind cop | cop vs evader |
|---|---|---|---|
| hand-set prior | 43.5% | 14.5% | 100% |
| **outcome regression (ships)** | **58.0%** | **32.5%** | **100%** |
| (1+λ)-ES | 20.0% | 85.5% | 93.5% |

The ES vector is a specialist that collapses against the stronger and more likely archetype
— a competent opponent uses its barrier quota, and rule 46 makes that decisive — so the
balanced vector ships and the ES run is kept as a **documented negative result** rather than
deleted. Training also flipped the sign of two features the hand-set prior had backwards
(`chokepoint_density` +0.40 → −0.49, `thief_on_chokepoint` +0.30 → −0.39).

**The run-1 figures are still in the tree** (`artifacts/curves/winrate_cop.png`,
`winrate_thief.png`, `mean_reward.png`, and the raw `curves.csv`). They are retained as the
evidence of a **withdrawn** design, not as a description of this product, and the CLI that
drew them was removed with the rest of that stack. Their story — a gate that failed and was
reported failing rather than lowered — is in
[`RUN-1-POSTMORTEM.md`](docs/phases/phase-3/RUN-1-POSTMORTEM.md).

---

## Security model

| Property | How it is obtained |
|---|---|
| A move cannot be changed after seeing the opponent's | Four-phase commit-reveal. The hash input is canonical JSON (`sort_keys=True, separators=(",",":")`), so both peers hash byte-identical input. |
| The commitment cannot be brute-forced | A 16-byte nonce from `secrets.token_hex(16)` — never `random` — kept hidden until the Final Reveal. |
| A forged or withheld reveal is caught | The end-of-game mutual audit re-derives every commitment from the nonces and records a durable `audit_verdict`. Its join key is derived locally, not taken from the peer. |
| Both sides agreed the same rules and numbers | A Step-0 declaration carrying identity, hardware, model, code version and **commit hash** (rule 53), cross-signed and compared with `secrets.compare_digest`; the game parameters and scent kernel are compared by digest during the handshake. |
| The GUI cannot leak the truth | The local-truth firewall — a CI gate that walks the AST of every `gui/`-reachable module (rules 8–9). |
| No secret is in the repository | `os.environ.get()` only; `.env-example` carries dummy values; credential filenames are in `.gitignore` (rules 39–40). |

Evidence: [`GATE-6-MEASUREMENT.md`](docs/phases/phase-6/GATE-6-MEASUREMENT.md) (all three
criteria PASS, including a tamper harness and a live Step-0 mismatch) and
[`docs/PRD_commit_reveal.md`](docs/PRD_commit_reveal.md).

---

## Quality gates

Segal §19.1 Table 5 is enforced, not aspired to. Every command below runs offline.

```bash
uv run pytest --cov=pursuit --cov=training   # tests + coverage (floor 85%)
uv run ruff check .                          # lint (0 violations required)
bash scripts/check_line_limit.sh             # every file <= 150 code lines
uv run python scripts/check_local_truth.py   # rules 8-9 firewall
uv run python scripts/check_no_llm_in_strategy.py  # rule 25 firewall
uv run python scripts/check_submission.py    # 86 submission rows, re-derived
uv lock --check                              # the lockfile is current
```

Measured 2026-08-17: **2366 passed, 0 failed**, coverage **97.44%**, ruff **0** violations,
line-limit **0** violations, local-truth firewall OK over 7 modules, rule-25 firewall OK.
Every one of those numbers is reproducible by running the commands above — they are quoted
here so a stale claim can be caught, not so they can be taken on trust. The same jobs run in CI
([`.github/workflows/quality-gate.yml`](.github/workflows/quality-gate.yml)) and the
150-line check additionally runs as a pre-commit hook.

`scripts/check_submission.py` is deliberately the one gate that **fails**: it re-derives 86
submission requirements from the tree on every run and exits 1 while any remains open, so
the open ones cannot be forgotten. Its verdicts are narrated in
[`docs/SUBMISSION-CHECKLIST.md`](docs/SUBMISSION-CHECKLIST.md).

---

## Companion repository

Rule 49 requires the cop and the thief to be published as **two separate repositories**, each
README linking to the other.

> **Cross-link: NOT PRESENT.** Neither repository has been created or pushed. Nothing in this
> project has been published: there is no remote, and `git tag -l` is empty. The two URLs are
> `null` in `config/<role>/league.json`, each with a cited reason, and a guessed
> `github.com/...` literal would be an invented value shipped inside a grader-facing
> artifact. The link is filled in when a human creates both repositories (plan 08-12) — and
> `scripts/check_submission.py` reports the slot as open until then, so it cannot ship empty
> and unnoticed.

---

## Documentation map

| Document | What it is |
|---|---|
| [`docs/RULES.md`](docs/RULES.md) · [`docs/PARAMETERS.md`](docs/PARAMETERS.md) | The game and protocol rules, and every numeric value with its fixed/minimum/negotiable status — both extracted from the course book |
| [`docs/SEGAL_GUIDELINES.md`](docs/SEGAL_GUIDELINES.md) | The engineering standard this repository is graded against |
| [`docs/PRD.md`](docs/PRD.md) · [`docs/PLAN.md`](docs/PLAN.md) · [`docs/TODO.md`](docs/TODO.md) | Project-level requirements, design and task tracking |
| `docs/PRD_<mechanism>.md` | One PRD per algorithm or central mechanism (§2.3) — the matrix mover, commit-reveal, the belief map, the scent map, deception, the MCP transport, the gatekeeper, the log/result artifacts, the display belief |
| [`docs/PRD_rl_strategy.md`](docs/PRD_rl_strategy.md) | **Superseded** — the withdrawn run-1 design, retained under a banner because deleting a reversal hides it |
| [`docs/phases/`](docs/phases/) | A PRD/PLAN/TODO triplet per phase, plus each phase's `GATE-N-MEASUREMENT.md` |
| [`docs/STRATEGY.md`](docs/STRATEGY.md) · [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md) | Strategy design notes and project orientation |
| [`docs/SUBMISSION-CHECKLIST.md`](docs/SUBMISSION-CHECKLIST.md) | The submission audit's narrated register, gap by gap |

---

## Contributing

This is a university final project, built solo, published so it can be read, run and graded.
Pull requests are not expected — but every gate above is reproducible by anyone who clones
it, which is the point.

The working standard, the setup steps, the commit conventions and the review checklist are
in **[CONTRIBUTING.md](CONTRIBUTING.md)**. The two rules worth repeating here: `uv` is
mandatory, and a file over 150 code lines is **split, never compressed** — the pre-commit
hook enforces it and `--no-verify` is not an option.

---

## Licence

A licence file is prepared at **[LICENSE](LICENSE)** and **has not been adopted**.

The file carries a `PREPARED, NOT ADOPTED` block at the top. Choosing a licence is a legal
declaration about the owner's own coursework, so the text below that block (the conventional
academic MIT default) takes effect only once the repository owner confirms the licence, the
copyright-holder line and the year. Until then, treat this repository as **all rights
reserved**. `pyproject.toml` points at the file rather than declaring an SPDX string, so the
caveat travels with the package metadata instead of being contradicted by it. The open
question is tracked as `OQ8-5` in
[`docs/SUBMISSION-CHECKLIST.md`](docs/SUBMISSION-CHECKLIST.md).

---

## Credits and acknowledgements

**Author:** Khaled Manaa — University of Haifa, *Orchestration of AI Agents*, final project.
Team code `khm-mn17`.

**Course and specification:** Dr. Yoram Segal — the game specification
(`police_thief_p2p.pdf`, book v3.0.0) and the software submission guidelines
(`software_submission_guidelines-V3.pdf`, v3.00). Every rule and every number in this
repository is traceable to one of those two documents through
[`docs/RULES.md`](docs/RULES.md) and [`docs/PARAMETERS.md`](docs/PARAMETERS.md); nothing
numeric was invented.

**Third-party software**, all pinned in `uv.lock`: [FastMCP](https://gofastmcp.com) (the MCP
peer layer), [`anthropic`](https://github.com/anthropics/anthropic-sdk-python) (hint decoding
and bluff composition only — never move selection), `google-api-python-client` /
`google-auth` (send-only Gmail reporting), `httpx`, `pyngrok` (tunnelling), `psutil`, and the
development toolchain `pytest`, `pytest-cov`, `ruff`, `matplotlib` and
[`uv`](https://docs.astral.sh/uv/).

**Tooling disclosure.** Parts of this repository were written with AI coding assistance under
the author's direction and review; the prompts and their revisions are logged for the
submission audit.
