# Engineering Standard — Segal Software Guidelines V3

> Source: `software_submission_guidelines-V3.pdf` — *"Guidelines for Writing Professional
> Software at the Highest Level of Excellence"*, Dr. Yoram Segal, v3.00, 2026-03-26.
>
> **This is a second binding document, separate from the game rulebook.** The rulebook
> ([RULES.md](RULES.md)) governs *what the agents do*; this governs *how the code is
> written*. Both apply.

## How binding is it?

§19 states it plainly: the document sets a very high bar, **not every section is mandatory
in full, but the more criteria you meet, the higher the quality assessment.** So this is a
graded rubric rather than the rulebook's pass/fail disqualification model — with one
exception: **Table 5 below is the hard summary**, and several of its rows are
automatically checked.

§19 also explicitly endorses using LLM tools and AI agents to help build and test the
project. Using GSD is sanctioned, not a workaround.

---

## Table 5 (§19.1) — The enforcement gate

| Rule | Threshold | Enforced by |
|---|---|---|
| SDK architecture | All logic through the SDK layer | Code review |
| OOP / no duplication | Extract at 2+ copies | Code review |
| API gatekeeper | Every external call goes through it | Code review + test |
| Rate limits | In configuration, never in source | Config check |
| Overflow handling | Queue, never crash | Integration test |
| Version control | Starts at 1.00 | Version module |
| TDD | Red → green → refactor | Work process |
| **File size** | **≤ 150 lines** | **Automatic check** |
| **Linter** | **0 Ruff violations** | **`ruff check`** |
| **Test coverage** | **≥ 85%** | **`pytest --cov`** |
| **Hardcoded values** | **0 in source** | Code review |
| **Secrets** | **`.env-example` + 0 in source** | **Automatic scan** |
| **Package manager** | **Everything through `uv`** | **Automatic check** |

The bolded rows are machine-checkable. Treat them as a pre-commit gate.

---

## 1. Mandatory project structure (§2)

### README.md at repo root (§2.1)
Written to full **user-manual** standard, containing:
installation instructions (prerequisites, step-by-step, environment setup, troubleshooting)
· usage instructions (running in different modes, flags, CLI/GUI, typical workflow)
· examples and code samples, screenshots, common use-cases
· configuration guide · contribution guidelines · license & credits.

### docs/ — mandatory (§2.2)

| File | Contents |
|---|---|
| `docs/PRD.md` | Context, user problem, target audience, market analysis · goals, KPIs, acceptance criteria · functional and non-functional requirements, user stories, use-cases · assumptions, dependencies, explicit out-of-scope items · timeline and milestones with expected deliverables |
| `docs/PLAN.md` | C4 model diagrams (Context, Container, Component, Code) · UML for complex processes, deployment diagrams · architecture decisions (ADRs) with rationale, trade-offs and alternatives · API documentation, interfaces, data schemas, contracts |
| `docs/TODO.md` | Detailed task list with priorities and status (not started / in progress / done) · split into phases with milestones · owner per task · definition of done per task |

### Per-mechanism PRDs (§2.3) — "critical requirement"
**Every specific algorithm, central mechanism, or complex technical component needs its own
separate PRD**, named `docs/PRD_<mechanism>.md`. Each contains a detailed description
including theoretical background, specific requirements, expected input/output, performance
metrics, constraints, alternatives considered and why this one was chosen, plus success
criteria and specific test scenarios.

For this project that implies at minimum:

- `docs/PRD_rl_strategy.md` — the Q-Learning policy
- `docs/PRD_commit_reveal.md` — the cryptographic protocol
- `docs/PRD_scent_map.md` — pheromone emission and decay
- `docs/PRD_belief_map.md` — Bayesian belief update
- `docs/PRD_mcp_transport.md` — the FastMCP peer layer
- `docs/PRD_gatekeeper.md` — rate limiting and reporting
- `docs/PRD_deception.md` — the LLM hint/bluff layer

### Recommended layout (§2.4)

```
project-root/
├── src/
│   └── <package>/
│       ├── __init__.py
│       ├── sdk/            # SDK layer — single entry point
│       │   └── sdk.py
│       ├── services/       # Business logic
│       ├── shared/
│       │   ├── gatekeeper.py
│       │   ├── config.py
│       │   └── version.py
│       └── constants.py
│   └── main.py
├── tests/
│   ├── unit/
│   └── integration/
├── docs/                   # MANDATORY
│   ├── PRD.md
│   ├── PLAN.md
│   ├── TODO.md
│   └── PRD_<mechanism>.md
├── config/
│   ├── setup.json
│   └── rate_limits.json
├── data/ · results/ · assets/ · notebooks/
├── README.md               # MANDATORY
├── pyproject.toml
├── uv.lock
├── .env-example
└── .gitignore
```

