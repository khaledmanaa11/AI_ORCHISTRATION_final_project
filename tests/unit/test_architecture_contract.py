"""`docs/ARCHITECTURE.md` held to the three facts CLAUDE.md makes binding
(08-07).

NOTHING TESTS PROSE, WHICH IS WHY THIS FILE EXISTS. In one night this project
found a README describing a withdrawn Q-learning agent, a docstring calling the
live opponent kernel "our own reconstruction", a `.gitignore` comment asserting
the opposite of the tree, and a documented command deleted in `f3d9847`. A
diagram drifts the same way and is read first. Every assertion below fails
against the document as it stood before 08-07 -- most of them because it did
not exist.

The three claims a wrong diagram would turn into a depicted disqualification:
symmetric peers (each simultaneously server and client), no shared runtime
state (rule 2), and the GUI as a separate process (D-76). Each is asserted
about the drawn GRAPH, not about a sentence.
"""

from __future__ import annotations

from tests.unit.doc_citation_helpers import cited_paths, unresolved_citations
from tests.unit.submission_gate_helpers import load

parse = load("diagram_parse")
graph_mod = load("diagram_graph")
check = load("check_diagrams")
common = load("submission_common")

ARCHITECTURE = "docs/ARCHITECTURE.md"
#: The six diagrams 08-07 owes: C4's four levels, deployment, and the
#: four-phase commit-reveal exchange.
REQUIRED = (
    "c4-context", "c4-container", "c4-component", "c4-code",
    "deployment", "commit-reveal",
)
POLICE, THIEF = "POLICE", "THIEF"


def _blocks() -> dict:
    text = common.read_tracked(ARCHITECTURE)
    blocks, problems = parse.extract_blocks(ARCHITECTURE, text)
    assert problems == [], problems
    return parse.by_marker(blocks)


def test_the_architecture_document_is_tracked():
    assert common.is_tracked(ARCHITECTURE)


def test_all_six_required_diagrams_are_present_and_marked():
    assert set(REQUIRED) <= set(_blocks()), sorted(_blocks())


def test_every_mermaid_block_in_every_tracked_doc_is_well_formed():
    """A block with a syntax error renders as a red error box on GitHub."""
    blocks, problems, unresolved = check.collect()
    assert len(blocks) >= len(REQUIRED), f"only {len(blocks)} blocks scanned"
    assert problems == [], problems
    assert unresolved == [], unresolved


def test_the_label_resolution_is_not_vacuous():
    """A run that resolved no label would pass this file having judged nothing."""
    blocks, _, _ = check.collect()
    labels = {label for block in blocks for label in parse.module_labels(block)}
    assert len(labels) >= 20, sorted(labels)
    assert all(check._resolves(label) for label in labels)


def test_the_two_agents_are_drawn_as_symmetric_separate_peers():
    """Symmetry, and rule 2's process separation, read off the container graph."""
    container = graph_mod.parse_flowchart(_blocks()["c4-container"].body)
    assert graph_mod.peer_symmetry_problems(container, POLICE, THIEF) == []


def test_each_peer_is_drawn_as_both_a_server_and_a_client():
    """`@mcp.tool` handlers AND calls into the opponent, on both sides."""
    container = graph_mod.parse_flowchart(_blocks()["c4-container"].body)
    for name in (POLICE, THIEF):
        modules = container.containers[name].modules
        assert "src/pursuit/network/tools.py" in modules, modules
        assert "src/pursuit/network/peer_runtime.py" in modules, modules


def test_no_referee_or_shared_state_node_is_drawn_between_the_peers():
    """A node inside both processes would depict the rule-2 leak."""
    container = graph_mod.parse_flowchart(_blocks()["c4-container"].body)
    police = container.containers[POLICE].nodes
    thief = container.containers[THIEF].nodes
    assert police and thief and not (police & thief)


def test_the_live_gui_is_drawn_outside_both_agent_processes():
    """D-76: `tk.mainloop()` blocks the loop the 60 s watchdog times, and a
    separate process cannot hold `ctx.state` at all."""
    container = graph_mod.parse_flowchart(_blocks()["c4-container"].body)
    assert graph_mod.outside_every_container(container, "gui")
    assert "src/pursuit/gui/live_app.py" not in container.containers[POLICE].modules
    assert "src/pursuit/gui/live_app.py" not in container.containers[THIEF].modules


def test_the_commit_reveal_sequence_draws_all_four_phases_in_order():
    body = "\n".join(_blocks()["commit-reveal"].body)
    positions = [body.find(phase) for phase in ("COMMIT", "ACK", "REVEAL", "FINAL_REVEAL")]
    assert all(position >= 0 for position in positions), positions
    assert positions == sorted(positions), positions


def test_the_commit_reveal_sequence_never_shows_the_nonce_before_final_reveal():
    """Rule 18 / SEC-04: the nonce stays local until game end."""
    body = _blocks()["commit-reveal"].body
    for index, line in enumerate(body):
        if "nonce" not in line.lower():
            continue
        earlier = "\n".join(body[: index + 1])
        assert "FINAL_REVEAL" in earlier or "local" in line.lower(), line


def test_the_prose_around_the_diagrams_cites_only_paths_that_exist():
    """The diagrams are label-checked; the deployment instructions are not,
    unless this asks. A runbook naming a deleted file is the `f3d9847` defect."""
    assert len(cited_paths(ARCHITECTURE)) >= 10, cited_paths(ARCHITECTURE)
    assert unresolved_citations(ARCHITECTURE) == []


def test_the_deployment_diagram_covers_two_tunnels_and_the_gmail_path():
    body = "\n".join(_blocks()["deployment"].body)
    assert body.count("ngrok") >= 2, body
    assert "gmail" in body.lower()
    assert "src/pursuit/services/reporting/gmail_sink.py" in body
