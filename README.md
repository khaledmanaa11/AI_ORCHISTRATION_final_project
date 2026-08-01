# P2P Cops-and-Robbers — Cop & Thief Agents

Two autonomous AI agents — a **cop** and a **thief** — that play a distributed
cops-and-robbers match on a 7×7 grid over a peer-to-peer network with **no central server
and no referee**. Final project for *Orchestration of AI Agents* (University of Haifa).
Each agent is a symmetric [FastMCP](https://gofastmcp.com) peer (server + client) that
decides moves with a trained tabular **Q-learning** policy (Bayes + BFS fallback),
communicates through deceptive natural-language hints and a decaying scent trail, and
proves honesty via SHA-256 commit-reveal — then competes in a league against other teams'
agents.

## Status

Built in 8 phases, mirroring the book's build order (§10.3). See
[docs/TODO.md](docs/TODO.md) and [.planning/ROADMAP.md](.planning/ROADMAP.md) for the
live phase-by-phase status.

| Phase | What it delivers |
|---|---|
| 1 | Base game logic — grid, movement, barrier quota, capture |
| 2 | FastMCP P2P infrastructure — two processes, localhost |
| 3 | Strategy module (Q-learning policy), playing blind *(in progress — this README's [Learning Curves](#learning-curves-phase-3-rule-42) section)* |
| 4 | Language & scent — hints, pheromones, deception |
| 5 | Cloud exposure and tunneling |
| 6 | Security — commit-reveal, nonce, Step-0 |
| 7 | Reporting shell — Gmail API, live GUI, replay viewer |
| 8 | Submission — two cross-linked repos, tag, league games |

## Documentation

- [docs/RULES.md](docs/RULES.md) / [docs/PARAMETERS.md](docs/PARAMETERS.md) — the game/protocol
  rules and every numeric game value (both extracted from the book, `police_thief_p2p.pdf`)
- [docs/SEGAL_GUIDELINES.md](docs/SEGAL_GUIDELINES.md) — the engineering standard this repo is
  graded against
- [docs/PRD.md](docs/PRD.md) · [docs/PLAN.md](docs/PLAN.md) · [docs/TODO.md](docs/TODO.md) —
  project-level requirements/design/task tracking
- [docs/PRD_rl_strategy.md](docs/PRD_rl_strategy.md) — the Phase-3 Q-learning mechanism contract
  (state encoding, reward, update rule, fallback, training regime, evaluation bar)
- [docs/phases/](docs/phases/) — per-phase PRD/PLAN/TODO triplets

## Development

```bash
uv sync                          # install dependencies (uv only — see CLAUDE.md)
uv run pytest --cov=pursuit --cov=training   # tests + coverage (>= 85%)
uv run ruff check .              # lint (0 violations required)
bash scripts/check_line_limit.sh # every source/test file <= 150 code lines
```

Copy `.env-example` to `.env` and fill in real values before running anything that reads
secrets (`os.environ.get()` only — never hardcoded, per project rule 4).

## Learning Curves (Phase 3, rule 42)

Rule 42 makes learning curves a mandatory, graded README section. `training/curves.py`
appends one row per role (`episode, epsilon, alpha, mean_reward, winrate_vs_baseline,
fallback_rate, role`) from **episode 1 of run 1** — instrumentation is not retrofitted onto
an already-running job (D-16). `training/plot_curves.py` renders the PNGs below and computes
the E6 convergence verdict; run it yourself with:

```bash
uv run python training/plot_curves.py <artifacts_dir>/curves.csv <outdir>
```

Cop and thief are always plotted and judged **separately**, never averaged into one line or
one verdict — averaging would hide one role converging while the other stays random (D-25).

### Evaluation bar (configured, `config/police/strategy.json` / `config/thief/strategy.json`)

| Quantity | Configured value | Meaning |
|---|---|---|
| `win_rate_margin` | 0.10 | Q-policy must beat `HeuristicBrain` by at least this margin (E5), and the final-decile mean win-rate must exceed the first-decile mean by at least this margin (E6) |
| `min_win_rate_absolute` | 0.55 | Absolute win-rate floor, guards against a trivially weak baseline (E5) |
| `eval_games` | 200 per arm, per role | 20 scenarios × 10 seeds each ([docs/phases/phase-3](docs/phases/phase-3/)) |
| `convergence_window` / `convergence_tolerance` | 20000 episodes / 0.02 | The trailing win-rate drift must fall within this bound for the curve to count as flattened (E6) |
| `episodes` | 300000 | Overnight training run length |
| `seed` | 1337 | Logged with every run for reproducibility (training and eval both) |

### Cop

**Win rate vs baseline (ε schedule, secondary axis):**
`artifacts/curves/winrate_cop.png` — *pending: the overnight training run (phase-3 plan
03-10) has not executed yet. This plan (03-09) ships the instrumentation and rendering code;
03-10 runs training and fills in this figure and the measured numbers below.*

**Mean reward:** see the shared [mean-reward figure](#mean-reward-both-roles) below.

**Measured win rate vs `HeuristicBrain`:** *pending (03-10)* — must be ≥ baseline +
`win_rate_margin` (0.10) and ≥ `min_win_rate_absolute` (0.55) over `eval_games` (200) games.

**E6 convergence verdict:** *pending (03-10)* — `training.curve_analysis.check_convergence`
computed against the real run's `curves.csv`.

### Thief

**Win rate vs baseline (ε schedule, secondary axis):**
`artifacts/curves/winrate_thief.png` — *pending (03-10), same reason as the cop figure above.*

**Mean reward:** see the shared [mean-reward figure](#mean-reward-both-roles) below.

**Measured win rate vs `HeuristicBrain`:** *pending (03-10)* — same bar as the cop: ≥ baseline
+ `win_rate_margin` (0.10) and ≥ `min_win_rate_absolute` (0.55) over `eval_games` (200) games.

**E6 convergence verdict:** *pending (03-10)*.

### Mean reward (both roles)

`artifacts/curves/mean_reward.png` — *pending (03-10)*. One figure, one separately-labelled
line per role (never averaged together, D-25).

No number above this line has been measured — every win-rate and convergence value in this
section is a **configured bar**, not a result, until phase-3 plan 03-10's overnight run
completes and this section is updated with the real figures and numbers.