### Mandatory work process (§2.5)
1. Write `docs/PRD.md` — **approve before continuing**
2. Write `docs/PLAN.md` — architectural design
3. Write `docs/TODO.md` — task list
4. Write a dedicated PRD for every algorithm / central mechanism
5. **Approve all documents before development begins**
6. Begin development — keep `TODO.md` updated with progress
7. Save results, produce visualizations, update `README.md`

## 2. Code structure (§3)

- **≤ 150 lines per file**, excluding blank lines and comments. When a file exceeds the
  limit, **split it into more files — never compress code to fit.** Split strategies:
  extract helper functions, extract a mixin, 50/50 split on two logical halves
  (read/write), extract constants to `constants.py`, extract models to their own file.
- Docstrings on every function, class, and module. Comments explain the **why**, not the
  what — design decisions, assumptions, preconditions, and they are updated with the code.
- Descriptive variable and function names · short functions with a single responsibility ·
  DRY · consistent style project-wide.

## 3. SDK architecture and OOP (§4)

```
External Consumers (GUI / CLI / REST / Third Party)
        ↓
    +---------+
    |   SDK   |  ← Single entry point for ALL logic
    +---------+
        ↓
    Domain Services  ← services, models, orchestrators
        ↓
    Infrastructure   ← DB, file I/O, external APIs
```

- Every business function is exposed through the SDK class.
- **No business logic in the GUI, CLI, or scripts** — those are thin shells over the SDK.
- External consumers can import the SDK and drive every operation without touching
  internal modules.
- OOP, no code duplication. The same function body in two files, the same `try/except`
  pattern in three, an identical method in three classes, or repeating logic with slight
  variations → extract into a shared module, base class, mixin, or Template Method.
- **Mixin rules:** one concern each · never override each other's methods · independently
  testable.

## 4. API Gatekeeper (§5)

Every external API call must pass through a **central gatekeeper**.

```python
class ApiGatekeeper:
    """Centralized API call manager."""
    def __init__(self, config: RateLimitConfig): ...
    def execute(self, api_call, *args, **kwargs):
        """Check rate limits → queue if limited → retry transient failures → log all."""
    def get_queue_status(self) -> QueueStatus: ...
```

- **No direct API calls that bypass the gatekeeper.**
- Rate limits are read from configuration, **never** hardcoded (`config/rate_limits.json`):
  `requests_per_minute: 30` · `requests_per_hour: 500` · `concurrent_max: 5` ·
  `retry_after_seconds: 30` · `max_retries: 3`
- On overflow: **FIFO queue, not rejection and not a crash.** Queue depth from config,
  backpressure alert when full, drain mechanism when the rate window reopens.
- All calls logged for monitoring.

> Note the overlap with the game rulebook's Gatekeeper (§9.3.1: quota manager → token
> bucket → DOS detector). Build **one** gatekeeper satisfying both — the rulebook's
> numeric thresholds live in [PARAMETERS.md](PARAMETERS.md) Table 19, and where the two
> documents differ, take the stricter value.

## 5. TDD and testing (§6)

- **Red → green → refactor.** Tests written **before** or alongside the code, never as an
  afterthought.
- Every new module has a matching test file. Every public function/method has at least one
  test. Tests cover the **happy path and the error case**.
- Test layout mirrors `src/`: `tests/unit/test_<module>/test_<file>.py`,
  `tests/integration/test_<feature>.py`, shared fixtures in `conftest.py`.
- Mock external dependencies (database, files, API). **No test depends on an external
  service.**
- **Test files obey the 150-line rule too.**
- **Coverage ≥ 85% globally** — the suite must fail below it:
  ```toml
  [tool.coverage.run]
  source = ["src"]
  omit = ["src/main.py", "*/tests/*", "src/**/gui/*"]

  [tool.coverage.report]
  fail_under = 85
  ```
  Required coverage kinds: statement, branch, and path coverage for critical routes.
- Edge cases documented with a description and a screenshot where relevant; error handling
  must include graceful degradation, clear messages, and detailed logs.

## 6. Linting and configuration (§7)

