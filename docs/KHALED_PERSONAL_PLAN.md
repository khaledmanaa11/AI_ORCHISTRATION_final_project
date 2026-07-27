# Khaled's Personal Plan

Your execution manual. Every step is either **a command you run** or **text you paste**.
Nothing here needs interpretation — if a box says PASTE, copy the whole box.

**Symbols**
- 🖥️ **RUN** — type this command
- 📋 **PASTE** — copy this text into the chat/prompt when asked
- ✅ **CHECK** — confirm this before moving on
- 🙋 **YOU ONLY** — a manual task no agent can do for you (accounts, GitHub, forms)

**Rules of the road**
- `/clear` between planning and executing. Not optional — a full context makes vague plans.
- `CLAUDE.md` auto-loads every session. You never need to re-explain the project rules.
- If a phase gate fails, fix it before moving on. Skipping is how you lose a weekend.

---

# PART 0 — Done already ✅

Committed in `c670dfc`: `docs/RULES.md`, `docs/PARAMETERS.md`, `docs/PROJECT_GUIDE.md`,
`docs/STRATEGY.md`, `docs/SEGAL_GUIDELINES.md`, `CLAUDE.md`, `.gitignore`.

---

# PART 1 — Setup (do once, ~30 min)

## Step 1.1 — Pick your team ID 🙋

You need a **unique 8-character code, no spaces** (rule 45). It goes in every report.
Write it here and never change it:

```
TEAM ID: ________
```

Suggestion: `KM26CTP1` (Khaled Manaa, 2026, Cop-Thief P2P, v1). Any 8 chars work.

## Step 1.2 — Configure GSD

🖥️ **RUN**
```
/gsd:settings
```
Choose: **Interactive** mode (not YOLO). Enable researcher, plan checker, and verifier.

🖥️ **RUN**
```
/gsd:config --profile quality
```

## Step 1.3 — Initialize the project

🖥️ **RUN**
```
/gsd:new-project
```

📋 **PASTE** this as your answer to the first question (it answers most of what follows too):

