# Pursuit and Evasion Strategy — Sourced Research

**Status:** COMPLETE (2026-08-02).
**Scope:** literature + code survey for a 7x7 grid, 1 cop vs 1 thief, cop-places-barriers
variant. Evader first, pursuer second, equal depth.

**Citation rule used in this document:** every claim carries a paper/author/year, a book
section, or a URL. Where nothing was found, the text says **"no source found"** verbatim
rather than asserting anything.

---

## Top findings at a glance

1. The brief's premise is right but **cited to the wrong paper** — fix the bibliography (§1).
2. The thief has a **provably unbeatable rule on the open board**: move to any free
   neighbour/STAY that is not in the cop's closed neighbourhood. Nowakowski–Winkler 1983.
   Our 90% is a bug, not a ceiling (§2.1.1).
3. Our board is triangle-free, so **cop-win ⟺ the thief's free region is a forest**. Both
   agents' true objective is *cycles*, not *distance* (§2.1.1, §2.2, §3.2, §3.3).
4. The decycling number of the 7×7 grid is **13** (cited lower bound + a 13-cell set we
   verified computationally) — our quota of **14** is sufficient by exactly one barrier, but
   the **35-turn deadline is the binding constraint**, not the quota (§3.2).
5. **Conway's Angel Problem is the same mechanic** and says a block-placer with unlimited
   quota beats an evader as weak as ours *without any cop* (§3.1).
6. Our current barrier objective (BFS distance to a fixed corner anchor) has **no source in
   the literature**; six sourced alternatives are ranked in §3.3.
7. Use **iterative-deepening alpha-beta, not MCTS** — this is a shallow-trap domain
   (Ramanujan et al., ICAPS 2010) (§2.4.2).

---

## 0. Game under study (restated for the reader)

- 7x7 square grid graph, 2 players, perfect information, alternating moves.
- Cop moves first: one orthogonal step or STAY. Then the thief moves the same way.
- After moving, the cop may delete a cell (BARRIER). Quota 14 for the whole game.
  A barriered cell is permanently impassable to both players.
- Thief wins by surviving 35 turns; cop wins by stepping onto the thief's cell.
- Current hand-written BFS heuristics: cop wins 10%, thief survives 90%.

---

## 1. The baseline theorem (verified independently)

**Verdict: the premise is correct, but the citation given in the brief is the wrong paper.**
The two numbers quoted (cop number 2, 2-capture time ⌊(m+n)/2⌋−1, and ⌈(k+1)/2⌉ for a
product of k trees) are real published results, but they come from Neufeld & Nowakowski
1998 and Mehrabian 2010/2011 respectively — **not** from arXiv:1708.08255.

| Claim | Correct source | Verified statement |
|---|---|---|
| Cop number of the Cartesian product of *k* trees is ⌈(k+1)/2⌉; hence a grid (k=2 paths) has cop number **2** | S. Neufeld and R. Nowakowski, "A game of cops and robbers played on products of graphs", *Discrete Mathematics* **186**(1–3):253–268, 1998. <https://www.sciencedirect.com/science/article/pii/S0012365X97001659> | Cop number of Cartesian product of k trees = ⌈(k+1)/2⌉; of k cycles of length ≥ 4 = k+1. For k = 2 trees this gives ⌈3/2⌉ = **2**. |
| 2-capture time of the m×n grid = ⌊(m+n)/2⌋ − 1 | A. Mehrabian, "The capture time of grids", arXiv:1008.4424 (2010), *Discrete Mathematics* 311(1):102–105, 2011. <https://arxiv.org/abs/1008.4424> | For a Cartesian product G of two trees, capt₂(G) = ⌊diam(G)/2⌋. For an m×n grid diam = (m−1)+(n−1) = m+n−2, so capt₂ = ⌊(m+n−2)/2⌋ = ⌊(m+n)/2⌋ − 1. **Algebraically identical to the brief's figure.** For 7×7: ⌊12/2⌋ = **6 moves for two cops**. |
| arXiv:1708.08255 | F. Luccio and L. Pagli, "Cops and robber on grids and tori", arXiv:1708.08255 (2017, rev. 2019). <https://arxiv.org/abs/1708.08255> | This paper is about **tori**: 2 cops suffice on semi-tori, 3 are necessary and sufficient on full tori; plus k-cop algorithms and capture-time bounds. It is a legitimate companion reference for grids/tori but it is **not** the origin of either quoted formula. **Correct the bibliography before submission.** |

**Consequence for this project — the brief's conclusion stands and is a theorem, not a
tuning problem.** Cop number 2 for a grid means: for any strategy of a *single* cop there
exists a robber strategy that evades forever on the open m×n grid (this is the definition
of the cop number; Nowakowski & Winkler 1983, below). Our 10%/90% split is therefore the
*expected* shape of the result against a decent evader, and no amount of cop-side heuristic
tuning changes the open-grid case. The barrier mechanic (permanent vertex deletion) is the
only lever that can change the game class.

