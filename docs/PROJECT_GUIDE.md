# Project Guide — Distributed Cops-and-Robbers over P2P

Plain-language guide to the final project for *Orchestration of AI Agents*
(University of Haifa). Assumes no prior knowledge. Every term is defined at first use.

Companion files: [RULES.md](RULES.md) (the 55 binding rules) ·
[PARAMETERS.md](PARAMETERS.md) (every number) · [STRATEGY.md](STRATEGY.md) (our strategy module).

---

## Part 0 — Three corrections to the original brief

| Assumption | Reality |
|---|---|
| "MCB (Message-Control-Bridge) server" | No such thing. The protocol is **MCP — Model Context Protocol** — implemented with the **FastMCP** Python library (§2.3). |
| "RL is the required approach" | §6.3 states RL is *"an optional tool only, and not what the course taught,"* that the course never covered RL, and that many teams will win without it. The reference implementation defaults to Bayes + Manhattan heuristics. **We are choosing RL deliberately** — the case is argued in §B below. |
| "Two robots competing against each other" | You build **one cop and one thief**. They must run as separate processes and ship as two separate GitHub repos. In the league your cop plays *another team's* thief, and your thief plays their cop. |

One more, easy to miss: **Gmail API reporting is mandatory, not incidental.** If a report
does not arrive, that game scores zero — even if you won on the board (§9.3, rule 35).

---

# Part 1 — The Brief

## Reinforcement-Learning Justification

The game is formally a **Dec-POMDP** — a Decentralized Partially Observable Markov
Decision Process (§1.3). Unpacked: *decentralized* means two agents decide independently
with no coordinator; *partially observable* means neither can see the true board; *Markov
decision process* means the world moves in discrete steps where each choice changes what
happens next. That is precisely the shape of problem reinforcement learning exists to solve.

Reinforcement learning means an agent learns by doing: it tries an action, receives a
numeric reward, and adjusts its future behaviour to earn more reward. The spec hands us
the reward signal directly — §1.3 says the reward function "translates directly from the
scoring table," so capture (20 points), survival (10), and their counterparts *are* the
training signal. Nothing has to be invented.

The alternative is a hand-written rulebook of if-then heuristics. It works, and it is the
reference default — but it is fixed. A competent opponent watches it for a few turns,
infers the rule, and exploits it. A learned policy can weigh a barrier placed now against
a capture eleven turns later — a trade-off that is painful to hand-code and natural to
express through the discount factor. The spec agrees: whoever picks RL "will build a
thinking opponent," genuinely a case of multi-agent RL where the environment itself
changes as the opponent learns.

## MCP Server Overview

MCP is an open standard for connecting language models to external tools. Each of our two
agents runs a **FastMCP server**, which publishes a set of functions — called **tools** —
that the opponent is allowed to call over the network.

The twist: every agent is **simultaneously a server and a client**. As a server it exposes
tools (receive a move, receive a hint). As a client it calls the *opponent's* tools to send
its own move. There is no strong side and no weak side, and no central referee — the
topology is perfectly symmetric.

Inside each agent: a **PeerRuntime** (the process that plays), an **orchestrator** with a
state machine driving turn order, a pluggable **strategy module** that picks moves, a
**Gatekeeper** that protects outgoing API calls, and a **watchdog** that stops the process
hanging while it waits for an opponent who never replies.

## Tunneling & Crypto Audit

**Tunneling** solves an address problem. Your machine sits behind a home router doing NAT
(Network Address Translation) — it has no address the outside world can dial. A tunneling
tool (**ngrok** or **Localtonet**) opens an outbound connection and hands you a public URL
that forwards back to your local server. Localhost is fine while developing; the league
requires public exposure (rule 10).

**The crypto audit** solves a trust problem. With no referee, what stops a player editing
a move after seeing yours? A **commit-reveal** protocol. First you send only a
**SHA-256 hash** — a short fingerprint of your move that reveals nothing about its content
but cannot be forged. Your opponent locks it in. Only then do both sides reveal the actual
move. At game end, everyone publishes their **nonces** (one-time random values mixed into
each hash) and both logs are re-hashed and compared. Any mismatch is a technical loss —
score zero (rule 19). The cryptography decides, not human argument.

## Construction Guide

Seven stages, each proven end-to-end before the next begins (§10.3):
**1** board and movement rules → **2** FastMCP messaging over localhost → **3** the strategy
module, playing blind → **4** natural-language hints and the decaying scent trail →
**5** tunneling to the public internet → **6** commit-reveal cryptography →
**7** the reporting shell: Gmail, live GUI, replay viewer. Then submission.