```
Read @CLAUDE.md, @docs/RULES.md, @docs/PARAMETERS.md, @docs/SEGAL_GUIDELINES.md and
@docs/PROJECT_GUIDE.md before answering anything. They are the binding specification
and they are already written — do not re-derive them.

WHAT WE ARE BUILDING
Two autonomous agents — a cop and a thief — that play a distributed cops-and-robbers
match on a 7x7 grid over a peer-to-peer network using MCP (Model Context Protocol) via
the FastMCP Python library. No central server, no referee. Each agent is simultaneously
an MCP server and an MCP client. Neither agent can see the true board; each builds a
belief map from a decaying scent trail and from the opponent's free-text hints, which
are allowed to be lies. Move decisions are made by a reinforcement-learning Q-policy.
The language model is used ONLY to decode incoming hints and to write outgoing bluff
text — it never chooses a move.

DO NOT RUN DOMAIN RESEARCH. The authoritative specification is already extracted into
docs/. Skip the research agents entirely; they would only rediscover what is in docs/.

ROADMAP IS FIXED — DO NOT INVENT PHASES
Use exactly these 8 phases, in this order, with these exact goals and success criteria.
Phases 1-7 are mandated by the specification (book section 10.3) and their success
criteria are the book's own milestone gates (section 10.4). Do not merge, split,
reorder, or rename them.

Phase 1 — Base logic
  Goal: grid, movement rules, barrier quota, capture detection. No networking, no AI.
  Gate: both agents move legally on the grid; a barrier beyond quota is rejected;
        coordinate overlap triggers capture.

Phase 2 — FastMCP infrastructure
  Goal: two separate processes exposing geometric tools over localhost, coordinates only.
  Gate: a geometric message sent by agent A over localhost is received and decoded
        correctly by agent B.

Phase 3 — Blind strategy module (RL policy)
  Goal: the Q-Learning decision engine, with no scent and no natural language yet.
  Gate: given a known target location, the agent computes and walks the shortest path
        with no manual intervention.

Phase 4 — Language and scent
  Goal: free-text hints, pheromone emission and decay, LLM for hint decoding and deception.
  Gate: a hint is translated into an inference; the scent map updates and decays; the LLM
        emits a hint each turn, either true or false.

Phase 5 — Cloud exposure and tunneling
  Goal: expose the local FastMCP server publicly via ngrok or Localtonet.
  Gate: an agent on a remote machine connects through the tunnel and plays a full round
        against the local agent.

Phase 6 — Security and cryptography
  Goal: commit-reveal protocol over SHA-256, nonce handling, Step-0 hardware declaration.
  Gate: a move is committed and then revealed with a valid nonce; Step-0 verified.

Phase 7 — Reporting and visualization shell
  Goal: Gmail API reporting via OAuth 2.0, live GUI, replay viewer application.
  Gate: game summary sent by mail; GUI displays state; replay app reconstructs a
        recorded round and shows Verified OK.

Phase 8 — Submission and league operations
  Goal: split into two public GitHub repos, academic README, Git tag, play league games.
  Gate: two cross-linked public repos, submission form filled, at least 2 scored league
        games played and reported.

DOCUMENTATION — READ THIS CAREFULLY
The engineering standard (docs/SEGAL_GUIDELINES.md section 2.2) requires these to exist
as REAL, FULL documents at these exact paths, because that is where the grader looks:

  docs/PRD.md   — product requirements
  docs/PLAN.md  — architecture and technical planning
  docs/TODO.md  — task list with priorities, status, and definition of done

Your .planning/ directory does NOT satisfy this requirement. Files that merely point at
.planning/ do NOT satisfy it either. These three must be real documents with real
content, and docs/TODO.md must be kept up to date as work progresses (section 2.5 step 6).

Set this up now: create docs/PRD.md, docs/PLAN.md and docs/TODO.md as part of project
initialization, and add a task to EVERY phase plan that updates docs/TODO.md when the
phase completes.

Additionally, section 2.3 calls per-mechanism PRDs a critical requirement: every
algorithm or central mechanism needs its own docs/PRD_<mechanism>.md. Add the writing
of each one as an explicit task in the phase that builds it:
  docs/PRD_mcp_transport.md   -> Phase 2
  docs/PRD_rl_strategy.md     -> Phase 3
  docs/PRD_belief_map.md      -> Phase 4
  docs/PRD_scent_map.md       -> Phase 4
  docs/PRD_deception.md       -> Phase 4
  docs/PRD_commit_reveal.md   -> Phase 6
  docs/PRD_gatekeeper.md      -> Phase 7

REQUIREMENTS
Seed REQ-IDs from the 55 rules in docs/RULES.md so that every rule maps to a traceable
requirement. Also create requirements for the code-quality gate in
docs/SEGAL_GUIDELINES.md section 19.1 Table 5.

HARD CONSTRAINTS FOR EVERY PHASE
- uv only. Never pip, never bare python, never venv. pyproject.toml is the single
  dependency source; there is no requirements.txt.
- Every source and test file is 150 lines or fewer, excluding blanks and comments.
  When a file gets too long, SPLIT IT — never compress code to fit.
- ruff check must report zero violations.
- pytest coverage must be 85% or above, with fail_under = 85.
- Zero hardcoded values in source. Everything configurable lives in config/,
  constants.py, or an Enum.
- Zero secrets in source. os.environ.get() only. .env-example is committed with dummy
  values.
- All business logic sits behind an SDK layer. GUI and CLI are thin shells.
- Every external API call goes through a single API gatekeeper. Rate limits come from
  config. On overflow it queues — it never crashes.
- TDD: tests written before or alongside the code, covering happy path AND error case.
  Mock every external service; no test may touch a live network or the opponent.
- Version starts at 1.00 in src/<pkg>/shared/version.py and in the config JSON files.
- The cop and the thief run as two SEPARATE PROCESSES under config/police/ and
  config/thief/. They may share library code but must never share live game state,
  memory, or variables. Sharing runtime state is an instant disqualification.
- Never take a number from prose. Every numeric value comes from docs/PARAMETERS.md,
  where each is tagged fixed / minimum / negotiable. A wrong "fixed" value disqualifies
  the team. If a number you need is missing there, stop and ask me.

TEAM CONTEXT
Solo project — one person, no teammates, no code review by another human. The quality
gates above are the review.
```

✅ **CHECK** after it finishes:

