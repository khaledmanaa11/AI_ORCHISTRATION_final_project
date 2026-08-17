"""The container diagram read as a GRAPH, so three disqualification-adjacent
claims stop being prose (08-07).

CLAUDE.md makes three architectural facts binding, and a diagram that depicts
any of them wrongly depicts a disqualification:

* the two agents are SYMMETRIC PEERS -- each is simultaneously server and
  client, with no strong side and no referee;
* they share NO RUNTIME STATE (rule 2) -- two processes, two config
  directories, two `AgentContext`s;
* the live GUI is a SEPARATE PROCESS fed by a published snapshot (D-76).

Prose can assert all three and drift; this module turns them into questions
about the drawn graph. Symmetry becomes "the two subgraphs name the same
modules, and an edge crosses in each direction". No shared state becomes "no
node id is declared inside both subgraphs". The GUI's separateness becomes
"the GUI node is declared outside both".

DELIBERATELY SMALL AND DELIBERATELY STRICT ABOUT SHAPE. It understands the
flowchart subset `docs/ARCHITECTURE.md` is written in -- one node declaration
per line, edges on their own lines -- and reports an empty parse rather than
guessing. `tests/unit/test_diagram_parse.py` proves each finding fires.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SUBGRAPH_OPEN = re.compile(r"^\s*subgraph\s+(\w+)")
BLOCK_END = re.compile(r"^\s*end\s*$")
NODE_DECL = re.compile(r"^\s*(\w+)[\[(]")
EDGE = re.compile(r"(\w+)\s*(?:-{2,3}>|-\.->|={2,3}>)\s*(?:\|[^|]*\|\s*)?(\w+)")

MODULE_LABEL = re.compile(r"src/pursuit/[\w./]*[\w]")


@dataclass
class Container:
    """One `subgraph ... end` region: its node ids and the modules it names."""

    name: str
    nodes: set[str] = field(default_factory=set)
    modules: set[str] = field(default_factory=set)


@dataclass
class Graph:
    """A parsed flowchart: subgraphs, free nodes, and directed edges."""

    containers: dict[str, Container] = field(default_factory=dict)
    free_nodes: set[str] = field(default_factory=set)
    edges: set[tuple[str, str]] = field(default_factory=set)

    def owner(self, node: str) -> str | None:
        """The subgraph a node belongs to, or None when it is free."""
        for name, container in self.containers.items():
            if node in container.nodes:
                return name
        return None

    def crosses(self, source: str, target: str) -> bool:
        """True when some edge runs from a node of *source* to one of *target*."""
        return any(
            self.owner(left) == source and self.owner(right) == target
            for left, right in self.edges
        )


def parse_flowchart(body: tuple[str, ...]) -> Graph:
    """Parse the flowchart subset used by `docs/ARCHITECTURE.md`.

    Node declarations inside a `subgraph` belong to it; anything declared
    outside every subgraph is a free node. `subgraph X["label"]` itself is not
    a node -- a label on the region, not a participant.
    """
    graph = Graph()
    stack: list[str] = []
    for line in body:
        opened = SUBGRAPH_OPEN.match(line)
        if opened:
            name = opened.group(1)
            graph.containers.setdefault(name, Container(name))
            stack.append(name)
            continue
        if BLOCK_END.match(line):
            if stack:
                stack.pop()
            continue
        declared = NODE_DECL.match(line)
        if declared:
            node = declared.group(1)
            modules = set(MODULE_LABEL.findall(line))
            if stack:
                graph.containers[stack[-1]].nodes.add(node)
                graph.containers[stack[-1]].modules |= modules
            else:
                graph.free_nodes.add(node)
            continue
        graph.edges |= set(EDGE.findall(line))
    return graph


def peer_symmetry_problems(graph: Graph, left: str, right: str) -> list[str]:
    """Every way the drawn peers fail to be symmetric, separate processes."""
    problems: list[str] = []
    for name in (left, right):
        if name not in graph.containers:
            problems.append(f"no subgraph named {name}")
    if problems:
        return problems
    one, two = graph.containers[left], graph.containers[right]
    shared = one.nodes & two.nodes
    if shared:
        problems.append(f"node ids declared inside BOTH peer processes: {sorted(shared)}")
    if not one.modules or not two.modules:
        problems.append("a peer process names no src/pursuit module at all")
    elif one.modules != two.modules:
        problems.append(
            f"the peers are not mirror images -- only in {left}: "
            f"{sorted(one.modules - two.modules)}; only in {right}: "
            f"{sorted(two.modules - one.modules)}"
        )
    for source, target in ((left, right), (right, left)):
        if not graph.crosses(source, target):
            problems.append(f"no edge runs {source} -> {target}: the peers are not both clients")
    return problems


def outside_every_container(graph: Graph, node: str) -> bool:
    """True when *node* is declared and belongs to no subgraph (D-76's GUI)."""
    return node in graph.free_nodes and graph.owner(node) is None