---

# Part 2 — The Build Guide

## §A. What you are actually building

Two autonomous agents on a **7×7** grid: a **cop** hunting a **thief**. No central server,
no referee, no shared memory. Each agent holds only its *own* truth and builds a
**belief map** — a probability grid of where the opponent might be — from two information
sources:

- **A scent trail.** Each agent leaves a pheromone in the cells it passes: strength `0.9`
  at the source, decaying `0.10` per turn, over a `5×5` window. This is *involuntary* —
  you cannot choose not to smell. The only counter-play is exploiting it: strengthening
  scent in a cell you are leaving, so the opponent chases where you *were*.
- **Verbal hints.** Each turn, an agent sends the opponent a free-text sentence of at most
  15 words. **These are allowed to be lies** — deception is the one fully voluntary
  information channel in the game.

The cop additionally places barriers (quota 14) to shrink the thief's space. The thief
wins by surviving 35 turns; the cop wins by capture — landing on the thief's cell, walling
it into a cell, or leaving it with no legal move (rules 46–47).

## §B. Why reinforcement learning (expanded)

### The formal hook
The spec defines the game as the tuple `⟨n, S, {A_i}, P, R, {Ω_i}, O, γ⟩` (§1.3):
`n`=2 agents · `S` = full world state · `A_i` = each agent's actions (move, build, communicate)
· `P` = transition function · `R` = reward · `Ω_i`/`O` = each agent's partial observation ·
`γ` = discount factor. That is a reinforcement-learning problem statement written out in
full. Choosing RL is following the formalism the spec already committed to, not bolting
something on.

### The learning rule
Q-Learning keeps a table `Q(s,a)` — the estimated total future reward for taking action `a`
in state `s`. After each move it updates via the Bellman equation (§6.3):

```
Q(s,a) ← Q(s,a) + α [ r + γ · max_a' Q(s',a') − Q(s,a) ]
```

- `Q(s,a)` — current estimate of how good this action is here.
- `r` — the immediate reward, straight from the scoring table.
- `α` (learning rate, 0–1) — how much new evidence overrides old. Too high and the agent
  forgets what worked; too low and it barely learns.
- `γ` (discount factor, 0–1) — how much future reward matters against immediate reward.
  **A high `γ` is exactly what buys strategic patience** — spending three turns building a
  barrier trap that pays off on turn fourteen.
- `max_a' Q(s',a')` — the best reward available from the state we land in.

### Exploration
A policy that always picks the highest-scoring action becomes predictable, and predictable
loses. **ε-greedy** fixes this: with small probability `ε` take a random action, otherwise
take the best known one. This keeps discovering new routes and stops the agent locking into
a loop the opponent can read.

### Why this beats fixed heuristics here
The state space is finite — 7×7 board, two positions, a barrier layout — so a tabular
Q-table is tractable rather than requiring a neural network. And the opponent is not
scenery: it adapts. The spec calls this out as genuine multi-agent RL, where the learning
environment itself shifts as the opponent improves. A frozen heuristic cannot answer that;
a learned policy can.

### Honest engineering notes
These are build constraints, not second thoughts:

- **The environment is non-stationary.** Because the opponent learns too, convergence is
  not guaranteed the way it is against a fixed environment. Budget for this.
- **There is no training phase during a league match.** Train offline first — self-play
  against your own agents, plus the reference implementation — and ship a trained Q-table.
- **Keep a heuristic fallback.** When the Q-table hits a state it has never visited, fall
  back to Bayes + Manhattan rather than acting on a meaningless zero. This is the
  reference default and costs almost nothing to keep alive.
- **Learning curves are a submission requirement** when RL is used (§9.4.2 item 4,
  rule 42). Instrument training from day one; regenerating curves later is painful.

### The hard constraint that survives this choice
**The algorithm decides the move. The language model never does.** (§6.2, rule 25.)
Language models hallucinate and confuse directions and distances; a hallucinated move is an
illegal move and a technical loss. The decision pipeline (§6.2, Figure 7) is:

```
incoming hint + scent → hint decode (parse text) → belief update (Bayes)
    → Q-policy move choice → LLM bluff text (deception) → Commit pack (out)
```

The language model appears exactly twice, at the two ends: decoding the opponent's words on
the way in, and writing our deceptive hint on the way out. The move itself comes from the
Q-policy in the middle.