🖥️ **RUN**
```
/gsd:progress
```
Confirm `.planning/ROADMAP.md` lists **exactly 8 phases** with the goals above.
If a phase is wrong: 🖥️ `/gsd:phase --edit N` and fix it.

✅ **CHECK** that `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` exist and have real
content — not one-line pointers to `.planning/`.

---

# PART 2 — The build phases

## Repeat this loop for every phase

```
/gsd:discuss-phase N --batch
/clear
/gsd:plan-phase N
/clear
/gsd:execute-phase N
/gsd:code-review N
/gsd:verify-work N
```

After **every** phase, run the gate check (Part 3) before starting the next one.

---

## PHASE 1 — Base logic

*Grid, movement, barriers, capture. No networking, no AI.*

🖥️ **RUN** `/gsd:discuss-phase 1 --batch`

📋 **PASTE**
```
This phase also does the one-time project scaffolding, since it is the first code phase.

SCAFFOLDING (do it in this phase):
- uv project: pyproject.toml with ruff config (line-length 100, target py310,
  select E,F,W,I,N,UP,B,C4,SIM, ignore E501) and coverage config (source=src,
  omit main.py/tests/gui, fail_under=85). Generate uv.lock.
- Layout: src/<package>/{sdk,services,shared,constants.py}, tests/{unit,integration},
  config/police/, config/thief/, .env-example with dummy values.
- src/<package>/shared/version.py starting at 1.00.
- A script that checks every .py file is 150 lines or fewer, so I can run it as a gate.

GAME LOGIC for this phase — all values from docs/PARAMETERS.md, do not invent any:
- Board 7x7 (minimum), origin (0,0) top-left, axis index starts at 0.
- Thief starts centre (3,3), cop starts corner (0,0).
- Movement: one orthogonal step OR stay. No diagonals. This is FIXED — any deviation
  disqualifies.
- Barrier quota 14 (minimum). Reject any placement beyond quota.
- Move ceiling 35 (minimum). Survival threshold 35 (minimum).
- Scoring, all FIXED: cop capture 20, thief captured 5, cop on thief survival 5,
  thief survives 10, tie 2 each. Technical loss is 0/0.

CAPTURE — three distinct ways, all must be implemented:
1. The cop lands on the thief's cell.
2. A barrier is placed on the cell where the thief stands at the moment of contact
   (rule 46) — the cop wins.
3. The thief is left with no legal move (rule 47) — counts as captured.

CONFIG SEPARATION: config/police/ and config/thief/ are separate from the start. The
board rules live in a shared library, but each side loads its own config. No shared
mutable game state.

Keep this phase completely free of networking and of any AI or strategy logic.
```

🖥️ `/clear` → `/gsd:plan-phase 1` → `/clear` → `/gsd:execute-phase 1`
→ `/gsd:code-review 1` → `/gsd:verify-work 1`

✅ **GATE 1** — both agents move legally; over-quota barrier rejected; all three capture
types fire correctly.

---

## PHASE 2 — FastMCP infrastructure

*Two processes talking over localhost. Coordinates only, no language yet.*

🖥️ **RUN** `/gsd:spike "FastMCP server and client handshake between two local Python processes"`

> This is a throwaway experiment to prove FastMCP works before you plan around it.
> If it comes back INVALIDATED, tell me before continuing.

🖥️ **RUN** `/gsd:discuss-phase 2 --batch`

📋 **PASTE**
```
Protocol is MCP via the FastMCP Python library. Use Context7 to fetch current FastMCP
documentation rather than relying on memory.

ARCHITECTURE:
- Each peer is simultaneously an MCP server (exposes tools with @mcp.tool) and an MCP
  client (calls the opponent's tools). Fully symmetric — no strong or weak side.
- Cop and thief run as two SEPARATE OS PROCESSES, launched independently, reading
  config/police/ and config/thief/ respectively. They must never share memory or live
  state. This is rule 1 and rule 2 — sharing is instant disqualification.

COMPONENTS to build this phase:
- PeerRuntime — the running agent process.
- Orchestrator with an explicit state machine enforcing turn order. Every attempt to
  enter an illegal state must be reported (rules 4 and 5).
- Deadline tracker — never block forever waiting for the opponent (rule 6).
  Response timeout 30s, from config.
- Watchdog — monitor for process crashes and rescue data (rule 7).
  Watchdog threshold 60s, from config.

THIS PHASE ONLY: transmit coordinates and geometry over localhost. No natural language,
no scent, no strategy, no cryptography. Those are phases 4 and 6.

Note for later: in the real game, numeric coordinates are FORBIDDEN in the protocol
(rule 27) — communication must be free natural language only (rule 26). Coordinates
here are a scaffolding step for localhost testing and get replaced in Phase 4. Write the
transport so that swap is easy.

Also write docs/PRD_mcp_transport.md this phase (engineering standard section 2.3).
```

