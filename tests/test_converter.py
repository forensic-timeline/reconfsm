"""
Unit Tests for CSV-to-State-Machine Converter

Tests for converter.py covering:
- load_script()
- get_available_scripts()
- extract_states_and_transitions()
- generate_json()

Design note: converter.py uses module-level constants SCRIPTS_DIR and OUTPUT_DIR.
Tests use monkeypatch to override these at the module level so the real
scripts directory is never required for isolation tests.

Usage:
    pytest tests/test_converter.py -v
"""

import csv
import json
import os
import textwrap

import pytest

import reconfsm.converter.converter as converter_module
from reconfsm.converter.converter import (
    load_script,
    get_available_scripts,
    extract_states_and_transitions,
    generate_json,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path, rows):
    """Write a list-of-dicts to a CSV file."""
    if not rows:
        with open(path, "w", newline="") as f:
            f.write("")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _make_script(scripts_dir, name, body):
    """Write a minimal extractor script into scripts_dir."""
    path = os.path.join(scripts_dir, f"{name}.py")
    with open(path, "w") as f:
        f.write(textwrap.dedent(body))
    return path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scripts_dir(tmp_path):
    """Temporary directory used as SCRIPTS_DIR."""
    d = tmp_path / "scripts"
    d.mkdir()
    return str(d)


@pytest.fixture
def output_dir(tmp_path):
    """Temporary directory used as OUTPUT_DIR."""
    d = tmp_path / "output"
    d.mkdir()
    return str(d)


@pytest.fixture(autouse=True)
def patch_scripts_dir(monkeypatch, scripts_dir):
    """Patch SCRIPTS_DIR in the converter module for every test."""
    monkeypatch.setattr(converter_module, "SCRIPTS_DIR", scripts_dir)

