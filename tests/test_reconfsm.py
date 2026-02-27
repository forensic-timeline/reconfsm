"""
Unit Tests for core reconfsm's FSM Simulator (fsm.py, pathfinding.py, graph.py)

Coverage:
- FSMachine construction
- load_machine_from_json()
- main() argument validation
- pathfinding_simulation()
- sort_and_display_paths()
- graph_simulation()

Usage:
    pytest tests/test_reconfsm.py -v
"""

import json
import os
import sys
import pytest
from reconfsm.fsm.fsm import FSMachine, load_machine_from_json, main
from reconfsm.fsm.pathfinding import pathfinding_simulation, sort_and_display_paths
from reconfsm.fsm.graph import graph_simulation



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_machine(states=None, transitions=None, initial=None, name="test_machine"):
    states = states or ["A", "B", "C"]
    transitions = transitions or [
        {"trigger": "go_b", "source": "A", "dest": "B"},
        {"trigger": "go_c", "source": "B", "dest": "C"},
    ]
    initial = initial or states[0]
    return FSMachine(name, states, transitions, {}, initial)


# ===========================================================================
# FSMachine
# ===========================================================================

class TestFSMachine:

    def test_stores_name(self):
        m = _make_machine(name="my_machine")
        assert m.name == "my_machine"

    def test_stores_states(self):
        m = _make_machine(states=["X", "Y", "Z"])
        assert m.states == ["X", "Y", "Z"]

    def test_stores_initial_state(self):
        m = _make_machine(states=["Start", "End"], initial="Start")
        assert m.initial_state == "Start"

    def test_stores_transitions_data(self):
        transitions = [{"trigger": "go", "source": "A", "dest": "B"}]
        m = _make_machine(states=["A", "B"], transitions=transitions)
        assert m.transitions_data == transitions

    def test_machine_starts_in_initial_state(self):
        m = _make_machine(states=["A", "B"], initial="A")
        assert m.state == "A"

    def test_registered_trigger_changes_state(self):
        m = _make_machine(
            states=["A", "B"],
            transitions=[{"trigger": "go_b", "source": "A", "dest": "B"}],
            initial="A",
        )
        m.go_b()
        assert m.state == "B"

    def test_multi_hop_transition_sequence(self):
        m = _make_machine()  # A -> B -> C
        m.go_b()
        m.go_c()
        assert m.state == "C"

    def test_machine_attribute_is_graph_machine(self):
        from transitions.extensions import GraphMachine
        m = _make_machine()
        assert isinstance(m.machine, GraphMachine)


# ===========================================================================
# load_machine_from_json()
# ===========================================================================

class TestLoadMachineFromJson:

    def test_loads_name(self, dummy_machine):
        assert dummy_machine.name == "web_activity_20250605_182216"

    def test_loads_initial_state(self, dummy_machine):
        assert dummy_machine.initial_state == "Search Engine google: bing"

    def test_loads_correct_number_of_states(self, dummy_machine):
        assert len(dummy_machine.states) == 11

    def test_loads_correct_number_of_transitions(self, dummy_machine):
        assert len(dummy_machine.transitions_data) == 11

    def test_returns_fsmachine_instance(self, dummy_machine):
        assert isinstance(dummy_machine, FSMachine)

    def test_machine_starts_in_initial_state(self, dummy_machine):
        assert dummy_machine.state == dummy_machine.initial_state

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_machine_from_json(str(tmp_path / "missing.json"))

    def test_invalid_json_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not valid json")
        with pytest.raises(json.JSONDecodeError):
            load_machine_from_json(str(bad))

    def test_minimal_valid_json(self, tmp_path):
        data = {
            "my_machine": [
                {
                    "name": "minimal",
                    "initial_state": "Start",
                    "states": ["Start", "End"],
                    "transitions": [{"trigger": "go", "source": "Start", "dest": "End"}],
                    "functions": {},
                }
            ]
        }
        p = tmp_path / "minimal.json"
        p.write_text(json.dumps(data))
        m = load_machine_from_json(str(p))
        assert m.name == "minimal"
        assert m.initial_state == "Start"


# ===========================================================================
# main() – argument validation
# ===========================================================================