🖥️ `/clear` → `/gsd:plan-phase 2` → `/clear` → `/gsd:execute-phase 2`
→ `/gsd:code-review 2` → `/gsd:verify-work 2`

✅ **GATE 2** — a message sent by agent A over localhost arrives at agent B and decodes
correctly, with both running as separate processes.

---

## PHASE 3 — RL strategy module (playing blind)

*The Q-Learning brain. No scent, no language yet.*

🖥️ **RUN** `/gsd:ai-integration-phase 3`

> This one comes **before** planning. It produces `AI-SPEC.md` with the evaluation
> strategy for your RL policy — which is what generates the **learning curves the
> README mandates** when RL is used (rule 42, §9.4.2 item 4). Do not skip it.

📋 **PASTE** when it asks about the AI system:
```
Reinforcement learning — tabular Q-Learning — chosen as the movement policy.

Note the specification treats RL as optional (section 6.3) and defaults to Bayes +
Manhattan heuristics. We are choosing RL deliberately. Do not argue the choice; build it.

EVALUATION DIMENSIONS I need measured:
- Win rate versus a Bayes + Manhattan baseline opponent. Beating the baseline is the
  success criterion for this phase.
- Distribution of capture turn (cop) and survival turns (thief).
- Learning curves across training episodes — MANDATORY deliverable for the README.
- Rate at which the policy falls back to the heuristic (unvisited states).
- Illegal move rate. Must be zero.

REWARD comes straight from the scoring table in docs/PARAMETERS.md Table 17. The
specification states in section 1.3 that the reward function translates directly from
that table. Do not invent a reward scheme.
```

🖥️ **RUN** `/gsd:discuss-phase 3 --batch`

📋 **PASTE**
```
Build the strategy module as a SEPARATE module from the networking layer
(specification section 6.2). It is reached from PeerRuntime at exactly one point: after
the incoming hint is parsed and before the outgoing Commit is packed.

WIRING — required by the specification:
- Declared in the private per-peer config under a [strategy] section, with keys
  police_class and thief_class in "package.module:ClassName" form.
- Both classes inherit from a BrainBase and override _pick_move.
- The cop additionally overrides _decide_move for barrier placement.

Q-LEARNING:
- Bellman update: Q(s,a) <- Q(s,a) + alpha * [ r + gamma * max_a' Q(s',a') - Q(s,a) ]
- epsilon-greedy action selection so the policy does not become predictable.
- alpha, gamma and epsilon come from config — never hardcoded.
- Reward from docs/PARAMETERS.md Table 17.

REQUIRED SAFETY NET: when the Q-table has never visited a state, fall back to a
Bayes + Manhattan heuristic rather than acting on a meaningless zero. This heuristic is
the reference implementation's default policy and must always work on its own.

TRAINING: there is no training phase during a league match, so the policy must arrive
already trained. Build an offline self-play training harness in this phase, and
instrument it from the very first run so learning curves are captured automatically.

ABSOLUTE CONSTRAINT: the algorithm chooses the move. The language model never does
(section 6.2, rule 25). No LLM in this phase at all.

THIS PHASE: no scent, no natural language. The agent is "blind" — it is given a known
target location and must reach it. Those layers arrive in Phase 4.

Also write docs/PRD_rl_strategy.md this phase.
Also update docs/STRATEGY.md — it is currently a scaffold with TBD markers. Fill them in.
```

🖥️ `/clear` → `/gsd:plan-phase 3` → `/clear` → `/gsd:execute-phase 3`
→ `/gsd:code-review 3` → `/gsd:verify-work 3`