## §C. The MCP server (and client)

**MCP (Model Context Protocol)** is an open standard for connecting language models to
external tools and data sources. **FastMCP** is the Python library implementing it; a
function becomes a callable tool by adding the `@mcp.tool` decorator.

Each agent runs both halves:

| Role | Responsibility |
|---|---|
| **Server** | Exposes tools the opponent may call — receive a move, receive a hint, answer a geometric query |
| **Client** | Calls the *opponent's* exposed tools to transmit our own move and hint |

Components inside the process:

- **PeerRuntime** — the running agent.
- **Orchestrator + state machine** — enforces turn order and rejects illegal transitions
  (rules 3–5).
- **Strategy module** — pluggable, and deliberately separate from networking. Declared in the
  private config under `[strategy]` as `police_class` / `thief_class` in
  `package.module:Class` form, subclassing `BrainBase` and overriding `_pick_move`
  (plus barrier selection in `_decide_move` for the cop). See [STRATEGY.md](STRATEGY.md).
- **Gatekeeper** — quota manager → token bucket → DOS detector, guarding outgoing mail.
- **Watchdog + deadline tracker** — prevents a hang when the opponent never replies (rules 6–7).

A2A (Agent-to-Agent) and ACP (Agent Communication Protocol) are mentioned in the book as
worth knowing, but **MCP is the requirement** — the others are optional complements.

## §D. Tunneling and environment separation

**The problem.** Most machines sit behind a firewall and a NAT router and have no publicly
reachable address. **The fix.** A tunneling tool (ngrok, Localtonet) performs NAT traversal
and gives your local FastMCP server a public URL, so an opponent anywhere in the world can
reach it (§2.4). Localhost is permitted in early development only; **the league requires a
public address** (rule 10).

**The separation rule (§2.4.2, rules 1–2).** The cop and the thief must run as two separate
processes under separate config directories — `config/police/` versus `config/thief/`.
Sharing memory, a live state module, or variables between your own two agents is
**forbidden**, and the sanction is disqualification for information leakage. The reasoning:
sharing creates a back door through which one agent could see the other's local truth,
breaking the Zero-Trust model the whole architecture rests on — even if the game "works"
technically.

Note this constrains *runtime state*, not *source code*. A shared library is fine; a shared
live game-state object is not.

## §E. The crypto audit

### Why it exists
In a refereeless peer-to-peer game, trust cannot be assumed. Commit-reveal makes cheating
mathematically detectable rather than a matter of argument.

### The four phases (§5.3, Figure 6)

1. **Commit** — send only `H_commit`, the SHA-256 hash of your move. A hash is a one-way
   fingerprint: it proves you had *something* without revealing what. Your move is now
   locked but unknown.
2. **Acknowledge** — the opponent confirms receipt. Neither side can now retract.
3. **Reveal** — both send the actual move and hint. **The nonce stays hidden** — this is
   what prevents reverse-engineering the hash before the final audit.
4. **Final Reveal / Audit** — at game end all nonces are published, both logs are re-hashed,
   and the results compared.

### What gets hashed
The hash covers `{state, move, intent, nonce}`, serialized as **canonical JSON** —
`sort_keys=True, separators=(",", ":")` — so both peers hash byte-identical input. This
detail is not cosmetic: inconsistent serialization is the single most common cause of a
false mismatch, and a mismatch is a loss.

- **`intent`** — a mandatory `truth | lie` flag, declared *in advance*. This is what stops a
  player retroactively claiming they were "honestly lying."
- **`nonce`** — a one-time random value, generated with `secrets.token_hex(16)`, **not**
  `random`. Without it, an opponent could hash all possible moves and match yours by
  brute force (a dictionary attack). Verify with `secrets.compare_digest`.

### Step-0: computational fairness (§5.5)
Before the first move, each side publishes a signed declaration of its OS, CPU cores and
frequency, RAM, GPU/VRAM, language model, code version, and **the exact GitHub commit hash**
the game runs on (rule 53). This keeps a powerful workstation from simply out-searching a
laptop; scoring is normalised so a clever algorithm on modest hardware outranks brute force.

### The iron law
**Any hash mismatch at audit = technical loss, score 0 to the forging team** (rule 19).
There is no room for interpretation or statistical doubt: SHA-256 is sensitive to every bit,
so the smallest change to a move changes the signature completely. The cryptography decides,
not human judgment.

## §F. The seven construction stages

Each stage must run end-to-end before the next is added (§10.3). The gate column is the
book's own milestone test (§10.4).