**Zero Ruff violations.** `ruff check` must pass clean.

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]
```

`E` PEP 8 errors · `F` Pyflakes · `W` PEP 8 warnings · `I` import sort · `N` naming ·
`UP` pyupgrade · `B` bugbear · `C4` comprehensions · `SIM` simplification.

### No hardcoded values (§7.2)

| Category | Wrong | Right |
|---|---|---|
| API address | `"https://api.example.com"` | `cfg.get("api_url")` |
| Rate limit | `rate_limit = 10` | `cfg.get("rate_limit", 10)` |
| Timeouts | `timeout=60` | `cfg.get("timeout", 60)` |
| Secrets | `api_key = "abc123"` | `os.environ.get("API_KEY")` |

Permitted in code: physical/mathematical constants, default parameter values, entries in
`constants.py`, and `Enum` members.

### Configuration hierarchy (§7.3)
`config/setup.json` (versioned) · `config/rate_limits.json` (versioned) ·
`config/logging_config.json` · `.env` (git-ignored) · `.env-example` (committed) ·
`pyproject.toml` · `src/<package>/constants.py`.

### Secrets (§7.4)
No secret data in the project. Never store API keys, passwords, or tokens in source — use
`os.environ.get("API_KEY")` only. `.gitignore` **must** include `.env`, `*.key`, `*.pem`,
`credentials.json`. `.env-example` must exist with dummy values. Rotate keys periodically,
monitor usage, and grant minimum permissions.

## 7. Versioning and `uv` (§8)

Version tracking starts at **1.00** and rises on meaningful change, in three places:

| Item | Location | Initial |
|---|---|---|
| Code version | `src/<pkg>/shared/version.py` | 1.00 |
| Config version | `"version"` key in the JSON | 1.00 |
| Rate-limit version | `rate_limits.version` | 1.00 |

The application validates config-version compatibility at startup.

### uv is mandatory (§8.4)

| Task | Correct | **Forbidden** |
|---|---|---|
| Install dependencies | `uv sync` | `pip install` |
| Add a dependency | `uv add <pkg>` | `pip install <pkg>` |
| Run a script | `uv run python script.py` | `python script.py` |
| Run tests | `uv run pytest tests/` | `python -m pytest` |
| Lock dependencies | `uv lock` | `pip freeze` |

`pyproject.toml` is the single source of dependency truth (**no `requirements.txt`**).
`uv.lock` exists and is committed. No direct `pip` or `python -m` calls anywhere — in code,
scripts, CI/CD, or documentation. Every tool runs through `uv run`.

### Prompt Engineering Log (§8.3)
Because development uses AI agents, maintain a documented log of the significant prompts
used to build the project — context, goal, sample outputs received, iterative refinements,
and practices that proved effective.

## 8. Packaging and design (§14, §16)

- `pyproject.toml` (preferred over `setup.py`) with name, description, author, version,
  license, dependencies.
- `__init__.py` in the root package and **every** sub-package; use it to export the public
  interface via `__all__` and to define `__version__`.
- **Relative imports only** — never absolute paths. File read/write is relative to the
  package path.
- Every building block documents its **Input data** (types, valid ranges, external
  dependencies, validation), **Output data** (types, format, edge-case behaviour), and
  **Setup data** (parameters with defaults, configuration, initialization).
- Design principles: single responsibility · separation of concerns · reusability
  (independent of specific code) · testability (dependency injection).

## 9. Concurrency (§15)

- **Multiprocessing** for CPU-bound work (intensive computation, image processing, model
  training) — each process gets its own memory and core.
- **Multithreading** for I/O-bound work (network calls, database access, file I/O).
- Thread safety is critical: protect shared variables with locks, use `queue.Queue` for
  handing data between threads, avoid mutual locking, use context managers.

## 10. Final checklist (§17)

**Structure & documentation** — comprehensive root README at user-manual level · `docs/`
with PRD.md, PLAN.md, TODO.md · dedicated PRDs per algorithm/mechanism · architecture
documentation with clear diagrams · documented prompt log.

**Architecture & code** — SDK architecture, all business logic through the SDK · OOP with
no duplication, inheritance and mixins · API gatekeeper for all external calls · rate
limits from config, queue management · files ≤150 lines, comments and docstrings ·
consistent style, descriptive names.

**Testing & quality** — TDD, tests written before/with the code · coverage ≥85% · zero Ruff
violations · edge-case documentation and error handling · automated test reports.

**Configuration & security** — separate versioned config files · `.env-example` with dummy
values · no API keys or secrets in code · updated `.gitignore` · `uv` as the sole package
manager · `pyproject.toml` and `uv.lock` present.

**Research & visualization** — systematic experiments varying parameters · documented
sensitivity analysis, analysis notebook with graphs · quality graphs, screenshots,
architecture diagrams · token-cost analysis and optimization strategy.

**Extensibility & standards** — documented extension points · professional Python packaging
· parallel processing with thread safety · building-block design · ISO/IEC 25010 compliance
· orderly Git history, license, credits, deployment instructions.

## 11. Quality model (§13)

ISO/IEC 25010 — eight characteristics: functional suitability · performance efficiency ·
compatibility · usability · reliability · security · maintainability · portability.
