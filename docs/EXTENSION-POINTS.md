# Extension points — where this system is meant to be changed

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-08-17 · **Plan:** 08-07
**Covers:** §17 group 6 "documented extension points" · **Related:**
[ARCHITECTURE.md](ARCHITECTURE.md), [QUALITY-25010.md](QUALITY-25010.md)

> **A seam is only an extension point if adding an implementation requires editing
> nothing else.** Each of the five below is one interface, one registration site, and one
> config key — and each is already exercised by more than one implementation in the tree,
> which is the only honest evidence that a seam is real rather than aspirational.
>
> `tests/unit/test_quality_docs_contract.py` re-derives the registered brains from
> `src/pursuit/strategy/registry.py` and fails when this document names a brain the
> registry does not hold, or omits one it does. Every path below must exist in
> `git ls-files`.

---

## 1. `BrainBase` — the move policy

| | |
|---|---|
| **Contract** | `src/pursuit/strategy/base.py` — `BrainBase._pick_move` and `_decide_move`, plus the frozen `Observation` / `Decision` data contracts |
| **Registration** | `src/pursuit/strategy/registry.py`, an explicit name → class dict |
| **Selection** | `config/police/strategy.json` → `strategy.police_class` (thief: `config/thief/strategy.json`) |
| **Implementations today** | `ValueSearchBrain` (the shipped matrix-game mover), `ChaserCop` and `GreedyEvader` (the fixed sparring anchors in `src/pursuit/strategy/naive.py`) |
| **Proof the seam works** | `tests/integration/test_strategy_pluggable.py` swaps the brain through config alone |

**To add a brain:** implement `BrainBase` in a new module under `src/pursuit/strategy/`,
add one entry to the registry dict, and name it in a config file. Nothing in
`src/pursuit/network/` changes.

**Resolution goes through an explicit dict, never `eval`, `exec` or an unguarded
`importlib` call on a config string** — that is stated in the registry's own docstring and
it is a security boundary, not a style choice: this project ships config alongside the
agent, so a config file naming an arbitrary importable would be an arbitrary-code-execution
path.

**Two constraints an implementer must not break.** `Decision.source` carries provenance as
a data field and must be set truthfully — never defaulted to a value the brain did not
produce. And nothing under `src/pursuit/strategy/` may import anything that can reach a
language model: `scripts/check_no_llm_in_strategy.py` AST-walks the package and fails on an
import of `pursuit.services`, `subprocess`, `socket` or an HTTP client. **The algorithm
decides the move; the model never does** (rule 25).

## 2. `Provider` — the language-model backend

| | |
|---|---|
| **Contract** | `src/pursuit/services/llm/provider.py` — a `Protocol`, so an implementation inherits nothing |
| **Registration** | `register_provider(name, cls)`, called by each provider at the bottom of its own module; importing the package `src/pursuit/services/llm/__init__.py` populates the registry as a side effect |
| **Selection** | `config/police/language.json` |
| **Implementations today** | `AnthropicProvider` (`src/pursuit/services/llm/anthropic_provider.py`) and `TemplateProvider` (`src/pursuit/services/llm/template_provider.py`), which never touches a network |
| **Proof the seam works** | `tests/integration/test_llm_degradation.py` runs the whole pipeline through provider failure |

**The contract a new provider must honour is the failure contract.** Every failure is
**returned** as an `LlmFailure` with a reason from a closed vocabulary — never raised. The
`UNKNOWN` reason is the floor: `anthropic_provider.py`'s final `except Exception` still
degrades to a value. A provider that raises breaks the caller's degradation path, and
`src/pursuit/services/llm/bluff.py` contains a defensive arm for exactly that.

**A provider never calls the API directly.** Every external call goes through
`src/pursuit/services/llm/gatekeeper.py`, whose limits come from config. That is Table 5's
API-gatekeeper row, and there is no carve-out.

## 3. `MailSink` — the outgoing report transport