| # | Build | Milestone gate |
|---|---|---|
| **1** | **Base logic** — grid, movement rules, barrier quota, capture detection. No networking, no AI | Both agents move legally on the grid; a barrier beyond quota is rejected; coordinate overlap triggers capture |
| **2** | **FastMCP infrastructure** — separate processes, geometric tools over localhost, coordinates only | A geometric message sent by agent A over localhost is received and decoded correctly by agent B |
| **3** | **"Blind" strategy module** — the RL policy, with no scent and no natural language yet | Given a known target location, the agent computes and walks the shortest path with no manual intervention |
| **4** | **Language and scent** — free-text hints, pheromone emission and decay, LLM for inference and deception | A hint is translated into an inference; the scent map updates and decays; the LLM emits a hint each turn (true or false) |
| **5** | **Cloud exposure and tunneling** — ngrok/Localtonet, remote machines | An agent on a remote machine connects via tunnel and plays a full round against the local agent |
| **6** | **Security and cryptography** — commit-reveal, nonce, Step-0 | A move is committed and then revealed with a valid nonce; Step-0 hardware declaration verified |
| **7** | **Reporting and visualization shell** — Gmail API via OAuth 2.0, live GUI, Replay App | Game summary sent by mail; the GUI displays state; the Replay App reconstructs a recorded round |

> **Do not skip ahead** (§10.4). Reaching for cryptography or cloud before stages 1–2 run
> end-to-end means a fault in the lower layer hides behind the one above it, and hours
> vanish investigating a cause that does not exist.

## §G. Reporting and the Gatekeeper (stage 7 detail)

At the end of every legal game, **both** agents automatically send a signed JSON report.
Automation here is a blessing and a trap: it guarantees consistent, immediate reporting, but
a bug can start firing thousands of messages a minute at a live mail account.

The mandatory protection chain (§9.3.1, Figure 13):

```
Outgoing report → Quota Manager → Token Bucket → DOS Detector → Gmail API
                        ↓              ↓              ↓
                    Rejected        Blocked        LOCKED
                   (quota full)    (no token)     (anomaly)
```

- **Quota Manager** — tracks the daily send ceiling.
- **Token Bucket** — `tokens ← min(C, tokens + r·Δt)`; a report is allowed only if
  `tokens ≥ 1`. `C` is burst capacity, `r` the sustained refill rate. These are
  *rate-limiter* tokens — unrelated to language-model tokens, a collision of terms the
  book flags explicitly.
- **DOS Detector** — recognises a runaway send loop and locks the interface outright,
  sacrificing reporting to save the account.

Handle HTTP **429 (Too Many Requests)** with backoff — it is a warning, not a passing
glitch (rule 28). Use a **send-only** OAuth scope (rule 30). Reports must be attached JSON,
never free text (rules 33–34).

Four required JSON artifacts, listed with their contents in [PARAMETERS.md](PARAMETERS.md):
`declaration_` · `config_` · `log_` · `result_`.

**Both sides must report separately.** One missing or contradictory report zeroes *both*
teams for that game (rule 35).

## §H. Binding parameters

All numeric values, with their fixed / minimum / negotiable status, live in
**[PARAMETERS.md](PARAMETERS.md)**. Never take a number from the book's prose — it uses
illustrative placeholders. A wrong **fixed** value disqualifies the team.

## §I. Submission checklist

- Two **public** GitHub repos (cop, thief), each README linking to the other (rule 49).
- Every repo carries README + `config/` + PRD + PLAN + TODO (rule 50).
- Academic README with its six mandatory sections (§9.4.2): the chosen Dec-POMDP model ·
  orchestration dilemmas · the chosen strategy · **learning curves, since we use RL** ·
  screenshots of the live GUI and the replay viewer showing `Verified OK` · link to the
  companion repo.
- Secrets in `.gitignore`, never pushed (rules 39–40).
- Git tag on the submitted version (rule 41).
- Unique 8-character team code, no spaces (rule 45).
- Submission form filled, saved as PDF, unaltered — submitted **per team member**
  (rules 43–44).
- Config file of every game attached to the repo; each game's commit hash emailed.

## §J. The cheapest ways to lose

See the ranked list at the end of [RULES.md](RULES.md). The top three are worth memorising:
a missing game report zeroes both teams; shared state between your own two agents is
instant disqualification; and showing the true board in the live GUI — the tempting
debugging shortcut — disqualifies the project.