✅ **GATE 3** — given a known target, the agent computes and walks the shortest path
with no manual intervention, and beats the Bayes+Manhattan baseline in self-play.

---

## PHASE 4 — Language and scent

*The hardest phase. Hints, lies, pheromones, belief maps.*

🖥️ **RUN** `/gsd:ai-integration-phase 4`

📋 **PASTE**
```
This phase adds the language model in two narrow roles only:
1. Decoding an opponent's incoming free-text hint into an inference about their position.
2. Writing our own outgoing hint, which may be a deliberate lie.

The language model NEVER selects a move. That stays with the Q-policy from Phase 3.

EVALUATION DIMENSIONS:
- Hint decode accuracy against known ground truth.
- Robustness of decoding when the opponent is lying — measure how much a lying opponent
  degrades our belief map.
- Whether our generated bluffs are plausible and stay within the word limit.
- Belief map calibration: is the probability mass actually near the true position.
```

🖥️ **RUN** `/gsd:discuss-phase 4 --batch`

📋 **PASTE**
```
All values from docs/PARAMETERS.md. Do not invent any.

SCENT / PHEROMONES — all three values are FIXED, and the model is cryptographically
locked before the game starts (rule 23). Any deviation in the decay formula voids the game:
- Scent strength at source: 0.9
- Decay rate per turn: 0.10
- Emission field size: 5x5 around the agent

Scent is involuntary — an agent cannot choose not to emit. The counter-play is
exploiting it (for example strengthening scent in a cell you are leaving so the opponent
chases where you were).

BELIEF MAP: a probability grid over the opponent's position, updated by Bayes rule from
two evidence sources — the scent map and the decoded hint. When a hint contradicts the
scent, the belief update must weigh them rather than blindly trusting the text.

VERBAL HINTS:
- Free natural language ONLY (rule 26). Numeric coordinates in the protocol are
  FORBIDDEN (rule 27) — this replaces the coordinate transport from Phase 2.
- Maximum 15 words per hint (negotiable value, default 15). The limit applies both to
  our template and to the system prompt given to the language model.
- Game arena is "New York" (negotiable) — a real-world region supplying genuine
  directional cues.

DECEPTION:
- Hints are allowed to be lies. This is the only voluntary information channel.
- An intent flag of exactly "truth" or "lie" is declared IN ADVANCE and will be sealed
  into the commit hash in Phase 6, so a side cannot retroactively claim it was honest.
- EXCEPTION: at the moment of capturing a thief, the declaration must be true
  (rules 21 and 22). Lying there is immediate disqualification. Barrier placements must
  also always be declared truthfully (rules 15 and 16).

DECISION PIPELINE, exact order:
incoming hint + scent -> hint decode -> belief update (Bayes) -> Q-policy move choice
-> LLM bluff text -> Commit pack

Write docs/PRD_belief_map.md, docs/PRD_scent_map.md and docs/PRD_deception.md this phase.
```

🖥️ `/clear` → `/gsd:plan-phase 4` → `/clear` → `/gsd:execute-phase 4`
→ `/gsd:code-review 4` → `/gsd:verify-work 4`

✅ **GATE 4** — a hint becomes an inference; the scent map updates and decays correctly;
the LLM emits a hint every turn, sometimes true and sometimes false.

---

## PHASE 5 — Cloud exposure and tunneling

### 🙋 YOU ONLY — do this before the phase

1. Create a free account at **https://ngrok.com**
2. Copy your **authtoken** from the dashboard
3. Put it in your local `.env` file (never commit it):
   ```
   NGROK_AUTHTOKEN=your_token_here
   ```
4. Add the matching dummy line to `.env-example`:
   ```
   NGROK_AUTHTOKEN=your_ngrok_token_here
   ```

🖥️ **RUN** `/gsd:spike "expose a local FastMCP server to a public URL through an ngrok tunnel"`

🖥️ **RUN** `/gsd:discuss-phase 5 --batch`