| | |
|---|---|
| **Contract** | `src/pursuit/services/reporting/sink.py` — a runtime-checkable `Protocol` with one `async send(report) -> SendReceipt` |
| **Injection** | `ReportingChain` takes its sink as an injected callable **with no default** |
| **Selection** | `config/police/reporting.json` → `reporting.mode` (`dry_run` or `live`) |
| **Implementations today** | `DryRunSink` (writes the report and the `.eml` and transmits nothing) and `GmailSink` (`src/pursuit/services/reporting/gmail_sink.py`) |
| **Proof the seam works** | `tests/integration/test_end_of_game_reporting.py`, plus `tests/unit/test_gmail_sink.py` driving the live sink with an injected fake transport |

**`SendReceipt` is never a bare bool**, on purpose: a dry run's evidence is the two paths
it wrote and a live send's is the id the API returned, and a caller that cannot tell them
apart cannot report honestly.

**A sink must raise on failure.** Raising is how the gatekeeper's retry ladder is told to
back off; a sink that swallows a failure and returns a receipt would report a delivery that
never happened — which under rules 32/35 costs both teams the game.

**Status, stated plainly: every shipped config reads `dry_run`, and nothing has ever been
delivered.** The single supervised live send is 07-10's open human checkpoint.

## 4. `ResolutionRules` — the two negotiated terminal predicates

| | |
|---|---|
| **Contract** | `src/pursuit/shared/resolution.py`, consumed by `src/pursuit/sdk/terminal.py` |
| **Selection** | `config/police/resolution.json` — `capture_on_barrier_race`, `capture_on_swap` |
| **Proof the seam works** | `tests/unit/test_resolution_config.py` and the predicate tests around `src/pursuit/sdk/terminal.py` |

Six terminal predicates decide a joint turn. Four are **unconditional book rules and are
not extension points** — changing them would change the game. Exactly two are *negotiated*
between the teams before a series, and only those two are config-gated.
`docs/phases/phase-3/RULES-RESOLUTION.md` §3 lists all six with their sourcing and §5
explains how the two negotiated rows are agreed without breaking the config-digest
handshake.

**This is the seam most likely to be abused.** A fixed value from `docs/PARAMETERS.md` must
never migrate into this file to make a game easier to win.

## 5. `handshake_handler` — the MCP tool surface

| | |
|---|---|
| **Contract** | `src/pursuit/network/tools.py` — `register_tools(mcp, queue, handshake_handler=...)` |
| **Wiring** | `src/pursuit/network/agent_wiring.py` supplies the real handler |
| **Proof the seam works** | `tests/integration/test_peer_roundtrip.py` and `tests/integration/test_game_id_negotiation.py` |

Nine `@mcp.tool` handlers attach to a server through one call. Every handler is `async` and
**enqueues and returns immediately**: a handler that blocked waiting on this agent's own
outgoing call would deadlock both peers. A new message type is an additive `MessageType`
member and a new handler — never a reshape of the four-key `Envelope` (D-06, frozen since
Phase 2).

**The seam is load-bearing rather than decorative.** With no handler supplied, the
handshake tool returns a generic stub ack that carries no sender, payload or digest and
cannot decode as an `Envelope` — so an unwired handshake would abort every real
peer-to-peer game before move 1.

---

## What is deliberately *not* an extension point

| Not extensible | Why |
|---|---|
| The `Envelope` shape | frozen at four keys since Phase 2 (D-06); every new wire kind is an additive `MessageType` member |
| The commit hash recipe | `src/pursuit/security/commit_pack.py` — one canonicalisation for the whole project, shared with the config and scent digests. Two recipes is two protocols |
| Anything in `src/pursuit/gui/` | `pyproject.toml` omits `*/gui/*` from coverage, so logic placed there is invisible to the `fail_under = 85` gate. `tests/unit/test_gui_structural.py` enforces it structurally |
| Anything in `scripts/` | `scripts/check_line_limit.sh` scans `src/`, `tests/` and `training/` only, so logic parked in `scripts/` escapes **both** the size gate and coverage |
| Any value marked **fixed** in `docs/PARAMETERS.md` | deviation is a disqualification. Minimum values may be negotiated upward, never downward |
| The withdrawn tabular Q-learner | superseded, not merely replaced — `docs/PRD_rl_strategy.md` carries a DO-NOT-IMPLEMENT banner pointing at `docs/PRD_matrix_mover.md`, because simultaneous play made it unsound here |