class TestLoadScript:

    def test_loads_valid_script_and_returns_function(self, scripts_dir):
        _make_script(scripts_dir, "dummy", """
            def dummy(row):
                return None
        """)
        fn = load_script("dummy")
        assert callable(fn)
        assert fn.__name__ == "dummy"

    def test_raises_file_not_found_for_missing_script(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_script("nonexistent_script")

    def test_raises_attribute_error_when_function_missing(self, scripts_dir):
        _make_script(scripts_dir, "no_func", """
            SOME_CONSTANT = 42
        """)
        with pytest.raises(AttributeError, match="must contain a function"):
            load_script("no_func")

    def test_loaded_function_is_callable_and_works(self, scripts_dir):
        _make_script(scripts_dir, "identity", """
            def identity(row):
                return row.get('x'), 'trigger', None
        """)
        fn = load_script("identity")
        result = fn({"x": "StateA"})
        assert result == ("StateA", "trigger", None)

    def test_function_name_matches_script_type(self, scripts_dir):
        _make_script(scripts_dir, "my_extractor", """
            def my_extractor(row):
                return None
        """)
        fn = load_script("my_extractor")
        assert fn.__name__ == "my_extractor"


class TestGetAvailableScripts:

    def test_returns_empty_list_when_scripts_dir_missing(self, monkeypatch):
        monkeypatch.setattr(converter_module, "SCRIPTS_DIR", "/nonexistent/path")
        assert get_available_scripts() == []

    def test_returns_script_names_without_extension(self, scripts_dir):
        _make_script(scripts_dir, "alpha", "def alpha(r): return None")
        _make_script(scripts_dir, "beta", "def beta(r): return None")
        scripts = get_available_scripts()
        assert "alpha" in scripts
        assert "beta" in scripts

    def test_excludes_dunder_files(self, scripts_dir):
        _make_script(scripts_dir, "__init__", "")
        _make_script(scripts_dir, "__utils__", "")
        _make_script(scripts_dir, "real_script", "def real_script(r): return None")
        scripts = get_available_scripts()
        assert "__init__" not in scripts
        assert "__utils__" not in scripts
        assert "real_script" in scripts

    def test_excludes_non_py_files(self, scripts_dir):
        open(os.path.join(scripts_dir, "readme.txt"), "w").close()
        open(os.path.join(scripts_dir, "data.csv"), "w").close()
        _make_script(scripts_dir, "valid", "def valid(r): return None")
        scripts = get_available_scripts()
        assert "readme" not in scripts
        assert "data" not in scripts

    def test_returns_list_type(self, scripts_dir):
        assert isinstance(get_available_scripts(), list)

    def test_empty_scripts_dir_returns_empty_list(self, scripts_dir):
        assert get_available_scripts() == []


class TestExtractStatesAndTransitions:

    def _make_extractor(self, mapping):
        """Return a plain extractor function using a dict mapping."""
        def extractor(row):
            return mapping.get(row.get("key"))
        extractor.__name__ = "web_activity"
        return extractor

    def test_basic_state_sequence(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [
            {"key": "a"},
            {"key": "b"},
            {"key": "c"},
        ])
        mapping = {
            "a": ("StateA", "go_b", None),
            "b": ("StateB", "go_c", None),
            "c": ("StateC", "done", None),
        }
        extractor = self._make_extractor(mapping)
        states, transitions = extract_states_and_transitions(csv_path, extractor)
        assert "StateA" in states
        assert "StateB" in states
        assert "StateC" in states

    def test_transitions_connect_sequential_states(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        mapping = {
            "a": ("StateA", "go_b", None),
            "b": ("StateB", "done", None),
        }
        extractor = self._make_extractor(mapping)
        _, transitions = extract_states_and_transitions(csv_path, extractor)
        assert ("StateA", "StateB", "done") in transitions

    def test_rows_returning_none_are_skipped(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [
            {"key": "a"},
            {"key": "skip"},
            {"key": "b"},
        ])
        mapping = {
            "a": ("StateA", "go", None),
            "b": ("StateB", "end", None),
        }
        extractor = self._make_extractor(mapping)
        states, transitions = extract_states_and_transitions(csv_path, extractor)
        assert "StateA" in states
        assert "StateB" in states
        assert ("StateA", "StateB", "end") in transitions

    def test_no_duplicate_states(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "a"}, {"key": "a"}])
        mapping = {"a": ("StateA", "loop", None)}
        extractor = self._make_extractor(mapping)
        states, _ = extract_states_and_transitions(csv_path, extractor)
        assert states.count("StateA") == 1

    def test_no_self_transitions_for_non_application_activity(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "a"}])
        mapping = {"a": ("StateA", "repeat", None)}
        extractor = self._make_extractor(mapping)
        _, transitions = extract_states_and_transitions(csv_path, extractor)
        assert ("StateA", "StateA", "repeat") not in transitions

    def test_application_activity_allows_self_loop(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "a"}])
        mapping = {"a": ("StateA", "repeat", None)}
        def application_activity(row):
            return mapping.get(row.get("key"))
        application_activity.__name__ = "application_activity"
        _, transitions = extract_states_and_transitions(csv_path, application_activity)
        assert ("StateA", "StateA", "repeat") in transitions

    def test_application_activity_starts_with_desktop_state(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}])
        def application_activity(row):
            return ("AppState", "launch_app", None)
        application_activity.__name__ = "application_activity"
        states, _ = extract_states_and_transitions(csv_path, application_activity)
        assert states[0] == "Desktop"

    def test_prev_overrides_previous_state(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        mapping = {
            "a": ("StateA", "go", "Override"),
            "b": ("StateB", "end", None),
        }
        extractor = self._make_extractor(mapping)
        _, transitions = extract_states_and_transitions(csv_path, extractor)
        assert ("Override", "StateA", "go") in transitions

    def test_transitions_are_sorted(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}, {"key": "c"}])
        mapping = {
            "a": ("A", "to_b", None),
            "b": ("B", "to_c", None),
            "c": ("C", "done", None),
        }
        extractor = self._make_extractor(mapping)
        _, transitions = extract_states_and_transitions(csv_path, extractor)
        assert transitions == sorted(transitions)

    def test_empty_csv_returns_empty_states_and_transitions(self, tmp_path):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "skip"}])
        extractor = self._make_extractor({})  # everything returns None
        states, transitions = extract_states_and_transitions(csv_path, extractor)
        assert states == []
        assert transitions == []