📋 **PASTE**
```
PROBLEM: both machines sit behind NAT and a firewall, so neither has a publicly
reachable address. A tunnel performs NAT traversal and gives the local FastMCP server a
public URL the opponent can call from anywhere.

REQUIREMENTS:
- Use ngrok (Localtonet is the permitted alternative). Rule 10 makes public exposure
  mandatory for league play — localhost is allowed only during early development.
- The authtoken comes from the environment via os.environ.get(). It must never appear in
  source or in any committed file. ngrok.yml is already gitignored.
- The public URL must be configurable and easy to exchange with an opponent before a
  match, since it changes on each tunnel restart with a free account.
- Handle tunnel death mid-game gracefully — the watchdog from Phase 2 should catch it
  rather than hanging.

REMINDER: process and config separation still applies. Cop and thief each get their own
tunnel and their own public URL. They must not share state.
```

🖥️ `/clear` → `/gsd:plan-phase 5` → `/clear` → `/gsd:execute-phase 5`
→ `/gsd:code-review 5` → `/gsd:verify-work 5`

✅ **GATE 5** — a remote agent connects through the tunnel and plays a full round against
your local agent.

---

## PHASE 6 — Security and cryptography

*Commit-reveal. The phase where small bugs cause automatic losses.*

🖥️ **RUN** `/gsd:discuss-phase 6 --batch`

📋 **PASTE**
```
COMMIT-REVEAL over SHA-256 (specification chapter 5). Four phases, in this exact order:

1. COMMIT       — send ONLY H_commit, the SHA-256 hash. Reveals nothing, cannot be forged.
2. ACKNOWLEDGE  — opponent confirms receipt; the move is now locked.
3. REVEAL       — send the actual move and hint. The NONCE STAYS HIDDEN at this stage.
4. FINAL REVEAL / AUDIT — at game end all nonces are published, both logs are re-hashed
                  and compared.

HASH INPUT — get this exactly right, it is the most common source of a false mismatch:
- Fields: {state, move, intent, nonce}
- Serialized as CANONICAL JSON: json.dumps(..., sort_keys=True, separators=(",", ":"))
  so both peers hash byte-identical input.
- intent is exactly "truth" or "lie", declared in advance.
- nonce = secrets.token_hex(16). NEVER use the random module — that invites a dictionary
  attack and is a disqualification risk (rule 18).
- Verify with secrets.compare_digest, never with ==.

THE IRON LAW (rule 19): any hash mismatch at audit is a technical loss, score 0 to the
forging team. There is no human judgement involved. Because of this, the canonical JSON
serialization needs its own dedicated unit tests proving byte-identical output across
processes, dict insertion orders, and unicode content.

STEP-0 HARDWARE DECLARATION (section 5.5), signed before the first move:
OS, CPU cores and frequency, RAM, GPU/VRAM presence, language model name, code version,
and THE EXACT GITHUB COMMIT HASH the game runs on (rule 53). Code may change between
games, but every game must record its own commit hash.

Also required: token counting. The final JSON must report total language-model tokens
consumed in the game and across the series (rule 54).

Write docs/PRD_commit_reveal.md this phase.
```

🖥️ `/clear` → `/gsd:plan-phase 6` → `/clear` → `/gsd:execute-phase 6`

🖥️ **RUN** `/gsd:secure-phase 6`

> Independent audit of the crypto. Worth it here specifically, because rule 19 turns a
> serialization bug into an automatic loss.

🖥️ **RUN** `/gsd:code-review 6` → `/gsd:verify-work 6`

✅ **GATE 6** — a move is committed then revealed with a valid nonce; Step-0 declaration
verified; canonical JSON proven identical across processes.

---

## PHASE 7 — Reporting shell, GUI, replay viewer

### 🙋 YOU ONLY — Google Cloud setup (do this first, ~20 min)

1. Go to **https://console.cloud.google.com**
2. Create a new project (name it anything, e.g. `cop-thief-p2p`)
3. **APIs & Services → Library** → search **Gmail API** → **Enable**
4. **APIs & Services → OAuth consent screen** → choose **External** → fill required
   fields → add **your own email** as a Test user
5. **APIs & Services → Credentials** → **Create Credentials** → **OAuth client ID** →
   application type **Desktop app**
6. **Download JSON** → save it into the project root as `credentials.json`
7. ✅ **CHECK** `git status` does **not** list `credentials.json` (it is already
   gitignored — if it shows up, stop and tell me)

🖥️ **RUN** `/gsd:spike "Gmail API send-only OAuth 2.0 flow with a persisted refresh token"`

