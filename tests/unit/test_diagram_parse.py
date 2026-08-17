"""Counter-controls for the 08-07 diagram checker: every finding it can report,
fired on purpose.

A checker that only ever runs against a document written to satisfy it proves
nothing -- `docs/PRD_gui.md` Sec4 records this repository's own case, a local-truth
gate that returned `violations: []` against a panel that leaked. So each test
here feeds `diagram_parse`/`diagram_graph` a block that is malformed in exactly
one way and asserts THAT problem is named, and each structural claim is paired
with the clean input it must stay silent about.
"""

from __future__ import annotations

from tests.unit.submission_gate_helpers import load

parse = load("diagram_parse")
graph_mod = load("diagram_graph")

_CLEAN = """<!-- diagram: sample -->
```mermaid
flowchart LR
    a["engine (facade)<br/>src/pursuit/sdk/engine.py"]
    b["turn loop<br/>src/pursuit/network/orchestrator.py"]
    a --> b
```
"""


def _only(text: str):
    blocks, problems = parse.extract_blocks("doc.md", text)
    assert not problems, problems
    assert len(blocks) == 1, blocks
    return blocks[0]


def test_a_clean_block_is_parsed_and_reports_nothing():
    block = _only(_CLEAN)
    assert block.kind == "flowchart"
    assert block.marker == "sample"
    assert parse.block_problems(block) == []


def test_the_parenthesis_inside_a_quoted_label_is_not_counted():
    """`["engine (facade)"]` is legal mermaid; a naive paren count rejects it."""
    assert "(" not in parse.strip_quoted('a["engine (facade)"]')
    assert parse.block_problems(_only(_CLEAN)) == []


def test_an_unclosed_fence_is_reported_rather_than_silently_dropped():
    blocks, problems = parse.extract_blocks("doc.md", "```mermaid\nflowchart LR\n  a --> b\n")
    assert blocks == []
    assert problems and "never closed" in problems[0]


def test_an_unknown_diagram_kind_is_reported():
    """`flowhcart` renders as a red error box on GitHub, not as a diagram."""
    block = _only(_CLEAN.replace("flowchart LR", "flowhcart LR"))
    assert any("unknown diagram kind" in note for note in parse.block_problems(block))


def test_an_unbalanced_bracket_is_reported():
    block = _only(_CLEAN.replace('src/pursuit/sdk/engine.py"]', 'src/pursuit/sdk/engine.py"'))
    assert any("unbalanced []" in note for note in parse.block_problems(block))


def test_an_odd_quote_count_is_reported():
    block = _only(_CLEAN.replace('a["engine', "a[engine"))
    assert any("odd number of quotes" in note for note in parse.block_problems(block))


def test_an_empty_block_is_a_problem_not_a_pass():
    block = _only("```mermaid\n\n```\n")
    assert parse.block_problems(block) == ["doc.md:1 empty mermaid block"]


def test_module_labels_are_extracted_from_inside_quoted_labels():
    assert parse.module_labels(_only(_CLEAN)) == (
        "src/pursuit/sdk/engine.py", "src/pursuit/network/orchestrator.py",
    )


def test_a_marker_only_binds_to_the_fence_that_follows_it():
    """Prose between the marker and a later fence breaks the binding, so a
    block cannot inherit a name written for a different diagram."""
    stray = "<!-- diagram: sample -->\n\nunrelated prose\n\n```mermaid\nflowchart LR\n  a --> b\n```\n"
    assert _only(stray).marker == ""


_PEERS = """flowchart TB
    subgraph POLICE["police"]
        p1["src/pursuit/network/tools.py"]
        p2["src/pursuit/sdk/engine.py"]
    end
    subgraph THIEF["thief"]
        t1["src/pursuit/network/tools.py"]
        t2["src/pursuit/sdk/engine.py"]
    end
    gui["src/pursuit/gui/live_app.py"]
    p1 -->|"MCP tool call"| t1
    t1 -->|"MCP tool call"| p1
    p2 --> gui
"""


def _peers(text: str):
    return graph_mod.parse_flowchart(tuple(text.splitlines()))


def test_symmetric_separate_peers_report_no_problem():
    assert graph_mod.peer_symmetry_problems(_peers(_PEERS), "POLICE", "THIEF") == []
    assert graph_mod.outside_every_container(_peers(_PEERS), "gui")


def test_a_one_way_edge_is_reported_as_a_missing_client_side():
    broken = _PEERS.replace('    t1 -->|"MCP tool call"| p1\n', "")
    problems = graph_mod.peer_symmetry_problems(_peers(broken), "POLICE", "THIEF")
    assert any("THIEF -> POLICE" in note for note in problems)


def test_peers_drawn_asymmetrically_are_reported():
    lopsided = _PEERS.replace('        t2["src/pursuit/sdk/engine.py"]\n', "")
    problems = graph_mod.peer_symmetry_problems(_peers(lopsided), "POLICE", "THIEF")
    assert any("not mirror images" in note for note in problems)


def test_a_node_drawn_inside_both_processes_is_reported_as_shared_state():
    """Rule 2: a state store drawn inside both processes depicts the leak."""
    shared = _PEERS.replace('        t1["src/pursuit/network/tools.py"]', '        p1["x"]\n        t1["src/pursuit/network/tools.py"]')
    problems = graph_mod.peer_symmetry_problems(_peers(shared), "POLICE", "THIEF")
    assert any("declared inside BOTH" in note for note in problems)


def test_a_gui_drawn_inside_an_agent_process_is_not_outside_every_container():
    """D-76: `tk.mainloop()` inside the agent blocks the loop the watchdog times."""
    inlined = _PEERS.replace(
        '    gui["src/pursuit/gui/live_app.py"]\n',
        "",
    ).replace('        p2["src/pursuit/sdk/engine.py"]',
              '        p2["src/pursuit/sdk/engine.py"]\n        gui["src/pursuit/gui/live_app.py"]')
    assert not graph_mod.outside_every_container(_peers(inlined), "gui")


def test_a_missing_subgraph_is_reported_rather_than_passing_vacuously():
    assert graph_mod.peer_symmetry_problems(_peers("flowchart TB\n"), "POLICE", "THIEF") == [
        "no subgraph named POLICE", "no subgraph named THIEF",
    ]