class TestGenerateJson:

    def _simple_extractor(self):
        def extractor(row):
            key = row.get("key")
            if key == "a":
                return "StateA", "to_b", None
            if key == "b":
                return "StateB", "done", None
            return None
        extractor.__name__ = "web_activity"
        return extractor

    def test_creates_output_subdirectory(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        generate_json(csv_path, output_dir, self._simple_extractor(), "web_activity")
        assert os.path.isdir(os.path.join(output_dir, "web_activity"))

    def test_creates_json_file(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        generate_json(csv_path, output_dir, self._simple_extractor(), "web_activity")
        subdir = os.path.join(output_dir, "web_activity")
        json_files = [f for f in os.listdir(subdir) if f.endswith(".json")]
        assert len(json_files) == 1

    def test_json_has_machine_key(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        generate_json(csv_path, output_dir, self._simple_extractor(), "myprefix")
        subdir = os.path.join(output_dir, "myprefix")
        json_file = os.listdir(subdir)[0]
        with open(os.path.join(subdir, json_file)) as f:
            data = json.load(f)
        assert "myprefix_machine" in data

    def test_json_contains_states(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        generate_json(csv_path, output_dir, self._simple_extractor(), "web_activity")
        subdir = os.path.join(output_dir, "web_activity")
        json_file = os.listdir(subdir)[0]
        with open(os.path.join(subdir, json_file)) as f:
            data = json.load(f)
        machine = data["web_activity_machine"][0]
        assert "StateA" in machine["states"]
        assert "StateB" in machine["states"]

    def test_json_contains_transitions(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        generate_json(csv_path, output_dir, self._simple_extractor(), "web_activity")
        subdir = os.path.join(output_dir, "web_activity")
        json_file = os.listdir(subdir)[0]
        with open(os.path.join(subdir, json_file)) as f:
            data = json.load(f)
        machine = data["web_activity_machine"][0]
        assert len(machine["transitions"]) >= 1

    def test_json_transition_has_required_fields(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        generate_json(csv_path, output_dir, self._simple_extractor(), "web_activity")
        subdir = os.path.join(output_dir, "web_activity")
        json_file = os.listdir(subdir)[0]
        with open(os.path.join(subdir, json_file)) as f:
            data = json.load(f)
        for t in data["web_activity_machine"][0]["transitions"]:
            assert "trigger" in t
            assert "source" in t
            assert "dest" in t

    def test_initial_state_is_first_state(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        generate_json(csv_path, output_dir, self._simple_extractor(), "web_activity")
        subdir = os.path.join(output_dir, "web_activity")
        json_file = os.listdir(subdir)[0]
        with open(os.path.join(subdir, json_file)) as f:
            data = json.load(f)
        machine = data["web_activity_machine"][0]
        assert machine["initial_state"] == machine["states"][0]

    def test_json_file_is_valid_json(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        generate_json(csv_path, output_dir, self._simple_extractor(), "web_activity")
        subdir = os.path.join(output_dir, "web_activity")
        json_file = os.path.join(subdir, os.listdir(subdir)[0])
        with open(json_file) as f:
            try:
                json.load(f)
            except json.JSONDecodeError:
                pytest.fail("Output file is not valid JSON")

    def test_prefix_used_in_filename(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "a"}, {"key": "b"}])
        generate_json(csv_path, output_dir, self._simple_extractor(), "myprefix")
        subdir = os.path.join(output_dir, "myprefix")
        json_files = os.listdir(subdir)
        assert any(f.startswith("myprefix_") for f in json_files)

    def test_empty_csv_produces_unknown_initial_state(self, tmp_path, output_dir):
        csv_path = str(tmp_path / "data.csv")
        _write_csv(csv_path, [{"key": "none"}])
        def noop(row):
            return None
        noop.__name__ = "web_activity"
        generate_json(csv_path, output_dir, noop, "web_activity")
        subdir = os.path.join(output_dir, "web_activity")
        json_file = os.path.join(subdir, os.listdir(subdir)[0])
        with open(json_file) as f:
            data = json.load(f)
        assert data["web_activity_machine"][0]["initial_state"] == "unknown"