🖥️ **RUN** `/gsd:ui-phase 7`

📋 **PASTE** when asked about the interface:
```
Two separate applications.

1. LIVE GUI — shown during a match. Displays the belief heatmap (probability of the
   opponent's position), our own position, known barriers, and a turn banner.

   ABSOLUTE RULE: it shows ONLY LOCAL TRUTH (rule 8). Displaying the full objective board
   state in the live GUI is a project disqualification for illegal advantage (rule 9).
   This is the tempting debugging shortcut — do not build it, not even behind a flag.

2. REPLAY VIEWER — used after a game, where showing everything is fine. It reads the
   game log, re-hashes every turn, verifies each commitment against its revealed nonce,
   and displays "Verified OK" when the log is intact (rule 20).

Screenshots of both are a mandatory README deliverable (section 9.4.2 item 5).
```

🖥️ **RUN** `/gsd:discuss-phase 7 --batch`

📋 **PASTE**
```
REPORTING — this is pass/fail. Rule 35: if a report is not received from one side, that
side scores ZERO for the game even if it won on the board, and contradictory reports
zero BOTH teams.

- Both agents automatically send a signed JSON report at the end of every legal game.
- Recipient, fixed in both agents: rmisegal+uoh26finalgame@gmail.com
- Reports are ATTACHED JSON FILES. Free-text reports are rejected and score zero
  (rules 33 and 34).
- OAuth 2.0 with a SEND-ONLY scope (rule 30). Anything broader is a security breach that
  disqualifies the code.
- credentials.json and the token file are gitignored and read via os.environ.get().

FOUR REQUIRED JSON FILES — exact names, from docs/PARAMETERS.md:
  declaration_<game_id>.json     pre-game declaration: identities, repo URLs, MCP server
                                 addresses, hardware spec, model, token ceiling, times
  config_<game_id>_g<NN>.json    the agreed configuration, locked and identical both sides
  log_<game_id>_g<NN>.json       turn-by-turn journal: commitments, moves, hints,
                                 verdicts, nonce and hash
  result_<game_id>.json          final results — THIS is the file that gets emailed
All four share a game_uid. These files MUST be committed to the repo (rule 50) — they are
deliverables, not runtime junk.

API GATEKEEPER — mandatory chain, in this order:
  outgoing report -> Quota Manager -> Token Bucket -> DOS Detector -> Gmail API
- Token bucket rule: tokens <- min(C, tokens + r * dt), allow only if tokens >= 1.
- Handle HTTP 429 with backoff — it is a warning, not a passing glitch (rule 28).
- The DOS detector locks the interface outright on a runaway send loop, sacrificing
  reporting to save the account (rule 29).
- All limits come from config/rate_limits.json, never hardcoded. Values in
  docs/PARAMETERS.md Table 19; where the engineering standard's section 5.2 differs,
  take the stricter value.
- Overflow QUEUES, it never crashes.

Write docs/PRD_gatekeeper.md this phase.
```

🖥️ `/clear` → `/gsd:plan-phase 7` → `/clear` → `/gsd:execute-phase 7`
→ `/gsd:code-review 7` → `/gsd:verify-work 7`

✅ **GATE 7** — summary email actually arrives with the JSON attached; GUI shows local
truth only; replay viewer prints **Verified OK**.

---

## PHASE 8 — Submission and league

### 🙋 YOU ONLY — GitHub setup

1. Create **two public** repos on GitHub:
   - `cop-p2p-<yourteamid>`
   - `thief-p2p-<yourteamid>`
2. Share both with **rmisegal@gmail.com**

🖥️ **RUN** `/gsd:discuss-phase 8 --batch`