class TestMain:

    def test_no_arguments_exits_with_code_1(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["fsm.py"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    def test_no_arguments_prints_usage(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["fsm.py"])
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_missing_json_file_exits_with_code_1(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr(sys, "argv", ["fsm.py", str(tmp_path / "nope.json"), "graph"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    def test_missing_json_file_prints_error(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr(sys, "argv", ["fsm.py", str(tmp_path / "nope.json"), "graph"])
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert "Error" in captured.out


# ===========================================================================
# pathfinding_simulation()
# ===========================================================================

class TestPathfindingSimulation:

    def test_finds_direct_path(self, capsys):
        m = _make_machine(
            states=["A", "B"],
            transitions=[{"trigger": "go_b", "source": "A", "dest": "B"}],
        )
        pathfinding_simulation(m, "B", 2)
        captured = capsys.readouterr()
        assert "B" in captured.out

    def test_finds_multi_hop_path(self, capsys):
        m = _make_machine()  # A -> B -> C
        pathfinding_simulation(m, "C", 3)
        captured = capsys.readouterr()
        assert "C" in captured.out
        assert "path" in captured.out.lower()

    def test_no_path_within_depth_zero(self, capsys):
        m = _make_machine() 
        pathfinding_simulation(m, "C", 0)
        captured = capsys.readouterr()
        assert "C" in captured.out

    def test_unreachable_state_reports_no_paths(self, capsys):
        m = _make_machine(
            states=["A", "B", "Isolated"],
            transitions=[{"trigger": "go_b", "source": "A", "dest": "B"}],
        )
        pathfinding_simulation(m, "Isolated", 5)
        captured = capsys.readouterr()
        assert "No paths found" in captured.out or "Isolated" in captured.out

    def test_wildcard_source_transition(self, capsys):
        m = _make_machine(
            states=["A", "B", "C"],
            transitions=[{"trigger": "emergency", "source": "*", "dest": "C"}],
        )
        pathfinding_simulation(m, "C", 1)
        captured = capsys.readouterr()
        assert "A" in captured.out or "B" in captured.out

    def test_dest_state_single_node_path_always_included(self, capsys):
        m = _make_machine(states=["A", "B"], transitions=[])
        pathfinding_simulation(m, "B", 5)
        captured = capsys.readouterr()
        assert "B" in captured.out



class TestSortAndDisplayPaths:

    def test_prints_path_count(self, capsys):
        paths = [["A", "B"], ["A", "B", "C"]]
        transition_map = {"A->B": ["go_b"], "B->C": ["go_c"]}
        sort_and_display_paths(paths, "C", 3, transition_map)
        captured = capsys.readouterr()
        assert "2" in captured.out

    def test_paths_sorted_by_length(self, capsys):
        paths = [["A", "B", "C"], ["A", "C"]]
        transition_map = {"A->B": ["t1"], "B->C": ["t2"], "A->C": ["t3"]}
        sort_and_display_paths(paths, "C", 3, transition_map)
        captured = capsys.readouterr()
        idx_short = captured.out.index("Path 1")
        idx_long = captured.out.index("Path 2")
        assert idx_short < idx_long

    def test_no_paths_prints_not_found(self, capsys):
        sort_and_display_paths([], "Z", 5, {})
        captured = capsys.readouterr()
        assert "No paths found" in captured.out

    def test_prints_triggers(self, capsys):
        paths = [["A", "B"]]
        transition_map = {"A->B": ["my_trigger"]}
        sort_and_display_paths(paths, "B", 2, transition_map)
        captured = capsys.readouterr()
        assert "my_trigger" in captured.out

    def test_multiple_triggers_shown_with_pipe(self, capsys):
        paths = [["A", "B"]]
        transition_map = {"A->B": ["trigger1", "trigger2"]}
        sort_and_display_paths(paths, "B", 2, transition_map)
        captured = capsys.readouterr()
        assert "|" in captured.out

    def test_single_node_path_shows_no_transitions(self, capsys):
        paths = [["B"]]
        sort_and_display_paths(paths, "B", 0, {})
        captured = capsys.readouterr()
        assert "Single node" in captured.out

    def test_unknown_trigger_shown_when_missing_from_map(self, capsys):
        paths = [["A", "B"]]
        sort_and_display_paths(paths, "B", 2, {})
        captured = capsys.readouterr()
        assert "unknown" in captured.out


class TestGraphSimulation:

    def _machine_with_mock_graph(self, mocker_or_mock, name="test_machine"):
        """Return a minimal FSMachine whose graphviz draw() is replaced with a Mock."""
        m = _make_machine(name=name)
        mock_graph = mocker_or_mock()
        m.machine.get_graph = lambda: mock_graph
        return m, mock_graph

    def test_creates_result_subdirectory(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        monkeypatch.chdir(tmp_path)
        m = _make_machine(name="my_machine")
        m.machine.get_graph = lambda: MagicMock()
        graph_simulation(m)
        assert (tmp_path / "result" / "my_machine").is_dir()

    def test_directory_named_after_machine(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        monkeypatch.chdir(tmp_path)
        m = _make_machine(name="custom_name")
        m.machine.get_graph = lambda: MagicMock()
        graph_simulation(m)
        assert (tmp_path / "result" / "custom_name").exists()

    def test_draw_called_once(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        monkeypatch.chdir(tmp_path)
        m = _make_machine(name="test_machine")
        mock_graph = MagicMock()
        m.machine.get_graph = lambda: mock_graph
        graph_simulation(m)
        mock_graph.draw.assert_called_once()

    def test_draw_called_with_dot_prog(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        monkeypatch.chdir(tmp_path)
        m = _make_machine(name="test_machine")
        mock_graph = MagicMock()
        m.machine.get_graph = lambda: mock_graph
        graph_simulation(m)
        _, kwargs = mock_graph.draw.call_args
        assert kwargs.get("prog") == "dot"

    def test_draw_called_with_visual_png_filename(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        import os
        monkeypatch.chdir(tmp_path)
        m = _make_machine(name="test_machine")
        mock_graph = MagicMock()
        m.machine.get_graph = lambda: mock_graph
        graph_simulation(m)
        args, _ = mock_graph.draw.call_args
        output_path = args[0]
        assert os.path.basename(output_path) == "visual.png"

    def test_prints_saved_path(self, tmp_path, monkeypatch, capsys):
        from unittest.mock import MagicMock
        monkeypatch.chdir(tmp_path)
        m = _make_machine(name="test_machine")
        m.machine.get_graph = lambda: MagicMock()
        graph_simulation(m)
        captured = capsys.readouterr()
        assert "Graph saved to" in captured.out

    def test_printed_path_contains_machine_name(self, tmp_path, monkeypatch, capsys):
        from unittest.mock import MagicMock
        monkeypatch.chdir(tmp_path)
        m = _make_machine(name="myfsm")
        m.machine.get_graph = lambda: MagicMock()
        graph_simulation(m)
        captured = capsys.readouterr()
        assert "myfsm" in captured.out