**Foundational background these rest on** (needed later for the evader's losing positions):

- A. Quilliot, thèse, Université de Paris VI, 1978 — first characterisation of cop-win
  graphs. Cited as the independent co-discovery in essentially every survey, e.g. Bonato &
  Nowakowski, *The Game of Cops and Robbers on Graphs*, AMS Student Mathematical Library
  vol. 61, 2011.
- R. Nowakowski and P. Winkler, "Vertex-to-vertex pursuit in a graph", *Discrete
  Mathematics* **43**(2–3):235–239, 1983. <https://doi.org/10.1016/0012-365X(83)90160-7> —
  a graph is cop-win (one cop suffices) **iff** it is *dismantlable*: repeatedly deleting a
  *corner* (a vertex u whose closed neighbourhood is contained in the closed neighbourhood
  of some other vertex v — u is "dominated" by v) reduces the graph to a single vertex.
- M. Aigner and M. Fromme, "A game of cops and robbers", *Discrete Applied Mathematics*
  **8**(1):1–12, 1984. <https://doi.org/10.1016/0166-218X(84)90073-8> — cop number of any
  planar graph ≤ 3; introduces the **shadow / guarded-path** argument (§2.1 below), which
  is the single most reusable idea in the whole literature for both sides.

The 7×7 grid is **triangle-free and has no dominated vertices** (in a grid, no vertex's
closed neighbourhood contains another's), so it is *not* dismantlable and therefore
**not cop-win** — which is the one-line proof of why our single cop loses on the open board.
This is the direct application of Nowakowski–Winkler 1983 to our exact board.

---

## 2. EVADER (priority section)

### 2.1 Q1a — Published evader / robber strategies

#### 2.1.1 The headline result: the *no-corner* robber strategy is provably optimal and is 5 lines of code

This is the single most important finding in this document for the thief.

**Source.** R. Nowakowski and P. Winkler, "Vertex-to-vertex pursuit in a graph", *Discrete
Mathematics* 43(2–3):235–239, 1983; independently A. Quilliot (thèse, Paris VI, 1978).
Textbook statement: A. Bonato and R. Nowakowski, *The Game of Cops and Robbers on Graphs*,
AMS Student Mathematical Library 61, 2011, Ch. 2 (the "cop-win ⟺ dismantlable" theorem).

**Definitions.** `N[u]` = closed neighbourhood of u (u plus its neighbours). Vertex u is a
**corner** (equivalently *dominated*, or *irreducible*) if there is some v ≠ u with
`N[u] ⊆ N[v]`. A graph is **dismantlable** if repeatedly deleting corners reduces it to one
vertex. Theorem: **G is cop-win (one cop suffices) ⟺ G is dismantlable.**

**The robber strategy that falls straight out of the theorem** (this is the standard proof
of the "only if" direction, and it is a complete, deterministic, O(deg) per move evader):

> If the current board graph has **no corner at all**, the robber never loses. Invariant:
> it is the robber's move and the robber is not on the cop's cell. Cop is at c, robber at
> r. Because r is not dominated by c, there exists `w ∈ N[r] \ N[c]`. Move to w. The cop
> cannot reach w on its next move, because w ∉ N[c]. Restore the invariant and repeat.

**Applied to our exact board — a proof our thief should survive 100%, not 90%.**
The 7×7 grid is **triangle-free** (it is bipartite). In a triangle-free graph, suppose
`N[u] ⊆ N[v]`, u ≠ v. Then v ∈ N[u] so u~v; and any other neighbour w of u satisfies
w ∈ N[v], so w~v, giving the triangle u–w–v. Contradiction unless u has no other
neighbour. **So in a triangle-free graph the only corners are degree-1 vertices (leaves).**
The open 7×7 grid has minimum degree 2, hence **no corners**, hence is **not** dismantlable,
hence **not cop-win** — a second, independent, one-line proof of the brief's premise that
does not rely on Neufeld–Nowakowski at all.

**Consequences that are directly actionable:**

1. On the *open* board the thief has a **provably unbeatable, constant-time** rule:
   move to any cell in `N[r] \ N[c]`, i.e. **any free neighbour (or STAY) that is not
   adjacent to and not equal to the cop's cell after the cop has moved.** No search, no
   evaluation function. Our 90% survival number means our current thief is *failing at a
   problem with a closed-form solution*.
2. The set `N[r] \ N[c]` is only empty when every one of r's free neighbours is in the
   cop's closed neighbourhood — which on a triangle-free board means r has been reduced to
   effective degree ≤ 1. **Barriers are the cop's only way to make that set empty**, which
   is exactly the bridge to §3.
3. Corollary worth stating in the report: **a triangle-free graph is cop-win iff it is a
   tree** (dismantling can only ever remove leaves, and leaf-removal reduces a graph to a
   point iff it is acyclic). So the cop's true objective is *acyclicity of the thief's free
   region*, and the thief's true objective is **keep a cycle alive in your own component**.
   See §3.2 for the quantitative version of this.

#### 2.1.2 Why "exploit the 4-cycles" is the right instinct, made precise

The brief asks how an evader exploits the grid's induced 4-cycles. The precise mechanism is
the one above: a 4-cycle is the minimal structure that guarantees `N[r] \ N[c] ≠ ∅` for a
degree-2 cell. Concretely, if the thief stands on a cycle and the cop is on that same cycle,
the thief can always move *around* the cycle away from the cop; a single cop can never close
a cycle because it can only occupy one of the two arcs. Formally this is the k = 2 case of
Neufeld & Nowakowski 1998 — a product of two trees needs ⌈3/2⌉ = 2 cops precisely because
the second cop is what closes the second arc. See also Aigner & Fromme 1984 §2 (below): one
cop can *guard* a shortest path but cannot guard two disjoint arcs at once.

Practical rule for our thief, derived from that: **prefer cells that lie on a cycle of the
current free subgraph, and prefer the largest such cycle.** A cell that lies on no cycle
(i.e. a bridge/leaf part of the free graph) is a cell from which the cop can eventually win.

#### 2.1.3 The cop-side idea every evader must know: the shadow / guarded-path strategy

**Source.** M. Aigner and M. Fromme, "A game of cops and robbers", *Discrete Applied
Mathematics* 8(1):1–12, 1984, <https://doi.org/10.1016/0166-218X(84)90073-8>. Result: any
planar graph has cop number ≤ 3. Technique: a cop can **guard a shortest path** P — after a
finite number of moves, the cop can shadow the robber's projection onto P such that the
robber can never enter P without being caught. Three cops on a planar graph work by
repeatedly guarding paths that split the robber's territory in half.

**Why the evader cares.** This is the published mechanism of "being herded into a shrinking
region". Every published cop strategy for planar graphs and grids is a *territory-halving*
argument built from guarded paths. Therefore the evader's counter is territory-preservation:
never let the pursuer establish a guarded separator that halves your region. On our board
the cop cannot guard a full path *and* chase (only one cop), but **a barrier line is a
permanently guarded path that costs no cop time** — that is exactly what makes barriers
dangerous and it is the reason our thief must treat barrier placement, not cop motion, as
the real threat.

#### 2.1.4 The continuous-domain analogue: maximise distance is *not* optimal

**Source.** A. S. Besicovitch's evasion strategy for the Lion-and-Man problem, reported in
J. E. Littlewood, *A Mathematician's Miscellany* (1953; reissued as *Littlewood's
Miscellany*, ed. B. Bollobás, CUP, 1986), section on the lion and man. Rado posed the
problem (~1930s): lion and man of equal speed in a closed circular arena. The "obvious"
answer — the man runs to the boundary and along it — is **wrong**; Besicovitch gave a simple
strategy (a sequence of straight dashes perpendicular to the man–lion line, with step
lengths whose squares sum finitely but whose lengths sum infinitely) by which the man evades
capture **forever**, approaching but never reaching the boundary.

Two transferable lessons, both sourced:
- **Hugging the boundary loses.** The natural greedy "run to the wall" evader is refuted.
  This maps directly onto our board: edge and corner cells are traps, not safety.
- **Optimal evasion is not "maximise instantaneous distance to the pursuer."** Besicovitch's
  man repeatedly moves *perpendicular* to the pursuit direction, which barely changes the
  distance but preserves manoeuvring room. The discrete analogue is our §2.1.1 rule:
  what matters is the *existence of a non-dominated successor*, not the distance number.

For the continuous-domain framing generally see the survey T. Ba¸sar-style treatment in
"An Introduction to Pursuit-Evasion Differential Games", arXiv:2003.05013, and the original
R. Isaacs, *Differential Games*, Wiley, 1965.

---

### 2.2 Q1b — Why an evader loses: characterised losing positions

Ranked by how well-characterised each mechanism is in the literature.

**(1) Being forced onto a corner (dominated vertex) — fully characterised, exact.**
Nowakowski & Winkler 1983 (above). This is not a heuristic: the *only* way one cop ever
wins is by driving the game into the dismantling order. Losing positions are exactly those
from which the cop can force the robber into successively smaller retracts. On a
triangle-free board (ours, permanently — deleting cells cannot create a triangle) this
degenerates to the crisp statement: **the thief loses iff its free component is a tree and
the cop is inside it** (with enough turns left; see §3.2 for the turn budget). Equivalent
phrasing for our code: *the thief is lost the moment its own connected free component
contains no cycle.*

**(2) Cornering / low-degree cells — documented, but note the direction of the effect.**
The literature on grids notes explicitly that the boundary and corners of a grid are what
make it *harder* than a torus for cops in the multi-cop setting: Luccio & Pagli,
arXiv:1708.08255 — grids have low-degree edge and corner vertices which let a robber
*isolate himself*, so grids can need attention that tori do not. **Do not over-read this**:
that argument is about a robber hiding in a region no cop is near, in a many-cop
partitioning strategy. In *our* one-cop-with-barriers game, low degree is a liability for
the thief because the barrier quota can finish the job of removing the remaining exits. We
found **no source** stating that low-degree cells are good for a single evader against a
single pursuer that can delete cells.

**(3) Reachable-set collapse / articulation points — the strongest *practical*
characterisation, and it comes from competitive game AI rather than graph theory.**
Source: Andy Sloane (a1k0n), "Google AI Challenge post-mortem" (Tron light-cycles, 2010),
<https://www.a1k0n.net/2010/03/04/google-ai-postmortem.html>, and the entry's code at
<https://github.com/a1k0n/tronbot>. Tron is the closest *playable* analogue to our game:
every cell a player leaves becomes permanently impassable — i.e. **it is a
vertex-deletion pursuit game**, exactly our barrier mechanic with a different deletion rule.
The contest-winning insight there was explicitly:
- compute **articulation points / biconnected components** of the free graph, build a
  "chamber tree", and evaluate which chamber you would be sealed into;
- the author credits the articulation-point chamber evaluation as "probably the
  contest-winning idea", and states that **a better evaluation heuristic beats deeper
  search** ("a deep minimax search using a flawed evaluation heuristic is self-deluded about
  what its opponent is actually going to do").

Practical characterisation of a losing position from that work: *you are lost when the
opponent can reach the articulation point that separates you from the larger chamber before
you can*. This is the thing to implement for the thief.

**(4) Traps that close 2–3 moves later — how much lookahead is needed.**
Source: R. Ramanujan, A. Sabharwal and B. Selman, "On Adversarial Search Spaces and
Sampling-Based Planning", ICAPS 2010, <https://ojs.aaai.org/index.php/ICAPS/article/view/13437>
(see also their arXiv:1203.4011 follow-up). They define a **level-k trap**: a position where
the opponent has a k-move forced win that a shallow or sampling-based search misses. Their
measured findings, directly applicable to our question:
- **shallow traps (roughly levels 3–7) occur frequently** in trap-rich domains such as Chess
  (they occur even in grandmaster games), and are essentially absent in Go;
- **UCT / MCTS systematically fails to detect shallow traps**, giving the trapped move a
  near-best score, whereas **minimax/alpha-beta at depth ≥ k finds them reliably**.

**Answer to the brief's question**: to avoid a trap that closes in *k* of your own moves you
need a **full-width adversarial search of depth ≥ 2k plies** (your move + cop move + barrier
per round). For a trap closing 2–3 thief moves later that is **4–6 plies minimum**, and the
Ramanujan et al. result says this must be *full-width* (alpha-beta), not sampled (MCTS).
Our game is a trap-rich, Chess-like domain, **not** a Go-like domain — this is the decisive
argument for the search choice in §2.4.

**(5) Herding into a shrinking region.** Aigner & Fromme 1984 (guarded shortest paths,
§2.1.3) is the published mechanism. No source found for a *quantitative* threshold ("region
of size < X is lost") on a grid; the closest quantitative statement we found is the
tree/cycle criterion in (1) plus the turn-budget arithmetic in §3.2.

### 2.3 Q1c — Evader evaluation features, ranked by reported usefulness

The one place in the literature where these features are **compared against each other with
measured results** is competitive Tron light-cycle AI, because Tron is the only widely-played
game that is a *vertex-deletion pursuit game* like ours. The ranking below is taken from the
winner's own post-mortem, which reports what helped and what did not.

Primary source for rows 1–5: Andy Sloane (a1k0n), "Google AI Challenge post-mortem", 4 March
2010, <https://www.a1k0n.net/2010/03/04/google-ai-postmortem.html>; code
<https://github.com/a1k0n/tronbot>. Secondary sources given per row.

| Rank | Feature | What the source actually says | Verdict for our thief |
|---|---|---|---|
| **1** | **Articulation points / biconnected "chamber tree" of the free graph** | a1k0n calls the articulation-point chamber evaluation *"probably the contest-winning idea"*: compute cut vertices, decompose the free space into chambers, and evaluate which chamber each player gets sealed into and which chambers are "battlefronts" (bordering the opponent) versus dead territory. | **Implement first.** It is the computational form of "the trap that closes in 3 moves". Hopcroft–Tarjan runs in O(V+E) = O(49+84) per node — trivially inside 50 ms. |
| **2** | **Size of the evader's connected free component** | a1k0n's *endgame* evaluation is literally `1000 * (size of my connected component − size of opponent's connected component)` once the two players are separated. | Direct analogue: once a barrier wall separates cop from thief, the thief's survival is determined by its own component size vs turns remaining. Cheap flood-fill. |
| **3** | **Voronoi / territory share (cells you reach strictly before the pursuer)** | a1k0n: for every square decide "whether player 1 can reach it before player 2 does or vice versa", then "count the number of squares on each side and subtract". Independently, in continuous robotics: **Z. Zhou, W. Zhang, J. Ding, H. Huang, D. M. Stipanović, C. J. Tomlin, "Cooperative pursuit with Voronoi partitions", *Automatica* 72:64–72, 2016** (<https://www.sciencedirect.com/science/article/abs/pii/S0005109816301911>) — pursuers provably capture by **monotonically shrinking the area of the evader's Voronoi cell**; guaranteed capture in finite time in convex environments with equal speeds. | **Use it, and read the Automatica result as the definition of the threat**: if the cop is shrinking your Voronoi cell every turn you are losing. Two BFS sweeps (one from cop, one from thief) = ~100 cell visits. |
| **4** | **Edge count of your region, not just cell count** | a1k0n fitted a linear evaluation on **11,691 games**: predicted endgame-move difference `= K1·(N1−N2) + K2·(E1−E2)` with **K1 ≈ 0.055 (nodes) and K2 ≈ 0.194 (edges)**. | Quantitative and directly reusable: **edges are weighted ≈3.5× nodes**. Manoeuvring room (degree structure) matters far more than raw territory count. This is the best-sourced weight ratio we found anywhere. |
| **5** | **Degree of the current cell / number of escape routes** | a1k0n's greedy space-filling rule when not searching: *"always choose the move that removes the least number of edges from the graph"*, i.e. hug walls to avoid fragmenting your own space. | Useful but as a **tiebreak**, and note it is a *space-filling* rule; for pure survival the theoretically correct version is row 6. |
| **6** | **`\|N[r] \ N[c]\|` — count of successors not covered by the pursuer's closed neighbourhood** | Nowakowski & Winkler 1983 (§2.1.1). This quantity being ≥ 1 is *exactly* the non-domination condition, and keeping it ≥ 1 forever is *exactly* a winning evader strategy. | **This is the only feature in the table with a proof attached.** Should be a hard constraint (never enter a cell where it can be driven to 0), not a soft weight. |
| **7** | **Distance to the pursuer** | Used as the primary state feature in essentially all RL pursuit-evasion work, e.g. the survey "An Introduction to Pursuit-Evasion Differential Games", arXiv:2003.05013. **But** Besicovitch's lion-and-man solution (Littlewood, *A Mathematician's Miscellany*, 1953) shows the distance-maximising evader is *not* optimal — the optimal evader moves roughly perpendicular to the pursuit line, barely changing the distance. | **Demote it.** Our current BFS-distance thief is exactly the refuted strategy. Keep distance only as a low-weight term or a tiebreak. |
| **8** | **Distance to board edge / corner** | Besicovitch (above) refutes boundary-hugging in the continuous case. Luccio & Pagli, arXiv:1708.08255, note grid boundary/corner vertices have low degree, which is what distinguishes grids from tori. | Encode as a **penalty** for being near the edge, not a reward. Low weight — it is largely subsumed by rows 1–4. |
| **9** | **Colour-class (checkerboard) parity** | a1k0n implemented a checkerboard count following *"dmj's mostly useless idea"* — counting red/black squares separately to find territory that can never be occupied because of colour surplus. He explicitly rates it as marginal in Tron. | **Derived, not from literature — flagged as ours:** the 7×7 grid is bipartite, so every non-STAY move flips colour class. If the cop and thief occupy the *same* colour class when the cop is to move, the cop physically cannot capture that turn (it must move to the opposite class). Only STAY breaks this, and both sides have STAY, so it is a tempo/zugzwang fight rather than a free win. Cheap to compute (1 XOR) and worth a small bonus term. **No source found** for this parity argument stated for Cops-and-Robbers on bipartite boards. |

**Feature we expected to find and did not:** a published, ranked ablation of evader features
for *graph* Cops-and-Robbers. **No source found.** Everything ranked above comes from either
(a) a proof, or (b) one competitive-AI post-mortem with fitted weights. Treat the ordering as
"best available evidence", not as a validated benchmark.

---

### 2.4 Q1d — Search from the evader's side: survive-to-deadline is a *safety game*

#### 2.4.1 The objective has a name, and it changes the algorithm

"Survive N steps" is not a scoring objective — it is a **safety objective**, the dual of a
reachability objective. Source: E. Grädel, W. Thomas and T. Wilke (eds.), *Automata, Logics,
and Infinite Games: A Guide to Current Research*, LNCS 2500, Springer, 2002 (the standard
reference; see the chapters on infinite games on finite graphs). Established facts we can use:

- Reachability/safety games on finite graphs are **memorylessly determined**: from every
  state either the reach player or the safe player wins, with a strategy that depends only
  on the *current state*, not on the history.
- They are solved exactly in **linear time in the number of edges** by **attractor
  computation** (backward induction from the target set to a fixpoint).

**Why this matters concretely for our thief.** Freeze the barrier set. The remaining game
state is `(cop cell, thief cell, side to move)` = 49 × 49 × 2 = **4 802 states**, with ≤ 5
moves each — roughly 24 000 edges. A full attractor computation over that is *microseconds*
in pure Python and yields the **exact** set of positions from which the cop can force capture
with unlimited time. Add a "turns remaining" dimension (0…35) and it is 49 × 49 × 2 × 36 =
**172 872 states** — still small enough to solve once per barrier change (at most 14 times per
game), though not once per 50 ms move.

This is the single highest-leverage engineering recommendation in this document: **our thief
can play *provably optimally* against the no-more-barriers subgame** rather than heuristically.
The only genuinely hard part of the game is anticipating *future* barriers, which is where
search and heuristics belong. (Foundational precedent for solving a finite game by backward
induction: E. Zermelo, "Über eine Anwendung der Mengenlehre auf die Theorie des Schachspiels",
Proc. Fifth Congress of Mathematicians, Cambridge, 1913.)

#### 2.4.2 Minimax/alpha-beta vs MCTS — the literature is unambiguous for *this* domain

- **R. Ramanujan, A. Sabharwal, B. Selman, "On Adversarial Search Spaces and Sampling-Based
  Planning", ICAPS 2010** (<https://ojs.aaai.org/index.php/ICAPS/article/view/13437>; follow-up
  arXiv:1203.4011). Domains rich in **shallow traps** (levels ~3–7) are exactly where **UCT/MCTS
  underperforms minimax**: MCTS scores the trapped move as near-best and wastes samples deep in
  the tree, while alpha-beta at depth ≥ k finds the refutation. Chess is trap-rich; Go is not.
- Our game with permanently-deleted cells is **structurally trap-rich** — a barrier sequence
  that seals a chamber *is* a shallow trap. So we are in the Chess-like regime.
- Counter-evidence, for balance: **T. Pepels, M. H. M. Winands, M. Lanctot, "Real-Time Monte
  Carlo Tree Search in Ms Pac-Man", *IEEE Trans. Computational Intelligence and AI in Games*
  6(3):245–257, 2014** (<https://ieeexplore.ieee.org/document/6731713/>). Ms Pac-Man is a real
  evader-with-a-deadline domain and MCTS works well there — but only with heavy
  domain-specific enhancements (variable-depth tree, a *separate* survival reward channel
  distinct from the score channel, tree reuse, safe-move enforcement). Note their explicit
  framing: the agent has **two subgoals, surviving and scoring**, handled separately.
- a1k0n's Tron post-mortem adds the practical warning that applies to both: *"a better
  evaluation heuristic will always beat deeper minimax searches"* — and that a deep search on
  a bad evaluation is "self-deluded about what its opponent is actually going to do".

**Recommendation for the thief: iterative-deepening alpha-beta, not MCTS.** MCTS would also
be hard to make deterministic-given-a-seed *and* fit 50 ms of pure Python; alpha-beta with a
transposition table is naturally deterministic.

#### 2.4.3 Continuous-domain framing (for the report's related-work section only)

Reach-avoid / safety in continuous state spaces is solved with Hamilton-Jacobi reachability:
I. M. Mitchell, A. M. Bayen, C. J. Tomlin, "A time-dependent Hamilton–Jacobi formulation of
reachable sets for continuous dynamic games", *IEEE Transactions on Automatic Control*
50(7):947–957, 2005. The discrete analogue of the backward reachable set is precisely the
attractor of §2.4.1 — worth one sentence in the report to connect the two literatures, but
**not** worth implementing.

---

### 2.5 Q1e — Existing strong grid evaders (code)

| Project | What it is / approach | Why it is relevant | Licence |
|---|---|---|---|
| <https://github.com/a1k0n/tronbot> | Andy Sloane's winning 2010 Google AI Challenge Tron entry. C++. Alpha-beta + iterative deepening, Voronoi territory evaluation, articulation points / biconnected chamber tree, fitted linear eval `K1ΔN + K2ΔE`, greedy wall-following endgame fill. | **Closest existing strong player to our game** — Tron is a vertex-deletion pursuit game. Read the post-mortem plus `calc_articulations`. | **No licence declared** (checked via the GitHub API, 2026-08-02: `license: null`). Treat as a read-only reference — **cite the ideas, do not copy the code**. |
| <https://github.com/coreyabshire/Tron> | Another Google AI Challenge 2010 Tron bot, **Python**. | Python reference for the same ideas; much easier to read than the C++ entry. | **BSD-3-Clause** (GitHub API, 2026-08-02) — reusable with attribution if we ever wanted to. |
| <https://github.com/gorisanson/quoridor-ai> | Quoridor AI (JavaScript) based on MCTS. The README reports that **pure MCTS performed poorly** and only became strong after adding heuristics to the selection, expansion and simulation phases. | Quoridor is the best-known board game where one side **places walls** to lengthen the other's path — the closest *game* analogue to our barrier mechanic. Its reported MCTS failure supports §2.4.2. | **MIT** (GitHub API, 2026-08-02). |
| Academic: V. Massagué Respall, J. A. Brown, H. Aslam, "Monte Carlo Tree Search for Quoridor", 2018 | Published MCTS treatment of a wall-placing game. | Cite in related work for the barrier-placement branching-factor problem. | n/a (paper) |
| PettingZoo SISL `pursuit_v4` | Multi-agent gridworld pursuit-evasion RL environment. <https://pettingzoo.farama.org/environments/sisl/pursuit/> | Standard benchmark **environment**, not a strong evader. Useful only as a sanity-check harness; its evaders are learned, not strong baselines. | **MIT** (GitHub API on `Farama-Foundation/PettingZoo`, 2026-08-02). Note: pulling it in would add a heavy dependency — recommend **not** adding it. |

**No source found** for: a published, competition-grade *single-evader-vs-single-pursuer on a
small grid with pursuer-placed obstacles* reference implementation. Nothing matches our exact
game; Tron and Quoridor are the two nearest playable relatives.

---

### 2.6 Evader recommendation under our hard constraints

Everything below is pure Python 3.10+, no numpy required (a 49-cell board fits in a single
Python `int` used as a bitboard, which is both fast and deterministic).

**Layered policy, cheapest layer first — each layer is separately testable:**

1. **Hard safety filter (proof-backed, §2.1.1).** Discard any candidate move `w` with
   `N[w] \ N[c'] = ∅` for the cop's reachable cells `c'`. On the open board this alone is a
   winning strategy. ~20 lines.
2. **Exact safety-game solve of the frozen-barrier subgame (§2.4.1).** Recompute the
   attractor only when the barrier set changes (≤ 14 times per game), cache it, and refuse
   any move into a cop-win state. 4 802 states, unbounded-horizon version.
3. **Iterative-deepening alpha-beta (§2.4.2), 4–6 plies**, over `(thief move, cop move,
   barrier)`; **restrict barrier candidates to a top-k shortlist (k ≈ 6–8)** or the branching
   factor (≈49 barrier choices × 5 cop moves) makes depth impossible in 50 ms.
4. **Evaluation** = articulation-point chamber value + component size + Voronoi share, with
   a1k0n's ≈3.5:1 edge:node ratio as the starting weights; distance-to-cop only as a tiebreak.

**Realistic file split under the ≤150-code-line rule** (line counts are estimates from the
algorithms, not measured):

| File | Contents | Est. code lines |
|---|---|---|
| `thief/board_bits.py` | bitboard constants, neighbour masks, free-cell ops | 60–80 |
| `thief/reach.py` | BFS / multi-source BFS, distance maps, Voronoi split | 70–90 |
| `thief/components.py` | connected components + iterative Hopcroft–Tarjan articulation points | 90–120 |
| `thief/features.py` | feature extraction from a position | 60–80 |
| `thief/evaluate.py` | weighted linear evaluation + weights table | 40–60 |
| `thief/safety.py` | attractor / backward-induction solver over 4 802 states, cached | 80–110 |
| `thief/search.py` | iterative-deepening alpha-beta, transposition table, time budget | 100–140 |
| `thief/policy.py` | `decide()` — layer orchestration, deterministic tiebreak by seed | 50–70 |
| `thief/constants.py` | all numeric constants (satisfies the no-hardcoded-values rule) | 30–40 |

Nine files, none near the limit. Recursive Tarjan **must** be written iteratively — 49 cells
is fine for recursion depth but an explicit stack is easier to keep under the line limit and
easier to test. Determinism: sort candidate moves by a fixed cell ordering and break ties with
a seeded PRNG drawn once at construction, never at move time.

**A language model is not involved anywhere in the above** — every layer is a deterministic
algorithm, satisfying the hard disqualification rule.

---

## 3. PURSUER

### 3.1 Q2a — Closest published variant to the barrier mechanic

**Direct answer to the brief's challenge: we dug harder, and there is still no exact match.**
We found **no published Cops-and-Robbers variant in which the *cop* permanently deletes
vertices under a global quota.** Searched and checked: vertex deletion, blocking pursuit,
Angel and Devil, Isolation, surrounding pursuit, damage number, cops-and-robbers with traps,
bridge-burning, edge-blocking search, node search, firefighter, seepage. What exists is
listed below in order of closeness.

| # | Variant | Source | How close it is |
|---|---|---|---|
| **1** | **Conway's Angel Problem** — the **Devil** may, on its turn, "add a block on any single square not containing the angel"; the Angel of power *k* then jumps up to *k* king-moves and may leap over blocks but not land on them. Angel wins by surviving forever. | J. H. Conway, "The Angel Problem", in *Games of No Chance*, MSRI Publications 29, CUP, 1996, pp. 3–12, <https://library.slmath.org/books/Book29/files/conway.pdf> | **Structurally identical to our barrier mechanic** — arbitrary-cell permanent deletion, one per turn, not on the evader's cell. Differences: infinite board, unlimited quota, no chasing pursuer, and the evader loses by immobilisation rather than capture. |
| | **Results that transfer.** The Devil **beats** the Angel of **power 1**; the result is attributed to Berlekamp (early publications credited Conway), written up in §1.1 of M. Kutz's 2004 work. The Angel of **power ≥ 2 wins** on the infinite board: B. H. Bowditch, "The angel game in the plane", *Combin. Probab. Comput.* 16(3):345–362, 2007; A. Máthé, "The angel of power 2 wins", *Combin. Probab. Comput.* 16(3):363–374, 2007; O. Kloster, "A solution to the angel problem", *Theoret. Comput. Sci.* 389(1–2):152–161, 2007; P. Gács, "The Angel Wins", arXiv:0706.2817. | | **This is the strongest pro-cop result we found.** Our thief takes one *orthogonal* step — strictly weaker than a power-1 angel (which gets all 8 king moves). So a pure block-placer with an **unlimited** quota defeats our thief **even with no cop on the board**. The game is therefore decided entirely by the **quota (14)** and the **deadline (35)**, not by the mechanic. |
| **2** | **Cops, robber and traps** — a cop may place traps on vertices; the robber is caught if it steps on a trap. | N. E. Clarke and R. J. Nowakowski, "Cops, robber and traps", *Utilitas Mathematica* **60**:91–98, 2001. | Closest *quota-gadget-for-one-cop* result, and it is **negative**: **one cop plus any fixed number of traps is still not enough** on a graph that needs two cops without traps. **Do not assume our 14 barriers are automatically sufficient** — a superficially similar gadget provably is not. (Traps ≠ barriers: a trap captures, a barrier blocks and shrinks the graph. The negative result does not carry over as a proof, only as a warning.) |
| **3** | **Firefighter problem** — a defender permanently protects *f* vertices per turn against a fire spreading to all unprotected neighbours. | B. Hartnell, 1995 (originating); survey: S. Finbow and G. MacGillivray, "The Firefighter Problem: a survey of results, directions and questions", *Australasian J. Combinatorics* 43:57–77, 2009, <https://ajc.maths.uq.edu.au/pdf/43/ajc_v43_p057.pdf> | Same primitive (permanent vertex protection = deletion), different evader (a spreading set, not a token). **Quantitative threshold worth knowing:** on the infinite 2-D square grid, **one** protected vertex per turn is **not enough** to contain the fire; **two are necessary and sufficient** (Moeller & Wang; also proved by Fogarty, 2003). Our cop's rate is exactly the sub-threshold rate — the only reason it can still work is that a single thief token is far easier to contain than a spreading fire. |
| **4** | **Bridge-burning Cops and Robbers** — every edge the robber traverses is deleted. | "Cops, robbers, and burning bridges", arXiv:1812.09955; capture-time follow-up in *Discrete Applied Mathematics*, 2022. | Deletion is present but it is **edge** deletion driven by the **robber**, not cop-chosen vertex deletion. Useful only as a citation that graph-shrinking variants are a studied family. |
| **5** | **Edge-blocking search / node search** — cops block a set of edges each round, robber moves along unblocked edges. | Described in "Capturing an Invisible Robber using Separators", arXiv:2509.05024 (survey of adjacent models). | Blocking is **temporary** and on edges. Closest "cop obstructs the graph" model we located. |
| **6** | **Damage number** | K. Cox and A. Sanaei, 2019; multi-robber extension arXiv:2205.06956 | Objective is inverted (robber damages, cop minimises damage). Not our game. |
| **7** | **Surrounding Cops and Robbers** | A. Burgess et al., "Cops that surround a robber", arXiv:1910.14200 | Win condition = occupy every neighbour of the robber. Relevant conceptually — **a barrier is a permanent, free surrounder** — but the published results are about the surrounding cop number σ(G), not about deletions. |

**Nearest *playable* relatives** (better sources of engineering technique than the theory
above): **Tron light-cycles** (a vertex-deletion pursuit game; §2.3) and **Quoridor** (a board
game whose entire skill is wall placement to lengthen an opponent's path; §2.5).

---

### 3.2 Q2b — Is capture forceable with 14 barriers on 7×7 within 35 turns?

**There is no published answer. No source found.** What follows is a derivation from cited
results plus one computation we ran ourselves; it is labelled as such and is *not* a theorem
about our game.

**Step 1 — restate "cop wins" exactly.** By Nowakowski & Winkler 1983 the cop wins iff the
board becomes dismantlable, and by the triangle-free argument in §2.1.1 a triangle-free graph
is dismantlable iff it is a **forest**. Barriers cannot create triangles. Therefore:

> **The cop's exact objective is to make the thief's free connected component acyclic** (and
> to be inside it, with turns to spare).

**Step 2 — how many deletions does acyclicity cost?** That is the **decycling number**
(= minimum feedback vertex set) ∇(G). Sources: L. W. Beineke and R. C. Vandell, "Decycling
graphs", *J. Graph Theory* **25**(1):59–77, 1997 (introduces ∇ and treats grids);
grid bounds ⌈((m−1)(n−1)+1)/3⌉ ≤ ∇(P_m □ P_n) ≤ ⌈((m−1)(n−1)+1)/3⌉ + 1 as reported in the
literature on ∇(P_m □ P_n) (<https://www.researchgate.net/publication/267115021>).

- For 7×7: lower bound = ⌈(6·6+1)/3⌉ = ⌈37/3⌉ = **13**.
- **We verified the upper bound computationally** (randomised greedy over all 49 cells, scratch
  script, not project code): a 13-cell decycling set of the 7×7 grid exists, e.g.
  `(1,1) (1,3) (1,5) (2,2) (2,4) (3,1) (3,4) (3,6) (4,2) (4,5) (5,1) (5,3) (6,5)`.
  Combined with the cited lower bound, **∇(P₇□P₇) = 13**.
- Independent sanity check on the lower bound, from first principles: the 7×7 grid has
  n = 49, m = 84, cycle rank m−n+1 = 36, Δ = 4; each deleted vertex reduces the cycle rank by
  at most Δ−1 = 3, so ∇ ≥ 36/3 = 12 — consistent with, and weaker than, the cited 13.

**Step 3 — the quota is sufficient in the static sense, by exactly one barrier.**
13 ≤ **14**. This is a genuinely tight and non-obvious fact about our parameter set.

**Step 4 — but the turn budget probably is not.** Barriers are placed at ≤ 1 per turn, so a
full decycling costs ≥ 13 turns. After that the board is a forest of 36 cells and the cop must
still walk the thief down. Bound on that: the capture time of a cop-win graph of order n is at
most **n − 4** (A. Bonato, P. Golovach, G. Hahn, J. Kratochvíl, "The capture time of a graph",
*Discrete Mathematics* 309:5588–5595, 2009; refined by T. Gavenčiak, 2010; both quoted in
W. B. Kinnersley, "Bounds on the length of a game of Cops and Robbers", arXiv:1706.08379).
With n = 36 that is ≤ 32 rounds, and 13 + 32 = **45 > 35**. The naive "decycle the whole board,
then chase" plan **does not fit the deadline** in the worst case.

**Step 5 — what the cop must therefore do.** Decycle only the *thief's component* while
simultaneously shrinking it. The concrete target to aim the search at:

> at turn *T*, the thief's free component should be a tree of order *k* with *k* − 4 ≤ 35 − *T*.

**Step 6 — the honest gaps.**
- The thief resists: barriers presumably cannot be placed on the occupied cell (as in the
  Angel rules), so the cop must realise a decycling set *around a moving adversary*.
  **No source found** for an adversarial/online version of the decycling number.
- **No source found** for any bound or constructive strategy for one cop + a deletion quota on
  a finite grid with a deadline.
- **Recommendation:** answer this empirically for our exact parameters by exhaustive or
  self-play search and report the measured number, rather than claiming a theorem. The
  Angel-problem result (§3.1 row 1) says the mechanic is strong enough *in principle*; the
  Clarke–Nowakowski trap result says do not assume it *in practice*.

---

### 3.3 Q2c — What a barrier-placement policy should optimise

**First, the finding about our current policy.** Ours maximises BFS distance from the thief to
a fixed corner anchor. **No source found** — nothing in the pursuit-evasion or Cops-and-Robbers
literature proposes a fixed-anchor distance objective, and it is not a monotone quantity in any
published sense. Every sourced objective below dominates it.

Ranked, each with its source:

1. **Reduce the cycle rank of the thief's component to zero.** Proof-backed
   (Nowakowski & Winkler 1983 + §2.1.1 + §3.2). Cycle rank of a component = `E − V + 1`;
   a barrier on a degree-d cell of that component reduces it by `d − 1`. **Greedy rule:
   prefer barriers on degree-4 cells of the thief's component** — they buy 3 units of progress
   toward acyclicity, degree-2 cells buy 1. This is a one-line, exactly-computable objective
   with a theorem behind it, and it is the single change most likely to move our cop's win
   rate.
2. **Create/seize articulation points and seal the thief into the smaller chamber.**
   a1k0n's Tron post-mortem (<https://www.a1k0n.net/2010/03/04/google-ai-postmortem.html>)
   credits the articulation-point chamber evaluation as the contest-winning idea. Barrier
   placement is exactly "manufacture a cut vertex, then take it".
3. **Monotonically shrink the thief's Voronoi cell.** Z. Zhou, W. Zhang, J. Ding, H. Huang,
   D. M. Stipanović, C. J. Tomlin, "Cooperative pursuit with Voronoi partitions", *Automatica*
   72:64–72, 2016 — pursuers that never let the evader's generalised Voronoi cell grow achieve
   **guaranteed capture in finite time** (convex environment, equal speeds). Barriers make the
   monotonicity *free*, because deletions are permanent.
4. **Never create a hole — this is the counter-intuitive one and it is sourced.**
   L. J. Guibas, J.-C. Latombe, S. M. LaValle, D. Lin, R. Motwani, "Visibility-based
   pursuit-evasion in a polygonal environment", *Int. J. Computational Geometry and
   Applications* **9**(5):471–494, 1999: the number of pursuers needed is **θ(lg n)** for a
   simply-connected free space but **θ(√h + lg n)** for a free space with **h holes**.
   **More holes ⇒ harder pursuit.** A barrier dropped in open space creates an island the
   thief can orbit — i.e. a new cycle, the exact thing objective 1 is trying to destroy.
   **Implementable rule: only place a barrier that touches the board edge or an existing
   barrier, so the free region stays simply connected.** (Model caveat, stated honestly: this
   bound is for a *visibility* model with an unknown evader position; our game is
   perfect-information graph pursuit. The rule is still consistent with objective 1, which is
   proof-backed for our model.)
5. **Minimise the size of the thief's reachable free component.** a1k0n's endgame evaluation
   is `1000 · (my component size − opponent's component size)`; for us, the thief's component
   size versus turns remaining is the direct win condition of §3.2 Step 5.
6. **Keep the barrier wall contiguous / containment-shaped.** Firefighter analogy (§3.1 row 3):
   containment on a grid is achieved by closing a curve, and the sub-threshold protection rate
   means every barrier must contribute to the same curve. Scattered barriers waste the quota.

**Candidate generation (this is what makes the search affordable).** Do **not** consider all 49
cells. Restrict to cells that (a) are in the thief's current component, (b) are adjacent to an
existing barrier or to the board edge (objective 4), and (c) have degree ≥ 3 in that component
(objective 1). That typically leaves 6–12 candidates, which is what makes a 4–6 ply alpha-beta
fit inside 50 ms of pure Python.

---

### 3.4 Q2d — Territory/Voronoi, level-set and clearing methods; cornering

- **S. M. LaValle, *Planning Algorithms*, Cambridge University Press, 2006 — §12.4
  "Visibility-Based Pursuit-Evasion"**, with subsections **12.4.1 Problem Formulation**,
  **12.4.2 A Complete Algorithm**, **12.4.3 Other Variations**. Free online at
  <http://lavalle.pl/planning/>. The chapter's framing is the *information state*: the pursuer
  tracks the set of regions that are **contaminated** (may contain the evader) versus
  **cleared**, and searches in the space of contamination labellings. Our game is
  perfect-information, so the information-state machinery is not needed — but the
  **cleared/contaminated bookkeeping maps exactly onto "which free component can still contain
  the thief"**, which is what a barrier wall creates. This is the right way to present the cop
  in the report's related-work section.
- **Recontamination.** In polygonal environments recontamination is unavoidable in general
  (Guibas et al. 1999), whereas graph search can be made monotone. **In our game barriers make
  monotonicity structural** — a deleted cell is never recontaminated. That is the cop's single
  biggest structural advantage and it should be stated explicitly in the PRD.
- **Voronoi/territory partition:** Zhou et al., *Automatica* 72:64–72, 2016 (above), building
  on H. Huang, W. Zhang, J. Ding, D. M. Stipanović, C. J. Tomlin, "Guaranteed decentralized
  pursuit-evasion in the plane with multiple pursuers", CDC 2011.
- **Level-set / Hamilton-Jacobi reachability** (the continuous "clearing" formalism):
  I. M. Mitchell, A. M. Bayen, C. J. Tomlin, *IEEE Trans. Automatic Control* 50(7):947–957,
  2005. Discrete analogue = the attractor of §2.4.1. Cite, do not implement.
- **Cornering and wall-pinning.** The sourced content is thinner than the brief hopes:
  - Besicovitch's lion-and-man result (Littlewood, *A Mathematician's Miscellany*, 1953)
    establishes that the *boundary is bad for the evader*, hence good for the pursuer to drive
    toward — but it is a continuous-domain result.
  - Aigner & Fromme 1984's **guarded shortest path** is the canonical published pinning
    device: a cop that guards a path permanently denies it to the robber, and the planar
    3-cop proof is repeated territory-halving by guarded paths. **A barrier line is a guarded
    path that costs zero cop-time** — this is the cleanest one-sentence justification for the
    whole barrier mechanic and belongs in the PRD.
  - Luccio & Pagli, arXiv:1708.08255, on grids vs tori: grid boundary and corner vertices have
    low degree, which is precisely what makes them exploitable.
  - **No source found** for a formal "wall-pinning" or "cornering" strategy for a single
    pursuer on a finite grid with pursuer-placed obstacles.

---

### 3.5 Pursuer recommendation under our hard constraints

Same layered structure as the thief, sharing a **library** (not runtime state — the cop and
thief remain separate processes with no shared game-state object, per the project rules).

1. **Barrier candidate filter** (§3.3): in-thief-component ∧ (touches edge or existing barrier)
   ∧ degree ≥ 3. Reduces branching from 49 to ~6–12.
2. **Objective**: primary = cycle rank of the thief's component; secondary = thief component
   size; tertiary = Voronoi share; tiebreak = BFS distance cop→thief. Replace the fixed-corner
   anchor entirely.
3. **Search**: iterative-deepening alpha-beta over `(cop move, barrier choice, thief move)`,
   4–6 plies, transposition table keyed on `(cop, thief, barrier bitboard, side)`.
4. **Endgame switch**: once the thief's component is acyclic, drop the barrier logic and run
   the exact tree-chase (walk the unique path toward the thief); by Bonato et al. 2009 this
   terminates in ≤ n−4 rounds and is trivially correct.

**Realistic file split under the ≤150-code-line rule** (estimates):

| File | Contents | Est. code lines |
|---|---|---|
| `common/board_bits.py` | bitboard board representation, neighbour masks (shared library) | 60–80 |
| `common/reach.py` | BFS, distance maps, Voronoi split (shared library) | 70–90 |
| `common/components.py` | components + iterative articulation points (shared library) | 90–120 |
| `police/cycle_rank.py` | cycle rank of a component, per-cell reduction value | 50–70 |
| `police/barrier_candidates.py` | candidate filter incl. the no-new-hole test | 60–80 |
| `police/evaluate.py` | weighted objective | 50–70 |
| `police/search.py` | iterative-deepening alpha-beta + transposition table | 100–140 |
| `police/endgame.py` | acyclic-component tree chase | 40–60 |
| `police/policy.py` | `decide()` orchestration, deterministic tiebreaks | 50–70 |
| `police/constants.py` | all numeric constants | 30–40 |

**numpy is not required.** A 49-cell board is one Python `int`; `int.bit_count()` (3.10+) gives
population counts, and neighbour expansion is a handful of shifts and masks. Justify numpy only
if profiling shows the attractor solve (§2.4.1) misses the budget — and even then, precomputing
it once per barrier change avoids the need.

**No language model is involved in any decision** — every layer above is a deterministic
algorithm, satisfying the hard disqualification rule.

---

## 4. No source found

Everything in this list was searched for and **not** found. None of these should be asserted
in the PRD or the report as established.

1. **A Cops-and-Robbers variant in which the *cop* permanently deletes vertices under a
   global quota.** Searched: vertex deletion, blocking pursuit, Angel and Devil, Isolation,
   surrounding pursuit, damage number, cops-and-robbers with traps, bridge-burning,
   edge-blocking search, node search, firefighter, seepage. The Angel Problem is the closest
   *mechanic*; nothing combines it with a chasing pursuer, a finite board, a quota and a
   deadline. **This is a genuine gap and it is worth one paragraph in our report** — our game
   is a small original variant, not a re-implementation of a known one.
2. **Any bound or constructive strategy for "1 cop + 14 vertex deletions on 7×7, capture
   within 35 turns".** Nothing. §3.2 is our own derivation from cited pieces.
3. **An adversarial / online version of the decycling number** (building a feedback vertex set
   while an adversary occupies vertices you may not delete). Nothing found.
4. **A published, ranked ablation of *evader* evaluation features** for graph Cops-and-Robbers.
   The §2.3 ranking rests on one competitive-AI post-mortem plus proofs, not on a benchmark.
5. **Any support for a fixed-anchor distance objective** (our current barrier policy:
   maximise BFS distance from thief to a fixed corner). No source proposes anything like it.
6. **A quantitative "region smaller than X cells is lost" threshold** for an evader on a grid.
   The only exact criterion we found is the acyclicity/tree criterion (§2.2 item 1).
7. **The colour-class parity argument of §2.3 row 9** stated in the Cops-and-Robbers
   literature for bipartite boards. It is derived here; a1k0n's checkerboard count is the only
   precedent and he rates it marginal.
8. **A formal wall-pinning / cornering strategy for a single pursuer on a finite grid with
   pursuer-placed obstacles.** Only the continuous-domain (Besicovitch) and guarded-path
   (Aigner–Fromme) analogues exist.
9. **A competition-grade reference implementation** of single-evader-vs-single-pursuer on a
   small grid with pursuer-placed obstacles. Tron and Quoridor are the nearest relatives.
10. **A licence for `a1k0n/tronbot`.** The GitHub API reports none, so the code is
    all-rights-reserved by default; the *post-mortem article* may be cited freely, the code
    may not be copied.
11. **Discussion of finite-board variants of the Angel Problem** — the standard references
    treat the infinite board only.

**Also flagged, not a gap but an error to fix:** the brief attributes the cop-number and
capture-time formulas to arXiv:1708.08255. That paper (Luccio & Pagli, *Cops and robber on
grids and tori*) proves neither. See §1 for the correct attributions.

---

## 5. Bibliography

**Cops and Robbers — theory**

- A. Quilliot, thèse de 3e cycle, Université de Paris VI, 1978. (Independent characterisation
  of cop-win graphs.)
- R. Nowakowski, P. Winkler, "Vertex-to-vertex pursuit in a graph", *Discrete Mathematics*
  43(2–3):235–239, 1983. <https://doi.org/10.1016/0012-365X(83)90160-7>
- M. Aigner, M. Fromme, "A game of cops and robbers", *Discrete Applied Mathematics*
  8(1):1–12, 1984. <https://doi.org/10.1016/0166-218X(84)90073-8>
- S. Neufeld, R. Nowakowski, "A game of cops and robbers played on products of graphs",
  *Discrete Mathematics* 186(1–3):253–268, 1998.
  <https://www.sciencedirect.com/science/article/pii/S0012365X97001659>
- N. E. Clarke, R. J. Nowakowski, "Cops, robber and traps", *Utilitas Mathematica* 60:91–98,
  2001.
- A. Bonato, P. Golovach, G. Hahn, J. Kratochvíl, "The capture time of a graph", *Discrete
  Mathematics* 309:5588–5595, 2009. (Capture time of a cop-win graph ≤ n−4; see also
  T. Gavenčiak, 2010.)
- A. Mehrabian, "The capture time of grids", arXiv:1008.4424, 2010; *Discrete Mathematics*
  311(1):102–105, 2011. <https://arxiv.org/abs/1008.4424>
- A. Bonato, R. Nowakowski, *The Game of Cops and Robbers on Graphs*, AMS Student Mathematical
  Library vol. 61, 2011.
- W. B. Kinnersley, "Bounds on the length of a game of Cops and Robbers", arXiv:1706.08379.
- F. Luccio, L. Pagli, "Cops and robber on grids and tori", arXiv:1708.08255, 2017 (rev. 2019).
  <https://arxiv.org/abs/1708.08255>
- "Cops, robbers, and burning bridges", arXiv:1812.09955.
- A. Burgess et al., "Cops that surround a robber", arXiv:1910.14200.
- K. Cox, A. Sanaei, damage number, 2019; multi-robber extension arXiv:2205.06956.
- "Capturing an Invisible Robber using Separators", arXiv:2509.05024. (Edge-blocking / node
  search models.)

**Graph structure used in the derivations**

- L. W. Beineke, R. C. Vandell, "Decycling graphs", *Journal of Graph Theory* 25(1):59–77,
  1997. <https://onlinelibrary.wiley.com/doi/abs/10.1002/(SICI)1097-0118(199705)25:1%3C59::AID-JGT4%3E3.0.CO;2-H>
- "The decycling number of P_m □ P_n" (grid bounds
  ⌈((m−1)(n−1)+1)/3⌉ ≤ ∇ ≤ ⌈((m−1)(n−1)+1)/3⌉+1).
  <https://www.researchgate.net/publication/267115021_The_decycling_number_of_P_m_P_n>
- Feedback Vertex Set Number, Wolfram MathWorld (standard bound
  ∇ ≥ (m−n+1)/(Δ−1)). <https://mathworld.wolfram.com/FeedbackVertexSetNumber.html>

**Blocking / deletion games**

- J. H. Conway, "The Angel Problem", in *Games of No Chance*, MSRI Publications 29, CUP, 1996,
  pp. 3–12. <https://library.slmath.org/books/Book29/files/conway.pdf>
- M. Kutz, 2004 (§1.1 attributes the power-1 Devil win to Berlekamp).
- B. H. Bowditch, "The angel game in the plane", *Combin. Probab. Comput.* 16(3):345–362, 2007.
- A. Máthé, "The angel of power 2 wins", *Combin. Probab. Comput.* 16(3):363–374, 2007.
- O. Kloster, "A solution to the angel problem", *Theoret. Comput. Sci.* 389(1–2):152–161, 2007.
  <https://www.link.cs.cmu.edu/15859-s11/notes/Angel.pdf>
- P. Gács, "The Angel Wins", arXiv:0706.2817, 2007.
- S. Finbow, G. MacGillivray, "The Firefighter Problem: a survey of results, directions and
  questions", *Australasian J. Combinatorics* 43:57–77, 2009.
  <https://ajc.maths.uq.edu.au/pdf/43/ajc_v43_p057.pdf> (Contains the Moeller–Wang and Fogarty
  results: 2 firefighters per turn necessary and sufficient on the infinite 2-D grid.)

**Robotics / continuous pursuit-evasion**

- R. Isaacs, *Differential Games*, Wiley, 1965.
- J. E. Littlewood, *A Mathematician's Miscellany*, Methuen, 1953 (reissued as *Littlewood's
  Miscellany*, ed. B. Bollobás, CUP, 1986) — Rado's lion-and-man problem and Besicovitch's
  evasion strategy.
- L. J. Guibas, J.-C. Latombe, S. M. LaValle, D. Lin, R. Motwani, "Visibility-based
  pursuit-evasion in a polygonal environment", *Int. J. Computational Geometry and
  Applications* 9(5):471–494, 1999.
- I. M. Mitchell, A. M. Bayen, C. J. Tomlin, "A time-dependent Hamilton–Jacobi formulation of
  reachable sets for continuous dynamic games", *IEEE Trans. Automatic Control* 50(7):947–957,
  2005.
- S. M. LaValle, *Planning Algorithms*, Cambridge University Press, 2006 — §12.4
  Visibility-Based Pursuit-Evasion (12.4.1–12.4.3). <http://lavalle.pl/planning/>
- H. Huang, W. Zhang, J. Ding, D. M. Stipanović, C. J. Tomlin, "Guaranteed decentralized
  pursuit-evasion in the plane with multiple pursuers", CDC 2011.
- Z. Zhou, W. Zhang, J. Ding, H. Huang, D. M. Stipanović, C. J. Tomlin, "Cooperative pursuit
  with Voronoi partitions", *Automatica* 72:64–72, 2016.
  <https://www.sciencedirect.com/science/article/abs/pii/S0005109816301911>
- "An Introduction to Pursuit-Evasion Differential Games", arXiv:2003.05013.

**Search, games and safety objectives**

- E. Zermelo, "Über eine Anwendung der Mengenlehre auf die Theorie des Schachspiels",
  Proc. Fifth Congress of Mathematicians, Cambridge, 1913. (Backward induction.)
- E. Grädel, W. Thomas, T. Wilke (eds.), *Automata, Logics, and Infinite Games: A Guide to
  Current Research*, LNCS 2500, Springer, 2002. (Safety/reachability games; memoryless
  determinacy; linear-time attractor computation.)
- R. Ramanujan, A. Sabharwal, B. Selman, "On Adversarial Search Spaces and Sampling-Based
  Planning", ICAPS 2010. <https://ojs.aaai.org/index.php/ICAPS/article/view/13437>;
  follow-up arXiv:1203.4011.
- T. Pepels, M. H. M. Winands, M. Lanctot, "Real-Time Monte Carlo Tree Search in Ms Pac-Man",
  *IEEE Trans. Computational Intelligence and AI in Games* 6(3):245–257, 2014.
  <https://ieeexplore.ieee.org/document/6731713/>
- V. Massagué Respall, J. A. Brown, H. Aslam, "Monte Carlo Tree Search for Quoridor", 2018.

**Code and engineering write-ups**

- A. Sloane (a1k0n), "Google AI Challenge post-mortem", 2010.
  <https://www.a1k0n.net/2010/03/04/google-ai-postmortem.html> — code
  <https://github.com/a1k0n/tronbot> (no licence declared).
- <https://github.com/coreyabshire/Tron> — Python Tron bot, BSD-3-Clause.
- <https://github.com/gorisanson/quoridor-ai> — MCTS Quoridor AI, MIT.
- <https://pettingzoo.farama.org/environments/sisl/pursuit/> — PettingZoo `pursuit_v4`, MIT.