📋 **PASTE**
```
REPO SPLIT (rule 49): we developed in one repo. Now split into two PUBLIC GitHub repos,
one for the cop and one for the thief. Each carries the shared core library plus one
role's entry point and its own config directory. Each README must link to the other —
the cross-link is mandatory in both directions.

EVERY repo must contain (rule 50): README.md, config/, docs/PRD.md, docs/PLAN.md,
docs/TODO.md, the per-mechanism PRDs, and the four game JSON files.

ACADEMIC README — six mandatory sections (section 9.4.2):
1. The chosen Dec-POMDP model — scientific description of the state space,
   observations and uncertainty.
2. Orchestration dilemmas — turn management, network failure handling, the roles of the
   Gatekeeper and the Orchestrator.
3. The chosen strategy — how the decision mechanism works.
4. LEARNING CURVES — mandatory because we used RL.
5. Screenshots — the live GUI heatmap, and the replay app showing "Verified OK".
6. Link to the companion repo.

The README must also read as a full user manual (engineering standard section 2.1):
installation, usage, examples, configuration guide, contribution guidelines, license.

FINAL STEPS:
- Tag the submitted version with a Git tag (rule 41).
- Verify .gitignore is doing its job and no secret ever entered git history.
- Confirm every value used matches docs/PARAMETERS.md, especially the FIXED ones.
```

🖥️ `/clear` → `/gsd:plan-phase 8` → `/clear` → `/gsd:execute-phase 8`

🖥️ **RUN** `/gsd:audit-milestone`

### 🙋 YOU ONLY — playing the league

1. Find opponent teams from your course.
2. Before each game, agree the config file and verify it is **byte-for-byte identical**
   on both sides (rule 11).
3. Declare honestly how many games you have already played (rule 37 — lying here
   disqualifies the whole project, rule 38).
4. Play. **Minimum 2 scored games against different teams** or you get no passing grade
   (rule 31). Maximum 10 games. **One scored game per opponent** — no rematches for
   points, though unscored warm-ups are encouraged (rule 52).
5. After each game: agree the result, **both sides send their own report**, and email the
   lecturer the **GitHub commit hash** used for that game (Appendix F rule 5).
6. Give each game's config file a **different filename** and commit it (Appendix F rules
   3 and 4).

### 🙋 YOU ONLY — the form

1. Download the submission form, fill it in, save as **PDF**. Do not alter or forge
   fields (rule 43).
2. Include **both** repo links.
3. Submit **individually** — per team member (rule 44).
4. Give a self-assessment score for **code quality only**, not for league results
   (rule 55).

---

# PART 3 — The gate check (run after every phase)

🖥️ **RUN**
```
uv run ruff check .
uv run pytest --cov
```

✅ Ruff: **0 violations**. ✅ Coverage: **≥ 85%**.

File-length check (Phase 1 builds you a script for this; until then):

🖥️ **RUN** in PowerShell
```powershell
Get-ChildItem -Recurse -Include *.py -Path src,tests | ForEach-Object {
  $n = (Get-Content $_.FullName | Where-Object { $_.Trim() -ne '' -and -not $_.Trim().StartsWith('#') }).Count
  if ($n -gt 150) { "TOO LONG ($n): $($_.FullName)" }
}
```
✅ No output = every file passes. Any output = **split those files**, do not compress them.

---

# PART 4 — When things go wrong

| Situation | Command |
|---|---|
| Lost track of where you are | `/gsd:progress` |
| Coming back after a break | `/gsd:resume-work` |
| A bug you cannot pin down | `/gsd:debug "description"` — survives `/clear` |
| Phase went sideways | `/gsd:forensics` |
| Need to undo a phase | `/gsd:undo --phase NN` |
| Planning dir looks corrupted | `/gsd:health --repair` |
| Idea you do not want to lose | `/gsd:capture --note "..."` |

---

# PART 5 — Things that silently cost you everything

Read this list once now, and again before your first league game.

1. **A missing game report** — zeroes **both** teams, including the one that reported.
2. **Shared state between your own cop and thief** — instant disqualification. Easy to do
   by accident with a "convenient" shared module holding live game state.
3. **Showing the true board in the live GUI** — disqualifies the project. The tempting
   debugging shortcut.
4. **A hash mismatch at audit** — automatic loss. Usually a canonical-JSON bug, not fraud.
5. **A wrong `fixed` parameter value** — disqualification. Always read
   `docs/PARAMETERS.md`.
6. **Credentials committed** — `.gitignore` is already set up. Never override it.
7. **Free text instead of attached JSON** in a report — zero score.
8. **A false declaration** about a capture, a barrier, or your game count — the harshest
   sanction in the book.
9. **Fewer than 2 scored games** against different teams — no passing grade regardless of
   code quality.
