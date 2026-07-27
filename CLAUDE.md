# Project Standing Rules

Final project for *Orchestration of AI Agents* (University of Haifa): two autonomous
agents — a **cop** and a **thief** — playing a distributed cops-and-robbers match over a
peer-to-peer network with no central server and no referee.

**Every agent working in this repo follows the rules below.** They are not suggestions.

## Two binding documents

| Document | Governs | Extract |
|---|---|---|
| `police_thief_p2p.pdf` (Segal, book v3.0.0) | **What the agents do** — game rules, protocol, league | [docs/RULES.md](docs/RULES.md), [docs/PARAMETERS.md](docs/PARAMETERS.md) |
| `software_submission_guidelines-V3.pdf` (Segal, v3.00) | **How the code is written** — engineering standard | [docs/SEGAL_GUIDELINES.md](docs/SEGAL_GUIDELINES.md) |

**Read the extracts, not the PDFs.** Both source documents are in Hebrew and have already
been translated and structured. If an extract seems to contradict the PDF, say so — do not
silently re-derive.

Orientation: [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md) · Strategy design:
[docs/STRATEGY.md](docs/STRATEGY.md)

---

## Never do these — each one is a disqualification

1. **Never invent a numeric value.** Every number comes from
   [docs/PARAMETERS.md](docs/PARAMETERS.md). Values marked **fixed** disqualify the team on
   any deviation; **minimum** values may be negotiated upward, never downward. If a number
   you need is not in that file, stop and ask.
2. **Never share runtime state between the cop and the thief.** They run as two separate
   processes under `config/police/` and `config/thief/`. No shared memory, no shared live
   state module, no shared variables. A shared *library* is fine; a shared *game state
   object* is disqualification for information leakage (rule 2).
3. **Never display the true board state in the live GUI.** Only local truth. This is the
   tempting debugging shortcut and it disqualifies the project (rules 8–9).
4. **Never commit secrets.** No API keys, tokens, or credentials in source or in git —
   `os.environ.get()` only (rules 39–40).
5. **Never let the language model choose a move.** The algorithm decides. The LLM only
   decodes incoming hints and writes outgoing bluff text (§6.2, rule 25).
6. **Never lie in a capture declaration or a barrier declaration**, and never misreport the
   number of games played (rules 16, 22, 38).

Full list with sanctions: [docs/RULES.md](docs/RULES.md), including a ranked
"cheapest ways to score zero".

## Code standard — enforced

From [docs/SEGAL_GUIDELINES.md](docs/SEGAL_GUIDELINES.md) §19.1 Table 5. The first five are
machine-checkable; treat them as a pre-commit gate.

| Rule | Threshold |
|---|---|
| File size | **≤ 150 lines** (excluding blanks/comments) — **split files, never compress code to fit** |
| Linter | **`ruff check` → 0 violations** |
| Test coverage | **`pytest --cov` → ≥ 85%** (`fail_under = 85`) |
| Secrets | **0 in source**, `.env-example` committed with dummy values |
| Package manager | **`uv` only** |
| Hardcoded values | 0 in source — config, `constants.py`, or `Enum` |
| SDK architecture | All business logic behind the SDK layer; GUI/CLI are thin shells |
| No duplication | Extract at 2+ copies into a shared module, base class, or mixin |
| API gatekeeper | Every external call goes through it; limits from config; overflow queues, never crashes |
| TDD | Red → green → refactor; tests before or alongside code |
| Versioning | Starts at 1.00, tracked in `version.py` and config files |

### uv is mandatory — never call pip or python directly

| Task | Use | **Never** |
|---|---|---|
| Install | `uv sync` | `pip install` |
| Add dependency | `uv add <pkg>` | `pip install <pkg>` |
| Run | `uv run python script.py` | `python script.py` |
| Test | `uv run pytest tests/` | `python -m pytest` |
| Lock | `uv lock` | `pip freeze` |

`pyproject.toml` is the single source of dependency truth — **no `requirements.txt`**.

### Testing
Every module gets a test file. Every public function gets at least one test covering the
**happy path and the error case**. Mock all external services — no test may depend on a
live network, API, or the opponent. Test files obey the 150-line limit too.

### Documentation is not optional
`docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` are mandatory, plus a dedicated
`docs/PRD_<mechanism>.md` for **every** algorithm or central mechanism (§2.3). Approve the
documents before writing the code they describe (§2.5).

---

## Build order — do not skip ahead

Seven stages from the book (§10.3). Each must run end-to-end before the next is added.
Reaching for cryptography or cloud before stages 1–2 work means a fault in the lower layer
hides behind the one above it.

1. Base logic — grid, movement, barrier quota, capture
2. FastMCP infrastructure — two processes, localhost
3. Strategy module (RL policy), playing blind
4. Language and scent — hints, pheromones, deception
5. Cloud exposure and tunneling (ngrok/Localtonet)
6. Security — commit-reveal, nonce, Step-0
7. Reporting shell — Gmail API, live GUI, replay viewer

Then submission: two cross-linked repos, academic README, Git tag, league games.

## Architecture facts worth not re-deriving

- The protocol is **MCP (Model Context Protocol)** via the **FastMCP** Python library.
  There is no "MCB" — if you see that term anywhere, it is a mistake.
- Each peer is **simultaneously a server and a client**: it exposes tools with `@mcp.tool`
  and calls the opponent's tools. Symmetric — no strong or weak side.
- The decision pipeline is:
  `hint decode → belief update (Bayes) → Q-policy move choice → LLM bluff text → Commit pack`
- Commit-reveal has four phases: **Commit** (hash only) → **Acknowledge** → **Reveal**
  (move + hint, nonce still hidden) → **Final Reveal / Audit** (all nonces at game end).
  Hash input is canonical JSON: `sort_keys=True, separators=(",", ":")`. Nonce from
  `secrets.token_hex(16)`, never `random`. Verify with `secrets.compare_digest`.

## Workflow

This project is built with **GSD**. The roadmap phases mirror the book's seven stages 1:1 —
do not re-derive a phase breakdown. Standard loop per phase:

```
/gsd:discuss-phase N --batch  →  /clear  →  /gsd:plan-phase N  →  /clear
→  /gsd:execute-phase N  →  /gsd:verify-work N
```

Working solo: there are no teammates on this project. Do not assume review by another
person — the quality gates above are the review.

## Per-phase documentation triplet — grader-facing, enforced

Beyond the project-level `docs/PRD.md` · `docs/PLAN.md` · `docs/TODO.md` and the
per-mechanism `docs/PRD_<mechanism>.md`, **every phase keeps its own triplet** at:

```
docs/phases/phase-<N>/PRD.md    — what this phase delivers; its §10.4 milestone gate = acceptance criteria; REQ-IDs covered; phase in/out of scope
docs/phases/phase-<N>/PLAN.md   — how it is built: components, files, interfaces, test plan, phase-specific ADRs, links to per-mechanism PRDs
docs/phases/phase-<N>/TODO.md   — the phase task list with priority, status, owner, definition of done
```

Copy the skeletons from `docs/phases/_TEMPLATE/`. Enforcement across the GSD loop:

- **`/gsd:plan-phase N`** — in addition to the normal `.planning/` plan, **create or refresh
  `docs/phases/phase-<N>/{PRD,PLAN,TODO}.md`**. Approve them before executing (§2.5 step 5).
- **`/gsd:execute-phase N`** — keep `docs/phases/phase-<N>/TODO.md` status current as tasks land.
- **`/gsd:verify-work N`** — **mark every task in `docs/phases/phase-<N>/TODO.md` as `[x]`
  done**, and tick the matching rows in the root `docs/TODO.md`. A phase is **not verified**
  until its triplet exists and all its TODOs are checked.

This is deliberately stronger than Segal §2.2 (which requires only the single project triplet
+ per-mechanism PRDs). It exists so the grader can open `docs/phases/` and see a complete,
checked triplet for **every** phase.
